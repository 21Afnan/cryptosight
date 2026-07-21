import os
from dotenv import load_dotenv
from pybit.unified_trading import HTTP
from cryptosight.utils.logger import get_logger

logger = get_logger("BybitExecutor")
load_dotenv()


class BybitExecutor:
    """
    Class-based low-level REST API client for Bybit V5 Unified Trading Account.
    Handles wallet balance queries, leverage configuration, open position checks,
    atomic order placement with exchange-level TP/SL, and closed trade PnL history.
    """

    def __init__(self):
        self.api_key = os.getenv("BYBIT_API_KEY", "").strip()
        self.api_secret = os.getenv("BYBIT_API_SECRET", "").strip()
        self.has_valid_keys = bool(self.api_key and self.api_secret)

        if not self.has_valid_keys:
            logger.warning("BYBIT_API_KEY or BYBIT_API_SECRET missing in .env environment! Private endpoints will be guarded.")

        self.session = HTTP(
            testnet=False,
            api_key=self.api_key if self.has_valid_keys else None,
            api_secret=self.api_secret if self.has_valid_keys else None
        )
        logger.info("BybitExecutor initialized on Bybit Mainnet V5 API.")

    def format_symbol(self, symbol: str) -> str:
        """Formats base coin symbol (e.g. 'btc') to Bybit USDT Futures pair ('BTCUSDT')."""
        sym = symbol.upper().strip()
        return sym if sym.endswith("USDT") else f"{sym}USDT"

    def get_wallet_balance(self, coin: str = "USDT") -> float:
        """Queries total available wallet balance in USDT from Bybit Unified account."""
        try:
            res = self.session.get_wallet_balance(accountType="UNIFIED", coin=coin)
            result = res.get("result", {})
            list_data = result.get("list", [])
            if list_data:
                coin_list = list_data[0].get("coin", [])
                for item in coin_list:
                    if item.get("coin") == coin:
                        wallet_bal = float(item.get("walletBalance", 0.0))
                        return wallet_bal
            return 0.0
        except Exception as e:
            logger.error(f"Error fetching Bybit wallet balance for '{coin}': {e}")
            return 0.0

    def set_leverage(self, symbol: str, leverage: int = 1) -> bool:
        """Sets leverage for a specific futures trading pair on Bybit."""
        bybit_symbol = self.format_symbol(symbol)
        lev_str = str(int(leverage))
        try:
            self.session.set_leverage(
                category="linear",
                symbol=bybit_symbol,
                buyLeverage=lev_str,
                sellLeverage=lev_str
            )
            logger.info(f"Leverage for {bybit_symbol} set to {lev_str}x on Bybit.")
            return True
        except Exception as e:
            # Code 110043: Leverage not modified (already set to requested leverage)
            if "110043" in str(e) or "not modified" in str(e).lower():
                return True
            logger.error(f"Error setting leverage for {bybit_symbol}: {e}")
            return False

    def get_open_positions(self, symbol: str) -> list:
        """Queries active open futures positions for a symbol on Bybit."""
        if not self.has_valid_keys:
            return []
        bybit_symbol = self.format_symbol(symbol)
        try:
            res = self.session.get_positions(category="linear", symbol=bybit_symbol)
            list_data = res.get("result", {}).get("list", [])
            open_positions = []
            for pos in list_data:
                size = float(pos.get("size", 0.0))
                if size > 0:
                    open_positions.append({
                        "symbol": pos.get("symbol"),
                        "side": pos.get("side"),  # 'Buy' (LONG) or 'Sell' (SHORT)
                        "size": size,
                        "entry_price": float(pos.get("avgPrice", 0.0)),
                        "unrealised_pnl": float(pos.get("unrealisedPnl", 0.0)),
                        "take_profit": float(pos.get("takeProfit", 0.0)),
                        "stop_loss": float(pos.get("stopLoss", 0.0))
                    })
            return open_positions
        except Exception as e:
            logger.error(f"Error querying open positions for {bybit_symbol}: {e}")
            return []

    def place_order(
        self,
        symbol: str,
        side: str,
        qty: float,
        take_profit: float = None,
        stop_loss: float = None
    ) -> dict:
        """
        Submits a Market Buy or Sell order to Bybit with atomic exchange-level TP and SL.
        Side must be 'Buy' (LONG) or 'Sell' (SHORT).
        """
        if not self.has_valid_keys:
            logger.error("Cannot place Bybit order: BYBIT_API_KEY and BYBIT_API_SECRET missing in .env!")
            return {}
        bybit_symbol = self.format_symbol(symbol)
        order_params = {
            "category": "linear",
            "symbol": bybit_symbol,
            "side": side.capitalize(),
            "orderType": "Market",
            "qty": str(round(qty, 6)),
            "timeInForce": "GTC"
        }
        if take_profit and take_profit > 0:
            order_params["takeProfit"] = str(round(take_profit, 4))
        if stop_loss and stop_loss > 0:
            order_params["stopLoss"] = str(round(stop_loss, 4))

        try:
            res = self.session.place_order(**order_params)
            order_id = res.get("result", {}).get("orderId")
            logger.info(f"Bybit Order Placed: {side.upper()} {qty} {bybit_symbol} | OrderID: {order_id}")
            return res.get("result", {})
        except Exception as e:
            logger.error(f"Failed to place Bybit order for {bybit_symbol}: {e}")
            return {}

    def close_position(self, symbol: str, side: str, qty: float) -> dict:
        """Closes an active position by submitting a ReduceOnly Market order."""
        if not self.has_valid_keys:
            return {}
        bybit_symbol = self.format_symbol(symbol)
        close_side = "Sell" if side.capitalize() in ("Buy", "Long") else "Buy"
        try:
            res = self.session.place_order(
                category="linear",
                symbol=bybit_symbol,
                side=close_side,
                orderType="Market",
                qty=str(round(qty, 6)),
                reduceOnly=True,
                timeInForce="GTC"
            )
            logger.info(f"Position Closed for {bybit_symbol}: {close_side.upper()} {qty}")
            return res.get("result", {})
        except Exception as e:
            logger.error(f"Failed to close position for {bybit_symbol}: {e}")
            return {}

    def get_closed_pnl(self, symbol: str, limit: int = 50) -> list:
        """Queries actual closed trade history from Bybit server (fill price, closed PnL, fees, exit reason)."""
        if not self.has_valid_keys:
            return []
        bybit_symbol = self.format_symbol(symbol)
        try:
            res = self.session.get_closed_pnl(
                category="linear",
                symbol=bybit_symbol,
                limit=limit
            )
            return res.get("result", {}).get("list", [])
        except Exception as e:
            logger.error(f"Error fetching closed PnL for {bybit_symbol}: {e}")
            return []
