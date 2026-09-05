"""
Orchestration layer for the Earthquake Data Visualizer.

Single source of truth for "how loading and analyzing earthquake data
happens" — both ``main.py`` and ``app.py`` call into this module
rather than composing the pipeline themselves.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass

from src.earthquake_analysis import (
    DailyFrequency,
    MagnitudeDistribution,
    RiskZone,
    compute_daily_frequency,
    compute_magnitude_distribution,
    compute_risk_zones,
    filter_by_magnitude,
    get_significant_events,
    search_by_place,
)
from src.usgs_client import Earthquake, EarthquakeDataset, load_earthquake_data

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class VisualizerReport:
    """A complete, ready-to-render earthquake analysis.

    Attributes:
        earthquakes: The (magnitude- and place-filtered) events.
        source: ``"live"`` or ``"cached"`` — where the data came from.
        daily_frequency: Day-by-day event counts.
        risk_zones: Aggregated high-activity grid cells.
        magnitude_distribution: Counts per descriptive magnitude band.
        significant_events: Filtered events at or above the
            significant-magnitude threshold, most recent first —
            surfaced separately so a dashboard can highlight them
            without the user having to go looking.
    """

    earthquakes: list[Earthquake]
    source: str
    daily_frequency: list[DailyFrequency]
    risk_zones: list[RiskZone]
    magnitude_distribution: MagnitudeDistribution
    significant_events: list[Earthquake]


def build_report(
    min_magnitude: float = 0.0,
    max_magnitude: float = 10.0,
    place_query: str = "",
    significant_threshold: float = 6.0,
) -> VisualizerReport:
    """Load earthquake data and run the full analysis pipeline against it.

    Args:
        min_magnitude: Minimum magnitude to include (inclusive).
        max_magnitude: Maximum magnitude to include (inclusive).
        place_query: Optional case-insensitive substring to filter
            events by place name (e.g. ``"Alaska"``). Empty = no filter.
        significant_threshold: Magnitude at or above which an event is
            called out as "significant" in the returned report.

    Returns:
        A complete :class:`VisualizerReport`.

    Raises:
        DataFetchError: If neither the live feed nor the cached
            snapshot could be loaded.
        InvalidMagnitudeRangeError: If ``min_magnitude > max_magnitude``.
    """
    dataset: EarthquakeDataset = load_earthquake_data()
    filtered = filter_by_magnitude(dataset.earthquakes, min_magnitude, max_magnitude)
    filtered = search_by_place(filtered, place_query)

    report = VisualizerReport(
        earthquakes=filtered,
        source=dataset.source,
        daily_frequency=compute_daily_frequency(filtered),
        risk_zones=compute_risk_zones(filtered),
        magnitude_distribution=compute_magnitude_distribution(filtered),
        significant_events=get_significant_events(filtered, significant_threshold),
    )
    logger.info(
        "Built report: %d earthquake(s) (source=%s) after filtering to M%.1f-M%.1f%s — %d significant",
        len(filtered), dataset.source, min_magnitude, max_magnitude,
        f" matching '{place_query}'" if place_query.strip() else "", len(report.significant_events),
    )
    return report
