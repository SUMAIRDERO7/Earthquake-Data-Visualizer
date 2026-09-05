"""Custom exception hierarchy for the Earthquake Data Visualizer."""

from __future__ import annotations


class EarthquakeVisualizerError(Exception):
    """Base exception for all errors raised by this project."""


class DataFetchError(EarthquakeVisualizerError):
    """Raised when neither the live USGS API nor the cached snapshot can be loaded."""


class InvalidGeoJSONError(EarthquakeVisualizerError):
    """Raised when earthquake data doesn't match the expected USGS GeoJSON shape."""


class MapGenerationError(EarthquakeVisualizerError):
    """Raised when the Folium map can't be built or saved."""


class InvalidMagnitudeRangeError(EarthquakeVisualizerError):
    """Raised when a requested magnitude filter range is invalid (e.g. min > max)."""
