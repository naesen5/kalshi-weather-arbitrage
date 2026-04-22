"""Data loader — historical METAR and Kalshi price data."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from kalshi_weather_arb.client import KalshiClient


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
    """Loader for historical Kalshi price data via the Kalshi API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        secret_key: Optional[str] = None,
        cache_dir: str = "backtest/cache",
    ):
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)
        # Create KalshiClient — api_key/secret_key are optional for public endpoints
        # (candlestick data is available without auth on Kalshi)
        if api_key and secret_key:
            self.client = KalshiClient(api_key, secret_key)
        elif api_key:
            # Some endpoints work with just API key
            self.client = KalshiClient(api_key, "")
        else:
            # Create client without auth — will work for public endpoints
            self.client = KalshiClient("", "")

    def _get_cache_path(self, ticker: str) -> str:
        """Get the cache file path for a ticker."""
        safe_name = ticker.replace("/", "_").replace("-", "_")
        return os.path.join(self.cache_dir, f"{safe_name}.json")

    def _load_from_cache(self, ticker: str) -> Optional[List[Dict[str, Any]]]:
        """Load cached price data if available."""
        cache_path = self._get_cache_path(ticker)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _save_to_cache(self, ticker: str, data: List[Dict[str, Any]]) -> None:
        """Save price data to cache."""
        cache_path = self._get_cache_path(ticker)
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass  # Silently ignore cache write failures

    def load_kalshi_price_history(self, ticker: str) -> List[Dict[str, Any]]:
        """Load Kalshi price history for a ticker from the Kalshi API.

        Fetches historical candlestick data from the Kalshi API and converts
        it to a standardized format with timestamp, price, open, high, low,
        and volume fields.

        Args:
            ticker: Kalshi market ticker (e.g., 'KC-JFK-90')

        Returns:
            List of price dicts with keys: ticker, timestamp, price, open,
            high, low, volume. Returns empty list on error.
        """
        # Check cache first
        cached = self._load_from_cache(ticker)
        if cached is not None:
            return cached

        try:
            # Fetch candlestick data from Kalshi API
            ticks = self.client.get_historical_candlesticks(ticker)

            # Convert candlestick ticks to price history format
            price_data = []
            for tick in ticks:
                ts_ms = tick.get("ts_ms", 0)
                dt = datetime.fromtimestamp(ts_ms / 1000.0, tz=timezone.utc)
                price_data.append(
                    {
                        "ticker": ticker,
                        "timestamp": dt.isoformat(),
                        "price": tick.get("close", 0),
                        "open": tick.get("open", 0),
                        "high": tick.get("high", 0),
                        "low": tick.get("low", 0),
                        "volume": tick.get("volume", 0),
                    }
                )

            # Cache the results
            self._save_to_cache(ticker, price_data)

            return price_data

        except Exception:
            # Return empty list on any API error
            return []
