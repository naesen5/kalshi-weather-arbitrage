"""Tests for scanner module."""

from unittest.mock import MagicMock

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.scanner import Scanner


class TestScanner:
    """Test Scanner class."""

    def test_init(self):
        """Test initialization."""
        mock_client = MagicMock(spec=KalshiClient)
        scanner = Scanner(mock_client)
        assert scanner.client == mock_client

    def test_scan_opportunities(self):
        """Test scan_contracts returns empty list."""
        mock_client = MagicMock(spec=KalshiClient)
        scanner = Scanner(mock_client)
        result = scanner.scan_contracts()
        assert result == []

    def test_filter_by_weather(self):
        """Test filter_by_weather."""
        mock_client = MagicMock(spec=KalshiClient)
        scanner = Scanner(mock_client)
        contracts = [
            {"weather": "clear"},
            {"weather": "storm"},
            {"weather": "clear"},
        ]
        result = scanner.filter_by_weather(contracts, "clear")
        assert len(result) == 2
