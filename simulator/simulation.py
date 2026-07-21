import yaml
import pandas as pd
from datetime import datetime, timezone
from pathlib import Path
from cryptosight.utils.logger import get_logger
from cryptosight.utils.db import (
    get_connection,
    fetch_ohlcv,
    create_simulations_schema_and_tables,
    clear_simulation_data,
    save_simulation_position,
    close_simulation_position,
    insert_simulation_ledger,
    upsert_simulation_stats,
)
from cryptosight.utils.metadata import (
    fetch_strategy_from_db,
    list_all_strategies,
)
from cryptosight.stats.metrices import compute_all_metrics


class SimulatorEngine:
    """
    Sequential Event-Driven Trading Simulator Engine.
    """

    def __init__(self, strategy_id: str = None, config_path: str = "config.yaml"):
        self.logger = get_logger("Simulator")
        self.current_dir = Path(__file__).resolve().parent
        self.config_path = self.current_dir / config_path

        # 1. Establish PostgreSQL Database connection
        self.conn = get_connection()

        # 2. Fetch strategy list from DB if not passed
        if not strategy_id:
            strategies = list_all_strategies(self.conn)
            if not strategies:
                raise ValueError("No strategies found in metadata.strategy_data DB!")
            strategy_id = strategies[0]

        self.strategy_id = strategy_id

        # 3. Fetch full strategy info from DB (exchange, symbol, target_tf, indicators_config, strategy_config)
        self.strategy_info = fetch_strategy_from_db(self.conn, self.strategy_id)
        if not self.strategy_info:
            raise ValueError(f"Strategy '{self.strategy_id}' not found in metadata.strategy_data!")

        # 4. Load simulator configuration — the ONLY source for execution settings
        self.sim_config = self.load_config()

        # DB strategy_config — the ONLY source for trading-rule settings
        strat_cfg = self.strategy_info.get("strategy_config", {})

        # ── Execution settings: config.yaml ONLY. Never mixed with DB strategy_config. ──
        self.initial_balance = float(self.sim_config.get("initial_balance"))
        self.balance = self.initial_balance
        self.commission_rate = float(self.sim_config.get("commission"))
        self.slippage_rate = float(self.sim_config.get("slippage"))

        pos_val = self.sim_config.get("position_size")
        if isinstance(pos_val, dict):
            pos_val = pos_val.get("value")
        self.pos_size_pct = float(pos_val)

        # Trade permissions from simulator config.yaml
        self.allow_long = bool(self.sim_config.get("allow_long"))
        self.allow_short = bool(self.sim_config.get("allow_short"))

        take_profit = strat_cfg.get("take_profit")
        stop_loss = strat_cfg.get("stop_loss")
        if take_profit is None or stop_loss is None:
            raise ValueError(f"Strategy '{self.strategy_id}' missing take_profit/stop_loss in DB strategy_config!")
        self.tp_pct = float(take_profit) / 100.0
        self.sl_pct = float(stop_loss) / 100.0

        # 6. Market date window: config.yaml first, else fallback to signals/strategy_config.yaml
        self.start_time = self.sim_config.get("start_time")
        self.end_time = self.sim_config.get("end_time")

        if not self.start_time or not self.end_time:
            market_yaml_path = self.current_dir.parent / "signals" / "strategy_config.yaml"
            if market_yaml_path.exists():
                with open(market_yaml_path, "r", encoding="utf-8") as f:
                    market_cfg = (yaml.safe_load(f) or {}).get("market", {})
                    self.start_time = self.start_time or market_cfg.get("start_time")
                    self.end_time = self.end_time or market_cfg.get("end_time")

        if not self.start_time or not self.end_time:
            raise ValueError(f"start_time / end_time missing for '{self.strategy_id}'!")

        # 7. Create/Verify DB tables for simulations schema
        create_simulations_schema_and_tables(self.conn, self.strategy_id)

        self.logger.info(f"SimulatorEngine initialized for strategy: [{self.strategy_id}]")

    def load_config(self) -> dict:
        """Loads simulator configuration from config.yaml."""
        if not self.config_path.exists():
            raise FileNotFoundError(f"Configuration file not found at: {self.config_path}")
        with open(self.config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f) or {}

    def generate_signals(self) -> pd.DataFrame:
        """
        Calculates signals at runtime using this strategy's DB indicators_config and strategy_config.
        Calls the master signals pipeline.
        """
        exchange = self.strategy_info.get("exchange")
        symbol = self.strategy_info.get("symbol")
        target_tf = self.strategy_info.get("target_timeframe")

        from cryptosight.signals.main import run_signals_pipeline
        strat_dict = {
            "exchange": exchange,
            "symbol": symbol,
            "timeframe": "1m",
            "target_timeframe": target_tf,
            "indicators_config": self.strategy_info.get("indicators_config"),
            "strategy_config": self.strategy_info.get("strategy_config"),
        }
        signals_df = run_signals_pipeline(
            strat_dict=strat_dict,
            market_overrides={
                "start_time": self.start_time,
                "end_time": self.end_time,
                "max_retries": 5,
                "retry_delay": 3,
            },
        )
        if signals_df is None or signals_df.empty:
            raise RuntimeError(
                f"[{self.strategy_id}] Signals pipeline returned empty — "
                "check indicators_config and strategy_config in DB."
            )
        return signals_df

    def fetch_data(self) -> tuple[pd.DataFrame, pd.DataFrame]:
        """
        Fetches resampled signals via generate_signals(), and fetches 1m OHLCV price data from DB.
        Returns (ohlcv_df, signals_df).
        """
        exchange = self.strategy_info.get("exchange")
        symbol = self.strategy_info.get("symbol")

        self.logger.info(f"[{self.strategy_id}] Generating signals...")
        signals_df = self.generate_signals()

        self.logger.info(f"[{self.strategy_id}] Fetching 1m OHLCV price data from DB...")
        ohlcv_df = fetch_ohlcv(self.conn, exchange, symbol, "1m", str(self.start_time), str(self.end_time))
        if ohlcv_df.empty:
            raise RuntimeError(f"No 1m OHLCV data found for {exchange.upper()} {symbol.upper()} in DB!")

        return ohlcv_df, signals_df

    def merge_data(self, ohlcv_df: pd.DataFrame, signals_df: pd.DataFrame) -> pd.DataFrame:
        """
        Left-joins resampled 1h signals onto complete 1m OHLCV price candles.
        1m candles with no matching 1h signal timestamp get signal = 0.
        """
        if ohlcv_df.empty:
            raise ValueError("OHLCV DataFrame is empty!")

        if signals_df.empty or "signal" not in signals_df.columns:
            return ohlcv_df.assign(signal=0)

        if ohlcv_df.index.tz is None:
            ohlcv_df.index = pd.to_datetime(ohlcv_df.index, utc=True)
        if isinstance(signals_df.index, pd.DatetimeIndex) and signals_df.index.tz is None:
            signals_df.index = pd.to_datetime(signals_df.index, utc=True)

        merged = ohlcv_df.join(signals_df[["signal"]], how="left")
        merged["signal"] = merged["signal"].fillna(0).astype(int)
        return merged

    # ─── Exit: Hard SL / TP ────────────────────────────────────────────────

    def check_exit_conditions(self, position: dict, high_price: float, low_price: float) -> tuple[float | None, str | None]:
        """
        Checks hard Take Profit (TP) and Stop Loss (SL) levels on 1m candles.
        Returns (exit_price, exit_reason) or (None, None).
        """
        direction = position["direction"]
        take_profit = position["take_profit"]
        stop_loss = position["stop_loss"]

        if direction == "Long":
            if low_price <= stop_loss and high_price >= take_profit:
                return stop_loss, "stop_loss"
            if low_price <= stop_loss:
                return stop_loss, "stop_loss"
            if high_price >= take_profit:
                return take_profit, "take_profit"
        else:  # Short
            if high_price >= stop_loss and low_price <= take_profit:
                return stop_loss, "stop_loss"
            if high_price >= stop_loss:
                return stop_loss, "stop_loss"
            if low_price <= take_profit:
                return take_profit, "take_profit"

        return None, None

    # ─── Signal Routing ─────────────────────────────────────────────────────

    def handle_signal(
        self,
        active_position: dict | None,
        signal: int,
        open_price: float,
        timestamp,
        trade_counter: int,
        completed_trades: list,
    ) -> tuple[dict | None, int]:
        """
        Signal router — called when SL/TP was NOT hit on the candle:
          - signal == 0: hold/do nothing
          - same direction signal: hold position
          - opposite direction signal: close active trade + open opposite trade
          - flat + signal: open new trade
        """
        if signal == 0:
            return active_position, trade_counter

        new_direction = "Long" if signal == 1 else "Short"

        if active_position is not None:
            current_direction = active_position["direction"]

            if new_direction == current_direction:
                self.logger.info(
                    f"[{self.strategy_id}] Signal {signal} ({new_direction}) matches "
                    f"open {current_direction} — holding."
                )
                return active_position, trade_counter

            self.logger.info(
                f"[{self.strategy_id}] Opposite signal {signal} — "
                f"closing {current_direction}, opening {new_direction}."
            )
            trade = self.close_position(active_position, open_price, "opposite_signal", timestamp)
            completed_trades.append(trade)
            active_position = None

        if (signal == 1 and self.allow_long) or (signal == -1 and self.allow_short):
            trade_counter += 1
            active_position = self.open_position(signal, open_price, timestamp, trade_counter)

        return active_position, trade_counter

    # ─── PnL Calculation ────────────────────────────────────────────────────

    def calculate_pnl(self, direction: str, entry_price: float, exit_price: float, quantity: float) -> dict:
        """Calculates gross PnL, commission, slippage, net PnL, and percentage PnL."""
        entry_val = entry_price * quantity
        exit_val = exit_price * quantity

        gross_pnl = (
            (exit_price - entry_price) * quantity if direction == "Long"
            else (entry_price - exit_price) * quantity
        )
        fee = (entry_val + exit_val) * self.commission_rate
        slippage = (entry_val + exit_val) * self.slippage_rate
        net_pnl = gross_pnl - fee - slippage
        perc_pnl = (net_pnl / entry_val) * 100.0 if entry_val > 0 else 0.0

        return {
            "gross_pnl": gross_pnl,
            "commission": fee,
            "slippage": slippage,
            "net_pnl": net_pnl,
            "perc_pnl": perc_pnl,
        }

    # ─── Position Lifecycle ─────────────────────────────────────────────────

    def open_position(self, signal: int, open_price: float, timestamp, trade_counter: int) -> dict:
        """
        Opens a new position.
        Calculates TP & SL levels using self.tp_pct & self.sl_pct from DB strategy_config.
        Persists active position state into DB table simulations.positions.
        """
        direction = "Long" if signal == 1 else "Short"
        entry_price = open_price
        quantity = (self.balance * (self.pos_size_pct / 100.0)) / entry_price

        take_profit = entry_price * (1.0 + self.tp_pct) if signal == 1 else entry_price * (1.0 - self.tp_pct)
        stop_loss = entry_price * (1.0 - self.sl_pct) if signal == 1 else entry_price * (1.0 + self.sl_pct)

        position = {
            "trade_id": f"T_{trade_counter}",
            "direction": direction,
            "entry_time": timestamp,
            "entry_price": entry_price,
            "quantity": quantity,
            "take_profit": take_profit,
            "stop_loss": stop_loss,
            "current_price": entry_price,
            "unrealized_pnl": 0.0,
            "status": "Open",
        }
        save_simulation_position(self.conn, self.strategy_id, position)
        self.logger.info(
            f"[{self.strategy_id}] OPEN {direction} | T_{trade_counter} | "
            f"Price={entry_price:.2f} | TP={take_profit:.2f} | SL={stop_loss:.2f}"
        )
        return position

    def close_position(self, position: dict, exit_price: float, exit_reason: str, timestamp) -> dict:
        """
        Closes active position:
          - Computes net PnL and updates self.balance
          - Inserts completed trade into trade ledger table simulations.<strategy_id>
          - Removes closed position from DB table simulations.positions
        """
        pnl = self.calculate_pnl(position["direction"], position["entry_price"], exit_price, position["quantity"])
        self.balance += pnl["net_pnl"]

        completed_trade = {
            "trade_id": position["trade_id"],
            "entry_time": position["entry_time"],
            "exit_time": timestamp,
            "direction": position["direction"],
            "entry_price": position["entry_price"],
            "exit_price": exit_price,
            "quantity": position["quantity"],
            "gross_pnl": pnl["gross_pnl"],
            "commission": pnl["commission"],
            "slippage": pnl["slippage"],
            "net_pnl": pnl["net_pnl"],
            "perc_pnl": pnl["perc_pnl"],
            "exit_reason": exit_reason,
            "balance": self.balance,
        }

        insert_simulation_ledger(self.conn, self.strategy_id, completed_trade)
        close_simulation_position(self.conn, self.strategy_id, {
            "exit_price": exit_price,
            "exit_time": timestamp,
            "exit_reason": exit_reason,
        })

        self.logger.info(
            f"[{self.strategy_id}] CLOSE {position['direction']} | {position['trade_id']} | "
            f"Exit={exit_price:.2f} | {exit_reason} | NetPnL={pnl['net_pnl']:+.4f} | "
            f"Balance={self.balance:.2f}"
        )
        return completed_trade

    def update_position_state(self, position: dict, close_price: float):
        """Updates current_price and unrealized_pnl every 1m candle into simulations.positions."""
        position["current_price"] = close_price
        entry = position["entry_price"]
        qty = position["quantity"]
        position["unrealized_pnl"] = (
            (close_price - entry) * qty if position["direction"] == "Long"
            else (entry - close_price) * qty
        )
        save_simulation_position(self.conn, self.strategy_id, position)

    def close_end_of_data(self, position: dict, merged_df: pd.DataFrame) -> dict:
        """Force-closes position still open at end of dataset using last candle close price."""
        last_timestamp = merged_df.index[-1]
        last_close = float(merged_df.iloc[-1]["close"])
        return self.close_position(position, last_close, "end_of_data", last_timestamp)

    # ─── Main Simulation Loop ────────────────────────────────────────────────

    def run_simulation(self):
        """Candle-by-candle sequential 1m execution loop."""
        self.logger.info(f"[{self.strategy_id}] Starting simulation...")
        clear_simulation_data(self.conn, self.strategy_id)
        self.balance = self.initial_balance
        sim_start_utc = datetime.now(timezone.utc)

        ohlcv_df, signals_df = self.fetch_data()
        merged_df = self.merge_data(ohlcv_df, signals_df)

        active_position = None
        trade_counter = 0
        completed_trades = []

        for timestamp, row in merged_df.iterrows():
            open_price = float(row["open"])
            high_price = float(row["high"])
            low_price = float(row["low"])
            close_price = float(row["close"])
            signal = int(row["signal"])

            # 1. Check hard SL / TP exit
            if active_position is not None:
                exit_price, exit_reason = self.check_exit_conditions(active_position, high_price, low_price)
                if exit_price is not None:
                    trade = self.close_position(active_position, exit_price, exit_reason, timestamp)
                    completed_trades.append(trade)
                    active_position = None

            # 2. Signal routing
            active_position, trade_counter = self.handle_signal(
                active_position, signal, open_price, timestamp, trade_counter, completed_trades
            )

            # 3. Update position live state
            if active_position is not None:
                self.update_position_state(active_position, close_price)

        # 4. Force-close open position at dataset end
        if active_position is not None:
            trade = self.close_end_of_data(active_position, merged_df)
            completed_trades.append(trade)
            active_position = None

        sim_end_utc = datetime.now(timezone.utc)

        # 5. Save stats & Print summary
        self.save_stats_to_db(completed_trades, sim_start_utc, sim_end_utc, merged_df)
        self.print_summary(completed_trades)

        self.conn.close()

    # ─── Stats & Summary ────────────────────────────────────────────────────

    def save_stats_to_db(self, completed_trades: list, sim_start_utc: datetime, sim_end_utc: datetime, merged_df: pd.DataFrame):
        """Calculates QuantStats metrics & saves complete summary into simulations.stats DB table."""
        total_trades = len(completed_trades)
        winning_trades = sum(1 for t in completed_trades if t["net_pnl"] > 0)
        losing_trades = total_trades - winning_trades
        total_pnl = self.balance - self.initial_balance
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

        data_start = str(merged_df.index[0]) if not merged_df.empty else None
        data_end = str(merged_df.index[-1]) if not merged_df.empty else None

        stats_summary = {
            "initial_balance": self.initial_balance,
            "final_balance": self.balance,
            "total_pnl": total_pnl,
            "total_trades": total_trades,
            "winning_trades": winning_trades,
            "losing_trades": losing_trades,
            "win_rate": win_rate,
        }

        metrics_json = {
            "sim_start": sim_start_utc.isoformat(),
            "sim_end": sim_end_utc.isoformat(),
            "data_start": data_start,
            "data_end": data_end,
        }

        if total_trades > 0:
            try:
                ledger_df = pd.DataFrame(completed_trades)
                ledger_df["exit_time"] = pd.to_datetime(ledger_df["exit_time"])
                returns_series = ledger_df.sort_values("exit_time").set_index("exit_time")["perc_pnl"]
                qs_metrics = compute_all_metrics(returns_series, is_percentage=True)
                metrics_json.update(qs_metrics)
                self.logger.info(f"[{self.strategy_id}] Computed {len(qs_metrics)} QuantStats metrics.")
            except Exception as e:
                self.logger.error(f"[{self.strategy_id}] Failed to compute QuantStats metrics: {e}")

        upsert_simulation_stats(self.conn, self.strategy_id, stats_summary, metrics_json)
        self.logger.info(
            f"[{self.strategy_id}] Stats saved. "
            f"Run: {sim_start_utc.strftime('%Y-%m-%d %H:%M:%S')} -> "
            f"{sim_end_utc.strftime('%Y-%m-%d %H:%M:%S')} UTC"
        )

    def print_summary(self, completed_trades: list):
        """Prints simulation summary in terminal."""
        total_trades = len(completed_trades)
        winning_trades = sum(1 for t in completed_trades if t["net_pnl"] > 0)
        losing_trades = total_trades - winning_trades
        win_rate = (winning_trades / total_trades * 100.0) if total_trades > 0 else 0.0

        print("\n" + "=" * 60)
        print(f"  SIMULATION SUMMARY — {self.strategy_id}")
        print("=" * 60)
        print(f"  Initial Balance : ${self.initial_balance:,.2f}")
        print(f"  Final Balance   : ${self.balance:,.2f}")
        print(f"  Net PnL         : ${self.balance - self.initial_balance:+,.2f}")
        print(f"  Total Trades    : {total_trades}")
        print(f"  Winning Trades  : {winning_trades}")
        print(f"  Losing Trades   : {losing_trades}")
        print(f"  Win Rate        : {win_rate:.2f}%")
        print("=" * 60)


def run_all_simulations():
    """Main entry point: Runs SimulatorEngine sequentially for all DB strategies."""
    conn = get_connection()
    try:
        strategies = list_all_strategies(conn)
        if not strategies:
            raise RuntimeError("No strategies found in metadata.strategy_data DB!")
    finally:
        conn.close()

    print("\n" + "=" * 65)
    print(f"  CRYPTOSIGHT SIMULATOR  —  {len(strategies)} strategies found")
    print("=" * 65)

    results = {}
    for strat_id in strategies:
        engine = SimulatorEngine(strategy_id=strat_id)
        engine.run_simulation()
        results[strat_id] = engine.balance

    print("\n" + "=" * 65)
    print("  ALL STRATEGIES — FINAL SUMMARY")
    print("=" * 65)
    print(f"  {'Strategy':<45} {'Final Balance':>14}")
    print("  " + "-" * 61)
    for s_id, final_bal in results.items():
        print(f"  {s_id:<45} ${final_bal:>12,.2f}")
    print("=" * 65)

    return results


if __name__ == "__main__":
    run_all_simulations()