"""Title parser — parse Kalshi contract titles."""

import re
from typing import Any, Dict, Optional


def parse_title(title: str) -> Optional[Dict[str, Any]]:
    """Parse a Kalshi contract title into structured data."""
    # Pattern: "Weather, Xnm, $Y/MWh"
    pattern = r"^(\w+(?:\s+\w+)?),\s*(\d+)nm,\s*\$(\d+(?:\.\d+)?)\/MWh$"
    match = re.match(pattern, title.strip())
    if not match:
        return None

    weather_raw, distance, price = match.groups()
    weather = "clear" if weather_raw.lower() == "clear sky" else weather_raw.lower()

    return {
        "weather": weather,
        "distance_nm": int(distance),
        "price_per_mwh": float(price),
    }
