"""Tests for METAR mapper module."""

import pytest
from kalshi_weather_arb.metar.mapper import StationMapper


class TestStationMapper:
    """Test StationMapper class."""

    @pytest.fixture
    def mapper(self):
        """Create mapper instance."""
        return StationMapper()

    def test_init(self, mapper):
        """Test initialization."""
        assert mapper is not None
        assert len(mapper.stations) > 0

    def test_match_nyc(self, mapper):
        """Test matching NYC market."""
        market = "Will it be hotter than 90 in NYC on July 15, 2026?"
        icao = mapper.match_market(market)
        assert icao in ["KJFK", "KEWR"]

    def test_match_chicago(self, mapper):
        """Test matching Chicago market."""
        market = "Chicago temperature over 85 on August 1?"
        icao = mapper.match_market(market)
        assert icao in ["KORD", "KMDW"]

    def test_match_los_angeles(self, mapper):
        """Test matching LA market."""
        market = "LA heat wave over 95 degrees in July"
        icao = mapper.match_market(market)
        assert icao == "KLAX"

    def test_match_denver(self, mapper):
        """Test matching Denver market."""
        market = "Denver CO temperature under 70 on Memorial Day"
        icao = mapper.match_market(market)
        assert icao == "KDEN"

    def test_match_seattle(self, mapper):
        """Test matching Seattle market."""
        market = "Will Seattle WA be hotter than 80 on June 21?"
        icao = mapper.match_market(market)
        assert icao == "KSEA"

    def test_match_no_city(self, mapper):
        """Test market without city reference returns None."""
        market = "Will Kalshi stock price go up?"
        icao = mapper.match_market(market)
        assert icao is None

    def test_get_station_info(self, mapper):
        """Test getting station info by ICAO."""
        info = mapper.get_station_info("KJFK")
        assert info is not None
        assert info["city"] == "New York"
        assert info["region"] == "NY"

    def test_get_station_info_invalid(self, mapper):
        """Test getting info for invalid ICAO."""
        info = mapper.get_station_info("KINVALID")
        assert info is None
