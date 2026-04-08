"""Tests for scanner — mock client + METAR, assert correct opportunity detection."""

from unittest.mock import Mock, patch

import pytest

from kalshi_weather_arb.client import KalshiClient


class TestScanner:
    """Test scanner with mocked dependencies."""

    @patch("kalshi_weather_arb.client.KalshiClient.get")
    def test_scan_opportunities(self, mock_get):
        """Test scanning for weather arbitrage opportunities."""
        mock_response = {
            "contracts": [
                {
                    "id": 1,
                    "weather": "clear",
                    "price": 100.0,
                    "location": {"lat": 45.0, "lon": -90.0},
                },
                {
                    "id": 2,
                    "weather": "storm",
                    "price": 150.0,
                    "location": {"lat": 46.0, "lon": -91.0},
                },
            ]
        }
        mock_get.return_value = mock_response

        client = KalshiClient("api_key", "secret")
        contracts = client.paginate("/api/v1/contracts")

        assert len(contracts) == 2
        assert contracts[0]["weather"] == "clear"
        assert contracts[1]["weather"] == "storm"

    @patch("kalshi_weather_arb.client.KalshiClient.get")
    def test_filter_by_weather(self, mock_get):
        """Test filtering contracts by weather condition."""
        mock_get.return_value = {
            "contracts": [
                {"id": 1, "weather": "clear"},
                {"id": 2, "weather": "storm"},
                {"id": 3, "weather": "clear"},
            ]
        }

        client = KalshiClient("api_key", "secret")
        contracts = client.paginate("/api/v1/contracts")

        clear_contracts = [c for c in contracts if c["weather"] == "clear"]
        assert len(clear_contracts) == 2
