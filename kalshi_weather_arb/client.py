"""Kalshi API client — RSA signing, pagination, error handling."""

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

import requests


class DryRunError(Exception):
    """Raised when an operation is attempted in dry-run mode."""

    pass


class KalshiClient:
    """Client for Kalshi API with RSA signing."""

    def __init__(
        self,
        api_key: str,
        private_key_path: str,
        base_url: str = "https://api.kalshi.com",
        dry_run: bool = False,
    ):
        """
        Initialize Kalshi client.

        Args:
            api_key: Public API key
            private_key_path: Path to RSA private key (PEM format)
            base_url: API base URL (demo or production)
            dry_run: If True, skip actual API calls
        """
        self.api_key = api_key
        self.private_key = self._load_private_key(private_key_path)
        self.base_url = base_url.rstrip("/")
        self.dry_run = dry_run

    def _load_private_key(self, key_path: str):
        """Load RSA private key from PEM file."""
        from cryptography.hazmat.primitives import serialization

        with open(key_path, "rb") as f:
            return serialization.load_pem_private_key(
                f.read(),
                password=None,
            )

    def _sign_request(self, method: str, path: str, timestamp: str) -> str:
        """
        Generate RSA signature for request.

        Kalshi requires:
        - Message: method + newline + path + newline + timestamp
        - Signature: SHA256 with PKCS1v15 padding
        - Headers: KALSHI-ACCESS-KEY, KALSHI-ACCESS-TIMESTAMP, KALSHI-ACCESS-SIGNATURE
        """
        from cryptography.hazmat.primitives import hashes
        from cryptography.hazmat.primitives.asymmetric import padding
        import base64

        message = f"{method}\n{path}\n{timestamp}"
        signature = self.private_key.sign(
            message.encode(),
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode()

    def _get_headers(self, method: str, path: str, body: Optional[str] = None) -> Dict[str, str]:
        """Generate authentication headers for API request."""
        timestamp = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
        signature = self._sign_request(method, path, timestamp)

        return {
            "KALSHI-ACCESS-KEY": self.api_key,
            "KALSHI-ACCESS-TIMESTAMP": timestamp,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "Content-Type": "application/json",
        }

    def get(
        self, endpoint: str, params: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """GET request with RSA signing."""
        if self.dry_run:
            raise DryRunError("Dry run mode — skipping API call")

        path = endpoint.lstrip("/")
        headers = self._get_headers("GET", path)

        response = requests.get(
            f"{self.base_url}/{path}",
            headers=headers,
            params=params,
            timeout=30,
        )

        if response.status_code == 429:
            import time
            time.sleep(10)
            response.raise_for_status()

        response.raise_for_status()
        return response.json()

    def post(self, endpoint: str, data: Dict[str, Any]) -> Dict[str, Any]:
        """POST request with RSA signing."""
        if self.dry_run:
            raise DryRunError("Dry run mode — skipping API call")

        path = endpoint.lstrip("/")
        body = json.dumps(data)
        headers = self._get_headers("POST", path, body)

        response = requests.post(
            f"{self.base_url}/{path}",
            headers=headers,
            data=body,
            timeout=30,
        )

        if response.status_code == 429:
            import time
            time.sleep(10)
            response.raise_for_status()

        response.raise_for_status()
        return response.json()

    def paginate(self, endpoint: str) -> List[Dict[str, Any]]:
        """Fetch all pages from paginated endpoint."""
        results = []
        next_url = endpoint
        while next_url:
            data = self.get(next_url)
            results.extend(data.get("results", []))
            next_url = data.get("next")
        return results

    # API methods
    def get_markets(self, category: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all markets, optionally filtered by category."""
        endpoint = "/api/v1/markets"
        params = {"category": category} if category else {}
        return self.paginate(endpoint)

    def get_market(self, ticker: str) -> Dict[str, Any]:
        """Get a single market by ticker."""
        return self.get(f"/api/v1/market/{ticker}")

    def get_orderbook(self, ticker: str) -> Dict[str, Any]:
        """Get the orderbook for a market."""
        return self.get(f"/api/v1/market/{ticker}/orderbook")

    def place_order(
        self,
        ticker: str,
        side: str,
        count: int,
        price: int,
        good_till_cancel: bool = True,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        """Place an order."""
        if dry_run:
            raise DryRunError("Dry run mode — order not placed")

        return self.post(
            "/api/v1/orders",
            {
                "ticker": ticker,
                "side": side,
                "count": count,
                "price": price,
                "good_till_cancel": good_till_cancel,
            },
        )

    def get_positions(self, ticker: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all positions, optionally filtered by ticker."""
        endpoint = "/api/v1/positions"
        params = {"ticker": ticker} if ticker else {}
        return self.get(endpoint, params)

    def get_balance(self) -> Dict[str, Any]:
        """Get account balance."""
        return self.get("/api/v1/account")
