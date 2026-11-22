from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import planetary_computer
import rasterio
from pystac_client import Client
from rasterio.enums import Resampling
from rasterio.warp import reproject
from shapely.geometry import mapping


STAC_URL = "https://planetarycomputer.microsoft.com/api/stac/v1"


def fetch_landcover(dem_path: str | Path, output_path: str | Path) -> dict:
    output_path = Path(output_path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    from app.geospatial.footprint import calculate_dem_footprint

    crs, _, wgs84, bounds = calculate_dem_footprint(dem_path)
    catalog = Client.open(STAC_URL)
    search = catalog.search(collections=["esa-worldcover"], intersects=mapping(wgs84))
    items = list(search.get_items())
    if not items:
        raise ValueError("ESA WorldCover data was not found for the DEM footprint")

    signed_items = [planetary_computer.sign(item) for item in items[:20]]
    asset_items = []
    for item in signed_items:
        asset = (
            item.assets.get("map")
            or item.assets.get("classification")
            or item.assets.get("data")
        )
        if asset:
            asset_items.append(asset.href)
    if not asset_items:
        raise ValueError("WorldCover scenes had no usable map asset")

    with rasterio.open(dem_path) as dem:
        profile = dem.profile.copy()
        profile.update(driver="GTiff", count=1, dtype="uint8", nodata=0, compress="deflate")
        combined = np.zeros((dem.height, dem.width), dtype=np.uint8)
        valid = np.zeros((dem.height, dem.width), dtype=bool)
        scene_count = 0
        for href in asset_items:
            try:
                with rasterio.open(href) as src:
                    destination = np.zeros((dem.height, dem.width), dtype=np.uint8)
                    destination_valid = np.zeros((dem.height, dem.width), dtype=bool)
                    reproject(
                        source=rasterio.band(src, 1),
                        destination=destination,
                        src_transform=src.transform,
                        src_crs=src.crs,
                        dst_transform=dem.transform,
                        dst_crs=dem.crs,
                        dst_nodata=0,
                        resampling=Resampling.nearest,
                    )
                    destination_valid = destination != 0
                    combined[~valid & destination_valid] = destination[~valid & destination_valid]
                    valid |= destination_valid
                    scene_count += 1
            except (OSError, rasterio.errors.RasterioError):
                continue
        if not valid.any():
            raise ValueError("WorldCover scenes were found but no pixels covered the DEM")
        profile.update(nodata=0)
        with rasterio.open(output_path, "w", **profile) as output:
            output.write(combined, 1)
            output.set_band_description(1, "ESA WorldCover class")
            output.update_tags(
                1,
                source="ESA WorldCover via Microsoft Planetary Computer",
                licence="CC-BY-4.0",
                resampling="nearest-neighbour",
            )
    return {
        "source": "ESA WorldCover via Microsoft Planetary Computer",
        "licence": "CC-BY-4.0",
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "crs": crs.to_string(),
        "bounds": bounds,
        "scene_count": scene_count,
    }
