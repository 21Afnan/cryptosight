import os
import time
import pybit._helpers
from pybit.unified_trading import HTTP
from cryptosight.utils.db import get_connection
from cryptosight.utils.metadata import get_exchange_credentials
from cryptosight.utils.logger import get_logger

logger = get_logger("ExecutionClient")


class BybitExecutionClient:
    """Class-based Bybit Execution Client for DB integration & Live/Demo Trading API."""

    def __init__(self, conn=None):
        self.conn = conn

    def sync_server_time(self, testnet: bool = False, demo: bool = False):
        """Auto-syncs local timestamp with Bybit server time to prevent ErrCode 10002."""
        try:
            res = HTTP(testnet=testnet, demo=demo).get_server_time()
            if res.get("retCode") == 0:
                server_ms = int(res["result"]["timeNano"]) // 10**6
                offset_ms = server_ms - int(time.time() * 1000)
                pybit._helpers.generate_timestamp = lambda: int(time.time() * 1000) + offset_ms
                logger.info(f"Bybit server time synced (Offset: {offset_ms}ms).")
        except Exception as err:
            logger.warning(f"Server time sync skipped: {err}")

    def get_credentials(self, exchange: str = "bybit") -> dict:
        """Fetches API credentials for an exchange defined in DB metadata without printing sensitive keys."""
        creds = get_exchange_credentials(self.conn, exchange)
        if creds.get("api_key") and creds.get("api_secret"):
            logger.info(f"API credentials for '{exchange}' loaded successfully from DB.")
        else:
            logger.warning(f"API credentials for '{exchange}' missing in DB or .env.")
        return creds

    def get_session(self, exchange: str = "bybit") -> HTTP:
        """Creates an authenticated Pybit HTTP session with demo & auto-time sync support."""
        creds = self.get_credentials(exchange)
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")
        testnet = creds.get("testnet", False)
        demo = creds.get("demo", os.getenv("BYBIT_DEMO", "false").lower() in ("true", "1"))

        if not api_key or not api_secret:
            raise ValueError(f"Missing API Key or Secret for exchange '{exchange}'.")

        self.sync_server_time(testnet=testnet, demo=demo)
        return HTTP(testnet=testnet, demo=demo, api_key=api_key, api_secret=api_secret, recv_window=20000)

    def get_wallet_balance(self, exchange: str = "bybit") -> dict:
        """Fetches live wallet equity and available margin balance."""
        try:
            session = self.get_session(exchange)
            res = session.get_wallet_balance(accountType="UNIFIED")
            if res.get("retCode") == 0 and res.get("result", {}).get("list"):
                acc = res["result"]["list"][0]
                return {
                    "account_type": acc.get("accountType"),
                    "total_equity": float(acc.get("totalEquity", 0.0) or 0.0),
                    "total_wallet_balance": float(acc.get("totalWalletBalance", 0.0) or 0.0),
                    "total_available_balance": float(acc.get("totalAvailableBalance", 0.0) or 0.0),
                }
            return {}
        except Exception as err:
            logger.error(f"Error fetching balance: {err}")
            return {}

    def fetch_best_strategies(self, exchange: str = "bybit") -> list:
        """
        Fetches Bybit strategies sorted by highest total_pnl from DB.
        Enforces STRICT constraint: Only 1 strategy per symbol!
        """
        query = """
        SELECT DISTINCT ON (s.symbol) 
            s.strategy_id, s.strategy_name, s.exchange, s.symbol, s.target_timeframe, 
            s.strategy_config, s.indicators_config, COALESCE(st.total_pnl, 0.0) as total_pnl
        FROM metadata.strategy_data s
        LEFT JOIN simulations.stats st ON CAST(s.strategy_id AS VARCHAR) = CAST(st.strategy_id AS VARCHAR)
        WHERE LOWER(s.exchange) = LOWER(%s)
        ORDER BY s.symbol, COALESCE(st.total_pnl, 0.0) DESC;
        """
        strategies = []
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (exchange,))
                colnames = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    strat = dict(zip(colnames, row))
                    strat["total_pnl"] = float(strat.get("total_pnl", 0.0) or 0.0)
                    strategies.append(strat)
            strategies.sort(key=lambda x: x["total_pnl"], reverse=True)
            logger.info(f"Fetched {len(strategies)} unique-symbol best strategies dynamically from DB.")
            return strategies
        except Exception as err:
            logger.error(f"Error fetching best strategies: {err}")
            return []

    def place_order(
        self,
        symbol: str,
        side: str,
        order_type: str = "Market",
        qty: float = 0.001,
        price: float = None,
        category: str = "linear",
        take_profit: float = None,
        stop_loss: float = None
    ) -> dict:
        """
        Places a Market or Limit order on Bybit Demo/Live with optional TP/SL parameters.
        Side: 'Buy' or 'Sell'
        Order Type: 'Market' or 'Limit'
        Category: 'linear' (USDT Perpetual Futures) or 'spot' (Spot Trading)
        """
        try:
            session = self.get_session("bybit")
            sym = symbol.upper()
            if not sym.endswith("USDT"):
                sym = f"{sym}USDT"

            order_args = {
                "category": category.lower(),
                "symbol": sym,
                "side": side.capitalize(),
                "orderType": order_type.capitalize(),
                "qty": str(qty),
            }

            if price and order_type.capitalize() == "Limit":
                order_args["price"] = str(price)

            if take_profit:
                order_args["takeProfit"] = str(take_profit)
            if stop_loss:
                order_args["stopLoss"] = str(stop_loss)

            logger.info(f"Placing {order_type} {side} order for {sym} (Qty: {qty})...")
            res = session.place_order(**order_args)
            if res.get("retCode") == 0:
                order_id = res.get("result", {}).get("orderId")
                logger.info(f"Order SUCCESS! OrderID: {order_id}")
                return {"status": "Success", "order_id": order_id, "details": res.get("result")}
            else:
                logger.error(f"Order Placement Failed: {res.get('retMsg')}")
                return {"status": "Failed", "reason": res.get("retMsg")}
        except Exception as err:
            err_msg = str(err)
            if "10005" in err_msg or "Permission denied" in err_msg:
                logger.error("API Key Permission Error (10005): Read-Only Key. Enable Orders permission.")
                return {"status": "Failed", "reason": "API Key is Read-Only."}
            elif "10024" in err_msg or "regulatory restrictions" in err_msg:
                logger.error("Bybit Geo-Restriction Error (10024): Use Bybit Demo Trading (demo=True) or VPN.")
                return {"status": "Failed", "reason": "Geo-restriction (10024). Enable Bybit Demo Trading Mode."}
            logger.error(f"Exception during order placement: {err_msg}")
            return {"status": "Error", "reason": err_msg}


if __name__ == "__main__":
    client = BybitExecutionClient()
    balance = client.get_wallet_balance("bybit")
    print(f"Bybit Execution Client Ready! Live Wallet Balance: {balance}")