"""
Bybit Executor Module for Cryptosight Execution Engine.
Wraps PyBit unified_trading HTTP client for live/demo trading on Bybit.
Auto-fetches credentials from `account.api` and execution settings from `metadata.execution_config`.
Includes automatic server timestamp synchronization to prevent ErrCode 10002.
"""

import time
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

    def __init__(self, conn):
        self.conn = conn
        self.exchange = "bybit"

        # 1. Sync server time to prevent ErrCode 10002 timestamp skew
        self.sync_server_time()

        # 2. Fetch credentials from PostgreSQL account.api table
        api_creds = get_account_api(conn, self.exchange)
        if not api_creds:
            raise ValueError(f"No API credentials found in PostgreSQL 'account.api' for exchange '{self.exchange}'.")

        self.api_key = api_creds["api_key"]
        self.api_secret = api_creds["api_secret"]
        self.demo = api_creds["demo"]

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
            res = HTTP(demo=True).get_server_time()
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

    def get_wallet_balance(self, coin: str) -> dict:
        """
        Queries live account balance (total equity & available balance) from Bybit API.
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
                    return {"total_equity": total_equity, "available_balance": avail_bal, "coin": coin}
            else:
                logger.warning(f"Bybit get_wallet_balance returned error: {response.get('retMsg')}")
        except Exception as error:
            logger.error(f"Error fetching wallet balance: {error}")

        return {"total_equity": 0.0, "available_balance": 0.0, "coin": coin}

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

    def get_closed_pnl(self, symbol: str) -> dict:
        """
        Fetches exact exit price, net PnL, and exit reason from Bybit closed PnL history.
        """
        bybit_symbol = self.get_bybit_symbol(symbol)
        try:
            response = self.session.get_closed_pnl(category=self.category, symbol=bybit_symbol, limit=1)
            if response.get("retCode") == 0:
                pnl_list = response.get("result", {}).get("list", [])
                if pnl_list:
                    item = pnl_list[0]
                    exec_type = str(item.get("execType", ""))
                    exit_reason = "TAKE_PROFIT" if "tp" in exec_type.lower() else (
                        "STOP_LOSS" if "sl" in exec_type.lower() else "SIGNAL_REVERSAL"
                    )
                    return {
                        "order_id": item.get("orderId"),
                        "closed_pnl": float(item.get("closedPnl")),
                        "exit_price": float(item.get("avgExitPrice")),
                        "entry_price": float(item.get("avgEntryPrice")),
                        "quantity": float(item.get("qty")),
                        "commission": float(item.get("cumExitValue")) * 0.0006,
                        "exit_type": exec_type,
                        "exit_reason": exit_reason,
                    }
        except Exception as error:
            logger.error(f"Error fetching closed PnL for {bybit_symbol}: {error}")

        return None


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
