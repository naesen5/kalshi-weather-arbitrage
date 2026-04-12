"""Tests for PositionSizer class."""


from kalshi_weather_arb.risk.state import RiskState
from kalshi_weather_arb.sizer import PositionSizer, Sizer


class TestPositionSizer:
    """Test PositionSizer class."""

    def test_init(self):
        """Test initialization."""
        sizer = Sizer()
        state = RiskState()
        position_sizer = PositionSizer(sizer, state)
        assert position_sizer.sizer == sizer
        assert position_sizer.risk_state == state
        assert position_sizer.min_edge == 0.0
        assert position_sizer.max_observation_age_minutes == 90

    def test_approve_basic_success(self, tmp_path):
        """Test approve returns OrderSpec when all checks pass."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        sizer = Sizer()
        position_sizer = PositionSizer(sizer, state, min_edge=0.0)

        opportunity = {
            "ticker": "test_ticker",
            "side": "under",
            "edge": 0.05,
            "model_prob": 0.5,
            "market_prob": 0.5,
            "observation_age_minutes": 30,
        }

        result = position_sizer.approve(opportunity)
        assert result is not None
        assert result["ticker"] == "test_ticker"
        assert result["side"] == "under"
        assert result["count"] == 1

    def test_approve_exposure_limit_rejected(self, tmp_path):
        """Test approve returns None when exposure limit exceeded."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(daily_max=100.0, state_path=state_path)
        state.daily_exposure = 100.0  # Already at limit
        sizer = Sizer()
        position_sizer = PositionSizer(sizer, state, min_edge=0.0)

        opportunity = {
            "ticker": "test_ticker",
            "side": "under",
            "edge": 0.05,
            "model_prob": 0.5,
            "market_prob": 0.5,
            "observation_age_minutes": 30,
        }

        result = position_sizer.approve(opportunity)
        assert result is None

    def test_approve_existing_position_rejected(self, tmp_path):
        """Test approve returns None when existing position on ticker."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        state.open_positions = 1  # Existing position
        sizer = Sizer()
        position_sizer = PositionSizer(sizer, state, min_edge=0.0)

        opportunity = {
            "ticker": "test_ticker",
            "side": "under",
            "edge": 0.05,
            "model_prob": 0.5,
            "market_prob": 0.5,
            "observation_age_minutes": 30,
        }

        result = position_sizer.approve(opportunity)
        assert result is None

    def test_approve_edge_threshold_rejected(self, tmp_path):
        """Test approve returns None when edge below threshold."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        sizer = Sizer()
        position_sizer = PositionSizer(sizer, state, min_edge=0.05)

        opportunity = {
            "ticker": "test_ticker",
            "side": "under",
            "edge": 0.02,  # Below threshold
            "model_prob": 0.5,
            "market_prob": 0.5,
            "observation_age_minutes": 30,
        }

        result = position_sizer.approve(opportunity)
        assert result is None

    def test_approve_observation_age_rejected(self, tmp_path):
        """Test approve returns None when observation age too old."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(state_path=state_path)
        sizer = Sizer()
        position_sizer = PositionSizer(sizer, state, max_observation_age_minutes=60)

        opportunity = {
            "ticker": "test_ticker",
            "side": "under",
            "edge": 0.05,
            "model_prob": 0.5,
            "market_prob": 0.5,
            "observation_age_minutes": 90,  # Too old
        }

        result = position_sizer.approve(opportunity)
        assert result is None

    def test_approve_circuit_breaker_halted(self, tmp_path):
        """Test approve returns None when circuit breaker is halted."""
        state_path = str(tmp_path / "risk.json")
        state = RiskState(
            daily_max=500.0,
            circuit_breaker_threshold=50.0,
            state_path=state_path,
        )
        state.halted = True  # Circuit breaker triggered
        sizer = Sizer()
        position_sizer = PositionSizer(sizer, state, min_edge=0.0)

        opportunity = {
            "ticker": "test_ticker",
            "side": "under",
            "edge": 0.05,
            "model_prob": 0.5,
            "market_prob": 0.5,
            "observation_age_minutes": 30,
        }

        result = position_sizer.approve(opportunity)
        assert result is None
