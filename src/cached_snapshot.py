"""
Cached earthquake snapshot generator.

This sandbox has no network path to earthquake.usgs.gov (see
README), so ``usgs_client.py`` falls back to this module instead of
the live feed. Rather than pure random noise, this generates a
dataset shaped like a real recent 30-day window: events cluster
around real, named fault zones (Ring of Fire, the Alpide belt, etc.),
in real USGS "place" string style, with a Gutenberg-Richter-like
magnitude distribution (many small quakes, very few large ones — the
real statistical pattern, not a uniform random spread). The random
seed is fixed, so this is reproducible, not fresh noise every run.
"""

from __future__ import annotations

import json
import logging
import random
from datetime import datetime, timedelta, timezone
from pathlib import Path

from src.config import CACHED_SNAPSHOT_PATH

logger = logging.getLogger(__name__)

_SNAPSHOT_SEED = 20260101
_EVENT_COUNT = 260
_WINDOW_DAYS = 30

# (region name, center lat, center lon, spread degrees, relative event weight)
# Real, well-known seismically active zones — the Pacific "Ring of Fire" plus
# the Alpide belt (Mediterranean through the Himalayas to Indonesia).
_FAULT_ZONES: list[tuple[str, float, float, float, int]] = [
    ("Alaska", 61.0, -150.0, 4.0, 22),
    ("Southern California", 34.5, -118.0, 1.5, 14),
    ("Northern California", 38.5, -122.8, 1.5, 10),
    ("Japan", 36.0, 140.0, 3.0, 24),
    ("Indonesia", -2.0, 118.0, 6.0, 26),
    ("Chile", -33.0, -71.0, 5.0, 18),
    ("Philippines", 13.0, 122.0, 3.0, 16),
    ("Papua New Guinea", -6.0, 147.0, 2.5, 14),
    ("Mexico", 17.0, -100.0, 2.5, 12),
    ("New Zealand", -41.0, 174.0, 2.0, 10),
    ("Turkey", 39.0, 35.0, 3.0, 10),
    ("Nepal-Himalaya region", 28.0, 84.0, 2.5, 8),
    ("Peru", -10.0, -76.0, 3.0, 10),
    ("Fiji region", -18.0, 178.0, 2.0, 8),
    ("Puerto Rico region", 18.0, -66.5, 1.0, 6),
]

_DIRECTIONS = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]


def _sample_magnitude(rng: random.Random) -> float:
    """Sample a magnitude from a Gutenberg-Richter-like distribution.

    Real earthquake magnitude-frequency follows roughly log-linear
    decay (each whole-magnitude step is about 10x rarer) — this
    approximates that with an exponential draw clamped to a realistic
    range, rather than a uniform spread that would wildly overrepresent
    large earthquakes.

    Args:
        rng: A seeded ``Random`` instance.

    Returns:
        A magnitude between 2.5 and 7.8, rounded to 1 decimal place.
    """
    raw = 2.5 + rng.expovariate(1.8)
    return round(min(raw, 7.8), 1)


def _sample_place(rng: random.Random, region: str) -> str:
    """Build a real-USGS-style place description.

    Args:
        rng: A seeded ``Random`` instance.
        region: The fault zone / region name.

    Returns:
        A string like ``"42km ESE of Anchorage, Alaska"``.
    """
    distance = rng.randint(2, 180)
    direction = rng.choice(_DIRECTIONS)
    return f"{distance}km {direction} of {region}"


def generate_snapshot(seed: int = _SNAPSHOT_SEED, event_count: int = _EVENT_COUNT, now: datetime | None = None) -> dict:
    """Generate a realistic, deterministic earthquake dataset in USGS GeoJSON shape.

    Args:
        seed: Random seed — same seed always produces the same dataset.
        event_count: How many earthquake events to generate.
        now: The anchor "current time" event ages are computed relative
            to. Defaults to the real current time — accepting it as a
            parameter (rather than calling ``datetime.now()`` internally)
            is what makes two calls with the same seed produce
            byte-for-byte identical output, since real wall-clock time
            otherwise drifts by at least a millisecond between calls.

    Returns:
        A dict matching USGS's GeoJSON FeatureCollection schema closely
        enough that every downstream module (which only reads ``mag``,
        ``place``, ``time``, and ``geometry.coordinates``) works
        identically against real USGS data or this snapshot.
    """
    rng = random.Random(seed)
    now = now or datetime.now(timezone.utc)

    features = []
    for _ in range(event_count):
        region, center_lat, center_lon, spread, weight = rng.choices(
            _FAULT_ZONES, weights=[w for *_r, w in _FAULT_ZONES], k=1
        )[0]
        latitude = max(-89.9, min(89.9, center_lat + rng.gauss(0, spread)))
        longitude = center_lon + rng.gauss(0, spread)
        longitude = ((longitude + 180) % 360) - 180  # wrap to valid [-180, 180]
        depth_km = round(max(1.0, rng.gauss(35, 40)), 1)
        magnitude = _sample_magnitude(rng)
        event_time = now - timedelta(
            days=rng.uniform(0, _WINDOW_DAYS), hours=rng.uniform(0, 24), minutes=rng.uniform(0, 60)
        )

        features.append(
            {
                "type": "Feature",
                "properties": {
                    "mag": magnitude,
                    "place": _sample_place(rng, region),
                    "time": int(event_time.timestamp() * 1000),  # USGS uses epoch milliseconds
                    "title": f"M {magnitude} - {_sample_place(rng, region)}",
                },
                "geometry": {"type": "Point", "coordinates": [round(longitude, 3), round(latitude, 3), depth_km]},
            }
        )

    # Real USGS feeds are ordered most-recent-first.
    features.sort(key=lambda f: f["properties"]["time"], reverse=True)

    return {
        "type": "FeatureCollection",
        "metadata": {
            "generated": int(now.timestamp() * 1000),
            "count": len(features),
            "title": "Cached illustrative snapshot (not live USGS data — see README)",
        },
        "features": features,
    }


def write_snapshot_to_disk(path: str = CACHED_SNAPSHOT_PATH) -> str:
    """Generate the snapshot (if not already cached) and write it to disk.

    Args:
        path: Where to write the JSON file.

    Returns:
        The path written to.
    """
    snapshot = generate_snapshot()
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(snapshot, indent=2), encoding="utf-8")
    logger.info("Wrote cached snapshot (%d events) to '%s'", len(snapshot["features"]), path)
    return path
