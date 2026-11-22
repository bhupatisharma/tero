from __future__ import annotations

import math
from pathlib import Path

import rasterio
from pyproj import CRS, Transformer
from shapely.geometry import Polygon, box


def calculate_dem_footprint(dem_path: str | Path) -> tuple[CRS, Polygon, Polygon, dict]:
    """Calculate the full raster footprint and its WGS84 representation."""
    with rasterio.open(dem_path) as dataset:
        if dataset.crs is None:
            raise ValueError("DEM has no CRS")
        if not dataset.transform or dataset.transform.is_identity:
            raise ValueError("DEM has no usable affine transform")
        crs = CRS.from_user_input(dataset.crs)
        corners = [
            dataset.transform @ (0, 0),
            dataset.transform @ (dataset.width, 0),
            dataset.transform @ (dataset.width, dataset.height),
            dataset.transform @ (0, dataset.height),
        ]
        footprint = Polygon(corners)
        if not footprint.is_valid or footprint.is_empty:
            raise ValueError("DEM footprint is degenerate")
        transformer = Transformer.from_crs(crs, CRS.from_epsg(4326), always_xy=True)
        wgs84_points = []
        for start, end in zip(corners, corners[1:] + corners[:1]):
            for index in range(21):
                x = start[0] + (end[0] - start[0]) * index / 20
                y = start[1] + (end[1] - start[1]) * index / 20
                px, py = transformer.transform(x, y)
                if math.isfinite(px) and math.isfinite(py) and -180 <= px <= 180 and -90 <= py <= 90:
                    wgs84_points.append((px, py))
        wgs84 = Polygon(wgs84_points)
        if not wgs84.is_valid:
            wgs84 = wgs84.buffer(0)
        bounds = {
            "west": wgs84.bounds[0],
            "south": wgs84.bounds[1],
            "east": wgs84.bounds[2],
            "north": wgs84.bounds[3],
        }
        return crs, footprint, wgs84, bounds


def split_aoi(polygon: Polygon, max_width_degrees: float = 0.25) -> list[Polygon]:
    """Split a large WGS84 AOI into bounded tiles."""
    minx, miny, maxx, maxy = polygon.bounds
    tiles: list[Polygon] = []
    y = miny
    while y < maxy:
        north = min(maxy, y + max_width_degrees)
        x = minx
        while x < maxx:
            east = min(maxx, x + max_width_degrees)
            tile = box(x, y, east, north).intersection(polygon)
            if not tile.is_empty:
                tiles.append(tile)
            x = east
        y = north
    return tiles or [polygon]
