"""METAR client — fetch weather data from aviationweather.gov."""

import json
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional

import requests


class METARClient:
    """METAR client — fetch weather data from aviationweather.gov."""

    BASE_URL = "https://api.aviationweather.gov/v1"

    def __init__(self, api_key: str):
        self.api_key = api_key

    def fetch_station(self, station_id: str) -> Dict[str, Any]:
        """Fetch station data."""
        response = requests.get(
            f"{self.BASE_URL}/stations/{station_id}",
            headers={"X-API-Key": self.api_key},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def fetch_parameters(self, station_id: str) -> List[Dict[str, Any]]:
        """Fetch parameters for a station."""
        response = requests.get(
            f"{self.BASE_URL}/stations/{station_id}/parameters",
            headers={"X-API-Key": self.api_key},
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def calculate_age(self, timestamp: str) -> float:
        """Calculate age in minutes from ISO timestamp."""
        dt = datetime.fromisoformat(timestamp.replace("Z", "+00:00"))
        now = datetime.now(dt.tzinfo)
        return (now - dt).total_seconds() / 60

    def is_stale(self, timestamp: str, threshold_minutes: float = 10.0) -> bool:
        """Check if data is stale."""
        return self.calculate_age(timestamp) > threshold_minutes
