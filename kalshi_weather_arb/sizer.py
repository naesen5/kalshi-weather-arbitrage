"""Sizer — Kelly criterion calculator for bet sizing."""

from typing import Optional


class Sizer:
    """Sizer — Kelly criterion calculator for bet sizing."""

    def __init__(
        self,
        edge: float = 0.05,
        exposure_cap: Optional[float] = None,
        circuit_breaker: float = 1000.0,
    ):
        self.edge = edge
        self.exposure_cap = exposure_cap
        self.circuit_breaker = circuit_breaker

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
        bet = kelly_frac * max_bet

        if self.exposure_cap:
            bet = min(bet, self.exposure_cap)

        return min(bet, self.circuit_breaker)
