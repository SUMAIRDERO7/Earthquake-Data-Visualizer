"""Tests for src/map_builder.py."""

from __future__ import annotations

from datetime import datetime, timezone

import folium
import pytest

from src.earthquake_analysis import RiskZone
from src.exceptions import MapGenerationError
from src.map_builder import build_earthquake_map, save_map_to_html
from src.usgs_client import Earthquake


def _eq(magnitude: float = 5.0, lat: float = 35.0, lon: float = -120.0) -> Earthquake:
    return Earthquake(
        magnitude=magnitude, place="Test Location", latitude=lat, longitude=lon, depth_km=10.0,
        occurred_at=datetime(2026, 1, 1, tzinfo=timezone.utc),
    )


class TestBuildEarthquakeMap:
    def test_returns_a_folium_map(self) -> None:
        result = build_earthquake_map([_eq()])
        assert isinstance(result, folium.Map)

    def test_raises_on_empty_earthquake_list(self) -> None:
        with pytest.raises(MapGenerationError):
            build_earthquake_map([])

    def test_map_is_centered_near_the_average_location(self) -> None:
        earthquakes = [_eq(lat=10.0, lon=10.0), _eq(lat=20.0, lon=20.0)]
        fmap = build_earthquake_map(earthquakes)
        assert fmap.location == [15.0, 15.0]

    def test_includes_risk_zone_layer_when_provided(self) -> None:
        zones = [RiskZone(center_lat=35.0, center_lon=-120.0, event_count=5, max_magnitude=6.0, average_magnitude=4.5)]
        fmap = build_earthquake_map([_eq()], risk_zones=zones)
        rendered = fmap._repr_html_()
        assert "Risk Zones" in rendered or len(fmap._children) > 2

    def test_heatmap_can_be_disabled(self) -> None:
        with_heatmap = build_earthquake_map([_eq()], show_heatmap=True)
        without_heatmap = build_earthquake_map([_eq()], show_heatmap=False)
        assert len(with_heatmap._children) > len(without_heatmap._children)


class TestSaveMapToHtml:
    def test_writes_html_file(self, tmp_path) -> None:
        fmap = build_earthquake_map([_eq()])
        output_path = tmp_path / "map.html"

        result_path = save_map_to_html(fmap, str(output_path))

        assert result_path == str(output_path)
        assert output_path.exists()
        content = output_path.read_text(encoding="utf-8")
        assert "<html" in content.lower() or "<!doctype html>" in content.lower()

    def test_creates_parent_directories(self, tmp_path) -> None:
        fmap = build_earthquake_map([_eq()])
        output_path = tmp_path / "nested" / "dir" / "map.html"
        save_map_to_html(fmap, str(output_path))
        assert output_path.exists()
