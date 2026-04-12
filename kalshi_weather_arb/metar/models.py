"""METAR observation data model."""

from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo


@dataclass
class Observation:
    """METAR observation from aviationweather.gov."""

    icao: str
    temp_c: float
    obs_time: datetime
    dewpoint: float | None = None

    @property
    def temp_f(self) -> float:
        """Convert Celsius to Fahrenheit."""
        return self.temp_c * 9 / 5 + 32

    @property
    def age_minutes(self) -> float:
        """Calculate age in minutes from observation time to now."""
        now = datetime.now(self.obs_time.tzinfo)
        return (now - self.obs_time).total_seconds() / 60
