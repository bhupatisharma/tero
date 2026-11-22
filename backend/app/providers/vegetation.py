from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path
from tempfile import TemporaryDirectory

import numpy as np
import planetary_computer
import rasterio
from pystac_client import Client
from pystac_client.stac_api_io import StacApiIO
from rasterio.enums import Resampling
from rasterio.windows import Window
from rasterio.warp import reproject
from shapely.geometry import mapping


STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"
MAX_SCENES = 12
NDVI_BLOCK_ROWS = 256
SCL_CLEAR_VALUES = {4, 5, 6, 7}


def fetch_ndvi(dem_path: str | Path, output_path: str | Path) -> dict:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    from app.geospatial.footprint import calculate_dem_footprint

    crs, _, wgs84, bounds = calculate_dem_footprint(dem_path)
    catalog = Client.open(
        STAC_URL,
        stac_io=StacApiIO(timeout=(5, 20), max_retries=2),
    )
    search = catalog.search(
        collections=["sentinel-2-l2a"],
        intersects=mapping(wgs84),
        datetime=f"{(datetime.now(timezone.utc).year - 2)}-01-01/{datetime.now(timezone.utc).date()}",
        query={"eo:cloud_cover": {"lt": 80}},
        max_items=MAX_SCENES,
    )
    items = list(search.items())
    if not items:
        raise ValueError("No suitable Sentinel-2 imagery was found")

    with TemporaryDirectory(prefix=".tero-ndvi-", dir=output_path.parent) as temp_dir:
        stack_path = Path(temp_dir) / "scenes.tif"
        with rasterio.open(dem_path) as dem:
            dst_profile = dem.profile.copy()
            dst_profile.update(
                driver="GTiff",
                count=1,
                dtype="float32",
                nodata=-9999.0,
                compress="deflate",
            )
            stack_profile = dst_profile.copy()
            stack_profile.update(count=len(items))
            scene_errors = []
            scene_count = 0
            with rasterio.Env(
                GDAL_HTTP_CONNECTTIMEOUT=10,
                GDAL_HTTP_TIMEOUT=30,
                GDAL_HTTP_MAX_RETRY=1,
            ):
                with rasterio.open(stack_path, "w", **stack_profile) as stack:
                    for item in items:
                        try:
                            assets = planetary_computer.sign(item).assets
                            if not {"B04", "B08", "SCL"}.issubset(assets):
                                scene_errors.append(f"{item.id}: missing B04, B08, or SCL asset")
                                continue

                            red = np.full((dem.height, dem.width), np.nan, dtype=np.float32)
                            nir = np.full((dem.height, dem.width), np.nan, dtype=np.float32)
                            for asset_name, destination in (("B04", red), ("B08", nir)):
                                with rasterio.open(assets[asset_name].href) as source:
                                    reproject(
                                        source=rasterio.band(source, 1),
                                        destination=destination,
                                        src_transform=source.transform,
                                        src_crs=source.crs,
                                        dst_transform=dem.transform,
                                        dst_crs=dem.crs,
                                        dst_nodata=np.nan,
                                        resampling=Resampling.bilinear,
                                    )

                            scl_data = np.zeros((dem.height, dem.width), dtype=np.uint8)
                            with rasterio.open(assets["SCL"].href) as scl_source:
                                reproject(
                                    source=rasterio.band(scl_source, 1),
                                    destination=scl_data,
                                    src_transform=scl_source.transform,
                                    src_crs=scl_source.crs,
                                    dst_transform=dem.transform,
                                    dst_crs=dem.crs,
                                    dst_nodata=0,
                                    resampling=Resampling.nearest,
                                )

                            denominator = nir + red
                            valid = (
                                np.isin(scl_data, tuple(SCL_CLEAR_VALUES))
                                & np.isfinite(red)
                                & np.isfinite(nir)
                                & (denominator != 0)
                            )
                            if not valid.any():
                                scene_errors.append(f"{item.id}: no clear pixels overlap the DEM")
                                continue
                            scene_ndvi = np.full((dem.height, dem.width), -9999.0, dtype=np.float32)
                            np.divide(nir - red, denominator, out=scene_ndvi, where=valid)
                            stack.write(scene_ndvi, scene_count + 1)
                            scene_count += 1
                        except (OSError, rasterio.errors.RasterioError) as error:
                            scene_errors.append(
                                f"{item.id}: {type(error).__name__} reading signed raster assets"
                            )

            if not scene_count:
                detail = "; ".join(scene_errors[:3]) or "no usable clear pixels"
                raise ValueError(
                    f"Sentinel-2 scenes were found, but none produced NDVI data: {detail}"
                )

            valid_pixel_count = 0
            with rasterio.open(stack_path) as stack, rasterio.open(
                output_path,
                "w",
                **dst_profile,
            ) as output:
                output.set_band_description(1, "NDVI")
                output.update_tags(
                    1,
                    source="Sentinel-2 L2A",
                    licence="CC-BY-4.0",
                    cloud_mask="only SCL classes 4,5,6,7 retained",
                )
                for row in range(0, dem.height, NDVI_BLOCK_ROWS):
                    height = min(NDVI_BLOCK_ROWS, dem.height - row)
                    window = Window(0, row, dem.width, height)
                    scenes = stack.read(
                        indexes=list(range(1, scene_count + 1)),
                        window=window,
                        masked=True,
                    )
                    median = np.ma.median(scenes, axis=0)
                    valid_pixel_count += int(median.count())
                    output.write(median.filled(-9999.0).astype(np.float32), 1, window=window)
            if not valid_pixel_count:
                raise ValueError("Sentinel-2 scenes produced no valid NDVI pixels for the DEM")
    return {
        "source": "Sentinel-2 L2A via Microsoft Planetary Computer",
        "licence": "CC-BY-4.0",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "crs": crs.to_string(),
        "bounds": bounds,
        "scene_count": scene_count,
    }
