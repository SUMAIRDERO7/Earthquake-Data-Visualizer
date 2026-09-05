"""Tests for src/earthquake_analysis.py."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from src.earthquake_analysis import (
    classify_magnitude,
    compute_daily_frequency,
    compute_magnitude_distribution,
    compute_risk_zones,
    filter_by_magnitude,
    get_significant_events,
    search_by_place,
)
from src.exceptions import InvalidMagnitudeRangeError
from src.usgs_client import Earthquake


def _eq(magnitude: float, lat: float = 0.0, lon: float = 0.0, day: str = "2026-01-01", place: str = "Test") -> Earthquake:
    return Earthquake(
        magnitude=magnitude, place=place, latitude=lat, longitude=lon, depth_km=10.0,
        occurred_at=datetime.fromisoformat(f"{day}T00:00:00+00:00"),
    )


class TestClassifyMagnitude:
    def test_classifies_moderate_earthquake(self) -> None:
        assert classify_magnitude(5.5) == "Moderate"

    def test_classifies_minor_earthquake(self) -> None:
        assert classify_magnitude(1.0) == "Minor"

    def test_boundary_value_is_classified_correctly(self) -> None:
        assert classify_magnitude(5.0) == "Moderate"
        assert classify_magnitude(4.9) == "Light"

    def test_extreme_high_value_resolves_to_great(self) -> None:
        assert classify_magnitude(9.5) == "Great"


class TestFilterByMagnitude:
    def test_filters_to_range(self) -> None:
        earthquakes = [_eq(2.0), _eq(4.5), _eq(7.0)]
        result = filter_by_magnitude(earthquakes, 4.0, 8.0)
        assert len(result) == 2

    def test_inclusive_on_both_ends(self) -> None:
        earthquakes = [_eq(4.0), _eq(8.0)]
        result = filter_by_magnitude(earthquakes, 4.0, 8.0)
        assert len(result) == 2

    def test_invalid_range_raises(self) -> None:
        with pytest.raises(InvalidMagnitudeRangeError):
            filter_by_magnitude([_eq(5.0)], min_magnitude=8.0, max_magnitude=4.0)

    def test_empty_input_returns_empty(self) -> None:
        assert filter_by_magnitude([], 0.0, 10.0) == []


class TestComputeDailyFrequency:
    def test_groups_by_day(self) -> None:
        earthquakes = [_eq(4.0, day="2026-01-01"), _eq(5.0, day="2026-01-01"), _eq(3.0, day="2026-01-02")]
        result = compute_daily_frequency(earthquakes)
        assert len(result) == 2
        assert result[0].count == 2
        assert result[0].average_magnitude == 4.5

    def test_sorted_chronologically(self) -> None:
        earthquakes = [_eq(4.0, day="2026-01-05"), _eq(4.0, day="2026-01-01")]
        result = compute_daily_frequency(earthquakes)
        assert result[0].day < result[1].day

    def test_empty_input_returns_empty(self) -> None:
        assert compute_daily_frequency([]) == []


class TestComputeRiskZones:
    def test_groups_nearby_events_into_one_zone(self) -> None:
        earthquakes = [_eq(4.0, lat=35.0, lon=-120.0) for _ in range(5)]
        zones = compute_risk_zones(earthquakes)
        assert len(zones) == 1
        assert zones[0].event_count == 5

    def test_zones_below_minimum_count_are_excluded(self) -> None:
        earthquakes = [_eq(4.0, lat=35.0, lon=-120.0), _eq(4.0, lat=35.0, lon=-120.0)]  # only 2
        zones = compute_risk_zones(earthquakes)
        assert zones == []

    def test_distant_events_form_separate_zones(self) -> None:
        near_tokyo = [_eq(4.0, lat=36.0, lon=140.0) for _ in range(4)]
        near_santiago = [_eq(4.0, lat=-33.0, lon=-70.0) for _ in range(4)]
        zones = compute_risk_zones(near_tokyo + near_santiago)
        assert len(zones) == 2

    def test_sorted_busiest_first(self) -> None:
        busy = [_eq(4.0, lat=10.0, lon=10.0) for _ in range(6)]
        quiet = [_eq(4.0, lat=-50.0, lon=-50.0) for _ in range(3)]
        zones = compute_risk_zones(quiet + busy)
        assert zones[0].event_count == 6

    def test_max_and_average_magnitude_are_correct(self) -> None:
        earthquakes = [_eq(3.0, lat=1.0, lon=1.0), _eq(5.0, lat=1.0, lon=1.0), _eq(7.0, lat=1.0, lon=1.0)]
        zones = compute_risk_zones(earthquakes)
        assert zones[0].max_magnitude == 7.0
        assert zones[0].average_magnitude == 5.0


class TestComputeMagnitudeDistribution:
    def test_counts_every_configured_band(self) -> None:
        result = compute_magnitude_distribution([_eq(5.5)])
        assert result.band_counts["Moderate"] == 1
        assert result.band_counts["Minor"] == 0  # present even at zero

    def test_empty_input_gives_all_zero_counts(self) -> None:
        result = compute_magnitude_distribution([])
        assert all(count == 0 for count in result.band_counts.values())


class TestGetSignificantEvents:
    def test_default_threshold_filters_to_m6_plus(self) -> None:
        earthquakes = [_eq(4.5, day="2026-01-01"), _eq(6.2, day="2026-01-02"), _eq(7.0, day="2026-01-03")]
        significant = get_significant_events(earthquakes)
        assert len(significant) == 2
        assert all(eq.magnitude >= 6.0 for eq in significant)

    def test_exactly_at_threshold_is_included(self) -> None:
        earthquakes = [_eq(6.0, day="2026-01-01")]
        assert len(get_significant_events(earthquakes)) == 1

    def test_custom_threshold_is_respected(self) -> None:
        earthquakes = [_eq(5.0, day="2026-01-01"), _eq(7.0, day="2026-01-02")]
        significant = get_significant_events(earthquakes, threshold=4.0)
        assert len(significant) == 2

    def test_sorted_most_recent_first(self) -> None:
        earthquakes = [_eq(6.5, day="2026-01-01"), _eq(7.0, day="2026-01-10"), _eq(6.1, day="2026-01-05")]
        significant = get_significant_events(earthquakes)
        days = [eq.occurred_at.day for eq in significant]
        assert days == sorted(days, reverse=True)

    def test_no_significant_events_returns_empty(self) -> None:
        earthquakes = [_eq(2.0), _eq(3.5)]
        assert get_significant_events(earthquakes) == []

    def test_empty_input_returns_empty(self) -> None:
        assert get_significant_events([]) == []


class TestSearchByPlace:
    def test_matches_case_insensitively(self) -> None:
        earthquakes = [_eq(4.0, place="10km NW of Anchorage, Alaska"), _eq(4.0, place="Off the coast of Chile")]
        results = search_by_place(earthquakes, "alaska")
        assert len(results) == 1
        assert "Alaska" in results[0].place

    def test_empty_query_returns_everything(self) -> None:
        earthquakes = [_eq(4.0, place="Alaska"), _eq(4.0, place="Chile")]
        assert search_by_place(earthquakes, "") == earthquakes

    def test_whitespace_only_query_returns_everything(self) -> None:
        earthquakes = [_eq(4.0, place="Alaska")]
        assert search_by_place(earthquakes, "   ") == earthquakes

    def test_no_match_returns_empty(self) -> None:
        earthquakes = [_eq(4.0, place="Alaska")]
        assert search_by_place(earthquakes, "Antarctica") == []

    def test_partial_substring_matches(self) -> None:
        earthquakes = [_eq(4.0, place="Southern California")]
        assert len(search_by_place(earthquakes, "california")) == 1
