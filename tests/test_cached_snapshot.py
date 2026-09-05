"""Tests for src/cached_snapshot.py."""

from __future__ import annotations

from src.cached_snapshot import generate_snapshot


class TestGenerateSnapshot:
    def test_produces_the_requested_event_count(self) -> None:
        snapshot = generate_snapshot(event_count=50)
        assert len(snapshot["features"]) == 50

    def test_is_deterministic_for_the_same_seed(self) -> None:
        from datetime import datetime, timezone

        fixed_now = datetime(2026, 6, 1, tzinfo=timezone.utc)
        first = generate_snapshot(seed=42, event_count=20, now=fixed_now)
        second = generate_snapshot(seed=42, event_count=20, now=fixed_now)
        assert first["features"] == second["features"]

    def test_different_seeds_produce_different_data(self) -> None:
        first = generate_snapshot(seed=1, event_count=20)
        second = generate_snapshot(seed=2, event_count=20)
        assert first["features"] != second["features"]

    def test_matches_geojson_feature_collection_shape(self) -> None:
        snapshot = generate_snapshot(event_count=10)
        assert snapshot["type"] == "FeatureCollection"
        feature = snapshot["features"][0]
        assert feature["type"] == "Feature"
        assert "mag" in feature["properties"]
        assert "place" in feature["properties"]
        assert "time" in feature["properties"]
        assert feature["geometry"]["type"] == "Point"
        assert len(feature["geometry"]["coordinates"]) == 3

    def test_magnitudes_are_within_a_realistic_range(self) -> None:
        snapshot = generate_snapshot(event_count=200)
        magnitudes = [f["properties"]["mag"] for f in snapshot["features"]]
        assert all(2.5 <= m <= 7.8 for m in magnitudes)

    def test_magnitude_distribution_skews_toward_smaller_events(self) -> None:
        # Gutenberg-Richter-like: most events should be well below the
        # top of the range, not uniformly spread across it.
        snapshot = generate_snapshot(event_count=300)
        magnitudes = [f["properties"]["mag"] for f in snapshot["features"]]
        below_5 = sum(1 for m in magnitudes if m < 5.0)
        assert below_5 / len(magnitudes) > 0.7

    def test_coordinates_are_within_valid_ranges(self) -> None:
        snapshot = generate_snapshot(event_count=300)
        for feature in snapshot["features"]:
            lon, lat, _depth = feature["geometry"]["coordinates"]
            assert -180.0 <= lon <= 180.0
            assert -90.0 <= lat <= 90.0

    def test_depth_is_never_negative(self) -> None:
        snapshot = generate_snapshot(event_count=200)
        for feature in snapshot["features"]:
            assert feature["geometry"]["coordinates"][2] >= 0

    def test_features_are_sorted_most_recent_first(self) -> None:
        snapshot = generate_snapshot(event_count=100)
        times = [f["properties"]["time"] for f in snapshot["features"]]
        assert times == sorted(times, reverse=True)

    def test_metadata_is_honest_about_being_a_cached_snapshot(self) -> None:
        snapshot = generate_snapshot()
        assert "cached" in snapshot["metadata"]["title"].lower()

    def test_place_strings_look_realistic(self) -> None:
        snapshot = generate_snapshot(event_count=20)
        for feature in snapshot["features"]:
            place = feature["properties"]["place"]
            assert "km" in place
            assert " of " in place
