"""Tests for src/usgs_client.py."""

from __future__ import annotations

import json

import pytest
import requests

from src.exceptions import DataFetchError, InvalidGeoJSONError
from src.usgs_client import _parse_geojson, load_earthquake_data


def _sample_geojson() -> dict:
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "properties": {"mag": 4.5, "place": "10km N of Testville", "time": 1700000000000},
                "geometry": {"type": "Point", "coordinates": [-120.5, 35.2, 10.0]},
            }
        ],
    }


class TestParseGeojson:
    def test_parses_valid_geojson(self) -> None:
        earthquakes = _parse_geojson(_sample_geojson())
        assert len(earthquakes) == 1
        assert earthquakes[0].magnitude == 4.5
        assert earthquakes[0].place == "10km N of Testville"

    def test_skips_events_with_null_magnitude(self) -> None:
        raw = _sample_geojson()
        raw["features"][0]["properties"]["mag"] = None
        earthquakes = _parse_geojson(raw)
        assert earthquakes == []

    def test_missing_type_raises(self) -> None:
        with pytest.raises(InvalidGeoJSONError):
            _parse_geojson({"features": []})

    def test_missing_features_key_raises(self) -> None:
        with pytest.raises(InvalidGeoJSONError):
            _parse_geojson({"type": "FeatureCollection"})

    def test_malformed_feature_raises(self) -> None:
        raw = _sample_geojson()
        del raw["features"][0]["geometry"]
        with pytest.raises(InvalidGeoJSONError):
            _parse_geojson(raw)

    def test_missing_place_defaults_to_unknown(self) -> None:
        raw = _sample_geojson()
        del raw["features"][0]["properties"]["place"]
        earthquakes = _parse_geojson(raw)
        assert earthquakes[0].place == "Unknown location"


class TestLoadEarthquakeData:
    def test_falls_back_to_cached_snapshot_when_live_fetch_fails(self, monkeypatch, tmp_path) -> None:
        def _raise_connection_error(*args, **kwargs):
            raise requests.exceptions.ConnectionError("no network")

        monkeypatch.setattr("src.usgs_client.requests.get", _raise_connection_error)

        snapshot_path = str(tmp_path / "snapshot.json")
        dataset = load_earthquake_data(snapshot_path=snapshot_path)

        assert dataset.source == "cached"
        assert len(dataset.earthquakes) > 0

    def test_uses_live_data_when_fetch_succeeds(self, monkeypatch, tmp_path) -> None:
        class _FakeResponse:
            def raise_for_status(self):
                pass

            def json(self):
                return _sample_geojson()

        monkeypatch.setattr("src.usgs_client.requests.get", lambda *a, **k: _FakeResponse())

        dataset = load_earthquake_data(snapshot_path=str(tmp_path / "unused.json"))

        assert dataset.source == "live"
        assert len(dataset.earthquakes) == 1

    def test_generates_snapshot_file_on_first_use(self, monkeypatch, tmp_path) -> None:
        monkeypatch.setattr(
            "src.usgs_client.requests.get",
            lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.ConnectionError("no network")),
        )
        snapshot_path = tmp_path / "new_snapshot.json"
        assert not snapshot_path.exists()

        load_earthquake_data(snapshot_path=str(snapshot_path))

        assert snapshot_path.exists()
        # Should be valid JSON matching the expected shape
        data = json.loads(snapshot_path.read_text())
        assert data["type"] == "FeatureCollection"

    def test_raises_data_fetch_error_when_everything_fails(self, monkeypatch, tmp_path) -> None:
        monkeypatch.setattr(
            "src.usgs_client.requests.get",
            lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.ConnectionError("no network")),
        )
        broken_path = tmp_path / "broken.json"
        broken_path.write_text("not valid json {{{")

        with pytest.raises(DataFetchError):
            load_earthquake_data(snapshot_path=str(broken_path))
