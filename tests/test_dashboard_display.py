"""Tests for dashboard display module."""

from datetime import datetime
from io import StringIO

from rich.console import Console




from kalshi_weather_arb.dashboard.display import Dashboard


class TestDashboardDisplay:
    """Test Dashboard class."""

    def test_init(self):
        """Test initialization."""
        dashboard = Dashboard(dry_run=True)
        assert dashboard.dry_run is True
        assert dashboard.update_interval == 30.0

    def test_start_stop(self):
        """Test start/stop (skipped - requires terminal)."""
        # Skip - requires actual terminal for rich.live
        pass

    def test_format_edge_positive(self):
        """Test edge formatting for positive edge."""
        dashboard = Dashboard()
        text = dashboard._format_edge(10.0)
        assert "green" in str(text.style)
        assert "+10.0%" in str(text)

    def test_format_edge_negative(self):
        """Test edge formatting for negative edge."""
        dashboard = Dashboard()
        text = dashboard._format_edge(-5.0)
        assert "red" in str(text.style)
        assert "-5.0%" in str(text)

    def test_format_edge_borderline(self):
        """Test edge formatting for borderline edge."""
        dashboard = Dashboard()
        text = dashboard._format_edge(2.0)
        assert "yellow" in str(text.style)
        assert "+2.0%" in str(text)

    def test_format_checkmark_positive(self):
        """Test checkmark for positive edge."""
        dashboard = Dashboard()
        text = dashboard._format_checkmark(5.0)
        assert "green" in str(text.style)

    def test_format_checkmark_negative(self):
        """Test checkmark for negative edge."""
        dashboard = Dashboard()
        text = dashboard._format_checkmark(-5.0)
        assert "red" in str(text.style)

    def test_render_scan_results_empty(self):
        """Test scan results table with no data."""
        dashboard = Dashboard()
        table = dashboard.render_scan_results([])
        assert table.title == "Current Scan"

    def test_render_scan_results_with_data(self):
        """Test scan results table with data."""
        dashboard = Dashboard()
        results = [
            {
                "market": "NYC daily high > 65°F today",
                "station": "KJFK",
                "obs_age": "12m",
                "curr_temp": 71.2,
                "threshold": 65.0,
                "model_prob": 96,
                "market_prob": 72,
                "edge": 24.0,
            }
        ]
        table = dashboard.render_scan_results(results)
        assert table.title == "Current Scan"
        # Table renders as segments, not string; check via console
        console = Console(file=StringIO(), width=100)
        console.print(table)
        output = console.file.getvalue()
        assert "KJFK" in output

    def test_render_open_positions_empty(self):
        """Test open positions panel with no data."""
        dashboard = Dashboard()
        panel = dashboard.render_open_positions([])
        # rich.Panel doesn's render as string directly; check title attribute
        assert panel.title == "Open Positions"

    def test_render_open_positions_with_data(self):
        """Test open positions panel with data."""
        dashboard = Dashboard()
        positions = [
            {
                "ticker": "NYC daily high > 65°F today",
                "entry_price": 100.0,
                "current_price": 95.0,
                "unrealised_pl": -5.0,
                "model_prob": 80,
            }
        ]
        panel = dashboard.render_open_positions(positions)
        assert panel.title == "Open Positions"

    def test_render_recent_trades_empty(self):
        """Test recent trades panel with no data."""
        dashboard = Dashboard()
        panel = dashboard.render_recent_trades([])
        assert panel.title == "Recent Trades"

    def test_render_recent_trades_with_data(self):
        """Test recent trades panel with data."""
        dashboard = Dashboard()
        ledger = [
            {
                "timestamp": "2026-04-09T01:30:00",
                "contract_id": "abc123",
                "amount": 100.0,
                "profit": 50.0,
                "win": True,
            }
        ]
        panel = dashboard.render_recent_trades(ledger)
        assert panel.title == "Recent Trades"

    def test_render_system_status(self):
        """Test system status panel."""
        dashboard = Dashboard(dry_run=True)
        panel = dashboard.render_system_status(
            last_scan_time=datetime(2026, 4, 9, 1, 30, 0),
            next_scan_seconds=45,
            balance=1000.0,
            daily_pl=50.0,
            daily_exposure_used=200.0,
            daily_exposure_max=500.0,
        )
        assert panel.title == "System Status"

    def test_update(self):
        """Test update (skipped - requires terminal)."""
        # Skip - requires actual terminal for rich.live
        pass
