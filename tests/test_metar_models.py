"""Tests for METAR models."""

from datetime import datetime, timedelta
from zoneinfo import ZoneInfo

from kalshi_weather_arb.metar.models import Observation


class TestObservation:
    """Test Observation dataclass."""

    def test_init(self):
        """Test initialization."""
        obs = Observation(
            icao="KJFK",
            temp_c=-5.0,
            obs_time=datetime.now(ZoneInfo("America/New_York")),
        )
        assert obs.icao == "KJFK"
        assert obs.temp_c == -5.0

    def test_temp_f(self):
        """Test Fahrenheit conversion."""
        obs = Observation(
            icao="KJFK",
            temp_c=0.0,
            obs_time=datetime.now(ZoneInfo("UTC")),
        )
        assert obs.temp_f == 32.0

        obs2 = Observation(
            icao="KJFK",
            temp_c=10.0,
            obs_time=datetime.now(ZoneInfo("UTC")),
        )
        assert obs2.temp_f == 50.0

    def test_age_minutes(self):
        """Test age calculation."""
        now = datetime.now(ZoneInfo("UTC"))
        old_time = now - timedelta(minutes=5)
        obs = Observation(
            icao="KJFK",
            temp_c=10.0,
            obs_time=old_time,
        )
        assert 4 <= obs.age_minutes <= 6

    def test_dewpoint(self):
        """Test optional dewpoint."""
        obs = Observation(
            icao="KJFK",
            temp_c=10.0,
            obs_time=datetime.now(ZoneInfo("UTC")),
            dewpoint=100.0,
        )
        assert obs.dewpoint == 100.0

        obs2 = Observation(
            icao="KJFK",
            temp_c=10.0,
            obs_time=datetime.now(ZoneInfo("UTC")),
        )
        assert obs2.dewpoint is None
