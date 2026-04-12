"""Sizer — Kelly criterion calculator for bet sizing."""

from datetime import datetime
from typing import Optional

from kalshi_weather_arb.risk.state import RiskState


class DailyExposure:
    """Track daily exposure for risk management."""

    def __init__(self, max_exposure: float = 500.0):
        self.max_exposure = max_exposure
        self.today = datetime.utcnow().date()
        self.current_exposure = 0.0

    def add_bet(self, amount: float) -> bool:
        """Add a bet to current exposure. Returns False if limit exceeded."""
        if datetime.utcnow().date() != self.today:
            self.today = datetime.utcnow().date()
            self.current_exposure = 0.0
        if self.current_exposure + amount > self.max_exposure:
            return False
        self.current_exposure += amount
        return True

    def can_afford(self, amount: float) -> bool:
        """Check if this amount can be afforded within limit."""
        if datetime.utcnow().date() != self.today:
            return True
        return self.current_exposure + amount <= self.max_exposure


class Sizer:
    """Sizer — Kelly criterion calculator for bet sizing."""

    def __init__(
        self,
        edge: float = 0.05,
        exposure_cap: Optional[float] = None,
        circuit_breaker: float = 1000.0,
        fraction: float = 0.25,
    ):
        self.edge = edge
        self.exposure_cap = exposure_cap
        self.circuit_breaker = circuit_breaker
        self.fraction = fraction

    def kelly(self, odds: float, edge: Optional[float] = None) -> float:
        """Calculate Kelly fraction."""
        if edge is None:
            edge = self.edge
        if odds <= 1:
            return 0
        return (odds - 1) / odds - edge / odds

    def size_bet(self, odds: float, max_bet: float) -> float:
        """Calculate bet size with exposure cap and circuit breaker."""
        kelly_frac = self.kelly(odds)
        bet = kelly_frac * max_bet * self.fraction

        if self.exposure_cap:
            bet = min(bet, self.exposure_cap)

        return min(bet, self.circuit_breaker)


class PositionSizer:
    """Position Sizer — wraps Sizer with opportunity validation."""

    def __init__(
        self,
        sizer: Sizer,
        risk_state: RiskState,
        min_edge: float = 0.0,
        max_observation_age_minutes: int = 90,
    ):
        self.sizer = sizer
        self.risk_state = risk_state
        self.min_edge = min_edge
        self.max_observation_age_minutes = max_observation_age_minutes

    def approve(
        self,
        opportunity: dict,
    ) -> Optional[dict]:
        """
        Check if opportunity should be accepted and return OrderSpec or None.
        
        Opportunity dict must contain:
        - ticker: str
        - side: str
        - edge: float
        - model_prob: float
        - market_prob: float
        - observation_age_minutes: float (optional, defaults to 0)
        
        Returns OrderSpec dict or None if rejected.
        """
        ticker = opportunity.get("ticker")
        side = opportunity.get("side")
        edge = opportunity.get("edge", 0.0)
        model_prob = opportunity.get("model_prob", 0.0)
        market_prob = opportunity.get("market_prob", 0.0)
        observation_age = opportunity.get("observation_age_minutes", 0)

        # Check exposure limit
        cost = 1.0  # Assume $1 bet for now
        if not self.risk_state.can_afford(cost):
            return None

        # Check existing position on ticker
        if self.risk_state.open_positions > 0:
            return None

        # Check edge threshold
        if edge < self.min_edge:
            return None

        # Check observation age
        if observation_age > self.max_observation_age_minutes:
            return None

        # Calculate bet size
        odds = 1.0 / market_prob if market_prob > 0 else 2.0
        bet_size = self.sizer.size_bet(odds, 1000.0)

        return {
            "ticker": ticker,
            "side": side,
            "count": 1,
            "price_cents": int(bet_size * 100),
            "model_prob": model_prob,
            "market_prob": market_prob,
            "edge": edge,
        }
