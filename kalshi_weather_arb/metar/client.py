"""METAR client — fetch weather data from aviationweather.gov."""

import json
from datetime import datetime
from pathlib import Path

import requests

from .models import Observation


class METARClient:
    """METAR client — fetch observations from aviationweather.gov."""

    BASE_URL = "https://aviationweather.gov/api/data/metar"
    CACHE_DIR = Path.home() / ".cache" / "kalshi_metar"
    CACHE_TTL = 600  # 10 minutes

    def __init__(self):
        self.CACHE_DIR.mkdir(parents=True, exist_ok=True)

    def _parse_item(self, item: dict) -> Observation | None:
        """Parse a raw METAR item into an Observation.

        Args:
            item: Raw JSON dict from API

        Returns:
            Observation or None if invalid
        """
        if not isinstance(item, dict):
            return None

        # Parse timestamp
        obs_time_str = item.get("obsTime", "")
        if obs_time_str:
            try:
                obs_time = datetime.fromisoformat(
                    obs_time_str.replace("Z", "+00:00")
                )
            except ValueError:
                obs_time = datetime.now()
        else:
            obs_time = datetime.now()

        temp_c = item.get("temp", 0.0)
        if isinstance(temp_c, (int, float)):
            temp_c = float(temp_c)
        else:
            temp_c = 0.0

        dewpoint = item.get("dewpoint")
        if dewpoint is not None and not isinstance(dewpoint, (int, float)):
            dewpoint = None

        return Observation(
            icao=item.get("icaoId", ""),
            temp_c=temp_c,
            obs_time=obs_time,
            dewpoint=dewpoint,
        )

    def fetch(self, stations: list[str]) -> list[Observation]:
        """Fetch observations for multiple stations in a single GET request.

        Args:
            stations: List of ICAO station IDs (e.g., ['KJFK', 'KORD'])

        Returns:
            List of Observation objects
        """
        if not stations:
            return []

        # Build query with comma-separated station IDs
        station_str = ",".join(stations)
        url = f"{self.BASE_URL}?ids={station_str}"

        response = None
        last_error = None
        max_retries = 2
        for attempt in range(max_retries):
            try:
                response = requests.get(url, timeout=10)
                response.raise_for_status()
                break
            except requests.RequestException as e:
                last_error = e
                if attempt == max_retries - 1:
                    raise e
                continue

        if response is None:
            raise last_error or requests.RequestException("No response received")

        data = response.json()

        if not isinstance(data, list):
            return []

        observations = []
        for item in data:
            obs = self._parse_item(item)
            if obs is not None:
                observations.append(obs)

        return observations

    def get_cached(self, station: str) -> Observation | None:
        """Get cached observation for a station if not stale."""
        cache_path = self.CACHE_DIR / f"{station}.json"
        if not cache_path.exists():
            return None

        try:
            with open(cache_path) as f:
                data = json.load(f)
        except (json.JSONDecodeError, OSError):
            return None

        # Check age
        now = datetime.now()
        cached_time = datetime.fromtimestamp(data["timestamp"])
        age_seconds = (now - cached_time).total_seconds()

        if age_seconds > self.CACHE_TTL:
            return None

        # Reconstruct Observation
        obs_time = datetime.fromtimestamp(data["obs_time"])
        return Observation(
            icao=data["icao"],
            temp_c=data["temp_c"],
            obs_time=obs_time,
            dewpoint=data.get("dewpoint"),
        )

    def cache(self, observation: Observation) -> None:
        """Cache observation for 10 minutes."""
        cache_path = self.CACHE_DIR / f"{observation.icao}.json"
        data = {
            "timestamp": datetime.now().timestamp(),
            "icao": observation.icao,
            "temp_c": observation.temp_c,
            "obs_time": observation.obs_time.timestamp(),
            "dewpoint": observation.dewpoint,
        }
        with open(cache_path, "w") as f:
            json.dump(data, f)
