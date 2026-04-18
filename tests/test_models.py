"""Tests for Opportunity dataclass."""

from kalshi_weather_arb.models import Opportunity


class TestOpportunity:
    """Test Opportunity dataclass."""

    def test_init(self):
        """Test initialization with all fields."""
        opp = Opportunity(
            market_ticker="KLSHI-TEMP-NYC-90",
            market_title="Will NYC reach 90°F today?",
            station="KORD",
            current_temp_f=75.0,
            obs_age_minutes=15.0,
            threshold_f=90.0,
            model_probability=0.65,
            market_probability=0.45,
            edge=0.20,
            ask_price_cents=45,
            recommended_side="yes",
        )
        assert opp.market_ticker == "KLSHI-TEMP-NYC-90"
        assert opp.recommended_side == "yes"

    def test_edge_calculation(self):
        """Test that edge is correctly calculated."""
        opp = Opportunity(
            market_ticker="TEST",
            market_title="Test",
            station="KTST",
            current_temp_f=70.0,
            obs_age_minutes=10.0,
            threshold_f=80.0,
            model_probability=0.7,
            market_probability=0.5,
            edge=0.2,
            ask_price_cents=50,
            recommended_side="yes",
        )
        assert opp.edge == 0.2

    def test_is_tradeable_true(self):
        """Test is_tradeable returns True when edge >= min_edge."""
        opp = Opportunity(
            market_ticker="TEST",
            market_title="Test",
            station="KTST",
            current_temp_f=70.0,
            obs_age_minutes=10.0,
            threshold_f=80.0,
            model_probability=0.7,
            market_probability=0.5,
            edge=0.15,
            ask_price_cents=50,
            recommended_side="yes",
        )
        assert opp.is_tradeable(min_edge=0.10) is True
        assert opp.is_tradeable(min_edge=0.15) is True

    def test_is_tradeable_false(self):
        """Test is_tradeable returns False when edge < min_edge."""
        opp = Opportunity(
            market_ticker="TEST",
            market_title="Test",
            station="KTST",
            current_temp_f=70.0,
            obs_age_minutes=10.0,
            threshold_f=80.0,
            model_probability=0.55,
            market_probability=0.5,
            edge=0.05,
            ask_price_cents=50,
            recommended_side="yes",
        )
        assert opp.is_tradeable(min_edge=0.10) is False
        assert opp.is_tradeable(min_edge=0.05) is True

    def test_to_dict(self):
        """Test conversion to dictionary."""
        opp = Opportunity(
            market_ticker="TEST",
            market_title="Test",
            station="KTST",
            current_temp_f=70.0,
            obs_age_minutes=10.0,
            threshold_f=80.0,
            model_probability=0.6,
            market_probability=0.4,
            edge=0.2,
            ask_price_cents=40,
            recommended_side="yes",
        )
        data = opp.to_dict()
        assert data["market_ticker"] == "TEST"
        assert data["edge"] == 0.2
        assert data["recommended_side"] == "yes"

    def test_from_dict(self):
        """Test creation from dictionary."""
        data = {
            "market_ticker": "TEST",
            "market_title": "Test",
            "station": "KTST",
            "current_temp_f": 70.0,
            "obs_age_minutes": 10.0,
            "threshold_f": 80.0,
            "model_probability": 0.6,
            "market_probability": 0.4,
            "edge": 0.2,
            "ask_price_cents": 40,
            "recommended_side": "yes",
        }
        opp = Opportunity.from_dict(data)
        assert opp.market_ticker == "TEST"
        assert opp.edge == 0.2

    def test_recommended_side_yes(self):
        """Test recommended_side is 'yes' when model > market."""
        opp = Opportunity(
            market_ticker="TEST",
            market_title="Test",
            station="KTST",
            current_temp_f=70.0,
            obs_age_minutes=10.0,
            threshold_f=80.0,
            model_probability=0.7,
            market_probability=0.5,
            edge=0.2,
            ask_price_cents=50,
            recommended_side="yes",
        )
        assert opp.recommended_side == "yes"

    def test_recommended_side_no(self):
        """Test recommended_side is 'no' when market > model."""
        opp = Opportunity(
            market_ticker="TEST",
            market_title="Test",
            station="KTST",
            current_temp_f=70.0,
            obs_age_minutes=10.0,
            threshold_f=80.0,
            model_probability=0.4,
            market_probability=0.6,
            edge=-0.2,
            ask_price_cents=60,
            recommended_side="no",
        )
        assert opp.recommended_side == "no"
