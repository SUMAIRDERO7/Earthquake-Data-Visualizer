"""Central configuration for the Earthquake Data Visualizer."""

from __future__ import annotations

# --- USGS live API -------------------------------------------------------------
# Real, documented USGS feed — see README for why this sandbox always falls
# back to the cached snapshot instead of reaching it live.
USGS_FEED_URL: str = "https://earthquake.usgs.gov/earthquakes/feed/v1.0/summary/2.5_month.geojson"
USGS_REQUEST_TIMEOUT_SECONDS: int = 6

# --- File paths ------------------------------------------------------------------
CACHED_SNAPSHOT_PATH: str = "data/cached_earthquakes_snapshot.json"
HTML_MAP_PATH: str = "data/earthquake_map.html"

# --- Magnitude classification bands (USGS-standard descriptive ranges) -----------
MAGNITUDE_BANDS: list[tuple[float, float, str]] = [
    (0.0, 2.9, "Minor"),
    (3.0, 3.9, "Minor"),
    (4.0, 4.9, "Light"),
    (5.0, 5.9, "Moderate"),
    (6.0, 6.9, "Strong"),
    (7.0, 7.9, "Major"),
    (8.0, 10.0, "Great"),
]

# --- Risk-zone grid resolution ----------------------------------------------------
RISK_ZONE_GRID_DEGREES: float = 5.0   # aggregate quakes into 5x5 degree lat/lon cells
MIN_QUAKES_FOR_RISK_ZONE: int = 3       # a cell needs at least this many events to count

# --- Brand palette (2026 Master Project Standard) -----------------------------------
COLOR_PRIMARY: str = "#0A2540"
COLOR_SECONDARY: str = "#2563EB"
COLOR_ACCENT: str = "#38BDF8"
COLOR_SUCCESS: str = "#10B981"
COLOR_WARNING: str = "#F59E0B"
COLOR_DANGER: str = "#EF4444"
COLOR_BACKGROUND: str = "#F8FAFC"
COLOR_CARD: str = "#FFFFFF"
COLOR_TEXT_PRIMARY: str = "#111827"
COLOR_TEXT_SECONDARY: str = "#4B5563"
COLOR_BORDER: str = "#E2E8F0"

# --- Magnitude marker colors on the map (distinct from the severity bands above) ---
MAGNITUDE_MARKER_COLORS: dict[str, str] = {
    "Minor": "#38BDF8",
    "Light": "#2563EB",
    "Moderate": COLOR_WARNING,
    "Strong": "#F97316",
    "Major": COLOR_DANGER,
    "Great": "#7F1D1D",
}
