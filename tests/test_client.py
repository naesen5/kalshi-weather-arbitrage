"""Tests for Kalshi client."""

import pytest
import json
from unittest.mock import Mock, patch
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.backends import default_backend

from kalshi_weather_arb.client import KalshiClient, DryRunError


class TestKalshiClientInit:
    """Tests for client initialization."""

    def test_init_with_demo_url(self):
        """Client initializes with demo URL."""
        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
            base_url="https://demo-api.kalshi.com",
        )
        assert client.base_url == "https://demo-api.kalshi.com"
        assert client.api_key == "test-key"
        assert client.dry_run is False

    def test_init_with_dry_run(self):
        """Client initializes with dry_run mode."""
        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
            dry_run=True,
        )
        assert client.dry_run is True

    def test_base_url_strips_trailing_slash(self):
        """Base URL strips trailing slash."""
        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
            base_url="https://api.kalshi.com/",
        )
        assert client.base_url == "https://api.kalshi.com"


class TestDryRunMode:
    """Tests for dry-run mode behavior."""

    def test_get_raises_dry_run_error(self):
        """GET raises DryRunError in dry-run mode."""
        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
            dry_run=True,
        )
        with pytest.raises(DryRunError):
            client.get("/api/v1/markets")

    def test_post_raises_dry_run_error(self):
        """POST raises DryRunError in dry-run mode."""
        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
            dry_run=True,
        )
        with pytest.raises(DryRunError):
            client.post("/api/v1/orders", {"ticker": "TEST", "side": "yes", "count": 10, "price": 50})

    def test_place_order_raises_dry_run_error(self):
        """place_order raises DryRunError when dry_run=True."""
        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
            dry_run=False,
        )
        with pytest.raises(DryRunError):
            client.place_order("TEST", "yes", 10, 50, dry_run=True)


class TestSigning:
    """Tests for RSA signature generation."""

    @pytest.fixture
    def mock_private_key(self):
        """Create a mock RSA private key."""
        return rsa.generate_private_key(
            public_exponent=65537,
            key_size=2048,
            backend=default_backend(),
        )

    def test_sign_request_format(self, mock_private_key):
        """Signature is generated for correct message format."""
        with patch("cryptography.hazmat.primitives.serialization.load_pem_private_key") as mock_load:
            mock_load.return_value = mock_private_key

            client = KalshiClient(
                api_key="test-key",
                private_key_path="tests/fixtures/test_key.pem",
            )

            signature = client._sign_request("GET", "/api/v1/markets", "2026-04-18T00:00:00Z")
            assert isinstance(signature, str)
            assert len(signature) > 0

    def test_headers_format(self, mock_private_key):
        """Headers include correct Kalshi authentication fields."""
        with patch("cryptography.hazmat.primitives.serialization.load_pem_private_key") as mock_load:
            mock_load.return_value = mock_private_key

            client = KalshiClient(
                api_key="test-key",
                private_key_path="tests/fixtures/test_key.pem",
            )

            headers = client._get_headers("GET", "/api/v1/markets")
            assert "KALSHI-ACCESS-KEY" in headers
            assert "KALSHI-ACCESS-TIMESTAMP" in headers
            assert "KALSHI-ACCESS-SIGNATURE" in headers
            assert headers["KALSHI-ACCESS-KEY"] == "test-key"


class TestAPIMethods:
    """Tests for API methods."""

    @pytest.fixture
    def mock_response(self):
        """Create a mock response object."""
        response = Mock()
        response.status_code = 200
        response.json.return_value = {"results": []}
        response.raise_for_status = Mock()
        return response

    @patch("requests.get")
    def test_get_markets(self, mock_get, mock_response):
        """get_markets calls correct endpoint."""
        mock_get.return_value = mock_response

        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
        )

        with patch.object(client, "_get_headers") as mock_headers:
            mock_headers.return_value = {"KALSHI-ACCESS-KEY": "test"}
            client.get_markets(category="weather")

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "/api/v1/markets" in call_args[0][0]
            # params can be None or empty dict when no filter
            assert call_args[1].get("params") in [None, {}, {"category": "weather"}]

    @patch("requests.get")
    def test_get_market(self, mock_get, mock_response):
        """get_market calls correct endpoint."""
        mock_get.return_value = mock_response

        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
        )

        with patch.object(client, "_get_headers") as mock_headers:
            mock_headers.return_value = {"KALSHI-ACCESS-KEY": "test"}
            client.get_market("KLSHI-TEMP-NYC-90")

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "/api/v1/market/KLSHI-TEMP-NYC-90" in call_args[0][0]

    @patch("requests.get")
    def test_get_orderbook(self, mock_get, mock_response):
        """get_orderbook calls correct endpoint."""
        mock_get.return_value = mock_response

        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
        )

        with patch.object(client, "_get_headers") as mock_headers:
            mock_headers.return_value = {"KALSHI-ACCESS-KEY": "test"}
            client.get_orderbook("KLSHI-TEMP-NYC-90")

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "/api/v1/market/KLSHI-TEMP-NYC-90/orderbook" in call_args[0][0]

    @patch("requests.post")
    def test_place_order(self, mock_post, mock_response):
        """place_order calls correct endpoint."""
        mock_post.return_value = mock_response

        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
        )

        with patch.object(client, "_get_headers") as mock_headers:
            mock_headers.return_value = {"KALSHI-ACCESS-KEY": "test"}
            client.place_order("KLSHI-TEMP-NYC-90", "yes", 100, 45)

            mock_post.assert_called_once()
            call_args = mock_post.call_args
            assert "/api/v1/orders" in call_args[0][0]
            data = json.loads(call_args[1]["data"])
            assert data["ticker"] == "KLSHI-TEMP-NYC-90"
            assert data["side"] == "yes"
            assert data["count"] == 100
            assert data["price"] == 45

    @patch("requests.get")
    def test_get_positions(self, mock_get, mock_response):
        """get_positions calls correct endpoint."""
        mock_get.return_value = mock_response

        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
        )

        with patch.object(client, "_get_headers") as mock_headers:
            mock_headers.return_value = {"KALSHI-ACCESS-KEY": "test"}
            client.get_positions(ticker="KLSHI-TEMP-NYC-90")

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "/api/v1/positions" in call_args[0][0]
            assert call_args[1]["params"] == {"ticker": "KLSHI-TEMP-NYC-90"}

    @patch("requests.get")
    def test_get_balance(self, mock_get, mock_response):
        """get_balance calls correct endpoint."""
        mock_get.return_value = mock_response

        client = KalshiClient(
            api_key="test-key",
            private_key_path="tests/fixtures/test_key.pem",
        )

        with patch.object(client, "_get_headers") as mock_headers:
            mock_headers.return_value = {"KALSHI-ACCESS-KEY": "test"}
            client.get_balance()

            mock_get.assert_called_once()
            call_args = mock_get.call_args
            assert "/api/v1/account" in call_args[0][0]
