"""
CLI entry point for the Earthquake Data Visualizer.

Usage:
    python main.py --report
    python main.py --report --min-magnitude 4.5
    python main.py --map --output data/earthquake_map.html

Then:
    streamlit run app.py       # launch the interactive dashboard
"""

from __future__ import annotations

import argparse
import logging
import sys

from src.config import HTML_MAP_PATH
from src.exceptions import EarthquakeVisualizerError
from src.map_builder import build_earthquake_map, save_map_to_html
from src.visualizer_service import build_report

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s")
logger = logging.getLogger(__name__)


def _print_report(min_magnitude: float, max_magnitude: float, place_query: str) -> None:
    report = build_report(min_magnitude, max_magnitude, place_query=place_query)
    source_label = "LIVE USGS feed" if report.source == "live" else "CACHED snapshot (see README)"

    print(f"\nData source: {source_label}")
    if place_query.strip():
        print(f"Place filter: '{place_query}'")
    print(f"Earthquakes in range M{min_magnitude}-M{max_magnitude}: {len(report.earthquakes)}\n")

    if report.significant_events:
        print(f"🚨 {len(report.significant_events)} significant event(s) (M6.0+):")
        for eq in report.significant_events[:5]:
            print(f"  M{eq.magnitude}  {eq.place}  {eq.occurred_at.strftime('%Y-%m-%d %H:%M UTC')}")
        print()

    print("Magnitude distribution:")
    for band, count in report.magnitude_distribution.band_counts.items():
        print(f"  {band:10s} {count:4d}")

    print(f"\nDaily frequency ({len(report.daily_frequency)} day(s) with activity):")
    for day_stat in report.daily_frequency[-10:]:
        print(f"  {day_stat.day}  count={day_stat.count:3d}  avg_mag={day_stat.average_magnitude}")

    print(f"\nTop risk zones ({len(report.risk_zones)} found):")
    for zone in report.risk_zones[:10]:
        print(f"  ({zone.center_lat:7.2f}, {zone.center_lon:7.2f})  events={zone.event_count:3d}  "
              f"max_mag={zone.max_magnitude}  avg_mag={zone.average_magnitude}")
    print()


def _build_map(min_magnitude: float, max_magnitude: float, output_path: str) -> None:
    report = build_report(min_magnitude, max_magnitude)
    fmap = build_earthquake_map(report.earthquakes, risk_zones=report.risk_zones)
    path = save_map_to_html(fmap, output_path)
    print(f"\nMap saved to '{path}' — open it in a browser.\n")


def main() -> int:
    parser = argparse.ArgumentParser(description="Earthquake Data Visualizer CLI")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--report", action="store_true", help="Print a text analysis report")
    group.add_argument("--map", action="store_true", help="Generate an interactive HTML map")
    parser.add_argument("--min-magnitude", type=float, default=0.0, help="Minimum magnitude to include")
    parser.add_argument("--max-magnitude", type=float, default=10.0, help="Maximum magnitude to include")
    parser.add_argument("--place", default="", help="Filter to events whose place contains this text")
    parser.add_argument("--output", default=HTML_MAP_PATH, help="Output path for --map")
    args = parser.parse_args()

    try:
        if args.report:
            _print_report(args.min_magnitude, args.max_magnitude, args.place)
        elif args.map:
            _build_map(args.min_magnitude, args.max_magnitude, args.output)
    except EarthquakeVisualizerError as exc:
        logger.error("%s", exc)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
