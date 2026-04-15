"""Tests for ArbitrageScanner class."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.metar.client import METARClient
from kalshi_weather_arb.metar.models import Observation
from kalshi_weather_arb.metar.mapper import StationMapper
from kalshi_weather_arb.probability_model import TemperatureProbModel
from kalshi_weather_arb.scanner import ArbitrageScanner
from kalshi_weather_arb.models import Opportunity


class TestArbitrageScanner:
    """Tests for ArbitrageScanner class."""

    def test_init(self):
        """Test default initialization."""
        mock_client = MagicMock(spec=KalshiClient)
        scanner = ArbitrageScanner(mock_client)
        
        assert scanner.client == mock_client
        assert isinstance(scanner.metar_client, METARClient)
        assert isinstance(scanner.mapper, StationMapper)
        assert isinstance(scanner.model, TemperatureProbModel)
        assert scanner.min_edge == 0.05
        assert scanner.max_obs_age_minutes == 90.0

    def test_init_with_custom_params(self):
        """Test initialization with custom parameters."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_model = MagicMock(spec=TemperatureProbModel)
        scanner = ArbitrageScanner(
            mock_client,
            model=mock_model,
            min_edge=0.10,
            max_obs_age_minutes=60.0,
        )
        assert scanner.model == mock_model
        assert scanner.min_edge == 0.10
        assert scanner.max_obs_age_minutes == 60.0

    def test_scan_opportunities_empty(self):
        """Test scan_opportunities returns empty generator when no markets."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = []
        scanner = ArbitrageScanner(mock_client)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_non_weather(self):
        """Test scan_opportunities skips non-weather markets."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {"category": "crypto", "ticker": "BTC", "title": "Bitcoin > 50000"},
        ]
        scanner = ArbitrageScanner(mock_client)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_no_title_match(self):
        """Test scan_opportunities skips markets with unparseable titles."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {"category": "weather", "ticker": "TEST", "title": "Invalid title"},
        ]
        scanner = ArbitrageScanner(mock_client)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_no_station(self):
        """Test scan_opportunities skips markets with no station match."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "category": "weather",
                "ticker": "TEST",
                "title": "Will UnknownCity reach 90°F today?",
                "yesAsk": 40,
            },
        ]
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = None
        scanner = ArbitrageScanner(mock_client, mapper=mock_mapper)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_no_metar(self):
        """Test scan_opportunities skips markets with no METAR data."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "category": "weather",
                "ticker": "TEST",
                "title": "Will NYC reach 90°F today?",
                "yesAsk": 40,
            },
        ]
        mock_metar = MagicMock(spec=METARClient)
        mock_metar.fetch.return_value = []
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = "KJFK"
        scanner = ArbitrageScanner(mock_client, metar_client=mock_metar, mapper=mock_mapper)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_obs_too_old(self):
        """Test scan_opportunities skips markets with old METAR."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "category": "weather",
                "ticker": "TEST",
                "title": "Will NYC reach 90°F today?",
                "yesAsk": 40,
            },
        ]
        mock_metar = MagicMock(spec=METARClient)
        
        # METAR from 2 hours ago
        old_time = datetime.now(timezone.utc).replace(
            hour=datetime.now(timezone.utc).hour - 2
        )
        mock_obs = MagicMock(spec=Observation)
        mock_obs.icao = "KJFK"
        mock_obs.temp_c = 20.0
        mock_obs.dewpoint = 15.0
        mock_obs.obs_time = old_time
        mock_metar.fetch.return_value = [mock_obs]
        
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = "KJFK"
        scanner = ArbitrageScanner(mock_client, metar_client=mock_metar, mapper=mock_mapper, max_obs_age_minutes=10.0)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_no_edge(self):
        """Test scan_opportunities yields nothing when edge < min_edge."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "category": "weather",
                "ticker": "TEST",
                "title": "Will NYC reach 90°F today?",
                "yesAsk": 70,  # Market prob = 0.7
            },
        ]
        mock_metar = MagicMock(spec=METARClient)
        
        # Mock METAR and model to give low probability
        mock_obs = MagicMock(spec=Observation)
        mock_obs.icao = "KJFK"
        mock_obs.temp_c = 50.0  # Very cold
        mock_obs.dewpoint = 40.0
        mock_obs.obs_time = datetime.now(timezone.utc)
        mock_metar.fetch.return_value = [mock_obs]
        
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = "KJFK"
        
        mock_model = MagicMock(spec=TemperatureProbModel)
        mock_model.p_exceed.return_value = 0.5  # Low probability
        
        scanner = ArbitrageScanner(mock_client, metar_client=mock_metar, mapper=mock_mapper, model=mock_model, min_edge=0.10)
        opportunities = list(scanner.scan_opportunities())
        assert opportunities == []

    def test_scan_opportunities_with_opportunity(self):
        """Test scan_opportunities yields opportunity when edge >= min_edge."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "category": "weather",
                "ticker": "KC-NYC-90",
                "title": "Will NYC reach 90°F today?",
                "yesAsk": 40,  # Market prob = 0.4
            },
        ]
        mock_metar = MagicMock(spec=METARClient)
        
        # Mock METAR for NYC
        mock_obs = MagicMock(spec=Observation)
        mock_obs.icao = "KJFK"
        mock_obs.temp_c = 80.0  # Warm
        mock_obs.dewpoint = 70.0  # Humid
        mock_obs.obs_time = datetime.now(timezone.utc)
        mock_metar.fetch.return_value = [mock_obs]
        
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = "KJFK"
        
        mock_model = MagicMock(spec=TemperatureProbModel)
        mock_model.p_exceed.return_value = 0.8  # High probability
        
        scanner = ArbitrageScanner(mock_client, metar_client=mock_metar, mapper=mock_mapper, model=mock_model, min_edge=0.05)
        opportunities = list(scanner.scan_opportunities())
        assert len(opportunities) >= 1

    def test_scan_for_ticker_no_market(self):
        """Test scan_for_ticker returns None when market not found."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = []
        scanner = ArbitrageScanner(mock_client)
        result = scanner.scan_for_ticker("TEST", "NYC")
        assert result is None

    def test_scan_for_ticker_invalid_title(self):
        """Test scan_for_ticker returns None for invalid title."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {"ticker": "TEST", "title": "Invalid", "yesAsk": 40},
        ]
        scanner = ArbitrageScanner(mock_client)
        result = scanner.scan_for_ticker("TEST", "NYC")
        assert result is None

    def test_scan_for_ticker_no_station(self):
        """Test scan_for_ticker returns None when station not found."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "ticker": "TEST",
                "title": "Will UnknownCity reach 90°F today?",
                "yesAsk": 40,
            },
        ]
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = None
        scanner = ArbitrageScanner(mock_client, mapper=mock_mapper)
        result = scanner.scan_for_ticker("TEST", "UnknownCity")
        assert result is None

    def test_scan_for_ticker_with_opportunity(self):
        """Test scan_for_ticker returns opportunity when found."""
        mock_client = MagicMock(spec=KalshiClient)
        mock_client.paginate.return_value = [
            {
                "ticker": "KC-NYC-90",
                "title": "Will NYC reach 90°F today?",
                "yesAsk": 40,
            },
        ]
        mock_metar = MagicMock(spec=METARClient)
        
        mock_obs = MagicMock(spec=Observation)
        mock_obs.icao = "KJFK"
        mock_obs.temp_c = 80.0
        mock_obs.dewpoint = 70.0
        mock_obs.obs_time = datetime.now(timezone.utc)
        mock_metar.fetch.return_value = [mock_obs]
        
        mock_mapper = MagicMock(spec=StationMapper)
        mock_mapper.get_station.return_value = "KJFK"
        
        mock_model = MagicMock(spec=TemperatureProbModel)
        mock_model.p_exceed.return_value = 0.8
        
        scanner = ArbitrageScanner(mock_client, metar_client=mock_metar, mapper=mock_mapper, model=mock_model, min_edge=0.05)
        
        result = scanner.scan_for_ticker("KC-NYC-90", "NYC")
        assert result is not None
        assert isinstance(result, Opportunity)
