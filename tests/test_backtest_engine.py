"""Tests for backtest engine."""

from unittest.mock import MagicMock

from kalshi_weather_arb.backtest.data_loader import KalshiPriceLoader, METARLoader
from kalshi_weather_arb.backtest.engine import Backtester
from kalshi_weather_arb.probability_model import ProbabilityModel


class TestBacktester:
    """Test backtest engine."""

    def test_run_backtest(self, tmp_path):
        """Test running backtest with synthetic data."""
        metar_loader = MagicMock(spec=METARLoader)
        price_loader = MagicMock(spec=KalshiPriceLoader)
        model = MagicMock(spec=ProbabilityModel)

        metar_loader.load_metar_history.return_value = [
            {"station": "KJFK", "timestamp": "2025-01-01T00:00:00Z", "temp_f": 45.0}
        ]
        price_loader.load_kalshi_price_history.return_value = [
            {"ticker": "KC", "timestamp": "2025-01-01T00:00:00Z", "price": 100.0}
        ]
        model.calculate_probability.return_value = 0.6

        backtester = Backtester(metar_loader, price_loader, model)
        results = backtester.run_backtest(
            station="KJFK", ticker="KC", start_date="2025-01-01", end_date="2025-01-02"
        )

        assert "total_trades" in results
        assert "total_profit" in results
        assert "win_rate" in results
        assert "avg_edge" in results
        assert "sharpe_ratio" in results

    def test_run_backtest_empty_data(self, tmp_path):
        """Test backtest with no matching data."""
        metar_loader = MagicMock(spec=METARLoader)
        price_loader = MagicMock(spec=KalshiPriceLoader)
        model = MagicMock(spec=ProbabilityModel)

        metar_loader.load_metar_history.return_value = []
        price_loader.load_kalshi_price_history.return_value = []
        model.calculate_probability.return_value = 0.6

        backtester = Backtester(metar_loader, price_loader, model)
        results = backtester.run_backtest(
            station="KJFK", ticker="KC", start_date="2025-01-01", end_date="2025-01-02"
        )

        assert results["total_trades"] == 0
        assert results["total_profit"] == 0.0
        assert results["win_rate"] == 0.0
