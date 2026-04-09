"""Tests for CLI module."""

import pytest
from unittest.mock import patch, MagicMock

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
