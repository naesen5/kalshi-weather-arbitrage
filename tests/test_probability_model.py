"""Tests for temperature probability model."""

import pytest
from kalshi_weather_arb.probability_model import TemperatureProbModel


class TestTemperatureProbModel:
    """Test TemperatureProbModel class."""

    def test_init(self):
        """Test initialization."""
        model = TemperatureProbModel()
        assert model is not None

    def test_p_exceed_low_temp_below_threshold(self):
        """Test probability when current temp is well below threshold."""
        model = TemperatureProbModel()
        # Current 50°F, threshold 70°F - very unlikely to reach
        prob = model.p_exceed(current_temp_f=50, dewpoint_f=40, hour_of_day=12, threshold_f=70)
        assert 0.0 <= prob <= 0.1

    def test_p_exceed_high_temp_above_threshold(self):
        """Test probability when current temp is already above threshold."""
        model = TemperatureProbModel()
        # Current 75°F, threshold 70°F - already exceeded
        prob = model.p_exceed(current_temp_f=75, dewpoint_f=60, hour_of_day=14, threshold_f=70)
        assert prob > 0.95

    def test_p_exceed_midday_typical_summer(self):
        """Test probability for typical summer midday scenario."""
        model = TemperatureProbModel()
        # Current 82°F, dewpoint 65°F, 2pm - high chance of reaching 90°F
        prob = model.p_exceed(current_temp_f=82, dewpoint_f=65, hour_of_day=14, threshold_f=90)
        assert 0.6 <= prob <= 0.85

    def test_p_exceed_early_morning_low_prob(self):
        """Test probability for early morning (lowest temps)."""
        model = TemperatureProbModel()
        # Current 55°F, dewpoint 50°F, 6am - very unlikely to reach 85°F
        prob = model.p_exceed(current_temp_f=55, dewpoint_f=50, hour_of_day=6, threshold_f=85)
        assert prob < 0.05

    def test_p_exceed_evening_high_prob(self):
        """Test probability for evening (near daily high)."""
        model = TemperatureProbModel()
        # Current 78°F, dewpoint 68°F, 5pm - daily high usually 5-10°F above current
        prob = model.p_exceed(current_temp_f=78, dewpoint_f=68, hour_of_day=17, threshold_f=85)
        assert 0.3 <= prob <= 0.6

    def test_p_exceed_extreme_dewpoint_high_humidity(self):
        """Test probability with extreme dewpoint (high humidity)."""
        model = TemperatureProbModel()
        # High dewpoint suggests higher daily high
        prob = model.p_exceed(current_temp_f=75, dewpoint_f=72, hour_of_day=13, threshold_f=88)
        assert prob > 0.5

    def test_p_exceed_low_dewpoint_low_humidity(self):
        """Test probability with low dewpoint (dry air, larger diurnal range)."""
        model = TemperatureProbModel()
        # Low dewpoint allows larger temp swing, but 60°F to 82°F is still unlikely
        prob = model.p_exceed(current_temp_f=60, dewpoint_f=35, hour_of_day=12, threshold_f=82)
        assert prob < 0.01

    def test_p_exceed_threshold_equals_current(self):
        """Test when threshold equals current temperature."""
        model = TemperatureProbModel()
        prob = model.p_exceed(current_temp_f=70, dewpoint_f=60, hour_of_day=12, threshold_f=70)
        # Should be > 0.5 since daily high > current
        assert prob > 0.5

    def test_p_exceed_edge_case_zero_prob(self):
        """Test edge case where probability approaches zero."""
        model = TemperatureProbModel()
        # 30°F current, 75°F threshold - essentially impossible
        prob = model.p_exceed(current_temp_f=30, dewpoint_f=25, hour_of_day=10, threshold_f=75)
        assert prob < 0.001

    def test_p_exceed_edge_case_one_prob(self):
        """Test edge case where probability approaches one."""
        model = TemperatureProbModel()
        # 95°F current, 80°F threshold - already exceeded
        prob = model.p_exceed(current_temp_f=95, dewpoint_f=85, hour_of_day=15, threshold_f=80)
        assert prob > 0.99

    def test_p_exceed_different_hours(self):
        """Test that hour_of_day affects probability."""
        model = TemperatureProbModel()
        # Morning: 55°F at 8am, threshold 80°F - low probability
        prob_morning = model.p_exceed(current_temp_f=55, dewpoint_f=50, hour_of_day=8, threshold_f=80)
        # Afternoon: 70°F at 3pm, threshold 80°F - higher probability
        prob_afternoon = model.p_exceed(current_temp_f=70, dewpoint_f=60, hour_of_day=15, threshold_f=80)
        # Afternoon should have higher probability (warmer and closer to daily high)
        assert prob_afternoon > prob_morning

    def test_p_exceed_dewpoint_correlation(self):
        """Test that higher dewpoint increases probability."""
        model = TemperatureProbModel()
        # Same temp/hour, different dewpoints
        prob_low_dp = model.p_exceed(current_temp_f=70, dewpoint_f=50, hour_of_day=14, threshold_f=85)
        prob_high_dp = model.p_exceed(current_temp_f=70, dewpoint_f=65, hour_of_day=14, threshold_f=85)
        # Higher dewpoint should mean higher probability
        assert prob_high_dp > prob_low_dp
