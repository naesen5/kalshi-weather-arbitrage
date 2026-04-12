"""Tests for trade ledger."""

import os
import tempfile

from kalshi_weather_arb.trader.ledger import TradeLedger


class TestTradeLedger:
    """Test trade ledger."""

    def test_append_row(self, tmp_path):
        """Test appending a row."""
        ledger_path = str(tmp_path / "ledger.csv")
        ledger = TradeLedger(ledger_path=ledger_path)

        ledger.append_row(
            timestamp="2025-01-01T00:00:00Z",
            ticker="KC",
            side="OVER",
            count=1,
            price_cents=10000,
            cost_dollars=100.0,
            model_prob=0.6,
            market_prob=0.5,
            edge=10.0,
            dry_run=True,
            fill_price_cents=10000,
            status="dry_run",
        )

        assert os.path.exists(ledger_path)

        with open(ledger_path, "r") as f:
            content = f.read()
            assert "KC" in content
            assert "OVER" in content

    def test_read_all(self, tmp_path):
        """Test reading all entries."""
        ledger_path = str(tmp_path / "ledger.csv")
        ledger = TradeLedger(ledger_path=ledger_path)

        ledger.append_row(
            timestamp="2025-01-01T00:00:00Z",
            ticker="KC",
            side="OVER",
            count=1,
            price_cents=10000,
            cost_dollars=100.0,
            model_prob=0.6,
            market_prob=0.5,
            edge=10.0,
            dry_run=True,
            fill_price_cents=10000,
            status="dry_run",
        )

        entries = ledger.read_all()
        assert len(entries) == 1
        assert entries[0]["ticker"] == "KC"
