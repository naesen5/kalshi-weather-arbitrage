"""Tests for backtest data loader."""

import os
from unittest.mock import MagicMock

import pytest

from kalshi_weather_arb.backtest.data_loader import KalshiPriceLoader, METARLoader


class TestMETARLoader:
    """Test METAR data loading."""

    def test_load_metar_history(self, tmp_path):
        """Test loading METAR history."""
        loader = METARLoader(cache_dir=str(tmp_path))
        data = loader.load_metar_history("KJFK", "2025-01-01", "2025-01-02")

        assert len(data) > 0
        assert data[0]["station"] == "KJFK"
        assert "timestamp" in data[0]
        assert "temp_f" in data[0]


class TestKalshiPriceLoader:
    """Test Kalshi price data loading."""

    def test_load_kalshi_price_history(self, tmp_path):
        """Test loading Kalshi price history."""
        loader = KalshiPriceLoader(api_key="dummy", cache_dir=str(tmp_path))
        data = loader.load_kalshi_price_history("KC")

        assert len(data) > 0
        assert data[0]["ticker"] == "KC"
        assert "timestamp" in data[0]
        assert "price" in data[0]
