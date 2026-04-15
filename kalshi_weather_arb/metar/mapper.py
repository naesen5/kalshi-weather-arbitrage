"""Market-to-station mapper for Kalshi temperature markets."""

import re
from pathlib import Path
from typing import Optional

import yaml


class StationMapper:
    """Map Kalshi market titles to ICAO station codes."""

    def __init__(self, yaml_path: Optional[Path] = None):
        """Initialize mapper with station YAML file.
        
        Args:
            yaml_path: Path to stations.yaml (defaults to package location)
        """
        if yaml_path is None:
            pkg_dir = Path(__file__).parent
            yaml_path = pkg_dir / "stations.yaml"
        
        self.stations = self._load_stations(yaml_path)
    
    def _load_stations(self, yaml_path: Path) -> list[dict]:
        """Load station mapping from YAML file."""
        with open(yaml_path) as f:
            data = yaml.safe_load(f)
        return data.get("stations", [])
    
    def match_market(self, market_title: str) -> Optional[str]:
        """Find ICAO code matching a Kalshi market title.
        
        Uses fuzzy matching against station patterns.
        
        Args:
            market_title: Kalshi market title (e.g., "Will it be hotter than 90 in NYC on July 15?")
        
        Returns:
            ICAO code if match found, None otherwise
        """
        title_lower = market_title.lower()
        
        for station in self.stations:
            pattern = station.get("pattern", "").lower()
            if self._fuzzy_match(pattern, title_lower):
                return station["icao"]
        
        return None
    
    def _fuzzy_match(self, pattern: str, text: str) -> bool:
        """Check if pattern matches text with fuzzy matching.
        
        Pattern uses pipe-separated alternatives (e.g., "Chicago|IL|Illinois").
        Each alternative is matched as a whole word (case-insensitive).
        
        Args:
            pattern: YAML pattern string with pipe-separated alternatives
            text: Lowercase market title
        
        Returns:
            True if match found
        """
        alternatives = [a.strip().lower() for a in pattern.split("|")]
        
        for alt in alternatives:
            # Use word boundary matching: alt must be whole word or start/end of string
            # Pattern: (\balt\b) or (alt$) or (^alt)
            import re
            # Match alt as whole word or at start/end of string
            if re.search(rf'\b{re.escape(alt)}\b|^{re.escape(alt)}$|\b{re.escape(alt)}$|^{re.escape(alt)}\b', text):
                return True
        
        return False
    
    def get_station_info(self, icao: str) -> Optional[dict]:
        """Get station info by ICAO code.
        
        Args:
            icao: ICAO station code (e.g., "KJFK")
        
        Returns:
            Station dict with city, region, pattern or None
        """
        for station in self.stations:
            if station.get("icao") == icao:
                return station
        return None

    def get_station(self, city: str) -> Optional[str]:
        """Get ICAO station code for a city name.
        
        Args:
            city: City name (e.g., "NYC", "Chicago")
        
        Returns:
            ICAO code if match found, None otherwise
        """
        # Try matching against city field in stations
        city_lower = city.lower()
        for station in self.stations:
            station_city = station.get("city", "").lower()
            if city_lower in station_city or station_city in city_lower:
                return station.get("icao")
        
        # Try matching against pattern alternatives
        for station in self.stations:
            pattern = station.get("pattern", "").lower()
            alternatives = [a.strip().lower() for a in pattern.split("|")]
            for alt in alternatives:
                if alt == city_lower or city_lower in alt or alt in city_lower:
                    return station.get("icao")
        
        return None
