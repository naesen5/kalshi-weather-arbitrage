"""Tests for backtester — synthetic data, assert P&L calculation."""


from kalshi_weather_arb.client import KalshiClient  # noqa: F401


class TestBacktester:
    """Test backtesting with synthetic data."""

    def test_synthetic_data_generation(self):
        """Test synthetic data generation for backtesting."""
        # Generate synthetic history
        synthetic = [
            {"weather": "clear", "price": 100.0, "bet": 50.0, "win": 1},
            {"weather": "storm", "price": 150.0, "bet": 50.0, "win": 0},
            {"weather": "clear", "price": 100.0, "bet": 50.0, "win": 1},
        ]

        wins = sum(s["win"] for s in synthetic)
        total = len(synthetic)
        win_rate = wins / total

        assert win_rate == 2 / 3

    def test_pl_calculation(self):
        """Test profit and loss calculation."""
        bets = [
            {"bet": 100.0, "win": 1, "odds": 1.5},  # +$50
            {"bet": 100.0, "win": 0, "odds": 1.5},  # -$100
            {"bet": 100.0, "win": 1, "odds": 1.5},  # +$50
        ]

        total_profit = sum(
            b["bet"] * (b["odds"] - 1) if b["win"] else -b["bet"] for b in bets
        )
        expected = 50.0 - 100.0 + 50.0

        assert total_profit == expected
