"""Tests for probability model module."""

from kalshi_weather_arb.probability_model import ProbabilityModel


class TestProbabilityModel:
    """Test ProbabilityModel class."""

    def test_init(self):
        """Test initialization."""
        model = ProbabilityModel()
        assert model.TIERS is not None

    def test_tier_one_high_confidence(self):
        """Test tier 1 for high confidence."""
        model = ProbabilityModel()
        tier = model.get_tier(0.8)
        assert tier["tier"] == 1
        assert tier["name"] == "high_confidence"

    def test_tier_two_moderate_confidence(self):
        """Test tier 2 for moderate confidence."""
        model = ProbabilityModel()
        tier = model.get_tier(0.5)
        assert tier["tier"] == 2
        assert tier["name"] == "moderate_confidence"

    def test_tier_three_low_confidence(self):
        """Test tier 3 for low confidence."""
        model = ProbabilityModel()
        tier = model.get_tier(0.1)
        assert tier["tier"] == 3
        assert tier["name"] == "low_confidence"

    def test_calculate_probability(self):
        """Test probability calculation."""
        model = ProbabilityModel()
        history = {"favored": 7, "total": 10}
        prob = model.calculate_probability(history, 10)
        assert prob == 0.7

    def test_calculate_probability_no_contracts(self):
        """Test probability with zero contracts returns 0.5."""
        model = ProbabilityModel()
        prob = model.calculate_probability({}, 0)
        assert prob == 0.5
