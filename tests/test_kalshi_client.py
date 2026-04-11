"""Tests for KalshiClient — mocking requests, signing, pagination, errors."""

from unittest.mock import Mock, patch

import pytest

from kalshi_weather_arb.client import KalshiClient


class TestKalshiClient:
    """Test KalshiClient signing, pagination, and error handling."""

    def test_sign_request(self):
        """Test HMAC-SHA256 signature generation."""
        client = KalshiClient("api_key_123", "secret_key_456")
        sig = client._sign_request("GET", "/api/v1/test")
        assert "HMAC api_key_123:" in sig
        assert ":" in sig

    @patch("kalshi_weather_arb.client.requests.get")
    def test_get_success(self, mock_get):
        """Test GET request with mocked response."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_response.json.return_value = {"results": [{"id": 1}]}
        mock_get.return_value = mock_response

        client = KalshiClient("api_key", "secret")
        result = client.get("/api/v1/test")

        assert result == {"results": [{"id": 1}]}
        mock_get.assert_called_once()

    @patch("kalshi_weather_arb.client.requests.get")
    def test_get_error_handling(self, mock_get):
        """Test GET request raises exception on 4xx/5xx."""
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = Exception("404 Not Found")
        mock_get.return_value = mock_response

        client = KalshiClient("api_key", "secret")
        with pytest.raises(Exception, match="404"):
            client.get("/api/v1/not-found")

    @patch("kalshi_weather_arb.client.requests.get")
    def test_paginate(self, mock_get):
        """Test pagination across multiple pages."""
        page1 = {"results": [{"id": 1}], "next": "/api/v1/page2"}
        page2 = {"results": [{"id": 2}], "next": None}

        mock_response1 = Mock()
        mock_response1.raise_for_status = Mock()
        mock_response1.json.return_value = page1

        mock_response2 = Mock()
        mock_response2.raise_for_status = Mock()
        mock_response2.json.return_value = page2

        mock_get.side_effect = [mock_response1, mock_response2]

        client = KalshiClient("api_key", "secret")
        results = client.paginate("/api/v1/test")

        assert len(results) == 2
        assert results[0]["id"] == 1
        assert results[1]["id"] == 2
        assert mock_get.call_count == 2
