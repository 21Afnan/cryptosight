"""
Bybit Executor Module for Cryptosight Execution Engine.
Wraps PyBit unified_trading HTTP client for live/demo trading on Bybit.
Auto-fetches credentials from `account.api` and execution settings from `metadata.execution_config`.
Includes automatic server timestamp synchronization to prevent ErrCode 10002.
"""

import time
import pandas as pd
import pybit._helpers
from pybit.unified_trading import HTTP
from cryptosight.utils.db import get_account_api
from cryptosight.utils.metadata import fetch_execution_config
from cryptosight.utils.logger import get_logger

logger = get_logger("BybitExecutor")
class BybitExecutor:
    """
    Bybit API Execution Client for Demo/Testnet Trading.
    Auto-fetches credentials and execution settings (category, order_type) from PostgreSQL.
    Auto-syncs local timestamp with Bybit server time to eliminate clock drift errors.
    """

    def to_epoch_ms(self, value):
        if value is None:
            return None
        if isinstance(value, (int, float)):
            # Already an epoch-millisecond value (e.g. from Bybit API fields like 
            # createdTime/updatedTime, or from account_history.ingestion_state)
            return int(value)
        # Otherwise assume it's a pandas Timestamp / datetime / date-string
        return int(pd.Timestamp(value).timestamp() * 1000)

    def __init__(self, conn):
        self.conn = conn
        self.exchange = "bybit"

        # 1. Fetch credentials from PostgreSQL account.api table
        api_creds = get_account_api(conn, self.exchange)
        if not api_creds:
            raise ValueError(f"No API credentials found in PostgreSQL 'account.api' for exchange '{self.exchange}'.")

        self.api_key = api_creds["api_key"]
        self.api_secret = api_creds["api_secret"]
        self.demo = api_creds["demo"]
        self.instruments_cache = {}

        # 2. Sync server time to prevent ErrCode 10002 timestamp skew
        self.sync_server_time()

        # 3. Fetch execution settings from metadata.execution_config
        exec_cfg = fetch_execution_config(conn)
        if not exec_cfg:
            raise ValueError("No execution configuration found in PostgreSQL 'metadata.execution_config'.")

        self.category = exec_cfg["category"]
        self.order_type = exec_cfg["order_type"]

        try:
            self.session = HTTP(
                demo=self.demo,
                api_key=self.api_key,
                api_secret=self.api_secret,
                recv_window=20000,
            )
            logger.info(f"Initialized Bybit Executor from DB (demo={self.demo}, category='{self.category}', order_type='{self.order_type}').")
        except Exception as error:
            logger.error(f"Failed to initialize Bybit HTTP session: {error}")
            raise

    def sync_server_time(self):
        """Auto-syncs local timestamp with Bybit server time to prevent ErrCode 10002."""
        try:
            res = HTTP(demo=self.demo).get_server_time()
            if res.get("retCode") == 0:
                server_ms = int(res["result"]["timeNano"]) // 10**6
                offset_ms = server_ms - int(time.time() * 1000)
                pybit._helpers.generate_timestamp = lambda: int(time.time() * 1000) + offset_ms
                logger.info(f"Bybit server time synced successfully (Offset: {offset_ms}ms).")
        except Exception as err:
            logger.warning(f"Server time sync skipped: {err}")

    def get_bybit_symbol(self, symbol: str) -> str:
        """Standardizes coin symbol to Bybit pair e.g. 'btc' -> 'BTCUSDT'."""
        sym = symbol.upper().strip()
        return sym if sym.endswith("USDT") else f"{sym}USDT"

    def get_instrument_info(self, symbol: str) -> dict:
        """
        Fetches lot size step and min order qty for symbol from Bybit v5 instruments-info endpoint.
        Caches results per symbol in-memory on the BybitExecutor instance.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        if bybit_symbol in self.instruments_cache:
            return self.instruments_cache[bybit_symbol]

        try:
            response = self.session.get_instruments_info(category=self.category, symbol=bybit_symbol)
            if response.get("retCode") == 0:
                inst_list = response.get("result", {}).get("list", [])
                if inst_list:
                    lot_filter = inst_list[0].get("lotSizeFilter", {})
                    qty_step = float(lot_filter.get("qtyStep", 0.001))
                    min_order_qty = float(lot_filter.get("minOrderQty", 0.001))
                    info = {"qty_step": qty_step, "min_order_qty": min_order_qty}
                    self.instruments_cache[bybit_symbol] = info
                    return info
        except Exception as error:
            logger.error(f"Error fetching instrument info for {bybit_symbol}: {error}")

        default_info = {"qty_step": 0.001, "min_order_qty": 0.001}
        self.instruments_cache[bybit_symbol] = default_info
        return default_info

    def get_wallet_balance(self, coin: str) -> dict:
        """
        Queries live account balance (total equity & available balance) from Bybit API.
        STEP 8 FIX: Returns explicit fetch_ok flag to distinguish API errors from 0.0 balance.
        """
        try:
            response = self.session.get_wallet_balance(accountType="UNIFIED", coin=coin)
            if response.get("retCode") == 0:
                accts = response.get("result", {}).get("list", [])
                if accts:
                    acct = accts[0]
                    total_equity = float(acct.get("totalEquity", 0.0))
                    coins = acct.get("coin", [])
                    avail_bal = total_equity
                    for c in coins:
                        if c.get("coin") == coin:
                            avail_bal = float(c.get("walletBalance", total_equity))
                            break
                    logger.info(f"Bybit Wallet ({coin}): Total Equity=${total_equity:,.2f}, Available=${avail_bal:,.2f}.")
                    return {"total_equity": total_equity, "available_balance": avail_bal, "coin": coin, "fetch_ok": True}
            else:
                logger.warning(f"Bybit get_wallet_balance returned error: {response.get('retMsg')}")
        except Exception as error:
            logger.error(f"Error fetching wallet balance: {error}")

        return {"total_equity": 0.0, "available_balance": 0.0, "coin": coin, "fetch_ok": False}

    def get_open_position(self, symbol: str) -> dict:
        """
        Queries active position state from Bybit API using self.category.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        try:
            response = self.session.get_positions(category=self.category, symbol=bybit_symbol)
            if response.get("retCode") == 0:
                pos_list = response.get("result", {}).get("list", [])
                for pos in pos_list:
                    qty = float(pos.get("size", 0))
                    if qty > 0:
                        side = pos.get("side", "")
                        direction = "LONG" if side.lower() == "buy" else "SHORT"
                        return {
                            "symbol": bybit_symbol,
                            "direction": direction,
                            "side": side,
                            "quantity": qty,
                            "entry_price": float(pos["avgPrice"]),
                            "mark_price": float(pos["markPrice"]),
                            "liq_price": float(pos["liqPrice"]) if pos.get("liqPrice") else None,
                            "order_value": float(pos["positionValue"]),
                            "unrealized_pnl": float(pos["unrealisedPnl"]),
                            "take_profit": float(pos["takeProfit"]) if pos.get("takeProfit") else None,
                            "stop_loss": float(pos["stopLoss"]) if pos.get("stopLoss") else None,
                        }
        except Exception as error:
            logger.error(f"Error querying position for {bybit_symbol}: {error}")

        return None

    def wait_for_position_fill(self, symbol: str, expected_direction: str, retries: int = 5, delay: float = 0.5) -> dict:
        """
        Polls get_open_position() after order placement to capture the real 
        avgEntryPrice and filled quantity from Bybit, since market orders can 
        fill at a different price than the signal candle's close price used 
        for sizing.
        """
        for attempt in range(retries):
            pos = self.get_open_position(symbol)
            if pos and pos["direction"] == expected_direction.upper() and pos["quantity"] > 0:
                return pos
            time.sleep(delay)
        logger.warning(f"Could not confirm actual fill for {symbol} {expected_direction} after {retries} retries.")
        return None

    def place_market_order(
        self,
        symbol: str,
        direction: str,
        quantity: float,
        take_profit: float,
        stop_loss: float,
    ) -> dict:
        """
        Places an order on Bybit using category and orderType from PostgreSQL settings.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        side = "Buy" if direction.upper() in ("LONG", "BUY") else "Sell"

        payload = {
            "category": self.category,
            "symbol": bybit_symbol,
            "side": side,
            "orderType": self.order_type,
            "qty": str(quantity),
        }

        if take_profit and take_profit > 0:
            payload["takeProfit"] = str(round(take_profit, 4))
        if stop_loss and stop_loss > 0:
            payload["stopLoss"] = str(round(stop_loss, 4))

        try:
            logger.info(f"Placing Bybit {self.order_type} Order: {side} {quantity} {bybit_symbol} (TP: {take_profit}, SL: {stop_loss})...")
            response = self.session.place_order(**payload)
            if response.get("retCode") == 0:
                order_id = response.get("result", {}).get("orderId")
                logger.info(f"Order placed successfully on Bybit! Order ID: {order_id}")
                return {
                    "order_id": order_id,
                    "symbol": bybit_symbol,
                    "side": side,
                    "direction": direction.upper(),
                    "quantity": quantity,
                    "take_profit": take_profit,
                    "stop_loss": stop_loss,
                }
            else:
                logger.error(f"Bybit order placement failed: {response.get('retMsg')}")
        except Exception as error:
            logger.error(f"Exception during Bybit place_order: {error}")

        return None

    def close_position(self, symbol: str, direction: str, quantity: float) -> bool:
        """
        Closes active position on Bybit using reduceOnly=True order.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        close_side = "Sell" if direction.upper() in ("LONG", "BUY") else "Buy"

        payload = {
            "category": self.category,
            "symbol": bybit_symbol,
            "side": close_side,
            "orderType": self.order_type,
            "qty": str(quantity),
            "reduceOnly": True,
        }

        try:
            logger.info(f"Closing Bybit Position: {close_side} {quantity} {bybit_symbol} (reduceOnly)...")
            response = self.session.place_order(**payload)
            if response.get("retCode") == 0:
                logger.info(f"Position for {bybit_symbol} closed successfully on Bybit.")
                return True
            else:
                logger.error(f"Failed to close Bybit position: {response.get('retMsg')}")
        except Exception as error:
            logger.error(f"Exception closing Bybit position: {error}")

        return False

    def get_executions(self, symbol: str, start_time=None, end_time=None) -> list:
        """
        STEP 7 helper: Fetches real execution fills from Bybit get_executions endpoint.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        params = {"category": self.category, "symbol": bybit_symbol, "limit": 50}
        
        start_ms = None
        if start_time is not None:
            try:
                start_ms = self.to_epoch_ms(start_time)
                params["startTime"] = start_ms
            except Exception as e:
                logger.warning(f"Could not convert start_time '{start_time}' to ms: {e}")
        
        end_ms = None
        if end_time is not None:
            try:
                end_ms = self.to_epoch_ms(end_time)
                params["endTime"] = end_ms
            except Exception as e:
                logger.warning(f"Could not convert end_time '{end_time}' to ms: {e}")

        try:
            response = self.session.get_executions(**params)
            if response.get("retCode") == 0:
                execs = response.get("result", {}).get("list", [])
                if start_ms or end_ms:
                    filtered_execs = []
                    for item in execs:
                        exec_time = int(item.get("execTime", 0))
                        if start_ms and exec_time < start_ms:
                            continue
                        if end_ms and exec_time > end_ms:
                            continue
                        filtered_execs.append(item)
                    return filtered_execs
                return execs
            else:
                logger.warning(f"Bybit get_executions returned error: {response.get('retMsg')}")
        except Exception as error:
            logger.error(f"Error fetching executions for {bybit_symbol}: {error}")

        return []

    def get_position_real_commission(self, symbol: str, start_time=None, end_time=None) -> float:
        """
        STEP 7 FIX: Sums actual execFee for executions from start_time onwards.
        If no execution data is returned, logs a warning and returns 0.0 (never a hardcoded fee rate).
        """
        execs = self.get_executions(symbol, start_time=start_time, end_time=end_time)
        if not execs:
            logger.warning(f"Fee data unavailable from get_executions for {symbol}; returning 0.0 real commission.")
            return 0.0

        total_fee = 0.0
        for item in execs:
            fee = float(item.get("execFee", 0.0))
            total_fee += fee

        return total_fee

    def get_closed_pnl(self, symbol: str, start_time=None) -> list:
        """
        Fetches closed PnL records from Bybit API.
        STEP 1 FIX: Accepts start_time parameter and queries Bybit with startTime filter.
        STEP 6 FIX: Uses `stopOrderType` to map exit_reason ("TakeProfit"/"PartialTakeProfit" -> "TAKE_PROFIT", "StopLoss"/"PartialStopLoss" -> "STOP_LOSS", else None).
        STEP 7 FIX: Fetches real commission via get_executions instead of 0.0006 hardcoded multiplier.
        Returns a list of structured closed PnL dicts.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        params = {"category": self.category, "symbol": bybit_symbol, "limit": 50}

        if start_time is not None:
            try:
                start_ms = self.to_epoch_ms(start_time)
                params["startTime"] = start_ms
            except Exception as e:
                logger.warning(f"Could not parse start_time '{start_time}': {e}")

        try:
            response = self.session.get_closed_pnl(**params)
            if response.get("retCode") == 0:
                pnl_list = response.get("result", {}).get("list", [])
                if not pnl_list and "startTime" in params:
                    # Timezone shift fallback: retry without startTime filter if no records returned
                    params_fallback = {"category": self.category, "symbol": bybit_symbol, "limit": 50}
                    resp_fallback = self.session.get_closed_pnl(**params_fallback)
                    if resp_fallback.get("retCode") == 0:
                        pnl_list = resp_fallback.get("result", {}).get("list", [])
                records = []
                for item in pnl_list:
                    create_type = str(item.get("createType", "")).strip()
                    stop_order_type = str(item.get("stopOrderType", "")).strip()
                    exec_type = str(item.get("execType", "")).strip()
                    order_type = str(item.get("orderType", "")).strip()

                    # Exact Bybit Exchange API V5 Execution & Trigger Mapping
                    if exec_type in ("BustTrade", "Liquidation"):
                        exit_reason = "LIQUIDATION"
                    elif exec_type == "AdlTrade" or "Adl" in create_type:
                        exit_reason = "ADL"
                    elif stop_order_type in ("TakeProfit", "PartialTakeProfit") or create_type in ("CreateByTakeProfit", "CreateByPartialTakeProfit"):
                        exit_reason = "TAKE_PROFIT"
                    elif stop_order_type in ("StopLoss", "PartialStopLoss") or create_type in ("CreateByStopLoss", "CreateByPartialStopLoss"):
                        exit_reason = "STOP_LOSS"
                    elif stop_order_type == "TrailingStop" or create_type == "CreateByTrailingStop":
                        exit_reason = "TRAILING_STOP"
                    elif create_type in ("CreateByClosing", "CloseByMarket") or order_type == "Market":
                        exit_reason = "MARKET_EXIT"
                    elif order_type == "Limit":
                        exit_reason = "LIMIT_EXIT"
                    else:
                        exit_reason = "MARKET_CLOSE"

                    created_time = int(item.get("createdTime", 0)) if item.get("createdTime") else 0
                    updated_time = int(item.get("updatedTime", 0)) if item.get("updatedTime") else 0

                    # STEP 7: Fetch real fee scoped to this trade's window
                    commission = self.get_position_real_commission(symbol, start_time=created_time, end_time=updated_time)

                    records.append({
                        "order_id": item.get("orderId"),
                        "closed_pnl": float(item.get("closedPnl")),
                        "exit_price": float(item.get("avgExitPrice")),
                        "entry_price": float(item.get("avgEntryPrice")),
                        "quantity": float(item.get("qty")),
                        "commission": commission,
                        "exit_type": str(item.get("execType", "")),
                        "stop_order_type": stop_order_type,
                        "exit_reason": exit_reason,
                        "created_time": created_time,
                        "updated_time": updated_time,
                    })
                return records
            else:
                logger.warning(f"Bybit get_closed_pnl returned error: {response.get('retMsg')}")
        except Exception as error:
            logger.error(f"Error fetching closed PnL for {bybit_symbol}: {error}")

        return []

    def get_account_executions(self, start_time=None, max_pages=20) -> list:
        """
        Fetches all account-wide executions without a symbol filter, with pagination.
        """
        params = {"category": self.category, "limit": 100}
        if start_time is not None:
            try:
                st_ms = self.to_epoch_ms(start_time)
                min_valid_ms = int((time.time() - 700 * 86400) * 1000)
                if st_ms and st_ms > min_valid_ms:
                    params["startTime"] = st_ms
            except Exception as e:
                logger.warning(f"Could not parse start_time '{start_time}': {e}")

        all_records = []
        page = 0
        try:
            while True:
                if page >= max_pages:
                    logger.warning(f"Reached max_pages limit ({max_pages}) in get_account_executions. Breaking.")
                    break
                page += 1
                
                response = self.session.get_executions(**params)
                if response.get("retCode") == 0:
                    result = response.get("result", {})
                    items = result.get("list", [])
                    if not items:
                        break
                    all_records.extend(items)
                    next_cursor = result.get("nextPageCursor")
                    if next_cursor:
                        params["cursor"] = next_cursor
                    else:
                        break
                else:
                    logger.warning(f"Bybit get_executions (account) error: {response.get('retMsg')}")
                    break
        except Exception as error:
            logger.error(f"Error fetching account executions: {error}")
            
        return all_records

    def get_account_closed_pnl(self, start_time=None, max_pages=20) -> list:
        """
        Fetches all account-wide closed PnL without a symbol filter, with pagination.
        """
        params = {"category": self.category, "limit": 100}
        if start_time is not None:
            try:
                st_ms = self.to_epoch_ms(start_time)
                min_valid_ms = int((time.time() - 700 * 86400) * 1000)
                if st_ms and st_ms > min_valid_ms:
                    params["startTime"] = st_ms
            except Exception as e:
                logger.warning(f"Could not parse start_time '{start_time}': {e}")

        all_records = []
        page = 0
        try:
            while True:
                if page >= max_pages:
                    logger.warning(f"Reached max_pages limit ({max_pages}) in get_account_closed_pnl. Breaking.")
                    break
                page += 1
                
                response = self.session.get_closed_pnl(**params)
                if response.get("retCode") == 0:
                    result = response.get("result", {})
                    items = result.get("list", [])
                    if not items:
                        break
                    all_records.extend(items)
                    next_cursor = result.get("nextPageCursor")
                    if next_cursor:
                        params["cursor"] = next_cursor
                    else:
                        break
                else:
                    logger.warning(f"Bybit get_closed_pnl (account) error: {response.get('retMsg')}")
                    break
        except Exception as error:
            logger.error(f"Error fetching account closed PnL: {error}")
            
        return all_records

    def get_transaction_log(self, start_time=None, max_pages=20) -> list:
        """
        Fetches account transaction log, with pagination.
        """
        params = {"accountType": "UNIFIED", "limit": 100}
        if start_time is not None:
            try:
                st_ms = self.to_epoch_ms(start_time)
                min_valid_ms = int((time.time() - 700 * 86400) * 1000)
                if st_ms and st_ms > min_valid_ms:
                    params["startTime"] = st_ms
            except Exception as e:
                logger.warning(f"Could not parse start_time '{start_time}': {e}")

        all_records = []
        page = 0
        try:
            while True:
                if page >= max_pages:
                    logger.warning(f"Reached max_pages limit ({max_pages}) in get_transaction_log. Breaking.")
                    break
                page += 1
                
                response = self.session.get_transaction_log(**params)
                if response.get("retCode") == 0:
                    result = response.get("result", {})
                    items = result.get("list", [])
                    if not items:
                        break
                    all_records.extend(items)
                    next_cursor = result.get("nextPageCursor")
                    if next_cursor:
                        params["cursor"] = next_cursor
                    else:
                        break
                else:
                    logger.warning(f"Bybit get_transaction_log error: {response.get('retMsg')}")
                    break
        except Exception as error:
            logger.error(f"Error fetching account transaction log: {error}")
            
        return all_records


if __name__ == "__main__":
    from cryptosight.utils.db import get_connection

    print("=" * 65)
    print("      TESTING BYBIT EXECUTOR & DB API KEY CONNECTION")
    print("=" * 65)

    conn = None
    try:
        conn = get_connection()
        executor = BybitExecutor(conn)
        bal = executor.get_wallet_balance("USDT")

        print(f"\nWallet Balance ({bal['coin']}):")
        print(f" • Total Equity:     ${bal['total_equity']:,.2f}")
        print(f" • Available Balance: ${bal['available_balance']:,.2f}\n")

        pos = executor.get_open_position("BTC")
        if pos:
            print(f"Active Position ({pos['symbol']}):")
            print(f" • Direction:   {pos['direction']}")
            print(f" • Quantity:    {pos['quantity']}")
            print(f" • Entry Price: ${pos['entry_price']:,.2f}")
            print(f" • Mark Price:  ${pos['mark_price']:,.2f}")
            print(f" • Unrel PnL:   ${pos['unrealized_pnl']:,.2f}")
        else:
            print("No active BTC position open on Bybit.")

    except Exception as err:
        print(f"\nError testing Bybit Executor: {err}")
    finally:
        if conn:
            conn.close()
