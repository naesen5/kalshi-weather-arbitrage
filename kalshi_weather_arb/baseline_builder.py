"""Build baseline data for temperature probability model from NOAA ISD data."""

import json
import os
import re
from collections import defaultdict
from pathlib import Path
from typing import Any, Dict, List, Optional


class BaselineBuilder:
    """Build baseline data from NOAA ISD files."""

    # 12 core stations
    CORE_STATIONS = [
        "KDJF",  # Davis, NJ
        "KJFK",  # JFK
        "KNDY",  # NED
        "KQTH",  # QTH
        "KSGE",  # SGE
        "KSLF",  # SLF
        "KSFH",  # SFH
        "KSGR",  # SGR
        "KSRM",  # SRM
        "KSTF",  # STF
        "KSWF",  # SWF
        "KSYG",  # SYG
    ]

    # NOAA ISD URL pattern (replace {station} and {year})
    ISD_URL_PATTERN = (
        "https://ghpdap01.heotherg.com/data/isd/{station}/{station}{year}.isd"
    )

    def __init__(self, output_dir: Optional[str] = None):
        """
        Initialize the baseline builder.

        Args:
            output_dir: Directory to save baseline JSON files.
                       If None, uses model/baselines/ relative to this module.
        """
        self.output_dir = output_dir
        if self.output_dir is None:
            module_dir = os.path.dirname(os.path.abspath(__file__))
            self.output_dir = os.path.join(module_dir, "model", "baselines")

        Path(self.output_dir).mkdir(parents=True, exist_ok=True)

    def build_all_baselines(self, years: List[int]) -> Dict[str, Any]:
        """
        Build baselines for all core stations and years.

        Args:
            years: List of years to download and process

        Returns:
            Summary dict with counts
        """
        summary = {
            "stations_processed": 0,
            "years_processed": 0,
            "files_created": 0,
            "errors": [],
        }

        for station in self.CORE_STATIONS:
            for year in years:
                try:
                    self._build_baseline_for_station_year(station, year)
                    summary["years_processed"] += 1
                except Exception as e:
                    summary["errors"].append(f"{station}-{year}: {e}")

        summary["stations_processed"] = len(self.CORE_STATIONS)
        summary["files_created"] = len(self.CORE_STATIONS) * len(years)

        return summary

    def _build_baseline_for_station_year(self, station: str, year: int) -> None:
        """Build baseline for a single station and year."""
        # Download ISD file
        isd_data = self._download_isd(station, year)
        if not isd_data:
            raise ValueError(f"Failed to download ISD for {station}-{year}")

        # Parse ISD data
        hourly_rises = self._parse_isd_to_hourly_rises(isd_data, year)

        # Build baseline
        baseline = {
            "station": station,
            "year": year,
            "hour_rises": hourly_rises,
        }

        # Save to file
        filename = f"{station}_{year:04d}.json"
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, "w") as f:
            json.dump(baseline, f, indent=2)

        print(f"Created: {filename}")

    def _download_isd(self, station: str, year: int) -> Optional[str]:
        """Download ISD file for station and year."""
        url = self.ISD_URL_PATTERN.format(station=station, year=year)
        print(f"Downloading: {url}")
        # TODO: Implement actual download
        # For now, return placeholder
        return None

    def _parse_isd_to_hourly_rises(
        self, isd_data: str, year: int
    ) -> Dict[str, Dict[str, float]]:
        """
        Parse ISD data to extract hourly rise distributions.

        Args:
            isd_data: Raw ISD file content
            year: Year being processed

        Returns:
            Dict mapping hour (0-23) to rise stats {mean_rise_f, std_rise_f, count}
        """
        defaultdict(list)  # hour -> list of temps
        hourly_highs = defaultdict(list)  # hour -> list of daily highs

        # Parse ISD format (simplified)
        # Each line: YYYYMMDDHHMMSS,TEMP,DEWPOINT,...
        lines = isd_data.strip().split("\n")

        current_date = None
        current_day_temps = []
        current_day_high = None

        for line in lines:
            if not line.strip():
                continue

            # Parse line - extract date, hour, temp
            match = re.match(r"(\d{8})(\d{2})(\d{2})\d{2},(-?\d+\.?\d*)", line)
            if match:
                date_str = match.group(1)  # YYYYMMDD
                hour = int(match.group(2))
                int(match.group(3))
                temp = float(match.group(4))

                if current_date != date_str:
                    # New day
                    if current_date is not None and current_day_high is not None:
                        # Record the high for previous day
                        for h in range(24):
                            if (
                                h < len(current_day_temps)
                                and current_day_temps[h] is not None
                            ):
                                hourly_highs[h].append(
                                    current_day_high - current_day_temps[h]
                                )

                    current_date = date_str
                    current_day_temps = [None] * 24
                    current_day_high = None

                current_day_temps[hour] = temp
                if current_day_high is None or temp > current_day_high:
                    current_day_high = temp

        # Final day
        if current_date is not None and current_day_high is not None:
            for h in range(24):
                if h < len(current_day_temps) and current_day_temps[h] is not None:
                    hourly_highs[h].append(current_day_high - current_day_temps[h])

        # Calculate stats for each hour
        hourly_rises = {}
        for hour in range(24):
            rises = hourly_highs.get(hour, [])
            if rises:
                mean_rise = sum(rises) / len(rises)
                variance = sum((r - mean_rise) ** 2 for r in rises) / len(rises)
                std_rise = variance**0.5
                hourly_rises[str(hour)] = {
                    "mean_rise_f": round(mean_rise, 2),
                    "std_rise_f": round(std_rise, 2),
                    "count": len(rises),
                }

        return hourly_rises


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(
        description="Build temperature probability baselines"
    )
    parser.add_argument(
        "--years",
        nargs="+",
        type=int,
        default=[2023, 2024],
        help="Years to process",
    )
    parser.add_argument(
        "--output-dir",
        help="Output directory for baseline JSON files",
    )

    args = parser.parse_args()

    builder = BaselineBuilder(output_dir=args.output_dir)
    summary = builder.build_all_baselines(args.years)

    print("\n=== Summary ===")
    print(f"Stations processed: {summary['stations_processed']}")
    print(f"Years processed: {summary['years_processed']}")
    print(f"Files created: {summary['files_created']}")
    if summary["errors"]:
        print(f"\nErrors ({len(summary['errors'])}):")
        for err in summary["errors"][:5]:
            print(f"  - {err}")


if __name__ == "__main__":
    main()
