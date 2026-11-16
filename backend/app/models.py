from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    application: str = "Terrain-Aware Route Planning and GIS Analysis System"
    api_version: str = "1.0.0"


class ApiInfoResponse(BaseModel):
    application: str = "Terrain-Aware Route Planning and GIS Analysis System"
    api_version: str = "1.0.0"
    docs_url: str = "/docs"


class GeographicBounds(BaseModel):
    west: float
    south: float
    east: float
    north: float


class RasterTransform(BaseModel):
    a: float
    b: float
    c: float
    d: float
    e: float
    f: float


class ElevationStatistics(BaseModel):
    minimum: float | None = None
    maximum: float | None = None
    mean: float | None = None
    valid_pixel_count: int = 0
    units: str | None = None


class DemMetadata(BaseModel):
    dem_id: str
    file_name: str
    file_size_bytes: int
    format: str
    crs: str | None = None
    epsg: int | None = None
    original_bounds: GeographicBounds | None = None
    geographic_bounds: GeographicBounds | None = None
    footprint: list[tuple[float, float]] | None = None
    transform: RasterTransform | None = None
    pixel_resolution: tuple[float, float] | None = None
    resolution_units: str | None = None
    width: int
    height: int
    band_count: int
    data_type: str
    nodata: float | None = None
    elevation: ElevationStatistics
    geographic_coverage: str | None = None
    processing_status: str
    warning: str | None = None