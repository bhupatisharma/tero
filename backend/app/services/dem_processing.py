import math
from pathlib import Path

import numpy as np
import rasterio
from PIL import Image
from pyproj import CRS, Transformer
from rasterio.enums import Resampling
from rasterio.transform import from_bounds
from rasterio.warp import reproject

from app.models import (
    DemMetadata,
    ElevationStatistics,
    GeographicBounds,
    RasterTransform,
)

PREVIEW_MAX_DIMENSION = 1024
STATISTICS_WINDOW_SIZE = 512


class DemProcessingError(ValueError):
    pass


def _read_statistics(dataset: rasterio.DatasetReader) -> ElevationStatistics:
    minimum = math.inf
    maximum = -math.inf
    total = 0.0
    count = 0

    for row in range(0, dataset.height, STATISTICS_WINDOW_SIZE):
        for column in range(0, dataset.width, STATISTICS_WINDOW_SIZE):
            window = rasterio.windows.Window(
                column,
                row,
                min(STATISTICS_WINDOW_SIZE, dataset.width - column),
                min(STATISTICS_WINDOW_SIZE, dataset.height - row),
            )
            values = dataset.read(1, window=window, masked=True)
            valid = values.compressed()
            valid = valid[np.isfinite(valid)]
            if valid.size == 0:
                continue
            minimum = min(minimum, float(valid.min()))
            maximum = max(maximum, float(valid.max()))
            total += float(valid.sum(dtype=np.float64))
            count += int(valid.size)

    return ElevationStatistics(
        minimum=minimum if count else None,
        maximum=maximum if count else None,
        mean=total / count if count else None,
        valid_pixel_count=count,
        units=dataset.tags(1).get("units") or dataset.tags().get("units"),
    )


def _geographic_footprint(
    dataset: rasterio.DatasetReader, crs: CRS
) -> tuple[GeographicBounds, list[tuple[float, float]]]:
    transformer = Transformer.from_crs(crs, CRS.from_epsg(4326), always_xy=True)
    corners = ((0, 0), (dataset.width, 0), (dataset.width, dataset.height), (0, dataset.height))
    edge_points: list[tuple[float, float]] = []
    for start, end in zip(corners, (*corners[1:], corners[0])):
        edge_points.extend(
            dataset.transform @ (
                start[0] + (end[0] - start[0]) * index / 20,
                start[1] + (end[1] - start[1]) * index / 20,
            )
            for index in range(20)
        )
    longitudes, latitudes = transformer.transform(
        [point[0] for point in edge_points],
        [point[1] for point in edge_points],
        errcheck=True,
    )
    finite_points = [
        (longitude, latitude)
        for longitude, latitude in zip(longitudes, latitudes)
        if math.isfinite(longitude)
        and math.isfinite(latitude)
        and -180 <= longitude <= 180
        and -90 <= latitude <= 90
    ]
    if len(finite_points) < 3:
        raise DemProcessingError("The raster bounds cannot be transformed to WGS84.")
    geographic_bounds = GeographicBounds(
        west=min(point[0] for point in finite_points),
        south=min(point[1] for point in finite_points),
        east=max(point[0] for point in finite_points),
        north=max(point[1] for point in finite_points),
    )
    return geographic_bounds, finite_points + [finite_points[0]]


def _unit_scale(
    dataset: rasterio.DatasetReader, bounds: GeographicBounds | None
) -> tuple[float, float, float]:
    crs = CRS.from_user_input(dataset.crs) if dataset.crs else None
    if crs is not None and crs.is_geographic:
        latitude = (bounds.south + bounds.north) / 2 if bounds else 0.0
        x_scale = 111320.0 * max(abs(math.cos(math.radians(latitude))), 1e-6)
        y_scale = 110574.0
    elif crs is not None and crs.axis_info:
        x_scale = crs.axis_info[0].unit_conversion_factor or 1.0
        y_scale = crs.axis_info[1].unit_conversion_factor if len(crs.axis_info) > 1 else x_scale
        y_scale = y_scale or x_scale
    else:
        x_scale = y_scale = 1.0

    units = (dataset.tags(1).get("units") or dataset.tags().get("units") or "m").lower()
    elevation_scale = 0.3048 if units in {"ft", "foot", "feet", "us survey foot"} else 1.0
    return x_scale, y_scale, elevation_scale


def _generate_hillshade(
    dataset: rasterio.DatasetReader, output_path: Path, bounds: GeographicBounds | None
) -> None:
    if dataset.width < 2 or dataset.height < 2:
        raise DemProcessingError("Hillshade requires a raster at least 2 pixels wide and high.")

    x_unit_scale, y_unit_scale, elevation_scale = _unit_scale(dataset, bounds)
    transform = dataset.transform
    a = transform.a * x_unit_scale
    b = transform.b * x_unit_scale
    d = transform.d * y_unit_scale
    e = transform.e * y_unit_scale
    determinant = a * e - b * d
    if abs(determinant) < 1e-12:
        raise DemProcessingError("Hillshade cannot be generated from a degenerate geotransform.")
    profile = dataset.profile.copy()
    profile.update(driver="GTiff", count=1, dtype="uint8", nodata=0, compress="deflate")
    with rasterio.open(output_path, "w", **profile) as output:
        for row_offset in range(0, dataset.height, STATISTICS_WINDOW_SIZE):
            for col_offset in range(0, dataset.width, STATISTICS_WINDOW_SIZE):
                height = min(STATISTICS_WINDOW_SIZE, dataset.height - row_offset)
                width = min(STATISTICS_WINDOW_SIZE, dataset.width - col_offset)
                row_start = max(0, row_offset - 1)
                col_start = max(0, col_offset - 1)
                row_stop = min(dataset.height, row_offset + height + 1)
                col_stop = min(dataset.width, col_offset + width + 1)
                window = rasterio.windows.Window(
                    col_start, row_start, col_stop - col_start, row_stop - row_start
                )
                source = dataset.read(1, window=window, masked=True)
                invalid = np.ma.getmaskarray(source) | ~np.isfinite(source.data)
                padded_invalid = np.pad(invalid, 1, constant_values=False)
                invalid_neighborhood = np.any(
                    [
                        padded_invalid[row : row + invalid.shape[0], column : column + invalid.shape[1]]
                        for row in range(3)
                        for column in range(3)
                    ],
                    axis=0,
                )
                elevation = np.ma.filled(source, 0).astype(np.float64) * elevation_scale
                if elevation.shape[0] < 2 or elevation.shape[1] < 2:
                    continue
                dz_drow, dz_dcolumn = np.gradient(elevation)
                dz_dx = (e * dz_dcolumn - d * dz_drow) / determinant
                dz_dy = (-b * dz_dcolumn + a * dz_drow) / determinant
                slope = np.arctan(np.hypot(dz_dx, dz_dy))
                aspect = np.arctan2(-dz_dx, dz_dy)
                azimuth = math.radians(315)
                altitude = math.radians(45)
                shade = (
                    np.sin(altitude) * np.cos(slope)
                    + np.cos(altitude) * np.sin(slope) * np.cos(azimuth - aspect)
                )
                shade = np.clip(shade, 0, 1) * 254 + 1

                local_row = row_offset - row_start
                local_col = col_offset - col_start
                result = shade[local_row : local_row + height, local_col : local_col + width]
                result_invalid = invalid_neighborhood[
                    local_row : local_row + height, local_col : local_col + width
                ]
                output.write(
                    np.where(result_invalid, 0, result).astype(np.uint8),
                    1,
                    window=rasterio.windows.Window(col_offset, row_offset, width, height),
                )


def _write_map_preview(source_path: Path, output_path: Path, bounds: GeographicBounds) -> None:
    with rasterio.open(source_path) as source:
        width = max(1, source.width)
        height = max(1, source.height)
        scale = min(1.0, PREVIEW_MAX_DIMENSION / max(width, height))
        preview_width = max(1, round(width * scale))
        preview_height = max(1, round(height * scale))
        destination_transform = from_bounds(
            bounds.west,
            bounds.south,
            bounds.east,
            bounds.north,
            preview_width,
            preview_height,
        )
        destination = np.zeros((preview_height, preview_width), dtype=np.float32)
        reproject(
            source=rasterio.band(source, 1),
            destination=destination,
            src_transform=source.transform,
            src_crs=source.crs,
            src_nodata=source.nodata,
            dst_transform=destination_transform,
            dst_crs="EPSG:4326",
            dst_nodata=np.nan,
            resampling=Resampling.bilinear,
        )
        valid = np.isfinite(destination)
        if np.any(valid):
            low, high = float(destination[valid].min()), float(destination[valid].max())
            if high > low:
                gray = np.clip((destination - low) * (255.0 / (high - low)), 0, 255)
            else:
                gray = np.full(destination.shape, 128.0)
        else:
            gray = np.zeros(destination.shape)
        gray[~valid] = 0
        rgba = np.zeros((preview_height, preview_width, 4), dtype=np.uint8)
        rgba[:, :, :3] = gray[:, :, None].astype(np.uint8)
        rgba[:, :, 3] = valid.astype(np.uint8) * 220
        Image.fromarray(rgba, mode="RGBA").save(output_path, format="PNG", optimize=True)


def process_dem(
    dem_id: str,
    file_name: str,
    file_path: Path,
    file_size_bytes: int,
    output_directory: Path,
) -> DemMetadata:
    try:
        with rasterio.open(file_path) as dataset:
            if dataset.count != 1:
                raise DemProcessingError(
                    f"Expected a single-band elevation raster; received {dataset.count} bands."
                )
            if np.dtype(dataset.dtypes[0]).kind not in "iuf":
                raise DemProcessingError("Elevation data must use a real numeric raster data type.")
            if dataset.colorinterp[0].name not in {"undefined", "gray"}:
                raise DemProcessingError("Color or palette-indexed rasters are not supported as elevation data.")
            if dataset.width < 1 or dataset.height < 1:
                raise DemProcessingError("The raster has no pixels.")

            stats = _read_statistics(dataset)
            crs = CRS.from_user_input(dataset.crs) if dataset.crs else None
            transform = dataset.transform
            has_transform = not transform.is_identity and all(
                math.isfinite(value) for value in transform
            )
            if crs and has_transform:
                geographic_bounds, footprint = _geographic_footprint(dataset, crs)
            else:
                geographic_bounds, footprint = None, None
            warning = None
            if not crs:
                warning = "The raster has no CRS. Its geographic location cannot be identified."
            elif not has_transform:
                warning = "The raster has no usable geotransform. Its geographic location cannot be identified."
            elif stats.valid_pixel_count == 0:
                warning = "The raster contains no valid elevation pixels."

            if geographic_bounds and stats.valid_pixel_count:
                _generate_hillshade(dataset, output_directory / "hillshade.tif", geographic_bounds)
                _write_map_preview(file_path, output_directory / "dem-preview.png", geographic_bounds)
                _write_map_preview(
                    output_directory / "hillshade.tif",
                    output_directory / "hillshade-preview.png",
                    geographic_bounds,
                )

            metadata = DemMetadata(
                dem_id=dem_id,
                file_name=file_name,
                file_size_bytes=file_size_bytes,
                format=file_path.suffix.lstrip(".").upper(),
                crs=crs.to_string() if crs else None,
                epsg=crs.to_epsg() if crs else None,
                original_bounds=GeographicBounds(
                    west=dataset.bounds.left,
                    south=dataset.bounds.bottom,
                    east=dataset.bounds.right,
                    north=dataset.bounds.top,
                ) if has_transform else None,
                geographic_bounds=geographic_bounds,
                footprint=footprint,
                transform=RasterTransform(
                    a=transform.a, b=transform.b, c=transform.c,
                    d=transform.d, e=transform.e, f=transform.f,
                ) if has_transform else None,
                pixel_resolution=(
                    math.hypot(transform.a, transform.d),
                    math.hypot(transform.b, transform.e),
                ) if has_transform else None,
                resolution_units=(
                    "degrees" if crs.is_geographic else crs.axis_info[0].unit_name
                ) if crs and crs.axis_info else None,
                width=dataset.width,
                height=dataset.height,
                band_count=dataset.count,
                data_type=dataset.dtypes[0],
                nodata=dataset.nodata,
                elevation=stats,
                geographic_coverage=(
                    f"{geographic_bounds.west:.6f}, {geographic_bounds.south:.6f} to "
                    f"{geographic_bounds.east:.6f}, {geographic_bounds.north:.6f} (WGS84)"
                ) if geographic_bounds else None,
                processing_status="warning" if warning else "ready",
                warning=warning,
            )
    except DemProcessingError:
        raise
    except Exception as error:
        raise DemProcessingError(f"The uploaded file is not a readable georeferenced raster: {error}") from error

    (output_directory / "metadata.json").write_text(metadata.model_dump_json(indent=2), encoding="utf-8")
    return metadata


def load_metadata(output_directory: Path) -> DemMetadata:
    try:
        return DemMetadata.model_validate_json((output_directory / "metadata.json").read_text(encoding="utf-8"))
    except (OSError, ValueError) as error:
        raise DemProcessingError("DEM metadata is unavailable.") from error