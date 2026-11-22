from pathlib import Path

import geopandas as gpd
import rasterio
from shapely.geometry import box


def validate_raster_output(path: str | Path, footprint_wgs84) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Expected raster file was not created")
    with rasterio.open(path) as dataset:
        if dataset.count < 1 or dataset.width < 1 or dataset.height < 1:
            raise ValueError("Raster is empty")
        raster_bounds = box(*dataset.bounds)
        if not raster_bounds.is_valid:
            raise ValueError("Raster bounds are invalid")
        return {
            "crs": dataset.crs.to_string() if dataset.crs else None,
            "bounds": list(dataset.bounds),
            "width": dataset.width,
            "height": dataset.height,
        }


def validate_vector_output(path: str | Path, footprint_wgs84) -> dict:
    path = Path(path)
    if not path.is_file():
        raise ValueError("Expected vector file was not created")
    frame = gpd.read_file(path)
    if frame.empty:
        raise ValueError("No features were found")
    if frame.crs is None:
        raise ValueError("Vector data has no CRS")
    return {
        "crs": frame.crs.to_string(),
        "feature_count": len(frame),
        "bounds": list(frame.total_bounds),
    }
