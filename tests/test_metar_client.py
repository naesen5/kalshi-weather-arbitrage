"""Tests for METAR client module."""

from datetime import datetime, timedelta
from unittest.mock import patch

import pytest

import requests
from kalshi_weather_arb.metar.client import METARClient
from kalshi_weather_arb.metar.models import Observation


class TestMETARClient:
    """Test METARClient class."""

    def test_init(self):
        """Test initialization."""
        client = METARClient()
        assert client.BASE_URL == "https://aviationweather.gov/api/data/metar"
        assert client.CACHE_DIR.exists()

    @patch("requests.get")
    def test_fetch(self, mock_get):
        """Test fetch with multiple stations."""
        # Load fixture
        fixture_path = "tests/fixtures/metar_response.json"
        with open(fixture_path) as f:
            fixture_data = f.read()

        mock_response = type("MockResponse", (), {})()
        mock_response.json = lambda: [
            {"icaoId": "KJFK", "temp": -5.5, "obsTime": "2026-04-12T17:30:00Z", "dewpoint": 100.0},
            {"icaoId": "KORD", "temp": 12.0, "obsTime": "2026-04-12T17:25:00Z", "dewpoint": -50.0},
        ]
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        client = METARClient()
        result = client.fetch(["KJFK", "KORD"])

        assert len(result) == 2
        assert result[0].icao == "KJFK"
        assert result[0].temp_c == -5.5
        assert result[0].temp_f == pytest.approx(22.1, rel=0.1)
        assert result[0].dewpoint == 100.0

        mock_get.assert_called_once()

    @patch("requests.get")
    def test_fetch_empty_list(self, mock_get):
        """Test fetch with empty stations list."""
        mock_response = type("MockResponse", (), {})()
        mock_response.json = lambda: []
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        client = METARClient()
        result = client.fetch([])

        assert result == []
        mock_get.assert_not_called()

    @patch("requests.get")
    def test_fetch_single_station(self, mock_get):
        """Test fetch with single station."""
        mock_response = type("MockResponse", (), {})()
        mock_response.json = lambda: [
            {"icaoId": "KJFK", "temp": 10.0, "obsTime": "2026-04-12T17:30:00Z"}
        ]
        mock_response.raise_for_status = lambda: None
        mock_get.return_value = mock_response

        client = METARClient()
        result = client.fetch(["KJFK"])

        assert len(result) == 1
        assert result[0].icao == "KJFK"
        assert result[0].temp_c == 10.0
        assert result[0].temp_f == 50.0

    @patch("requests.get")
    def test_fetch_timeout_retry(self, mock_get):
        """Test fetch retries on failure."""
        # First call raises exception, second succeeds
        def side_effect(*args, **kwargs):
            if mock_get.call_count == 1:
                raise requests.exceptions.Timeout("Timeout")
            mock_response = type("MockResponse", (), {})()
            mock_response.json = lambda: [{"icaoId": "KJFK", "temp": 10.0, "obsTime": "2026-04-12T17:30:00Z"}]
            mock_response.raise_for_status = lambda: None
            return mock_response

        mock_get.side_effect = side_effect

        client = METARClient()
        result = client.fetch(["KJFK"])

        assert len(result) == 1
        assert result[0].icao == "KJFK"

    def test_cache_roundtrip(self):
        """Test cache save/load."""
        client = METARClient()
        now = datetime.now()
        obs = Observation(icao="KJFK", temp_c=10.0, obs_time=now, dewpoint=100.0)

        client.cache(obs)
        cached = client.get_cached("KJFK")

        assert cached is not None
        assert cached.icao == "KJFK"
        assert cached.temp_c == 10.0
        assert cached.dewpoint == 100.0
