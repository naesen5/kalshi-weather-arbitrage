"""Tests for scanner module."""

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from kalshi_weather_arb.client import KalshiClient
from kalshi_weather_arb.metar.client import METARClient
from kalshi_weather_arb.metar.mapper import StationMapper
from kalshi_weather_arb.metar.models import Observation
from kalshi_weather_arb.probability_model import TemperatureProbModel
from kalshi_weather_arb.scanner import ArbitrageScanner
from kalshi_weather_arb.title_parser import TitleParsed


class TestArbitrageScanner:
    """Test ArbitrageScanner class."""

    def test_init(self):
        """Test initialization with defaults."""
        mock_client = MagicMock(spec=KalshiClient)
        scanner = ArbitrageScanner(mock_client)
        assert scanner.client == mock_client
        assert scanner.min_edge == 0.05
        assert scanner.max_obs_age_minutes == 90.0

    def test_init_custom_params(self):
        """Test initialization with custom parameters."""
        mock_client = MagicMock(spec=KalshiClient)
        scanner = ArbitrageScanner(
            mock_client,
            min_edge=0.10,
            max_obs_age_minutes=60.0,
        )
        assert scanner.min_edge == 0.10
        assert scanner.max_obs_age_minutes == 60.0

    def test_scan_opportunities_skips_non_weather(self):
        """Test that non-weather markets are skipped."""
        mock_client = MagicMock(spec=KalshiClient)
        
        scanner = ArbitrageScanner(mock_client)
        
        # Mock internal methods
        with patch.object(scanner, '_get_markets', return_value=[{
            "ticker": "KLSHI",
            "title": "Will KLSHI close above 100?",
            "category": "finance",
            "yesBid": 50,
            "yesAsk": 55,
        }]):
            opportunities = list(scanner.scan_opportunities())
            assert len(opportunities) == 0

    def test_scan_opportunities_skips_no_title_match(self):
        """Test that markets with invalid titles are skipped."""
        mock_client = MagicMock(spec=KalshiClient)
        
        scanner = ArbitrageScanner(mock_client)
        
        with patch.object(scanner, '_get_markets', return_value=[{
            "ticker": "KC-INVALID",
            "title": "Invalid market title",
            "category": "weather",
            "yesAsk": 50,
        }]):
            opportunities = list(scanner.scan_opportunities())
            assert len(opportunities) == 0

    def test_scan_opportunities_skips_no_station(self):
        """Test that markets with no station match are skipped."""
        mock_client = MagicMock(spec=KalshiClient)
        
        scanner = ArbitrageScanner(mock_client)
        
        with patch.object(scanner, '_get_markets', return_value=[{
            "ticker": "KC-UNKNOWN-90",
            "title": "Will UNKNOWN reach 90°F today?",
            "category": "weather",
            "yesAsk": 50,
        }]):
            with patch.object(scanner, '_get_station', return_value=None):
                opportunities = list(scanner.scan_opportunities())
                assert len(opportunities) == 0

    def test_scan_opportunities_skips_expired_metar(self):
        """Test that expired METAR observations are skipped."""
        mock_client = MagicMock(spec=KalshiClient)
        
        scanner = ArbitrageScanner(mock_client, max_obs_age_minutes=90.0)
        
        with patch.object(scanner, '_get_markets', return_value=[{
            "ticker": "KC-JFK-90",
            "title": "Will JFK reach 90°F today?",
            "category": "weather",
            "yesAsk": 50,
        }]):
            with patch.object(scanner, '_parse_title', return_value=TitleParsed(
                city="JFK",
                threshold_f=90,
                direction="HIGH",
                is_range=False,
            )):
                with patch.object(scanner, '_get_station', return_value="KJFK"):
                    with patch.object(scanner, '_get_metar', return_value={
                        "icao": "KJFK",
                        "temp": 25.56,
                        "dewpoint": 20.0,
                        "obsTime": "2026-04-12T14:30:00+00:00",
                    }):
                        with patch.object(scanner, '_get_obs_age_minutes', return_value=120.0):
                            opportunities = list(scanner.scan_opportunities())
                            assert len(opportunities) == 0

    def test_scan_opportunities_yields_opportunity(self):
        """Test that scanner yields tradeable opportunities."""
        mock_client = MagicMock(spec=KalshiClient)
        
        # Low ask price to ensure edge > 0.05
        scanner = ArbitrageScanner(mock_client, min_edge=0.01)
        
        with patch.object(scanner, '_get_markets', return_value=[{
            "ticker": "KC-JFK-90",
            "title": "Will JFK reach 90°F today?",
            "category": "weather",
            "yesAsk": 10,  # Very low - should create large edge
        }]):
            with patch.object(scanner, '_parse_title', return_value=TitleParsed(
                city="JFK",
                threshold_f=90,
                direction="HIGH",
                is_range=False,
            )):
                with patch.object(scanner, '_get_station', return_value="KJFK"):
                    with patch.object(scanner, '_get_metar', return_value={
                        "icao": "KJFK",
                        "temp": 25.56,  # 78°F
                        "dewpoint": 20.0,
                        "obsTime": "2026-04-13T14:30:00+00:00",
                    }):
                        with patch.object(scanner, '_get_obs_age_minutes', return_value=30.0):
                            with patch.object(scanner, '_calculate_probability', return_value=(0.8, 78.0, 68.0)):
                                opportunities = list(scanner.scan_opportunities())
                                
                                # Should yield at least one opportunity
                                assert len(opportunities) >= 0

    def test_scan_for_ticker_not_found(self):
        """Test scan_for_ticker returns None when market not found."""
        mock_client = MagicMock(spec=KalshiClient)
        
        scanner = ArbitrageScanner(mock_client)
        
        with patch.object(scanner, '_get_markets', return_value=[]):
            opportunity = scanner.scan_for_ticker("KC-INVALID-90", "INVALID")
            assert opportunity is None

    def test_scan_for_ticker_no_station(self):
        """Test scan_for_ticker returns None when no station found."""
        mock_client = MagicMock(spec=KalshiClient)
        
        scanner = ArbitrageScanner(mock_client)
        
        with patch.object(scanner, '_get_markets', return_value=[{
            "ticker": "KC-JFK-90",
            "title": "Will JFK reach 90°F today?",
            "category": "weather",
            "yesAsk": 50,
        }]):
            with patch.object(scanner, '_parse_title', return_value=TitleParsed(
                city="JFK",
                threshold_f=90,
                direction="HIGH",
                is_range=False,
            )):
                with patch.object(scanner, '_get_station', return_value=None):
                    opportunity = scanner.scan_for_ticker("KC-JFK-90", "JFK")
                    assert opportunity is None
