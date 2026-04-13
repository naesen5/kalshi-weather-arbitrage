"""Data models for arbitrage scanner."""

from dataclasses import dataclass
from typing import Optional


@dataclass
class Opportunity:
    """
    Represents a trading opportunity identified by the scanner.

    An opportunity is created when the model's probability estimate
    exceeds the market's implied probability by more than the minimum edge threshold.
    """

    market_ticker: str
    """Kalshi market ticker symbol (e.g., 'KLSHI-TEMP-NYC-90')."""

    market_title: str
    """Full market title (e.g., 'Will NYC reach 90°F today?')."""

    station: str
    """ICAO station code for the city (e.g., 'KORD' for Chicago)."""

    current_temp_f: float
    """Current temperature in Fahrenheit from METAR."""

    obs_age_minutes: float
    """Age of the METAR observation in minutes."""

    threshold_f: float
    """Temperature threshold from the market (e.g., 90 for 'reach 90°F')."""

    model_probability: float
    """Model's estimated probability that daily high > threshold (0.0 to 1.0)."""

    market_probability: float
    """Market's implied probability (YES price / 100)."""

    edge: float
    """Edge = model_probability - market_probability."""

    ask_price_cents: int
    """Best available YES ask price in cents."""

    recommended_side: str
    """Recommended trade side: 'yes' or 'no'."""

    def is_tradeable(self, min_edge: float = 0.05) -> bool:
        """
        Check if this opportunity meets the minimum edge threshold.

        Args:
            min_edge: Minimum edge required for a tradeable opportunity

        Returns:
            True if edge >= min_edge, False otherwise
        """
        return self.edge >= min_edge

    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "market_ticker": self.market_ticker,
            "market_title": self.market_title,
            "station": self.station,
            "current_temp_f": self.current_temp_f,
            "obs_age_minutes": self.obs_age_minutes,
            "threshold_f": self.threshold_f,
            "model_probability": self.model_probability,
            "market_probability": self.market_probability,
            "edge": self.edge,
            "ask_price_cents": self.ask_price_cents,
            "recommended_side": self.recommended_side,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Opportunity":
        """Create from dictionary."""
        return cls(**data)
