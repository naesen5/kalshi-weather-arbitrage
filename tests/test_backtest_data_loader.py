"""Tests for backtest data loader."""

import json
from datetime import datetime, timezone
from unittest.mock import Mock, patch

from kalshi_weather_arb.backtest.data_loader import KalshiPriceLoader, METARLoader


class TestMETARLoader:
    """Test METAR data loading."""

    @patch("kalshi_weather_arb.backtest.data_loader.requests")
    def test_load_metar_history_no_api_token(self, mock_requests, tmp_path):
        """Test loading METAR history without API token returns empty list."""
        loader = METARLoader(cache_dir=str(tmp_path))
        data = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-02")
        assert data == []

    @patch("kalshi_weather_arb.backtest.data_loader.requests")
    def test_load_metar_history_api_success(self, mock_requests, tmp_path):
        """Test loading METAR history from real NOAA ISD API."""
        # Mock ISD API response with TAVG (daily average temperature) in Celsius
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "stationID": "USW00012839",
                    "date": "2025-01-01",
                    "data": [
                        {"datatype": "TAVG", "value": 10.0},
                        {"datatype": "TMAX", "value": 15.0},
                        {"datatype": "TMIN", "value": 5.0},
                    ],
                },
                {
                    "stationID": "USW00012839",
                    "date": "2025-01-02",
                    "data": [
                        {"datatype": "TAVG", "value": 12.0},
                        {"datatype": "TMAX", "value": 17.0},
                        {"datatype": "TMIN", "value": 7.0},
                    ],
                },
            ]
        }
        mock_requests.get.return_value = mock_response
        mock_response.raise_for_status = Mock()

        loader = METARLoader(
            api_token="dummy-token",
            cache_dir=str(tmp_path)
        )
        data = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-02")

        assert len(data) == 2
        assert data[0]["station"] == "KJFK"
        assert "timestamp" in data[0]
        assert "temp_f" in data[0]
        # 10.0 C = 50.0 F
        assert data[0]["temp_f"] == 50.0
        # 12.0 C = 53.6 F
        assert data[1]["temp_f"] == 53.6

    @patch("kalshi_weather_arb.backtest.data_loader.requests")
    def test_load_metar_history_api_error(self, mock_requests, tmp_path):
        """Test error handling — returns empty list on API failure."""
        mock_requests.get.side_effect = Exception("Network error")

        loader = METARLoader(
            api_token="dummy-token",
            cache_dir=str(tmp_path)
        )
        data = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-02")

        assert data == []

    @patch("kalshi_weather_arb.backtest.data_loader.requests")
    def test_load_metar_history_no_data(self, mock_requests, tmp_path):
        """Test loading when API returns empty results."""
        mock_response = Mock()
        mock_response.json.return_value = {"results": []}
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        loader = METARLoader(
            api_token="dummy-token",
            cache_dir=str(tmp_path)
        )
        data = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-02")

        assert data == []

    @patch("kalshi_weather_arb.backtest.data_loader.requests")
    def test_load_metar_history_caching(self, mock_requests, tmp_path):
        """Test that results are cached to disk."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "results": [
                {
                    "stationID": "USW00012839",
                    "date": "2025-01-01",
                    "data": [{"datatype": "TAVG", "value": 10.0}],
                },
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_requests.get.return_value = mock_response

        loader = METARLoader(
            api_token="dummy-token",
            cache_dir=str(tmp_path)
        )

        # First call — should hit API
        data1 = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-01")
        assert len(data1) == 1
        assert data1[0]["temp_f"] == 50.0

        # Second call — should use cache
        data2 = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-01")

        # API should NOT be called again
        mock_requests.get.assert_called_once()
        assert data1 == data2

    def test_load_metar_history_no_api_key(self, tmp_path):
        """Test that loader works without API key (returns empty list)."""
        loader = METARLoader(cache_dir=str(tmp_path))
        data = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-02")
        assert data == []


class TestKalshiPriceLoader:
    """Test Kalshi price data loading with real API integration."""

    @patch("kalshi_weather_arb.backtest.data_loader.KalshiClient")
    def test_load_kalshi_price_history(self, mock_client_class, tmp_path):
        """Test loading Kalshi price history from real API."""
        mock_client = Mock()
        mock_client.get_historical_candlesticks.return_value = [
            {
                "ts_ms": 1704067200000,
                "open": 50,
                "close": 55,
                "high": 60,
                "low": 48,
                "volume": 1000,
            },
            {
                "ts_ms": 1704153600000,
                "open": 55,
                "close": 52,
                "high": 58,
                "low": 50,
                "volume": 800,
            },
        ]
        mock_client_class.return_value = mock_client

        loader = KalshiPriceLoader(api_key="dummy", cache_dir=str(tmp_path))
        data = loader.load_kalshi_price_history("KC-JFK-90")

        assert len(data) == 2
        assert data[0]["ticker"] == "KC-JFK-90"
        assert "timestamp" in data[0]
        assert "price" in data[0]
        assert "open" in data[0]
        assert "high" in data[0]
        assert "low" in data[0]
        assert "volume" in data[0]
        mock_client.get_historical_candlesticks.assert_called_once_with("KC-JFK-90")

    @patch("kalshi_weather_arb.backtest.data_loader.KalshiClient")
    def test_load_kalshi_price_history_empty(self, mock_client_class, tmp_path):
        """Test loading when API returns empty ticks."""
        mock_client = Mock()
        mock_client.get_historical_candlesticks.return_value = []
        mock_client_class.return_value = mock_client

        loader = KalshiPriceLoader(api_key="dummy", cache_dir=str(tmp_path))
        data = loader.load_kalshi_price_history("KC-EMPTY")

        assert data == []

    @patch("kalshi_weather_arb.backtest.data_loader.KalshiClient")
    def test_load_kalshi_price_history_error(self, mock_client_class, tmp_path):
        """Test error handling — returns empty list on API failure."""
        mock_client = Mock()
        mock_client.get_historical_candlesticks.side_effect = Exception("API error")
        mock_client_class.return_value = mock_client

        loader = KalshiPriceLoader(api_key="dummy", cache_dir=str(tmp_path))
        data = loader.load_kalshi_price_history("KC-ERROR")

        assert data == []

    @patch("kalshi_weather_arb.backtest.data_loader.KalshiClient")
    def test_load_kalshi_price_history_caching(self, mock_client_class, tmp_path):
        """Test that results are cached to disk."""
        mock_client = Mock()
        mock_client.get_historical_candlesticks.return_value = [
            {
                "ts_ms": 1704067200000,
                "open": 50,
                "close": 55,
                "high": 60,
                "low": 48,
                "volume": 1000,
            },
        ]
        mock_client_class.return_value = mock_client

        loader = KalshiPriceLoader(api_key="dummy", cache_dir=str(tmp_path))

        # First call — should hit API
        data1 = loader.load_kalshi_price_history("KC-CACHE")
        assert len(data1) == 1

        # Second call — should use cache
        mock_client.reset_mock()
        data2 = loader.load_kalshi_price_history("KC-CACHE")

        # API should NOT be called again
        mock_client.get_historical_candlesticks.assert_not_called()
        assert data1 == data2

    def test_load_kalshi_price_history_no_api_key(self, tmp_path):
        """Test that loader works without API key (uses default client)."""
        loader = KalshiPriceLoader(cache_dir=str(tmp_path))
        assert loader.client is not None
