"""Title parser — parse Kalshi temperature market titles."""

import re
from dataclasses import dataclass
from typing import Optional


@dataclass
class TitleParsed:
    """Parsed temperature market title."""

    city: str
    """City name (may include state abbreviation)."""

    threshold_f: int
    """Temperature threshold in Fahrenheit."""

    direction: str
    """Direction: 'HIGH' for above threshold, 'RANGE' for temperature range."""

    is_range: bool
    """True if this is a range market (e.g., 75-85°F)."""


def parse_temperature_title(title: str) -> Optional[TitleParsed]:
    """
    Parse a Kalshi temperature market title into structured data.

    Supported formats:
    - "Will [City] reach [N]°F today?" → HIGH threshold
    - "[City] daily high above [N]°F" → HIGH threshold
    - "[City] high temp: [N]-[M]°F" → RANGE (lower bound)

    Args:
        title: Market title string

    Returns:
        TitleParsed if valid temperature market, None otherwise
    """
    if not title or not title.strip():
        return None

    title = title.strip()

    # Pattern 1: "Will [City] reach [N]°F today?"
    pattern1 = r"^will\s+(.+?)\s+reach\s+(-?\d+)\s*°?F\s+today\?$"
    match1 = re.match(pattern1, title, re.IGNORECASE)
    if match1:
        city = match1.group(1).strip()
        try:
            threshold = int(match1.group(2))
        except ValueError:
            return None
        return TitleParsed(
            city=city,
            threshold_f=threshold,
            direction="HIGH",
            is_range=False,
        )

    # Pattern 2: "[City] daily high above [N]°F"
    pattern2 = r"^(.+?)\s+daily\s+high\s+above\s+(-?\d+)\s*°?F$"
    match2 = re.match(pattern2, title, re.IGNORECASE)
    if match2:
        city = match2.group(1).strip()
        try:
            threshold = int(match2.group(2))
        except ValueError:
            return None
        return TitleParsed(
            city=city,
            threshold_f=threshold,
            direction="HIGH",
            is_range=False,
        )

    # Pattern 3: "[City] high temp: [N]-[M]°F" (range)
    pattern3 = r"^(.+?)\s+high\s+temp:\s*(-?\d+)-(-?\d+)\s*°?F$"
    match3 = re.match(pattern3, title, re.IGNORECASE)
    if match3:
        city = match3.group(1).strip()
        try:
            lower = int(match3.group(2))
            upper = int(match3.group(3))
        except ValueError:
            return None
        return TitleParsed(
            city=city,
            threshold_f=lower,  # Use lower bound as threshold
            direction="RANGE",
            is_range=True,
        )

    # Not a temperature market title
    return None
