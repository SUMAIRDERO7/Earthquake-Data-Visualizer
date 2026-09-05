"""
USGS earthquake data client.

Live-first, honest-fallback: attempts the real USGS GeoJSON feed, and
transparently falls back to the cached snapshot when unreachable
(always true in this sandbox — see README). The data source is
always surfaced to the caller, never silently substituted.
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import requests

from src.cached_snapshot import generate_snapshot
from src.config import CACHED_SNAPSHOT_PATH, USGS_FEED_URL, USGS_REQUEST_TIMEOUT_SECONDS
from src.exceptions import DataFetchError, InvalidGeoJSONError

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class Earthquake:
    """A single earthquake event, normalized from either the live feed
    or the cached snapshot — every downstream module only ever sees this shape.

    Attributes:
        magnitude: Richter-scale magnitude.
        place: Human-readable location description.
        latitude: Epicenter latitude.
        longitude: Epicenter longitude.
        depth_km: Depth below the surface, in kilometers.
        occurred_at: When the event occurred (UTC).
    """

    magnitude: float
    place: str
    latitude: float
    longitude: float
    depth_km: float
    occurred_at: datetime


@dataclass(frozen=True)
class EarthquakeDataset:
    """A full loaded dataset plus its provenance.

    Attributes:
        earthquakes: The normalized events.
        source: ``"live"`` if fetched from the real USGS API, ``"cached"``
            if the offline snapshot was used instead — never hidden.
    """

    earthquakes: list[Earthquake]
    source: str


def _parse_geojson(raw: dict) -> list[Earthquake]:
    """Parse a USGS-shaped GeoJSON FeatureCollection into normalized events.

    Args:
        raw: A dict matching the USGS GeoJSON FeatureCollection schema.

    Returns:
        Normalized :class:`Earthquake` objects.

    Raises:
        InvalidGeoJSONError: If the top-level shape or a feature is malformed.
    """
    if raw.get("type") != "FeatureCollection" or "features" not in raw:
        raise InvalidGeoJSONError("Expected a GeoJSON FeatureCollection with a 'features' list.")

    earthquakes = []
    for feature in raw["features"]:
        try:
            props = feature["properties"]
            longitude, latitude, depth_km = feature["geometry"]["coordinates"][:3]
            magnitude = props["mag"]
            if magnitude is None:
                continue  # USGS sometimes reports events with no magnitude yet — skip, don't crash
            earthquakes.append(
                Earthquake(
                    magnitude=float(magnitude),
                    place=props.get("place") or "Unknown location",
                    latitude=float(latitude),
                    longitude=float(longitude),
                    depth_km=float(depth_km),
                    occurred_at=datetime.fromtimestamp(props["time"] / 1000, tz=timezone.utc),
                )
            )
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            raise InvalidGeoJSONError(f"Malformed earthquake feature: {exc}") from exc

    return earthquakes


def _fetch_live() -> list[Earthquake]:
    """Attempt to fetch and parse the real USGS feed.

    Returns:
        Normalized earthquake events from the live feed.

    Raises:
        DataFetchError: If the request fails for any reason (network,
            timeout, non-200 status).
        InvalidGeoJSONError: If the response body isn't valid GeoJSON
            in the expected shape.
    """
    try:
        response = requests.get(USGS_FEED_URL, timeout=USGS_REQUEST_TIMEOUT_SECONDS)
        response.raise_for_status()
        raw = response.json()
    except requests.exceptions.RequestException as exc:
        raise DataFetchError(f"Could not reach the live USGS feed: {exc}") from exc
    except json.JSONDecodeError as exc:
        raise DataFetchError(f"USGS feed did not return valid JSON: {exc}") from exc

    return _parse_geojson(raw)


def _load_cached(snapshot_path: str) -> list[Earthquake]:
    """Load (generating if necessary) the cached snapshot from disk.

    Args:
        snapshot_path: Path to the cached JSON snapshot file.

    Returns:
        Normalized earthquake events from the cached snapshot.
    """
    path = Path(snapshot_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(generate_snapshot(), indent=2), encoding="utf-8")
        logger.info("Generated cached snapshot at '%s' (first run)", snapshot_path)

    raw = json.loads(path.read_text(encoding="utf-8"))
    return _parse_geojson(raw)


def load_earthquake_data(snapshot_path: str = CACHED_SNAPSHOT_PATH) -> EarthquakeDataset:
    """Load earthquake data, preferring the live USGS feed and falling
    back to the cached snapshot when it's unreachable.

    Args:
        snapshot_path: Path to the cached JSON snapshot file, used only
            if the live fetch fails.

    Returns:
        An :class:`EarthquakeDataset` with the events and their real source.

    Raises:
        DataFetchError: If both the live feed AND the cached snapshot fail.
    """
    try:
        earthquakes = _fetch_live()
        logger.info("Loaded %d earthquake(s) from the live USGS feed", len(earthquakes))
        return EarthquakeDataset(earthquakes=earthquakes, source="live")
    except (DataFetchError, InvalidGeoJSONError) as exc:
        logger.info("Live USGS feed unavailable (%s) — using cached snapshot.", exc)

    try:
        earthquakes = _load_cached(snapshot_path)
        logger.info("Loaded %d earthquake(s) from the cached snapshot", len(earthquakes))
        return EarthquakeDataset(earthquakes=earthquakes, source="cached")
    except (OSError, json.JSONDecodeError, InvalidGeoJSONError) as exc:
        raise DataFetchError(f"Both the live feed and the cached snapshot failed: {exc}") from exc
