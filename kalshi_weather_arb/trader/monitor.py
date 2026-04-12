"""Trade monitor — poll open positions and track settlements."""

from typing import Any, Dict, List

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.trader.ledger import TradeLedger


class TradeMonitor:
    """Trade monitor — poll open positions and track settlements."""

    def __init__(self, client: KalshiClient, ledger: TradeLedger):
        self.client = client
        self.ledger = ledger

    def poll_open_positions(self) -> List[Dict[str, Any]]:
        """Poll open positions from Kalshi API."""
        response = self.client.get("/api/v1/orders?status=open")
        return response.get("results", [])

    def check_settled(self, order_id: str) -> Dict[str, Any]:
        """Check settlement status of an order."""
        response = self.client.get(f"/api/v1/orders/{order_id}")
        return {
            "order_id": order_id,
            "status": response.get("status", "unknown"),
            "fill_price_cents": response.get("fill_price_cents", 0),
        }

    def update_ledger_from_settlement(
        self, order_id: str, status: str, fill_price_cents: int
    ) -> None:
        """Update ledger entry for a settled order."""
        entries = self.ledger.read_all()
        updated = False
        for entry in entries:
            if entry.get("order_id") == order_id:
                entry["fill_price_cents"] = fill_price_cents
                entry["status"] = status
                updated = True
                break
        if updated:
            # Re-write ledger (in production, use append-only with settlement flag)
            pass
