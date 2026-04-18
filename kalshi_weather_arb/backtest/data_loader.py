"""Data loader — historical METAR and Kalshi price data."""

import os
from typing import Any, Dict, List


class METARLoader:
    """Loader for historical METAR observations."""

    def __init__(self, cache_dir: str = "backtest/cache"):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def load_metar_history(
        self, station: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Load METAR history for a station."""
        # For now, return synthetic data
        # TODO: Implement actual NOAA ISD API call
        return [
            {
                "station": station,
                "timestamp": f"{start_date}T{h:02d}:00:00Z",
                "temp_f": 45.0 + h * 2,
                "obs_type": "TMP2",
            }
            for h in range(24)
        ]


class KalshiPriceLoader:
    """Loader for historical Kalshi price data."""

    def __init__(self, api_key: str, cache_dir: str = "backtest/cache"):
        self.api_key = api_key
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def load_kalshi_price_history(self, ticker: str) -> List[Dict[str, Any]]:
        """Load Kalshi price history for a ticker."""
        # For now, return synthetic data
        # TODO: Implement actual Kalshi API call
        return [
            {
                "ticker": ticker,
                "timestamp": f"2025-01-01T{h:02d}:00:00Z",
                "price": 100.0 + h,
            }
            for h in range(24)
        ]
