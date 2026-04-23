"""Data loader — historical METAR and Kalshi price data."""

import json
import os
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests

from kalshi_weather_arb.client import KalshiClient


class METARLoader:
    """Loader for historical temperature data from NOAA CDO ISD."""

    BASE_URL = "https://www.ncei.noaa.gov/cdo-web/api/v2/data"

    def __init__(
        self,
        api_token: Optional[str] = None,
        cache_dir: str = "backtest/cache",
    ):
        self.api_token = api_token
        self.cache_dir = cache_dir
        os.makedirs(cache_dir, exist_ok=True)

    def _get_cache_path(self, station: str, start_date: str, end_date: str) -> str:
        """Get the cache file path for a station and date range."""
        safe_name = f"{station}_{start_date}_{end_date}".replace("/", "_")
        return os.path.join(self.cache_dir, f"metar_{safe_name}.json")

    def _load_from_cache(self, station: str, start_date: str, end_date: str) -> Optional[List[Dict[str, Any]]]:
        """Load cached temperature data if available."""
        cache_path = self._get_cache_path(station, start_date, end_date)
        if os.path.exists(cache_path):
            try:
                with open(cache_path, "r") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                return None
        return None

    def _save_to_cache(self, station: str, start_date: str, end_date: str, data: List[Dict[str, Any]]) -> None:
        """Save temperature data to cache."""
        cache_path = self._get_cache_path(station, start_date, end_date)
        try:
            with open(cache_path, "w") as f:
                json.dump(data, f, indent=2)
        except IOError:
            pass

    @staticmethod
    def _celsius_to_fahrenheit(c: float) -> float:
        """Convert Celsius to Fahrenheit."""
        return round(c * 9 / 5 + 32, 1)

    def load_metar_history(
        self, station: str, start_date: str, end_date: str
    ) -> List[Dict[str, Any]]:
        """Load historical temperature data from NOAA CDO ISD.

        Fetches daily average temperature (TAVG) from the NOAA Climate Data
        Online API and converts to Fahrenheit.

        Args:
            station: NOAA station ID (e.g., 'USW00012839' for JFK)
            start_date: Start date in YYYY-MM-DD format
            end_date: End date in YYYY-MM-DD format

        Returns:
            List of temp dicts with keys: station, timestamp, temp_f.
            Returns empty list on error or if no API token configured.
        """
        if not self.api_token:
            return []

        # Check cache first
        cached = self._load_from_cache(station, start_date, end_date)
        if cached is not None:
            return cached

        try:
            params = {
                "datasetid": "PRSTD",
                "stationid": station,
                "startdate": start_date,
                "enddate": end_date,
                "datatypeid": "TAVG",
                "token": self.api_token,
                "limit": 1000,
            }

            response = requests.get(self.BASE_URL, params=params, timeout=15)
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            if not results:
                return []

            # Group TAVG values by date
            temps_by_date: Dict[str, float] = {}
            for result in results:
                date_str = result.get("date", "")[:10]
                for datum in result.get("data", []):
                    if datum.get("datatype") == "TAVG":
                        val = datum.get("value")
                        if val is not None:
                            try:
                                temps_by_date[date_str] = float(val)
                            except (ValueError, TypeError):
                                pass

            if not temps_by_date:
                return []

            # Build sorted list of daily records
            temp_data: List[Dict[str, Any]] = []
            for date_str in sorted(temps_by_date.keys()):
                temp_c = temps_by_date[date_str]
                dt = datetime.strptime(date_str, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                temp_data.append(
                    {
                        "station": station,
                        "timestamp": dt.isoformat(),
                        "temp_f": self._celsius_to_fahrenheit(temp_c),
                    }
                )

            # Cache the results
            self._save_to_cache(station, start_date, end_date, temp_data)

            return temp_data

        except Exception:
            return []


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
        if api_key and secret_key:
            self.client = KalshiClient(api_key, secret_key)
        elif api_key:
            self.client = KalshiClient(api_key, "")
        else:
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
            pass

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
        cached = self._load_from_cache(ticker)
        if cached is not None:
            return cached

        try:
            ticks = self.client.get_historical_candlesticks(ticker)

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

            self._save_to_cache(ticker, price_data)
            return price_data

        except Exception:
            return []
