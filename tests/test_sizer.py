"""Tests for sizer module."""

from kalshi_weather_arb.sizer import DailyExposure, Sizer


class TestDailyExposure:
    """Test DailyExposure class."""

    def test_init(self):
        """Test initialization."""
        exposure = DailyExposure()
        assert exposure.max_exposure == 500.0
        assert exposure.current_exposure == 0.0

    def test_init_custom_max(self):
        """Test initialization with custom max exposure."""
        exposure = DailyExposure(max_exposure=1000.0)
        assert exposure.max_exposure == 1000.0

    def test_add_bet_under_limit(self):
        """Test adding bet under limit."""
        exposure = DailyExposure(max_exposure=100.0)
        result = exposure.add_bet(50.0)
        assert result is True
        assert exposure.current_exposure == 50.0

    def test_add_bet_over_limit(self):
        """Test adding bet over limit."""
        exposure = DailyExposure(max_exposure=100.0)
        exposure.add_bet(80.0)
        result = exposure.add_bet(30.0)
        assert result is False
        assert exposure.current_exposure == 80.0

    def test_can_afford_under_limit(self):
        """Test can_afford under limit."""
        exposure = DailyExposure(max_exposure=100.0)
        assert exposure.can_afford(50.0) is True

    def test_can_afford_over_limit(self):
        """Test can_afford over limit."""
        exposure = DailyExposure(max_exposure=100.0)
        exposure.add_bet(80.0)
        assert exposure.can_afford(30.0) is False


class TestSizer:
    """Test Sizer class."""

    def test_init(self):
        """Test initialization."""
        sizer = Sizer(edge=0.05)
        assert sizer.edge == 0.05
        assert sizer.exposure_cap is None
        assert sizer.circuit_breaker == 1000.0

    def test_init_all_params(self):
        """Test initialization with all parameters."""
        sizer = Sizer(edge=0.03, exposure_cap=200.0, circuit_breaker=500.0)
        assert sizer.edge == 0.03
        assert sizer.exposure_cap == 200.0
        assert sizer.circuit_breaker == 500.0

    def test_kelly_positive_edge(self):
        """Test kelly calculation with positive edge."""
        sizer = Sizer(edge=0.05)
        result = sizer.kelly(odds=2.0)
        # (2-1)/2 - 0.05/2 = 0.5 - 0.025 = 0.475
        assert abs(result - 0.475) < 0.001

    def test_kelly_zero_edge(self):
        """Test kelly calculation with zero edge."""
        sizer = Sizer(edge=0.0)
        result = sizer.kelly(odds=2.0)
        # (2-1)/2 - 0/2 = 0.5
        assert abs(result - 0.5) < 0.001

    def test_kelly_odds_one(self):
        """Test kelly calculation with odds=1."""
        sizer = Sizer(edge=0.05)
        result = sizer.kelly(odds=1.0)
        assert result == 0.0

    def test_kelly_odds_below_one(self):
        """Test kelly calculation with odds<1."""
        sizer = Sizer(edge=0.05)
        result = sizer.kelly(odds=0.5)
        assert result == 0.0

    def test_size_bet_no_caps(self):
        """Test size_bet with no caps."""
        sizer = Sizer(edge=0.05)
        result = sizer.size_bet(odds=2.0, max_bet=100.0)
        # kelly_frac = 0.475, bet = 0.475 * 100 = 47.5
        assert abs(result - 47.5) < 0.1

    def test_size_bet_exposure_cap(self):
        """Test size_bet with exposure cap."""
        sizer = Sizer(edge=0.05, exposure_cap=30.0)
        result = sizer.size_bet(odds=2.0, max_bet=100.0)
        assert result == 30.0

    def test_size_bet_circuit_breaker(self):
        """Test size_bet with circuit breaker."""
        sizer = Sizer(edge=0.05, circuit_breaker=40.0)
        result = sizer.size_bet(odds=2.0, max_bet=100.0)
        # kelly_frac = 0.475, bet = 47.5, capped at 40
        assert result == 40.0
