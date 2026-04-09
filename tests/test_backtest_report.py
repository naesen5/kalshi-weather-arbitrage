"""Tests for backtest report."""

from unittest.mock import MagicMock

from kalshi_weather_arb.backtest.report import BacktestReport


class TestBacktestReport:
    """Test backtest report."""

    def test_print_summary(self):
        """Test printing summary."""
        console = MagicMock()
        report = BacktestReport(console=console)

        results = {
            "station": "KJFK",
            "ticker": "KC",
            "start_date": "2025-01-01",
            "end_date": "2025-01-02",
            "total_trades": 10,
            "total_profit": 500.0,
            "win_rate": 0.6,
            "avg_edge": 10.0,
            "sharpe_ratio": 2.5,
        }

        report.print_summary(results)

        assert console.print.called
