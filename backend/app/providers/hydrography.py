from datetime import datetime, timezone
from pathlib import Path

from app.providers.osm_query import query_osm_features


def _fetch_osm(dem_path: str | Path, output_path: Path, tags: dict, label: str) -> dict:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    from app.geospatial.footprint import calculate_dem_footprint

    _, _, footprint, bounds = calculate_dem_footprint(dem_path)
    frame = query_osm_features(footprint, tags, label)
    frame = frame[frame.geometry.notna() & ~frame.geometry.is_empty]
    frame = frame[frame.geometry.intersects(footprint)]
    frame = frame.copy()
    frame["geometry"] = frame.geometry.intersection(footprint)
    frame = frame[~frame.geometry.is_empty]
    if frame.empty:
        raise ValueError(f"No {label} features intersected the DEM footprint")
    frame = frame.drop_duplicates(subset=["geometry"])
    frame.to_file(output_path, driver="GeoJSON")
    return {
        "source": "OpenStreetMap via OSMnx",
        "licence": "ODbL",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "crs": "EPSG:4326",
        "bounds": bounds,
        "feature_count": len(frame),
    }


def fetch_rivers(dem_path: str | Path, output_path: str | Path) -> dict:
    return _fetch_osm(dem_path, Path(output_path), {"waterway": True}, "river")


def fetch_water_bodies(dem_path: str | Path, output_path: str | Path) -> dict:
    tags = {
        "natural": ["water", "wetland"],
        "landuse": ["reservoir", "basin"],
        "water": True,
    }
    return _fetch_osm(dem_path, Path(output_path), tags, "water-body")
