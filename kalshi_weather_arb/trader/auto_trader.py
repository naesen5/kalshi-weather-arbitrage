"""Auto-trader — execute approved orders with safety features."""

from datetime import datetime
from dataclasses import dataclass
from typing import Any, Dict

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.risk.state import RiskState
from kalshi_weather_arb.trader.ledger import TradeLedger


@dataclass
class TradeResult:
    """Result of a trade execution."""

    order_id: str
    filled: bool
    dry_run: bool
    status: str = ""


class AutoTrader:
    """Auto-trader — execute approved orders with safety features."""

    def __init__(
        self,
        client: KalshiClient,
        ledger: TradeLedger,
        risk_state: RiskState,
        dry_run: bool = True,
    ):
        self.client = client
        self.ledger = ledger
        self.risk_state = risk_state
        self.dry_run = dry_run

    def execute(self, spec: Dict[str, Any]) -> TradeResult:
        """Execute a trade from a spec."""
        ticker = spec["ticker"]
        side = spec["side"]
        count = spec["count"]
        price_cents = spec["price_cents"]
        cost_dollars = price_cents / 100.0

        # Check risk state
        if not self.risk_state.can_afford(cost_dollars):
            return TradeResult(
                order_id="rejected",
                filled=False,
                dry_run=self.dry_run,
                status="exposure_limit_reached",
            )

        if self.dry_run:
            order_id = (
                f"dry_run_{ticker}_{side}_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}"
            )
            self.ledger.append_row(
                timestamp=datetime.utcnow().isoformat(),
                ticker=ticker,
                side=side,
                count=count,
                price_cents=price_cents,
                cost_dollars=cost_dollars,
                model_prob=spec.get("model_prob", 0.0),
                market_prob=spec.get("market_prob", 0.0),
                edge=spec.get("edge", 0.0),
                dry_run=True,
                fill_price_cents=price_cents,
                status="dry_run",
            )
            return TradeResult(
                order_id=order_id,
                filled=True,
                dry_run=True,
                status="dry_run",
            )

        # Live mode — place order via API
        payload = {
            "ticker": ticker,
            "side": side,
            "count": count,
            "price_cents": price_cents,
        }

        response = self.client.post("/api/v1/orders", payload)
        order_id = response.get("order_id", "unknown")

        self.ledger.append_row(
            timestamp=datetime.utcnow().isoformat(),
            ticker=ticker,
            side=side,
            count=count,
            price_cents=price_cents,
            cost_dollars=cost_dollars,
            model_prob=spec.get("model_prob", 0.0),
            market_prob=spec.get("market_prob", 0.0),
            edge=spec.get("edge", 0.0),
            dry_run=False,
            fill_price_cents=response.get("fill_price_cents", 0),
            status=response.get("status", "placed"),
        )

        return TradeResult(
            order_id=order_id,
            filled=True,
            dry_run=False,
            status=response.get("status", "placed"),
        )
