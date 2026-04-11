"""Tests for METAR client module."""

from unittest.mock import patch, MagicMock

from kalshi_weather_arb.metar_client import METARClient


class TestMETARClient:
    """Test METARClient class."""

    def test_init(self):
        """Test initialization."""
        client = METARClient(api_key="test-key")
        assert client.api_key == "test-key"
        assert client.BASE_URL == "https://api.aviationweather.gov/v1"

    @patch("requests.get")
    def test_parse_station(self, mock_get):
        """Test fetch_station."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"id": "KJFK", "name": "Test Station"}
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = METARClient(api_key="test-key")
        result = client.fetch_station("KJFK")
        assert result["id"] == "KJFK"

    @patch("requests.get")
    def test_parse_parameter(self, mock_get):
        """Test fetch_parameters."""
        mock_response = MagicMock()
        mock_response.json.return_value = [{"id": "TMP", "name": "Temperature"}]
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        client = METARClient(api_key="test-key")
        result = client.fetch_parameters("KJFK")
        assert len(result) == 1

    def test_calculate_age(self):
        """Test age calculation."""
        client = METARClient(api_key="test-key")
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        old_time = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=5)
        age = client.calculate_age(old_time.isoformat())
        assert 4 <= age <= 6

    def test_is_stale(self):
        """Test stale check."""
        client = METARClient(api_key="test-key")
        from datetime import datetime, timedelta
        from zoneinfo import ZoneInfo

        old_time = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=15)
        assert client.is_stale(old_time.isoformat(), threshold_minutes=10.0) is True

        recent_time = datetime.now(ZoneInfo("UTC")) - timedelta(minutes=5)
        assert client.is_stale(recent_time.isoformat(), threshold_minutes=10.0) is False
