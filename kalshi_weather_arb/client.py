"""Kalshi API client — signing, pagination, error handling."""

import hashlib
import hmac
import json
from datetime import datetime
from typing import Any, Dict, List, Optional

import requests


class KalshiClient:
    """Client for Kalshi API with HMAC signing."""

    def __init__(
        self,
        api_key: str,
        secret_key: str,
        base_url: str = "https://api.kalshi.com",
    ):
        self.api_key = api_key
        self.secret_key = secret_key
        self.base_url = base_url.rstrip("/")

    def _sign_request(self, method: str, path: str, body: Optional[str] = None) -> str:
        """Generate HMAC-SHA256 signature for request."""
        timestamp = datetime.utcnow().isoformat()
        message = f"{method}\n{path}\n{timestamp}\n{body or ''}"
        signature = hmac.new(
            self.secret_key.encode(),
            message.encode(),
            hashlib.sha256,
        ).hexdigest()
        return f"HMAC {self.api_key}:{timestamp}:{signature}"

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """GET request with signing."""
        path = endpoint.lstrip("/")
        signature = self._sign_request("GET", path)
        headers = {
            "Authorization": signature,
            "Content-Type": "application/json",
        }
        response = requests.get(
            f"{self.base_url}{path}",
            headers=headers,
            params=params,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with signing."""
        path = endpoint.lstrip("/")
        body = json.dumps(data)
        signature = self._sign_request("POST", path, body)
        headers = {
            "Authorization": signature,
            "Content-Type": "application/json",
        }
        response = requests.post(
            f"{self.base_url}{path}",
            headers=headers,
            data=body,
            timeout=30,
        )
        response.raise_for_status()
        result: Dict[str, Any] = response.json()
        return result

    def paginate(self, endpoint: str) -> List[Dict[str, Any]]:
        """Fetch all pages from paginated endpoint."""
        results = []
        next_url = endpoint
        while next_url:
            data = self.get(next_url)
            results.extend(data.get("results", []))
            next_url = data.get("next")
        return results

    def get_historical_candlesticks(
        self,
        ticker: str,
        frames: Optional[str] = None,
    ) -> List[Dict[str, Any]]:
        """Fetch historical candlestick data for a market.

        Args:
            ticker: Market ticker (e.g., 'KC-JFK-90')
            frames: Candlestick frame size (e.g., '1day', '1hour').
                    If None, Kalshi returns the default frame.

        Returns:
            List of candlestick dicts with keys: ts_ms, open, close, high, low, volume

        Raises:
            requests.exceptions.HTTPError: On 4xx/5xx API errors.
        """
        path = f"/api/v1/historical/markets/{ticker}/candlesticks"
        params = {"frames": frames} if frames else None
        data = self.get(path, params=params)
        return data.get("ticks", [])
