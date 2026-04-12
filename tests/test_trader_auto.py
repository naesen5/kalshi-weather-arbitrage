"""Tests for auto-trader."""

from unittest.mock import MagicMock

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.risk.state import RiskState
from kalshi_weather_arb.trader.auto_trader import AutoTrader
from kalshi_weather_arb.trader.ledger import TradeLedger


class TestAutoTrader:
    """Test auto-trader."""

    def test_execute_dry_run(self, tmp_path):
        """Test dry-run execution."""
        client = MagicMock(spec=KalshiClient)
        ledger = TradeLedger(ledger_path=str(tmp_path / "ledger.csv"))
        risk_state = RiskState()

        trader = AutoTrader(
            client=client,
            ledger=ledger,
            risk_state=risk_state,
            dry_run=True,
        )

        spec = {
            "ticker": "KC",
            "side": "OVER",
            "count": 1,
            "price_cents": 10000,
            "model_prob": 0.6,
            "market_prob": 0.5,
            "edge": 10.0,
        }

        result = trader.execute(spec)

        assert result.dry_run is True
        assert result.filled is True
        assert result.order_id.startswith("dry_run_")
        assert client.post.called is False

    def test_execute_live(self, tmp_path):
        """Test live execution."""
        client = MagicMock(spec=KalshiClient)
        client.post.return_value = {"order_id": "test_order_123"}

        ledger = TradeLedger(ledger_path=str(tmp_path / "ledger.csv"))
        risk_state = RiskState()

        trader = AutoTrader(
            client=client,
            ledger=ledger,
            risk_state=risk_state,
            dry_run=False,
        )

        spec = {
            "ticker": "KC",
            "side": "OVER",
            "count": 1,
            "price_cents": 10000,
            "model_prob": 0.6,
            "market_prob": 0.5,
            "edge": 10.0,
        }

        result = trader.execute(spec)

        assert result.dry_run is False
        assert result.filled is True
        assert result.order_id == "test_order_123"
        assert client.post.called is True

    def test_execute_rejected_exposure(self, tmp_path):
        """Test execution rejected due to exposure limit."""
        client = MagicMock(spec=KalshiClient)
        ledger = TradeLedger(ledger_path=str(tmp_path / "ledger.csv"))
        risk_state = RiskState(daily_max=100.0)
        risk_state.daily_exposure = 100.0

        trader = AutoTrader(
            client=client,
            ledger=ledger,
            risk_state=risk_state,
            dry_run=True,
        )

        spec = {
            "ticker": "KC",
            "side": "OVER",
            "count": 1,
            "price_cents": 10000,
            "model_prob": 0.6,
            "market_prob": 0.5,
            "edge": 10.0,
        }

        result = trader.execute(spec)

        assert result.filled is False
        assert result.order_id == "rejected"
        assert client.post.called is False
