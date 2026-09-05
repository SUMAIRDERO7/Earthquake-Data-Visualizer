"""Tests for src/visualizer_service.py."""

from __future__ import annotations

import pytest
import requests

from src.exceptions import InvalidMagnitudeRangeError
from src.visualizer_service import build_report


@pytest.fixture(autouse=True)
def _force_cached_snapshot(monkeypatch):
    """Every test in this module should use the deterministic cached
    snapshot, never attempt a real network call."""
    monkeypatch.setattr(
        "src.usgs_client.requests.get",
        lambda *a, **k: (_ for _ in ()).throw(requests.exceptions.ConnectionError("no network in tests")),
    )


class TestBuildReport:
    def test_returns_a_complete_report(self) -> None:
        report = build_report()
        assert report.source == "cached"
        assert len(report.earthquakes) > 0
        assert len(report.daily_frequency) > 0

    def test_magnitude_filter_reduces_results(self) -> None:
        full_report = build_report(min_magnitude=0.0, max_magnitude=10.0)
        filtered_report = build_report(min_magnitude=6.0, max_magnitude=10.0)
        assert len(filtered_report.earthquakes) < len(full_report.earthquakes)

    def test_invalid_range_raises(self) -> None:
        with pytest.raises(InvalidMagnitudeRangeError):
            build_report(min_magnitude=9.0, max_magnitude=1.0)

    def test_magnitude_distribution_matches_filtered_earthquakes(self) -> None:
        report = build_report(min_magnitude=6.0, max_magnitude=10.0)
        total_in_bands = sum(report.magnitude_distribution.band_counts.values())
        assert total_in_bands == len(report.earthquakes)

    def test_risk_zones_only_include_filtered_earthquakes(self) -> None:
        narrow_report = build_report(min_magnitude=7.0, max_magnitude=10.0)
        # With a narrow high-magnitude filter, there should be very few
        # (likely zero) qualifying risk zones, since MIN_QUAKES_FOR_RISK_ZONE
        # requires multiple events in the same grid cell.
        assert all(zone.max_magnitude >= 7.0 for zone in narrow_report.risk_zones)

    def test_significant_events_are_included_and_correctly_filtered(self) -> None:
        report = build_report()
        assert all(eq.magnitude >= 6.0 for eq in report.significant_events)

    def test_significant_events_respect_the_magnitude_filter_too(self) -> None:
        # A magnitude filter that excludes all M6+ events should leave
        # significant_events empty, even if some exist in the raw dataset.
        report = build_report(min_magnitude=0.0, max_magnitude=3.0)
        assert report.significant_events == []

    def test_place_query_filters_earthquakes(self) -> None:
        full_report = build_report()
        if not full_report.earthquakes:
            pytest.skip("cached snapshot produced no events to search")
        sample_place_word = full_report.earthquakes[0].place.split()[-1]
        filtered_report = build_report(place_query=sample_place_word)
        assert all(sample_place_word.lower() in eq.place.lower() for eq in filtered_report.earthquakes)

    def test_empty_place_query_does_not_filter(self) -> None:
        report_a = build_report(place_query="")
        report_b = build_report(place_query="   ")
        assert len(report_a.earthquakes) == len(report_b.earthquakes)
