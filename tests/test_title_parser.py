"""Tests for temperature market title parser."""

import pytest
from kalshi_weather_arb.title_parser import parse_temperature_title, TitleParsed


class TestTitleParsed:
    """Test TitleParsed dataclass."""

    def test_init(self):
        """Test initialization."""
        parsed = TitleParsed(
            city="NYC",
            threshold_f=90,
            direction="HIGH",
            is_range=False,
        )
        assert parsed.city == "NYC"
        assert parsed.threshold_f == 90
        assert parsed.direction == "HIGH"


class TestParseTemperatureTitle:
    """Test parse_temperature_title function."""

    def test_parse_will_reach_today(self):
        """Test parsing 'Will [City] reach [N]°F today?' format."""
        result = parse_temperature_title("Will NYC reach 90°F today?")
        assert result is not None
        assert result.city == "NYC"
        assert result.threshold_f == 90
        assert result.direction == "HIGH"
        assert result.is_range is False

    def test_parse_daily_high_above(self):
        """Test parsing '[City] daily high above [N]°F' format."""
        result = parse_temperature_title("Chicago daily high above 85°F")
        assert result is not None
        assert result.city == "Chicago"
        assert result.threshold_f == 85
        assert result.direction == "HIGH"
        assert result.is_range is False

    def test_parse_high_temp_range(self):
        """Test parsing '[City] high temp: [N]-[M]°F' format (range)."""
        result = parse_temperature_title("Los Angeles high temp: 75-85°F")
        assert result is not None
        assert result.city == "Los Angeles"
        assert result.threshold_f == 75  # Lower bound
        assert result.direction == "RANGE"
        assert result.is_range is True

    def test_parse_with_comma(self):
        """Test parsing with comma after city name."""
        result = parse_temperature_title("Will Seattle, WA reach 70°F today?")
        assert result is not None
        assert result.city == "Seattle, WA"
        assert result.threshold_f == 70
        assert result.direction == "HIGH"

    def test_parse_multiple_words_city(self):
        """Test parsing city with multiple words."""
        result = parse_temperature_title("Will San Francisco reach 75°F today?")
        assert result is not None
        assert result.city == "San Francisco"
        assert result.threshold_f == 75
        assert result.direction == "HIGH"

    def test_parse_invalid_no_number(self):
        """Test parsing invalid title without temperature number."""
        result = parse_temperature_title("Will NYC reach today?")
        assert result is None

    def test_parse_invalid_no_city(self):
        """Test parsing invalid title without city."""
        result = parse_temperature_title("Will reach 90°F today?")
        assert result is None

    def test_parse_invalid_no_degree_symbol(self):
        """Test parsing title without degree symbol."""
        result = parse_temperature_title("Will NYC reach 90F today?")
        # Should still parse (F without degree symbol)
        assert result is not None
        assert result.threshold_f == 90

    def test_parse_invalid_not_temperature(self):
        """Test parsing non-temperature market title."""
        result = parse_temperature_title("Clear Sky, 100nm, $100/MWh")
        assert result is None

    def test_parse_invalid_empty(self):
        """Test parsing empty string."""
        result = parse_temperature_title("")
        assert result is None

    def test_parse_invalid_whitespace(self):
        """Test parsing whitespace only."""
        result = parse_temperature_title("   ")
        assert result is None

    def test_parse_celsius_not_supported(self):
        """Test parsing Celsius format (should return None)."""
        result = parse_temperature_title("Will NYC reach 32°C today?")
        assert result is None

    def test_parse_negative_threshold(self):
        """Test parsing negative temperature threshold."""
        result = parse_temperature_title("Will Chicago reach -10°F today?")
        assert result is not None
        assert result.threshold_f == -10
        assert result.direction == "HIGH"

    def test_parse_two_digit_threshold(self):
        """Test parsing two-digit threshold."""
        result = parse_temperature_title("Will Boston reach 55°F today?")
        assert result is not None
        assert result.threshold_f == 55

    def test_parse_three_digit_threshold(self):
        """Test parsing three-digit threshold (unlikely but possible)."""
        result = parse_temperature_title("Will Phoenix reach 115°F today?")
        assert result is not None
        assert result.threshold_f == 115
