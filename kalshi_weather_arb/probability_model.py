"""Temperature probability model — P(daily high > threshold) from current observation."""

import json
import math
import os
from typing import Any, Dict, Optional


class TemperatureProbModel:
    """
    Calculate probability that daily high temperature exceeds a threshold.

    Uses current temperature, dewpoint, time of day, station, and month to estimate the
    probability that the day's maximum temperature will exceed a given threshold.

    Model approach:
    - Tier 1: If current temp >= threshold, probability is ≥ 0.90 (explicit certainty)
    - Tier 2: Historical intraday rise distribution using NOAA ISD baselines
    - Tier 3 (optional): NWS hourly forecast integration

    Expected daily high = current_temp + diurnal_adjustment
    where diurnal_adjustment depends on:
      - Time until daily high (closer to 3-6 PM = smaller adjustment)
      - Dewpoint (higher = less overnight cooling, higher daily high)
      - Current temp relative to typical daily range
      - Station/month-specific historical rise distributions (from baselines)
    """

    # Typical diurnal temperature range (max - min) in Fahrenheit
    # Depends on humidity: dry air = larger range, humid air = smaller range
    BASE_DIURNAL_RANGE = 30.0  # °F for moderate humidity (slightly larger)

    # Time of daily high (hour of day, 0-23)
    DAILY_HIGH_HOUR = 15.5  # 3:30 PM typical (slightly earlier)

    # Standard deviation for temperature uncertainty (model uncertainty)
    TEMP_STD_DEV = 4.0  # °F (slightly larger for more uncertainty)

    # Tier 1 certainty (max 97%, scales with margin above threshold)
    TIER1_CERTAINTY_BASE = 0.90
    TIER1_CERTAINTY_MARGIN = 0.02

    def __init__(self, baselines_dir: Optional[str] = None):
        """
        Initialize the temperature probability model.

        Args:
            baselines_dir: Path to directory containing baseline JSON files.
                           If None, uses model/baselines/ relative to this module.
        """
        self.baselines_dir = baselines_dir
        if self.baselines_dir is None:
            # Default to model/baselines/ relative to this module
            module_dir = os.path.dirname(os.path.abspath(__file__))
            self.baselines_dir = os.path.join(module_dir, "model", "baselines")
        
        # Cache for loaded baselines
        self._baseline_cache: Dict[str, Dict[str, Any]] = {}

    def _load_baseline(self, station: str, month: int) -> Optional[Dict[str, Any]]:
        """
        Load baseline data for a station and month.

        Args:
            station: ICAO station identifier (e.g., 'KJFK')
            month: Month number (1-12)

        Returns:
            Baseline data dict or None if file not found
        """
        cache_key = f"{station}_{month}"
        if cache_key in self._baseline_cache:
            return self._baseline_cache[cache_key]

        filename = f"{station}_{month:02d}.json"
        filepath = os.path.join(self.baselines_dir, filename)

        if not os.path.exists(filepath):
            return None

        try:
            with open(filepath, "r") as f:
                data = json.load(f)
                self._baseline_cache[cache_key] = data
                return data
        except Exception:
            return None

    def p_exceed(
        self,
        current_temp_f: float,
        dewpoint_f: float,
        hour_of_day: float,
        threshold_f: float,
        station: str = "KJFK",
        month: int = 1,
    ) -> float:
        """
        Calculate probability that daily high exceeds threshold.

        Args:
            current_temp_f: Current temperature in Fahrenheit
            dewpoint_f: Current dewpoint in Fahrenheit (humidity indicator)
            hour_of_day: Current hour (0-23, float for sub-hour precision)
            threshold_f: Temperature threshold in Fahrenheit
            station: ICAO station identifier (e.g., 'KJFK')
            month: Month number (1-12)

        Returns:
            Probability (0.0 to 1.0) that daily high > threshold_f
        """
        # Tier 1: Explicit certainty if current temp >= threshold
        if current_temp_f >= threshold_f:
            # Scale certainty based on margin above threshold (max 97%)
            margin = current_temp_f - threshold_f
            certainty = self.TIER1_CERTAINTY_BASE + (margin * self.TIER1_CERTAINTY_MARGIN)
            return min(0.97, certainty)

        # Tier 2: Use baseline data if available
        baseline = self._load_baseline(station, month)
        if baseline is not None:
            prob = self._p_exceed_tier2(
                current_temp_f=current_temp_f,
                dewpoint_f=dewpoint_f,
                hour_of_day=hour_of_day,
                threshold_f=threshold_f,
                baseline=baseline,
            )
            if prob is not None:
                return prob

        # Tier 3 (fallback): Pure math model without station/month data
        return self._p_exceed_tier3(
            current_temp_f=current_temp_f,
            dewpoint_f=dewpoint_f,
            hour_of_day=hour_of_day,
            threshold_f=threshold_f,
        )

    def _p_exceed_tier2(
        self,
        current_temp_f: float,
        dewpoint_f: float,
        hour_of_day: float,
        threshold_f: float,
        baseline: Dict[str, Any],
    ) -> Optional[float]:
        """
        Tier 2: Use baseline data for probability calculation.

        Args:
            current_temp_f: Current temperature in Fahrenheit
            dewpoint_f: Current dewpoint in Fahrenheit
            hour_of_day: Current hour (0-23)
            threshold_f: Temperature threshold in Fahrenheit
            baseline: Loaded baseline data dict

        Returns:
            Probability (0.0 to 1.0) or None if baseline not applicable
        """
        # Get baseline rise distribution for current hour
        hour_key = str(int(hour_of_day))
        if hour_key not in baseline.get("hour_rises", {}):
            return None

        rise_data = baseline["hour_rises"][hour_key]
        mean_rise = rise_data.get("mean_rise_f", 10.0)
        std_rise = rise_data.get("std_rise_f", 3.0)

        # Calculate how much rise is needed to reach threshold
        rise_needed = threshold_f - current_temp_f

        # Probability that rise exceeds needed amount
        # Using normal CDF: P(rise > needed) = 1 - CDF((needed - mean) / std)
        if std_rise <= 0:
            return 0.0

        z_score = (rise_needed - mean_rise) / std_rise
        prob = 1.0 - self._normal_cdf(z_score)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, prob))

    def _p_exceed_tier3(
        self,
        current_temp_f: float,
        dewpoint_f: float,
        hour_of_day: float,
        threshold_f: float,
    ) -> float:
        """
        Tier 3: Pure math fallback without baseline data.

        Args:
            current_temp_f: Current temperature in Fahrenheit
            dewpoint_f: Current dewpoint in Fahrenheit
            hour_of_day: Current hour (0-23)
            threshold_f: Temperature threshold in Fahrenheit

        Returns:
            Probability (0.0 to 1.0)
        """
        # Calculate expected daily high
        expected_high = self._expected_daily_high(
            current_temp_f=current_temp_f,
            dewpoint_f=dewpoint_f,
            hour_of_day=hour_of_day,
        )

        # Calculate probability using normal CDF
        # P(T > threshold) = 1 - CDF((threshold - expected_high) / std_dev)
        z_score = (threshold_f - expected_high) / self.TEMP_STD_DEV
        probability = 1.0 - self._normal_cdf(z_score)

        # Clamp to [0, 1]
        return max(0.0, min(1.0, probability))

    def _expected_daily_high(
        self,
        current_temp_f: float,
        dewpoint_f: float,
        hour_of_day: float,
    ) -> float:
        """
        Estimate the day's maximum temperature.

        The expected daily high depends on:
        1. How far we are from the typical daily high time (4 PM)
        2. Current humidity (dewpoint) - higher dewpoint = less cooling overnight
        3. Current temperature

        Returns expected daily high in Fahrenheit.
        """
        # Time remaining until typical daily high
        time_to_high = self.DAILY_HIGH_HOUR - hour_of_day
        # Clamp to reasonable range (can't be negative if we're past daily high)
        time_to_high = max(0.0, min(time_to_high, 12.0))

        # Base adjustment: how much temp typically rises from now to daily high
        # Proportional to time remaining (linear approximation)
        base_adjustment = time_to_high * (self.BASE_DIURNAL_RANGE / 12.0)

        # Dewpoint adjustment: higher dewpoint means less overnight cooling
        # and typically higher daily high
        # Reference dewpoint: 55°F (moderate humidity)
        REFERENCE_DEWPOINT = 55.0
        DEWPOINT_FACTOR = 0.5  # Each °F dewpoint adds 0.5°F to expected high (stronger effect)
        dewpoint_adjustment = (dewpoint_f - REFERENCE_DEWPOINT) * DEWPOINT_FACTOR

        # Current temp adjustment: if current temp is already high,
        # daily high is likely closer to current temp
        # If current temp is low, there's more room to rise
        CURRENT_TEMP_REFERENCE = 70.0  # Reference current temp
        TEMP_ADJUSTMENT_FACTOR = 0.2  # Stronger adjustment for current temp
        current_temp_adjustment = (current_temp_f - CURRENT_TEMP_REFERENCE) * TEMP_ADJUSTMENT_FACTOR

        # Expected daily high = current + adjustments
        expected_high = current_temp_f + base_adjustment + dewpoint_adjustment + current_temp_adjustment

        return expected_high

    def _normal_cdf(self, x: float) -> float:
        """
        Cumulative distribution function for standard normal distribution.

        Uses approximation formula (Abramowitz and Stegun).
        Returns P(Z <= x) where Z ~ N(0, 1).
        """
        # Constants for approximation
        a1 = 0.254829592
        a2 = -0.284496736
        a3 = 1.421413741
        a4 = -1.453152027
        a5 = 1.454286261

        # Sign function
        sign = 1 if x >= 0 else -1
        x = abs(x)

        # Constants for approximation
        t = 1.0 / (1.0 + 0.2316419 * x)

        # PDF of standard normal at x
        y = (1.0 / math.sqrt(2.0 * math.pi)) * math.exp(-0.5 * x * x)

        # Approximation
        result = 1.0 - y * (a1 * t + a2 * t**2 + a3 * t**3 + a4 * t**4 + a5 * t**5)

        return result if sign == 1 else 1.0 - result

    def get_confidence_tier(self, probability: float) -> Dict[str, Any]:
        """
        Get confidence tier for a probability value.

        Args:
            probability: Probability value (0.0 to 1.0)

        Returns:
            Dict with tier info including tier_id, name, and min_prob
        """
        tiers = {
            1: {"name": "high_confidence", "min_prob": 0.7},
            2: {"name": "moderate_confidence", "min_prob": 0.4},
            3: {"name": "low_confidence", "min_prob": 0.0},
        }

        for tier_id, info in tiers.items():
            if probability >= info["min_prob"]:
                return {"tier": tier_id, **info}

        return {"tier": 3, **tiers[3]}
