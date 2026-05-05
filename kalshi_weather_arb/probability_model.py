"""Probability model — three-tier confidence system."""

from typing import Dict


class ProbabilityModel:
    """Three-tier confidence system for weather contract probabilities."""

    TIERS = {
        1: {"name": "high_confidence", "min_prob": 0.7},
        2: {"name": "moderate_confidence", "min_prob": 0.4},
        3: {"name": "low_confidence", "min_prob": 0.0},
    }

    def get_tier(self, probability: float) -> Dict[str, Any]:
        """Get tier info for a probability."""
        for tier_id, info in self.TIERS.items():
            if probability >= info["min_prob"]:
                return {"tier": tier_id, **info}
        return {"tier": 3, **self.TIERS[3]}

    def calculate_probability(
        self,
        weather_history: Dict[str, int],
        total_contracts: int,
    ) -> float:
        """Calculate probability from history."""
        if total_contracts == 0:
            return 0.5
        return weather_history.get("favored", 0) / total_contracts
