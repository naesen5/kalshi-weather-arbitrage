"""Tests for sizer module."""


from kalshi_weather_arb.sizer import Sizer


class TestSizer:
    """Test Sizer class."""

    def test_init(self):
        """Test initialization."""
        sizer = Sizer(edge=0.05, exposure_cap=100.0, circuit_breaker=500.0)
        assert sizer.edge == 0.05
        assert sizer.exposure_cap == 100.0
        assert sizer.circuit_breaker == 500.0

    def test_kelly_calculation(self):
        """Test kelly calculation."""
        sizer = Sizer(edge=0.05)
        result = sizer.kelly(odds=2.0)
        assert result > 0

    def test_kelly_zero_odds(self):
        """Test kelly with odds <= 1 returns 0."""
        sizer = Sizer()
        assert sizer.kelly(odds=1.0) == 0
        assert sizer.kelly(odds=0.5) == 0

    def test_exposure_cap(self):
        """Test exposure cap limits bet."""
        sizer = Sizer(edge=0.1, exposure_cap=50.0, circuit_breaker=1000.0)
        bet = sizer.size_bet(odds=2.0, max_bet=1000.0)
        assert bet <= 50.0

    def test_circuit_breaker(self):
        """Test circuit breaker limits bet."""
        sizer = Sizer(edge=0.01, exposure_cap=None, circuit_breaker=100.0)
        bet = sizer.size_bet(odds=2.0, max_bet=1000.0)
        assert bet <= 100.0
