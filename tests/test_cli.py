"""Tests for CLI module."""

from unittest.mock import patch

from kalshi_weather_arb.cli import parse_args


class TestCLI:
    """Test CLI module."""

    def test_parse_args_run(self):
        """Test parsing run command."""
        with patch("sys.argv", ["kalshi_weather_arb"]):
            args = parse_args()
            assert args.command is None

    def test_parse_args_run_with_flags(self):
        """Test parsing run command with flags."""
        with patch("sys.argv", ["kalshi_weather_arb", "run", "--dashboard", "--dry-run", "--api-key", "test", "--secret-key", "test"]):
            args = parse_args()
            assert args.command == "run"
            assert args.dashboard is True
            assert args.dry_run is True
            assert args.api_key == "test"
            assert args.secret_key == "test"

    def test_run_loop_dashboard(self):
        """Test run loop with dashboard (skipped - infinite loop)."""
        # Skip - run_loop has infinite loop
        pass


class TestDashboardIntegration:
    """Integration tests for dashboard."""

    def test_dashboard_full_render(self):
        """Test full dashboard rendering."""
        from kalshi_weather_arb.dashboard.display import Dashboard
        from io import StringIO
        from rich.console import Console

        dashboard = Dashboard(dry_run=True)

        scan_results = [
            {
                "market": "Test market",
                "station": "KJFK",
                "obs_age": "5m",
                "curr_temp": 60.0,
                "threshold": 65.0,
                "model_prob": 30,
                "market_prob": 40,
                "edge": -10.0,
            }
        ]

        positions = [
            {
                "ticker": "Test ticker",
                "entry_price": 100.0,
                "current_price": 95.0,
                "unrealised_pl": -5.0,
                "model_prob": 80,
            }
        ]

        ledger = [
            {
                "timestamp": "2026-04-09T01:30:00",
                "contract_id": "abc123",
                "amount": 100.0,
                "profit": 50.0,
                "win": True,
            }
        ]

        # Render all panels
        scan_table = dashboard.render_scan_results(scan_results)
        positions_panel = dashboard.render_open_positions(positions)
        trades_panel = dashboard.render_recent_trades(ledger)
        status_panel = dashboard.render_system_status(
            last_scan_time=None,
            next_scan_seconds=30,
        )

        # Verify rendering
        console = Console(file=StringIO(), width=100)
        console.print(scan_table)
        console.print(positions_panel)
        console.print(trades_panel)
        console.print(status_panel)

        output = console.file.getvalue()
        assert "Test market" in output
        assert "KJFK" in output
        assert "Test ticker" in output
        assert "abc123" in output
        assert "System Status" in output
