"""Tests for risk state module."""

import json
import os
import tempfile
from datetime import datetime

from kalshi_weather_arb.risk.state import RiskState
from kalshi_weather_arb.trader.ledger import TradeLedger


class TestRiskState:
    """Test RiskState class."""

    def test_init(self):
        """Test initialization."""
        state = RiskState(daily_max=500.0, circuit_breaker_threshold=50.0)
        assert state.daily_max == 500.0
        assert state.circuit_breaker_threshold == 50.0
        assert state.daily_exposure == 0.0
        assert state.halted is False

    def test_can_afford(self):
        """Test can_afford method."""
        state = RiskState(daily_max=500.0)
        assert state.can_afford(100.0) is True
        assert state.can_afford(600.0) is False

    def test_record_bet_won(self):
        """Test record_bet with won result."""
        state = RiskState(daily_max=500.0)
        state.record_bet(100.0, "won")
        assert state.daily_pnl == 100.0

    def test_record_bet_lost(self, tmp_path):
        """Test record_bet with lost result."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        state.record_bet(100.0, "lost")
        assert state.daily_pnl == -100.0

    def test_circuit_breaker_triggers(self, tmp_path):
        """Test circuit breaker triggers when loss exceeds threshold."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(
            daily_max=500.0,
            circuit_breaker_threshold=50.0,
            state_path=state_path,
        )
        state.record_bet(100.0, "lost")
        assert state.halted is True

    def test_update_from_ledger(self, tmp_path):
        """Test update_from_ledger with ledger entries."""
        ledger_path = str(tmp_path / "ledger.csv")
        ledger = TradeLedger(ledger_path)
        ledger.append_row(
            timestamp=datetime.utcnow().isoformat(),
            ticker="test",
            side="under",
            count=1,
            price_cents=100,
            cost_dollars=1.0,
            model_prob=0.5,
            market_prob=0.5,
            edge=0.05,
            dry_run=True,
            fill_price_cents=100,
            status="filled",
        )

        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        state.update_from_ledger(ledger)
        assert state.daily_exposure >= 0.0

    def test_reset_daily(self, tmp_path):
        """Test reset_daily clears state."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        state.daily_exposure = 100.0
        state.daily_pnl = 50.0
        state.open_positions = 2
        state.reset_daily()
        assert state.daily_exposure == 0.0
        assert state.daily_pnl == 0.0
        assert state.open_positions == 0
