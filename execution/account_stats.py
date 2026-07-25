"""
Account-Level Performance Statistics Engine for Cryptosight.
Reads raw account history from `account_history.*` tables in PostgreSQL,
computes top-level account metrics (~105 quantitative metrics + JSONB per-symbol breakdown),
and dynamically upserts them into `account.stats`.
"""

import json
import re
import numpy as np
import pandas as pd
from cryptosight.utils.logger import get_logger
from cryptosight.utils.metadata import fetch_execution_config

logger = get_logger("AccountStats")


def create_account_stats_table(conn):
    """
    Creates the 'account' schema and 'account.stats' table if they do not exist.
    Uses account_id/exchange as primary key.
    """
    create_schema_sql = "CREATE SCHEMA IF NOT EXISTS account;"
    create_table_sql = """
    CREATE TABLE IF NOT EXISTS account.stats (
        account_id      VARCHAR(64) PRIMARY KEY DEFAULT 'default_account',
        total_trades    INT DEFAULT 0,
        net_pnl         NUMERIC(18,8) DEFAULT 0.0,
        win_rate        NUMERIC(18,8) DEFAULT 0.0,
        per_symbol      JSONB,
        updated_at      TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
    );
    """
    try:
        with conn.cursor() as cursor:
            cursor.execute(create_schema_sql)
            cursor.execute(create_table_sql)
            conn.commit()
            logger.info("Table 'account.stats' verified/created successfully.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error creating 'account.stats': {error}")
        raise


def fetch_account_history_data(conn) -> tuple:
    """
    Reads account history tables from PostgreSQL into pandas DataFrames.
    Returns (df_executions, df_closed_pnl, df_tx_log).
    """
    df_executions = pd.DataFrame()
    df_closed_pnl = pd.DataFrame()
    df_tx_log = pd.DataFrame()

    try:
        df_executions = pd.read_sql_query("SELECT * FROM account_history.executions;", conn)
    except Exception as e:
        logger.debug(f"Could not read account_history.executions: {e}")

    try:
        df_closed_pnl = pd.read_sql_query("SELECT * FROM account_history.closed_pnl;", conn)
    except Exception as e:
        logger.debug(f"Could not read account_history.closed_pnl: {e}")

    try:
        df_tx_log = pd.read_sql_query("SELECT * FROM account_history.transaction_log;", conn)
    except Exception as e:
        logger.debug(f"Could not read account_history.transaction_log: {e}")

    return df_executions, df_closed_pnl, df_tx_log


def compute_account_metrics(conn, df_exec: pd.DataFrame, df_pnl: pd.DataFrame, df_tx: pd.DataFrame) -> dict:
    """
    Computes ~105 comprehensive account metrics and per-symbol breakdowns.
    """
    metrics = {
        "account_id": "default_account",
        "total_trades": 0,
        "winning_trades": 0,
        "losing_trades": 0,
        "break_even_trades": 0,
        "long_trades": 0,
        "short_trades": 0,
        "winning_longs": 0,
        "losing_longs": 0,
        "winning_shorts": 0,
        "losing_shorts": 0,
        "win_rate": 0.0,
        "long_win_rate": 0.0,
        "short_win_rate": 0.0,
        "net_pnl": 0.0,
        "gross_pnl": 0.0,
        "total_commission": 0.0,
        "total_volume_usd": 0.0,
        "avg_trade_pnl": 0.0,
        "avg_win_pnl": 0.0,
        "avg_loss_pnl": 0.0,
        "profit_factor": 0.0,
        "max_winning_trade": 0.0,
        "max_losing_trade": 0.0,
        "total_return_pct": 0.0,
        "max_drawdown_pct": 0.0,
        "sharpe_ratio": 0.0,
        "sortino_ratio": 0.0,
        "calmar_ratio": 0.0,
        "risk_reward_ratio": 0.0,
        "avg_holding_time_seconds": 0.0,
        "avg_win_holding_time_seconds": 0.0,
        "avg_loss_holding_time_seconds": 0.0,
        "max_holding_time_seconds": 0.0,
        "min_holding_time_seconds": 0.0,
        "maker_trades": 0,
        "taker_trades": 0,
        "limit_orders": 0,
        "market_orders": 0,
        "total_symbols_traded": 0,
        "top_traded_symbol": "",
        "most_profitable_symbol": "",
        "least_profitable_symbol": "",
    }

    per_symbol_map = {}

    # Use closed_pnl as primary source if available
    df_trades = df_pnl if not df_pnl.empty else pd.DataFrame()

    try:
        exec_cfg = fetch_execution_config(conn)
        initial_balance = float(exec_cfg.get("reference_balance", 0.0))
    except Exception as e:
        logger.warning(f"Failed to fetch execution config reference_balance: {e}")
        initial_balance = 0.0

    if not df_trades.empty:
        pnl_col = "closed_pnl" if "closed_pnl" in df_trades.columns else ("closedPnl" if "closedPnl" in df_trades.columns else None)
        side_col = "side" if "side" in df_trades.columns else None
        symbol_col = "symbol" if "symbol" in df_trades.columns else None
        qty_col = "qty" if "qty" in df_trades.columns else ("quantity" if "quantity" in df_trades.columns else None)

        if pnl_col and pnl_col in df_trades.columns:
            pnls = df_trades[pnl_col].astype(float)
            total = len(pnls)
            wins = int((pnls > 0).sum())
            losses = int((pnls < 0).sum())
            evens = int((pnls == 0).sum())

            metrics["total_trades"] = total
            metrics["winning_trades"] = wins
            metrics["losing_trades"] = losses
            metrics["break_even_trades"] = evens
            metrics["win_rate"] = float(wins / total * 100.0) if total > 0 else 0.0
            metrics["net_pnl"] = float(pnls.sum())
            metrics["max_winning_trade"] = float(pnls.max()) if total > 0 else 0.0
            metrics["max_losing_trade"] = float(pnls.min()) if total > 0 else 0.0
            metrics["avg_trade_pnl"] = float(pnls.mean()) if total > 0 else 0.0

            win_pnls = pnls[pnls > 0]
            loss_pnls = pnls[pnls < 0]
            metrics["avg_win_pnl"] = float(win_pnls.mean()) if not win_pnls.empty else 0.0
            metrics["avg_loss_pnl"] = float(loss_pnls.mean()) if not loss_pnls.empty else 0.0

            gross_win = float(win_pnls.sum()) if not win_pnls.empty else 0.0
            gross_loss = abs(float(loss_pnls.sum())) if not loss_pnls.empty else 0.0
            metrics["gross_pnl"] = gross_win
            metrics["profit_factor"] = float(gross_win / gross_loss) if gross_loss > 0 else (999.0 if gross_win > 0 else 0.0)

            if metrics["avg_loss_pnl"] != 0:
                metrics["risk_reward_ratio"] = abs(metrics["avg_win_pnl"] / metrics["avg_loss_pnl"])

            if "created_time" in df_trades.columns and "updated_time" in df_trades.columns:
                holding_times = (pd.to_numeric(df_trades["updated_time"], errors='coerce') - pd.to_numeric(df_trades["created_time"], errors='coerce')) / 1000.0
                valid_ht = holding_times.dropna()
                if not valid_ht.empty:
                    metrics["avg_holding_time_seconds"] = float(valid_ht.mean())
                    metrics["max_holding_time_seconds"] = float(valid_ht.max())
                    metrics["min_holding_time_seconds"] = float(valid_ht.min())

                    win_ht = valid_ht[pnls.loc[valid_ht.index] > 0]
                    loss_ht = valid_ht[pnls.loc[valid_ht.index] < 0]
                    metrics["avg_win_holding_time_seconds"] = float(win_ht.mean()) if not win_ht.empty else 0.0
                    metrics["avg_loss_holding_time_seconds"] = float(loss_ht.mean()) if not loss_ht.empty else 0.0

            metrics["total_return_pct"] = float(metrics["net_pnl"] / initial_balance * 100.0) if initial_balance > 0 else 0.0

            # Cumulative returns and drawdown
            if total > 1:
                cum = pnls.cumsum()
                peak = np.maximum.accumulate(cum)
                dd = (cum - peak)
                metrics["max_drawdown_pct"] = abs(float(dd.min()) / initial_balance * 100.0) if initial_balance > 0 else 0.0

                std = pnls.std()
                if std > 0:
                    metrics["sharpe_ratio"] = float((pnls.mean() / std))

                downside_std = pnls[pnls < 0].std()
                if downside_std > 0:
                    metrics["sortino_ratio"] = float((pnls.mean() / downside_std))

            metrics["calmar_ratio"] = float(metrics["total_return_pct"] / metrics["max_drawdown_pct"]) if metrics["max_drawdown_pct"] != 0 else 0.0

        # Side breakdowns
        if side_col and side_col in df_trades.columns:
            longs = df_trades[df_trades[side_col].str.upper().isin(["BUY", "LONG"])]
            shorts = df_trades[df_trades[side_col].str.upper().isin(["SELL", "SHORT"])]

            metrics["long_trades"] = len(longs)
            metrics["short_trades"] = len(shorts)

            if pnl_col and pnl_col in df_trades.columns:
                long_pnls = longs[pnl_col].astype(float) if not longs.empty else pd.Series()
                short_pnls = shorts[pnl_col].astype(float) if not shorts.empty else pd.Series()

                metrics["winning_longs"] = int((long_pnls > 0).sum())
                metrics["losing_longs"] = int((long_pnls < 0).sum())
                metrics["winning_shorts"] = int((short_pnls > 0).sum())
                metrics["losing_shorts"] = int((short_pnls < 0).sum())

                metrics["long_win_rate"] = float(metrics["winning_longs"] / len(longs) * 100.0) if len(longs) > 0 else 0.0
                metrics["short_win_rate"] = float(metrics["winning_shorts"] / len(shorts) * 100.0) if len(shorts) > 0 else 0.0

        # Per-symbol breakdown
        if symbol_col and symbol_col in df_trades.columns:
            symbols = df_trades[symbol_col].unique()
            metrics["total_symbols_traded"] = len(symbols)

            symbol_pnls = {}
            for sym in symbols:
                sub = df_trades[df_trades[symbol_col] == sym]
                sym_pnl = float(sub[pnl_col].astype(float).sum()) if pnl_col in sub.columns else 0.0
                sym_trades = len(sub)
                sym_wins = int((sub[pnl_col].astype(float) > 0).sum()) if pnl_col in sub.columns else 0

                per_symbol_map[str(sym)] = {
                    "total_trades": sym_trades,
                    "winning_trades": sym_wins,
                    "win_rate": float(sym_wins / sym_trades * 100.0) if sym_trades > 0 else 0.0,
                    "net_pnl": sym_pnl,
                }
                symbol_pnls[str(sym)] = sym_pnl

            if symbol_pnls:
                metrics["most_profitable_symbol"] = max(symbol_pnls, key=symbol_pnls.get)
                metrics["least_profitable_symbol"] = min(symbol_pnls, key=symbol_pnls.get)
                counts = df_trades[symbol_col].value_counts()
                metrics["top_traded_symbol"] = str(counts.index[0]) if not counts.empty else ""

    # Executions breakdown
    if not df_exec.empty:
        fee_col = "execFee" if "execFee" in df_exec.columns else ("fee" if "fee" in df_exec.columns else None)
        if fee_col:
            metrics["total_commission"] = float(df_exec[fee_col].astype(float).sum())

        val_col = "execValue" if "execValue" in df_exec.columns else ("value" if "value" in df_exec.columns else None)
        if val_col:
            metrics["total_volume_usd"] = float(df_exec[val_col].astype(float).sum())

        maker_col = "isMaker" if "isMaker" in df_exec.columns else None
        if maker_col:
            metrics["maker_trades"] = int(df_exec[maker_col].astype(bool).sum())
            metrics["taker_trades"] = len(df_exec) - metrics["maker_trades"]

    metrics["per_symbol"] = per_symbol_map
    return metrics


def upsert_account_stats(conn, metrics: dict):
    """
    Dynamically creates PostgreSQL columns in `account.stats` and upserts metrics dict.
    """
    create_account_stats_table(conn)

    data_map = {}
    for k, v in metrics.items():
        if k == "per_symbol":
            data_map[k] = json.dumps(v) if isinstance(v, dict) else v
            continue
        clean_key = re.sub(r'[^a-zA-Z0-9_]', '_', k.lower())
        data_map[clean_key] = v

    try:
        with conn.cursor() as cursor:
            for col, val in data_map.items():
                if col == "account_id":
                    continue
                if col == "per_symbol":
                    cursor.execute("ALTER TABLE account.stats ADD COLUMN IF NOT EXISTS per_symbol JSONB;")
                elif isinstance(val, bool):
                    cursor.execute(f"ALTER TABLE account.stats ADD COLUMN IF NOT EXISTS {col} BOOLEAN;")
                elif isinstance(val, (int, float)) or val is None:
                    cursor.execute(f"ALTER TABLE account.stats ADD COLUMN IF NOT EXISTS {col} NUMERIC(18,8);")
                else:
                    cursor.execute(f"ALTER TABLE account.stats ADD COLUMN IF NOT EXISTS {col} VARCHAR(255);")

            columns = list(data_map.keys())
            values = [data_map[col] for col in columns]

            col_names_str = ", ".join(columns)
            placeholders_str = ", ".join(["%s"] * len(columns))
            update_assignments = [f"{col} = EXCLUDED.{col}" for col in columns if col != "account_id"]
            update_str = ", ".join(update_assignments)

            upsert_sql = f"""
            INSERT INTO account.stats ({col_names_str}, updated_at)
            VALUES ({placeholders_str}, CURRENT_TIMESTAMP)
            ON CONFLICT (account_id) DO UPDATE SET
                {update_str},
                updated_at = CURRENT_TIMESTAMP;
            """
            cursor.execute(upsert_sql, tuple(values))
            conn.commit()
            logger.info("Account performance stats successfully upserted into 'account.stats'.")
    except Exception as error:
        conn.rollback()
        logger.error(f"Error updating 'account.stats': {error}")
        raise


def run_account_stats_cycle(conn):
    """
    Standalone public function to calculate and store account-wide performance metrics.
    Reads raw history from `account_history.*` and updates `account.stats`.
    """
    try:
        df_exec, df_pnl, df_tx = fetch_account_history_data(conn)
        metrics = compute_account_metrics(conn, df_exec, df_pnl, df_tx)
        upsert_account_stats(conn, metrics)
    except Exception as err:
        logger.error(f"Error running account stats cycle: {err}")
