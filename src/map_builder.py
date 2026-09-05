"""
Interactive Folium map generation.

Builds a real ``folium.Map`` object — magnitude-colored circle
markers sized by magnitude, plus an optional risk-zone reference
layer and a magnitude-weighted heatmap.
"""

from __future__ import annotations

import logging
from pathlib import Path

import folium
from folium.plugins import HeatMap

from src.config import HTML_MAP_PATH, MAGNITUDE_MARKER_COLORS
from src.earthquake_analysis import RiskZone, classify_magnitude
from src.exceptions import MapGenerationError
from src.usgs_client import Earthquake

logger = logging.getLogger(__name__)


def _marker_radius(magnitude: float) -> float:
    """Scale a magnitude to a reasonable circle-marker radius in pixels.

    Args:
        magnitude: The earthquake's magnitude.

    Returns:
        A radius that grows with magnitude but never gets so large it
        swamps the map at high zoom-out levels.
    """
    return max(3.0, magnitude * 2.2)


def build_earthquake_map(
    earthquakes: list[Earthquake], risk_zones: list[RiskZone] | None = None, show_heatmap: bool = True
) -> folium.Map:
    """Build an interactive Folium map of earthquake events.

    Args:
        earthquakes: Events to plot as circle markers, colored and
            sized by magnitude, with a popup showing place/magnitude/depth.
        risk_zones: Optional risk zones to draw as reference circles.
        show_heatmap: If True, add a magnitude-weighted heatmap layer
            (toggleable in the map's own layer control).

    Returns:
        A ready-to-render/save Folium map.

    Raises:
        MapGenerationError: If there are no earthquakes to plot (a
            map centered on nothing isn't a useful map).
    """
    if not earthquakes:
        raise MapGenerationError("Cannot build a map with zero earthquakes.")

    avg_lat = sum(eq.latitude for eq in earthquakes) / len(earthquakes)
    avg_lon = sum(eq.longitude for eq in earthquakes) / len(earthquakes)
    fmap = folium.Map(location=[avg_lat, avg_lon], zoom_start=2, tiles="CartoDB positron")

    marker_layer = folium.FeatureGroup(name="Earthquakes", show=True)
    for eq in earthquakes:
        band = classify_magnitude(eq.magnitude)
        color = MAGNITUDE_MARKER_COLORS.get(band, "#2563EB")
        folium.CircleMarker(
            location=[eq.latitude, eq.longitude],
            radius=_marker_radius(eq.magnitude),
            color=color,
            fill=True,
            fill_color=color,
            fill_opacity=0.7,
            weight=1,
            popup=folium.Popup(
                f"<b>M {eq.magnitude}</b> ({band})<br>{eq.place}<br>"
                f"Depth: {eq.depth_km} km<br>{eq.occurred_at.strftime('%Y-%m-%d %H:%M UTC')}",
                max_width=250,
            ),
        ).add_to(marker_layer)
    marker_layer.add_to(fmap)

    if show_heatmap:
        heat_data = [[eq.latitude, eq.longitude, eq.magnitude] for eq in earthquakes]
        heat_layer = folium.FeatureGroup(name="Magnitude Heatmap", show=False)
        HeatMap(heat_data, radius=18, blur=22, max_zoom=6).add_to(heat_layer)
        heat_layer.add_to(fmap)

    if risk_zones:
        zone_layer = folium.FeatureGroup(name="Risk Zones", show=False)
        for zone in risk_zones:
            folium.Circle(
                location=[zone.center_lat, zone.center_lon],
                radius=250_000,  # meters — a visual reference circle, not a precise hazard boundary
                color="#EF4444",
                fill=False,
                weight=2,
                dash_array="6",
                popup=f"{zone.event_count} events, avg M{zone.average_magnitude}, max M{zone.max_magnitude}",
            ).add_to(zone_layer)
        zone_layer.add_to(fmap)

    folium.LayerControl(collapsed=False).add_to(fmap)
    return fmap


def save_map_to_html(fmap: folium.Map, output_path: str = HTML_MAP_PATH) -> str:
    """Save a Folium map as a self-contained HTML file.

    Args:
        fmap: The map to save (from :func:`build_earthquake_map`).
        output_path: Where to write the file.

    Returns:
        The output path, for convenient chaining.

    Raises:
        MapGenerationError: If the file can't be written.
    """
    path = Path(output_path)
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fmap.save(str(path))
    except OSError as exc:
        raise MapGenerationError(f"Could not save map to '{output_path}': {exc}") from exc
    logger.info("Saved earthquake map to '%s'", output_path)
    return str(path)
