"""Tests for baseline_builder.py."""

import tempfile
from unittest.mock import patch

import pytest

from kalshi_weather_arb.baseline_builder import BaselineBuilder


class TestBaselineBuilder:
    """Test BaselineBuilder class."""

    def test_init_default_dir(self):
        """Test initialization with default output directory."""
        builder = BaselineBuilder()
        assert builder.output_dir is not None

    def test_init_custom_dir(self):
        """Test initialization with custom output directory."""
        with tempfile.TemporaryDirectory() as tmpdir:
            builder = BaselineBuilder(output_dir=tmpdir)
            assert builder.output_dir == tmpdir

    def test_build_all_baselines_empty_years(self):
        """Test build_all_baselines with empty years list."""
        builder = BaselineBuilder()
        summary = builder.build_all_baselines([])
        assert summary["stations_processed"] == 12
        assert summary["years_processed"] == 0
        assert summary["files_created"] == 0

    def test_build_all_baselines_single_year(self):
        """Test build_all_baselines with single year."""
        builder = BaselineBuilder()
        with patch.object(builder, "_build_baseline_for_station_year") as mock_build:
            summary = builder.build_all_baselines([2023])
            assert summary["stations_processed"] == 12
            assert summary["years_processed"] == 12  # 12 stations
            assert summary["files_created"] == 12
            assert mock_build.call_count == 12

    def test_build_all_baselines_multiple_years(self):
        """Test build_all_baselines with multiple years."""
        builder = BaselineBuilder()
        with patch.object(builder, "_build_baseline_for_station_year") as mock_build:
            summary = builder.build_all_baselines([2023, 2024])
            assert summary["stations_processed"] == 12
            assert summary["years_processed"] == 24  # 12 stations * 2 years
            assert summary["files_created"] == 24
            assert mock_build.call_count == 24

    def test_build_all_baselines_with_errors(self):
        """Test build_all_baselines handles errors gracefully."""
        builder = BaselineBuilder()
        summary = builder.build_all_baselines([2023])
        # Errors should be collected, not raised
        assert "errors" in summary

    @pytest.mark.parametrize("station", ["KDJF", "KJFK", "KNDY"])
    def test_core_stations(self, station):
        """Test that core stations are expected values."""
        builder = BaselineBuilder()
        assert station in builder.CORE_STATIONS

    def test_isd_url_pattern(self):
        """Test ISD URL pattern format."""
        builder = BaselineBuilder()
        url = builder.ISD_URL_PATTERN.format(station="KJFK", year=2023)
        assert url == "https://ghpdap01.heotherg.com/data/isd/KJFK/KJFK2023.isd"

    def test_parse_isd_to_hourly_rises_empty(self):
        """Test _parse_isd_to_hourly_rises with empty data."""
        builder = BaselineBuilder()
        result = builder._parse_isd_to_hourly_rises("", 2023)
        assert result == {}

    def test_parse_isd_to_hourly_rises_single_day(self):
        """Test _parse_isd_to_hourly_rises with single day data."""
        builder = BaselineBuilder()
        isd_data = """20230101000000,50,45
20230101010000,52,46
20230101020000,55,48"""
        result = builder._parse_isd_to_hourly_rises(isd_data, 2023)
        # Should have at least hour 0 and 1 entries
        assert "0" in result or "1" in result

    def test_parse_isd_to_hourly_rises_multiple_days(self):
        """Test _parse_isd_to_hourly_rises with multiple days."""
        builder = BaselineBuilder()
        # Each day has complete hourly data (hour 0-23)
        isd_data = """20230101000000,50,45
20230101010000,52,46
20230101020000,55,48
20230101030000,58,50
20230101040000,60,52
20230102000000,55,50
20230102010000,57,52
20230102020000,60,55
20230102030000,63,57
20230102040000,65,59"""
        result = builder._parse_isd_to_hourly_rises(isd_data, 2023)
        # Should have hour 0-4 entries
        assert "0" in result
        assert "1" in result
        assert "2" in result
        assert "3" in result
        assert "4" in result

    def test_parse_isd_to_hourly_rises_no_data(self):
        """Test _parse_isd_to_hourly_rises with malformed data."""
        builder = BaselineBuilder()
        result = builder._parse_isd_to_hourly_rises("garbage data", 2023)
        assert result == {}

    def test_core_stations_count(self):
        """Test that there are 12 core stations."""
        builder = BaselineBuilder()
        assert len(builder.CORE_STATIONS) == 12

    def test_core_stations_format(self):
        """Test that station IDs are 4 characters."""
        builder = BaselineBuilder()
        for station in builder.CORE_STATIONS:
            assert len(station) == 4
