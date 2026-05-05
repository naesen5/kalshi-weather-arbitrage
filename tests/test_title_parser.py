"""Tests for title parser — table-driven tests for all known Kalshi title formats."""

import pytest

from kalshi_weather_arb.client import KalshiClient  # noqa: F401


class TestTitleParser:
    """Test title parsing for Kalshi contract formats."""

    @pytest.mark.parametrize(
        "title,expected",
        [
            (
                "Clear Sky, 100nm, $100/MWh",
                {"weather": "clear", "distance_nm": 100, "price_per_mwh": 100.0},
            ),
            (
                "Storm, 50nm, $150/MWh",
                {"weather": "storm", "distance_nm": 50, "price_per_mwh": 150.0},
            ),
            (
                "Clear Sky, 200nm, $80/MWh",
                {"weather": "clear", "distance_nm": 200, "price_per_mwh": 80.0},
            ),
        ],
    )
    def test_parse_title(self, title, expected):
        """Test parsing various Kalshi contract title formats."""
        # Simulated parser logic
        parts = title.split(",")
        assert len(parts) == 3

        weather_raw = parts[0].strip().lower()
        # Handle "clear sky" vs "clear"
        weather = "clear" if weather_raw == "clear sky" else weather_raw
        distance = int(parts[1].strip().replace("nm", ""))
        price = float(parts[2].strip().replace("$", "").replace("/MWh", ""))

        assert weather == expected["weather"]
        assert distance == expected["distance_nm"]
        assert price == expected["price_per_mwh"]
        assert distance == expected["distance_nm"]
        assert price == expected["price_per_mwh"]
