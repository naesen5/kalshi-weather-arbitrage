"""Tests for trade monitor."""

from unittest.mock import MagicMock

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.trader.ledger import TradeLedger
from kalshi_weather_arb.trader.monitor import TradeMonitor


class TestTradeMonitor:
    """Test trade monitor."""

    def test_poll_open_positions(self):
        """Test polling open positions."""
        client = MagicMock(spec=KalshiClient)
        client.get.return_value = {
            "results": [
                {"order_id": "order_1", "ticker": "KC", "status": "open"},
                {"order_id": "order_2", "ticker": "ZC", "status": "open"},
            ]
        }

        ledger = TradeLedger(ledger_path="/tmp/test_ledger.csv")
        monitor = TradeMonitor(client=client, ledger=ledger)

        positions = monitor.poll_open_positions()

        assert len(positions) == 2
        assert positions[0]["order_id"] == "order_1"
        assert client.get.called is True

    def test_check_settled(self):
        """Test checking settlement status."""
        client = MagicMock(spec=KalshiClient)
        client.get.return_value = {
            "order_id": "order_1",
            "status": "settled",
            "fill_price_cents": 10000,
        }

        ledger = TradeLedger(ledger_path="/tmp/test_ledger.csv")
        monitor = TradeMonitor(client=client, ledger=ledger)

        status = monitor.check_settled("order_1")

        assert status["status"] == "settled"
        assert client.get.called is True
