from concurrent.futures import ThreadPoolExecutor
import json
from pathlib import Path

import numpy as np
from PIL import Image
import rasterio

from app.providers.hydrography import fetch_rivers, fetch_water_bodies
from app.providers.landcover import fetch_landcover
from app.providers.roads import fetch_roads
from app.providers.vegetation import fetch_ndvi
from app.services.layer_cache import (
    LAYER_FILES,
    fetched_directory,
    initialize_status,
    load_status,
    update_status,
)


_executor = ThreadPoolExecutor(max_workers=5, thread_name_prefix="tero-layers")


def _write_raster_preview(raster_path: Path, preview_path: Path, name: str) -> None:
    with rasterio.open(raster_path) as dataset:
        scale = min(1.0, 1024 / max(dataset.width, dataset.height))
        width = max(1, round(dataset.width * scale))
        height = max(1, round(dataset.height * scale))
        values = dataset.read(
            1,
            out_shape=(height, width),
            masked=True,
            resampling=rasterio.enums.Resampling.bilinear if name == "vegetation" else rasterio.enums.Resampling.nearest,
        )
        rgb = np.zeros((height, width, 4), dtype=np.uint8)
        valid = ~np.ma.getmaskarray(values)
        if name == "vegetation":
            data = np.ma.filled(values, 0).clip(-1, 1)
            red = np.clip(1 - data, 0, 1)
            green = np.clip((data + 1) / 2, 0, 1)
            rgb[:, :, 0] = (red * 190).astype(np.uint8)
            rgb[:, :, 1] = (green * 170 + 40).astype(np.uint8)
            rgb[:, :, 2] = 70
        else:
            palette = {
                10: (0, 100, 0), 20: (120, 200, 100), 30: (220, 220, 150),
                40: (180, 130, 70), 50: (200, 200, 200), 60: (40, 120, 200),
                80: (30, 60, 180), 90: (180, 220, 255), 95: (255, 255, 255),
            }
            data = np.ma.filled(values, 0).astype(np.uint8)
            for class_value, color in palette.items():
                selected = data == class_value
                rgb[:, :, 0][selected] = color[0]
                rgb[:, :, 1][selected] = color[1]
                rgb[:, :, 2][selected] = color[2]
        rgb[:, :, 3] = valid.astype(np.uint8) * 220
        Image.fromarray(rgb, mode="RGBA").save(preview_path, format="PNG", optimize=True)


def start_layer_fetches(dem_directory: Path) -> None:
    initialize_status(dem_directory)
    for name in LAYER_FILES:
        _executor.submit(fetch_one_layer, dem_directory, name)


def fetch_one_layer(dem_directory: Path, name: str, force: bool = False) -> dict:
    if name not in LAYER_FILES:
        raise ValueError("Unknown supporting layer")
    update_status(
        dem_directory,
        name,
        status="fetching",
        error=None,
    )
    output = fetched_directory(dem_directory) / LAYER_FILES[name]
    metadata_path = output.with_suffix(output.suffix + ".json")
    try:
        if not force and output.is_file() and metadata_path.is_file():
            metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
        else:
            dem_path = dem_directory / "original.tif"
            candidates = list(dem_directory.glob("original.*"))
            if candidates:
                dem_path = candidates[0]
            update_status(dem_directory, name, status="processing")
            if name == "vegetation":
                metadata = fetch_ndvi(dem_path, output)
            elif name == "landcover":
                metadata = fetch_landcover(dem_path, output)
            elif name == "rivers":
                metadata = fetch_rivers(dem_path, output)
            elif name == "water_bodies":
                metadata = fetch_water_bodies(dem_path, output)
            else:
                metadata = fetch_roads(dem_path, output)
            if not output.is_file():
                raise ValueError("Provider did not create an output file")

            metadata_path.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
            if name in {"vegetation", "landcover"}:
                _write_raster_preview(output, output.with_suffix(".preview.png"), name)

        raw_bounds = metadata.get("bounds")
        if isinstance(raw_bounds, dict):
            bounds = [
                raw_bounds.get("west"),
                raw_bounds.get("south"),
                raw_bounds.get("east"),
                raw_bounds.get("north"),
            ]
        elif isinstance(raw_bounds, list):
            bounds = raw_bounds
        else:
            bounds = None
        update_status(
            dem_directory,
            name,
            status="available",
            file_name=output.name,
            licence=metadata.get("licence"),
            fetched_at=metadata.get("fetched_at"),
            crs=metadata.get("crs"),
            bounds=bounds,
            feature_count=metadata.get("feature_count"),
            scene_count=metadata.get("scene_count"),
            metadata=metadata,
            error=None,
        )
        return load_status(dem_directory)[name]
    except Exception as error:
        update_status(
            dem_directory,
            name,
            status="failed",
            error=f"{type(error).__name__}: {error}",
            file_name=None,
            licence=None,
            fetched_at=None,
            crs=None,
            bounds=None,
            feature_count=None,
            scene_count=None,
            metadata=None,
        )
        return load_status(dem_directory)[name]
