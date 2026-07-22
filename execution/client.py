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

    def sync_server_time(self):
        """Auto-syncs local timestamp with Bybit server time to prevent ErrCode 10002."""
        try:
            res = HTTP().get_server_time()
            if res.get("retCode") == 0:
                server_ms = int(res["result"]["timeNano"]) // 10**6
                offset_ms = server_ms - int(time.time() * 1000)
                pybit._helpers.generate_timestamp = lambda: int(time.time() * 1000) + offset_ms
                logger.info(f"Bybit server time synced (Offset: {offset_ms}ms).")
        except Exception as err:
            logger.warning(f"Server time sync skipped: {err}")

    def get_credentials(self, exchange: str) -> dict:
        """Fetches API credentials for an exchange defined in DB metadata without printing sensitive keys."""
        creds = get_exchange_credentials(self.conn, exchange)
        if creds.get("api_key") and creds.get("api_secret"):
            demo_status = creds.get("demo")
            logger.info(f"API credentials for '{exchange}' (Demo Mode: {demo_status}) loaded successfully from DB.")
        else:
            logger.warning(f"API credentials for '{exchange}' missing in DB or .env.")
        return creds

    def get_session(self, exchange: str) -> HTTP:
        """Creates an authenticated Pybit HTTP session with demo & auto-time sync support."""
        creds = self.get_credentials(exchange)
        api_key = creds.get("api_key")
        api_secret = creds.get("api_secret")
        demo = creds.get("demo")

        if not api_key or not api_secret:
            raise ValueError(f"Missing API Key or Secret for exchange '{exchange}'.")

        self.sync_server_time()
        return HTTP(demo=demo, api_key=api_key, api_secret=api_secret, recv_window=20000)

    def get_execution_settings(self) -> dict:
        """Fetches global execution settings (top_n) from DB metadata.execution_settings table."""
        if not self.conn:
            return {"top_n": 1}
        query = "SELECT top_n FROM metadata.execution_settings LIMIT 1;"
        try:
            with self.conn.cursor() as cur:
                cur.execute(query)
                row = cur.fetchone()
                if row and row[0] is not None:
                    return {"top_n": int(row[0])}
        except Exception as err:
            logger.warning(f"Could not query metadata.execution_settings: {err}")
        return {"top_n": 1}

    def fetch_best_strategies(self, exchange: str = None) -> list:
        """
        Fetches strategies sorted by highest total_pnl from DB.
        Enforces STRICT constraint: Only 1 strategy per symbol!
        """
        query = """
        SELECT DISTINCT ON (s.symbol) 
            s.strategy_id, s.strategy_name, s.exchange, s.symbol, s.target_timeframe, 
            s.strategy_config, s.indicators_config, s.category, s.order_type,
            COALESCE(st.total_pnl, 0.0) as total_pnl,
            c.initial_balance, c.position_size_type, c.position_size_value, c.commission, c.slippage, c.allow_long, c.allow_short
        FROM metadata.strategy_data s
        LEFT JOIN metadata.simulator_config c ON CAST(s.strategy_id AS VARCHAR) = CAST(c.strategy_id AS VARCHAR)
        LEFT JOIN simulations.stats st ON CAST(s.strategy_id AS VARCHAR) = CAST(st.strategy_id AS VARCHAR)
        WHERE (%s IS NULL OR LOWER(s.exchange) = LOWER(%s))
        ORDER BY s.symbol, COALESCE(st.total_pnl, 0.0) DESC;
        """
        strategies = []
        try:
            with self.conn.cursor() as cur:
                cur.execute(query, (exchange, exchange))
                colnames = [desc[0] for desc in cur.description]
                for row in cur.fetchall():
                    strat = dict(zip(colnames, row))
                    strat["total_pnl"] = float(strat["total_pnl"])
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
        qty: float,
        exchange: str,
        category: str,
        order_type: str,
        price: float = None,
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
            session = self.get_session(exchange)
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
            logger.error(f"Exception during order placement: {err}")
            return {"status": "Error", "reason": str(err)}

    def get_active_positions(self, exchange: str, category: str = "linear", symbol: str = None) -> list:
        """Queries Bybit V5 API for active open positions on exchange."""
        try:
            session = self.get_session(exchange)
            kwargs = {"category": category.lower()}
            if symbol:
                sym = symbol.upper()
                kwargs["symbol"] = sym if sym.endswith("USDT") else f"{sym}USDT"
            res = session.get_positions(**kwargs)
            if res.get("retCode") == 0:
                return res.get("result", {}).get("list", [])
            else:
                logger.error(f"Failed to fetch active positions: {res.get('retMsg')}")
                return []
        except Exception as err:
            logger.error(f"Exception fetching active positions: {err}")
            return []

    def get_order_history(self, exchange: str, category: str = "linear", symbol: str = None, limit: int = 50) -> list:
        """Queries Bybit V5 API for historical order/trade execution history from exchange."""
        try:
            session = self.get_session(exchange)
            kwargs = {"category": category.lower(), "limit": limit}
            if symbol:
                sym = symbol.upper()
                kwargs["symbol"] = sym if sym.endswith("USDT") else f"{sym}USDT"
            res = session.get_order_history(**kwargs)
            if res.get("retCode") == 0:
                return res.get("result", {}).get("list", [])
            else:
                logger.error(f"Failed to fetch order history: {res.get('retMsg')}")
                return []
        except Exception as err:
            logger.error(f"Exception fetching order history: {err}")
            return []

