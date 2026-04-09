"""Tests for title parser module."""

from kalshi_weather_arb.title_parser import parse_title


class TestTitleParser:
    """Test parse_title function."""

    def test_parse_title(self):
        """Test parsing valid titles."""
        result = parse_title("Clear Sky, 100nm, $100/MWh")
        assert result is not None
        assert result["weather"] == "clear"
        assert result["distance_nm"] == 100
        assert result["price_per_mwh"] == 100.0

    def test_parse_title_storm(self):
        """Test parsing storm title."""
        result = parse_title("Storm, 50nm, $150/MWh")
        assert result is not None
        assert result["weather"] == "storm"
        assert result["distance_nm"] == 50
        assert result["price_per_mwh"] == 150.0

    def test_parse_title_clear_sky(self):
        """Test parsing clear sky title."""
        result = parse_title("Clear Sky, 200nm, $80/MWh")
        assert result is not None
        assert result["weather"] == "clear"
        assert result["distance_nm"] == 200
        assert result["price_per_mwh"] == 80.0

    def test_parse_invalid_title(self):
        """Test parsing invalid title returns None."""
        result = parse_title("invalid title")
        assert result is None
