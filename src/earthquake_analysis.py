"""
Earthquake data analysis.

Pure functions over a list of :class:`~src.usgs_client.Earthquake`
objects — no I/O, no plotting, trivially testable.
"""

from __future__ import annotations

import logging
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import date

from src.config import MAGNITUDE_BANDS, MIN_QUAKES_FOR_RISK_ZONE, RISK_ZONE_GRID_DEGREES
from src.exceptions import InvalidMagnitudeRangeError
from src.usgs_client import Earthquake

logger = logging.getLogger(__name__)


def classify_magnitude(magnitude: float) -> str:
    """Classify a magnitude into its USGS-standard descriptive band.

    Args:
        magnitude: The earthquake's magnitude.

    Returns:
        A band label (e.g. ``"Moderate"``). Magnitudes below the
        lowest configured band or above the highest still resolve to
        the nearest end band, so this never raises on an edge value.
    """
    for low, high, label in MAGNITUDE_BANDS:
        if low <= magnitude <= high:
            return label
    return MAGNITUDE_BANDS[-1][2] if magnitude > MAGNITUDE_BANDS[-1][1] else MAGNITUDE_BANDS[0][2]


def filter_by_magnitude(
    earthquakes: list[Earthquake], min_magnitude: float, max_magnitude: float = 10.0
) -> list[Earthquake]:
    """Filter earthquakes to a magnitude range, inclusive on both ends.

    Args:
        earthquakes: The full event list.
        min_magnitude: Minimum magnitude to include.
        max_magnitude: Maximum magnitude to include.

    Returns:
        Matching earthquakes, in their original order.

    Raises:
        InvalidMagnitudeRangeError: If ``min_magnitude > max_magnitude``.
    """
    if min_magnitude > max_magnitude:
        raise InvalidMagnitudeRangeError(
            f"min_magnitude ({min_magnitude}) cannot exceed max_magnitude ({max_magnitude})."
        )
    return [eq for eq in earthquakes if min_magnitude <= eq.magnitude <= max_magnitude]


def get_significant_events(earthquakes: list[Earthquake], threshold: float = 6.0) -> list[Earthquake]:
    """Find earthquakes at or above a "significant" magnitude threshold.

    USGS itself uses 6.0+ informally as a threshold worth separate
    attention (it's roughly where widespread structural damage
    becomes possible for shallow events) — surfacing these separately,
    sorted most-recent-first, is what makes a monitoring dashboard
    actually useful at a glance rather than just a wall of markers.

    Args:
        earthquakes: The event list to scan.
        threshold: Minimum magnitude to count as "significant".

    Returns:
        Matching earthquakes, most recent first.
    """
    significant = [eq for eq in earthquakes if eq.magnitude >= threshold]
    return sorted(significant, key=lambda eq: eq.occurred_at, reverse=True)


def search_by_place(earthquakes: list[Earthquake], query: str) -> list[Earthquake]:
    """Filter earthquakes to those whose place description contains a query string.

    Args:
        earthquakes: The event list to search.
        query: A case-insensitive substring to match against each
            event's ``place`` field (e.g. ``"California"``, ``"Japan"``).
            An empty/whitespace-only query returns every event unfiltered.

    Returns:
        Matching earthquakes, in their original order.
    """
    normalized = query.strip().lower()
    if not normalized:
        return list(earthquakes)
    return [eq for eq in earthquakes if normalized in eq.place.lower()]


@dataclass(frozen=True)
class DailyFrequency:
    """Earthquake count for a single day.

    Attributes:
        day: The calendar date (UTC).
        count: Number of earthquakes that occurred on that day.
        average_magnitude: Mean magnitude of that day's earthquakes.
    """

    day: date
    count: int
    average_magnitude: float


def compute_daily_frequency(earthquakes: list[Earthquake]) -> list[DailyFrequency]:
    """Compute a day-by-day earthquake frequency time series.

    Args:
        earthquakes: The event list to aggregate.

    Returns:
        One :class:`DailyFrequency` per day that had at least one
        event, sorted chronologically.
    """
    by_day: dict[date, list[float]] = defaultdict(list)
    for eq in earthquakes:
        by_day[eq.occurred_at.date()].append(eq.magnitude)

    return [
        DailyFrequency(day=day, count=len(mags), average_magnitude=round(sum(mags) / len(mags), 2))
        for day, mags in sorted(by_day.items())
    ]


@dataclass(frozen=True)
class RiskZone:
    """An aggregated cluster of seismic activity in one grid cell.

    Attributes:
        center_lat: Latitude at the center of this grid cell.
        center_lon: Longitude at the center of this grid cell.
        event_count: Number of earthquakes in this cell.
        max_magnitude: Strongest earthquake in this cell.
        average_magnitude: Mean magnitude in this cell.
    """

    center_lat: float
    center_lon: float
    event_count: int
    max_magnitude: float
    average_magnitude: float


def compute_risk_zones(
    earthquakes: list[Earthquake], grid_degrees: float = RISK_ZONE_GRID_DEGREES
) -> list[RiskZone]:
    """Aggregate earthquakes into a lat/lon grid to highlight high-activity zones.

    A simple, explainable heuristic — not a scientific seismic hazard
    model (see README) — but a genuinely useful "where has it actually
    been shaking" summary, ranked by event count.

    Args:
        earthquakes: The event list to aggregate.
        grid_degrees: Size of each square grid cell, in degrees.

    Returns:
        Risk zones with at least :data:`~src.config.MIN_QUAKES_FOR_RISK_ZONE`
        events, sorted by event count descending (busiest zone first).
    """
    cells: dict[tuple[int, int], list[Earthquake]] = defaultdict(list)
    for eq in earthquakes:
        cell_key = (round(eq.latitude / grid_degrees), round(eq.longitude / grid_degrees))
        cells[cell_key].append(eq)

    zones = []
    for (lat_cell, lon_cell), events in cells.items():
        if len(events) < MIN_QUAKES_FOR_RISK_ZONE:
            continue
        magnitudes = [eq.magnitude for eq in events]
        zones.append(
            RiskZone(
                center_lat=lat_cell * grid_degrees,
                center_lon=lon_cell * grid_degrees,
                event_count=len(events),
                max_magnitude=max(magnitudes),
                average_magnitude=round(sum(magnitudes) / len(magnitudes), 2),
            )
        )

    zones.sort(key=lambda z: z.event_count, reverse=True)
    logger.info("Computed %d risk zone(s) from %d earthquake(s)", len(zones), len(earthquakes))
    return zones


@dataclass(frozen=True)
class MagnitudeDistribution:
    """A count of earthquakes per descriptive magnitude band.

    Attributes:
        band_counts: Ordered mapping of band label -> count, in the
            same order as :data:`~src.config.MAGNITUDE_BANDS`.
    """

    band_counts: dict[str, int]


def compute_magnitude_distribution(earthquakes: list[Earthquake]) -> MagnitudeDistribution:
    """Count earthquakes per descriptive magnitude band.

    Args:
        earthquakes: The event list to summarize.

    Returns:
        A :class:`MagnitudeDistribution` with every configured band
        present (even at zero), in band order.
    """
    counts = Counter(classify_magnitude(eq.magnitude) for eq in earthquakes)
    ordered_labels = list(dict.fromkeys(label for _low, _high, label in MAGNITUDE_BANDS))
    return MagnitudeDistribution(band_counts={label: counts.get(label, 0) for label in ordered_labels})
