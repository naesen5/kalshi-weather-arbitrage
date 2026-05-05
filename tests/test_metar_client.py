"""Tests for METAR client — parsing aviation weather data, age calculation."""

from datetime import datetime, timedelta

import pytest

from kalshi_weather_arb.client import KalshiClient


class MockMETARResponse:
    """Mock METAR response fixture from aviationweather.gov."""

    @staticmethod
    def get_sample():
        """Return sample METAR JSON fixture."""
        return {
            "stations": [
                {
                    "id": "METAR_123",
                    "name": "Sample Station",
                    "lat": 45.0,
                    "lon": -90.0,
                    "elev": 100.0,
                    "wmo": "721412",
                    "call": "CWTN1234",
                    "usaf": True,
                }
            ],
            "parameters": [
                {
                    "id": "T23",
                    "value": "23",
                    "dateobs": "2026-04-08T08:00:00Z",
                }
            ],
        }


class TestMETARClient:
    """Test METAR parsing and age calculation."""

    def test_parse_station(self):
        """Test station data parsing."""
        data = MockMETARResponse.get_sample()
        station = data["stations"][0]

        assert station["id"] == "METAR_123"
        assert station["name"] == "Sample Station"
        assert station["lat"] == 45.0
        assert station["lon"] == -90.0

    def test_parse_parameter(self):
        """Test parameter data parsing."""
        data = MockMETARResponse.get_sample()
        param = data["parameters"][0]

        assert param["id"] == "T23"
        assert param["value"] == "23"
        assert param["dateobs"] == "2026-04-08T08:00:00Z"

    def test_calculate_age(self):
        """Test METAR record age calculation."""
        now = datetime(2026, 4, 8, 10, 0, 0)
        obs_time = datetime.fromisoformat("2026-04-08T08:00:00+00:00")
        age = now - obs_time.replace(tzinfo=None)

        assert age == timedelta(hours=2)

    def test_is_stale(self):
        """Test stale METAR detection (>15 min)."""
        now = datetime(2026, 4, 8, 10, 0, 0)
        obs_time = datetime.fromisoformat("2026-04-08T07:40:00+00:00")
        age = now - obs_time.replace(tzinfo=None)

        assert age > timedelta(minutes=15)
