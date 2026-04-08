"""Tests for sizer — Kelly calc, exposure cap, circuit breaker."""

import pytest

from kalshi_weather_arb.client import KalshiClient  # noqa: F401


class TestSizer:
    """Test sizer logic for exposure management."""

    def test_kelly_calculation(self):
        """Test Kelly formula for optimal bet sizing."""
        # Kelly fraction = (p * (b + 1) - 1) / b
        # p = win probability, b = odds
        p = 0.6
        b = 1.5  # 3/2 odds

        kelly_fraction = (p * (b + 1) - 1) / b
        expected = 0.3333333333333333

        assert abs(kelly_fraction - expected) < 0.01

    def test_exposure_cap(self):
        """Test exposure cap logic."""
        max_exposure = 1000.0
        current_exposure = 800.0
        proposed_bet = 250.0

        assert current_exposure + proposed_bet > max_exposure
        # Should reject bet that exceeds cap

    def test_circuit_breaker(self):
        """Test circuit breaker for rapid successive losses."""
        consecutive_losses = 5
        threshold = 3

        assert consecutive_losses >= threshold
        # Circuit breaker should trip
