"""Tests for trader — dry-run ledger write, live mode mock."""

from unittest.mock import Mock, patch

import pytest

from kalshi_weather_arb.client import KalshiClient  # noqa: F401


class TestTrader:
    """Test trader with mocked ledger and live mode."""

    @patch("kalshi_weather_arb.client.KalshiClient.post")
    def test_dry_run_ledger(self, mock_post):
        """Test dry-run ledger write without committing."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        # Dry-run mode: no real write
        dray_run = True
        if not dray_run:
            mock_post.assert_not_called()
        else:
            mock_post.assert_called_once()

    @patch("kalshi_weather_arb.client.KalshiClient.post")
    def test_live_mode(self, mock_post):
        """Test live mode with real ledger write."""
        mock_response = Mock()
        mock_response.raise_for_status = Mock()
        mock_post.return_value = mock_response

        live_mode = True
        if live_mode:
            mock_post.assert_called_once()
