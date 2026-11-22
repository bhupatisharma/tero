from pathlib import Path

from app.providers.hydrography import _fetch_osm


def fetch_roads(dem_path: str | Path, output_path: str | Path) -> dict:
    return _fetch_osm(
        dem_path,
        Path(output_path),
        {"highway": True},
        "road",
    )
