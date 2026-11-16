# Implementation Status

## Phase 1 Completed

- React, TypeScript, and Vite frontend with separate frontend dependencies.
- FastAPI backend with separate Python requirements and modular API routes.
- Interactive MapLibre 2D map with navigation controls, pan/zoom, attribution, click marker, selected and cursor coordinates, and resize handling.
- Responsive sidebar with zoom readout, base-map visibility control, dataset empty state, and frontend/backend/map status.
- Configurable backend URL and map style, health polling, and visible configuration/request/map errors.
- Root and health API endpoints, local CORS configuration, endpoint tests, frontend API-service tests, and Ubuntu/Windows GitHub Actions checks.
- README, architecture notes, and this phase status document.

## Phase 1 Completed

- React, TypeScript, Vite, FastAPI, and the interactive MapLibre workspace.
- Configurable backend/map settings, health monitoring, base-map control, coordinate inspection, and existing API tests.

## Phase 2 Completed

- Cancellable, progress-aware `.tif`/`.tiff` upload, frontend extension/size checks, backend streamed size enforcement, and Rasterio content validation.
- Single-band numeric raster validation; unsupported multiband and color/palette rasters are rejected rather than interpreted as elevation.
- Pydantic metadata for source CRS/EPSG, original-CRS bounds, transformed WGS84 bounds and footprint, affine transform, resolution/units, dimensions, data type, NoData, and elevation statistics.
- Fixed-window statistics and hillshade generation; masked and non-finite pixels are excluded, and NoData margins are masked in the output.
- Preserved original GeoTIFF, separate georeferenced hillshade, and downsampled (1024-pixel maximum dimension) DEM/hillshade PNG map previews.
- Independent MapLibre DEM and hillshade layer controls, hillshade opacity, footprint display, and automatic extent zoom. Missing CRS/geotransform yields a warning and no arbitrary map placement.
- Metadata, preview, hillshade-download, and delete endpoints; local storage and upload size are configurable.
- Added conda-forge Python 3.12 environment definition and updated setup/architecture documentation.

## Tests and Platform Coverage

- Backend: 12 tests passed on Linux with Python 3.13, including projected and geographic CRS, known bounds/statistics, NoData, invalid/unsupported/oversized files, absent georeferencing, rotated affine hillshade, source preservation, and deletion.
- Frontend: 9 Vitest tests passed, including the DEM upload interface, validation/error feedback, metadata rendering, progress/cancellation, layer visibility, and opacity controls.
- Frontend TypeScript check and production build passed. Vite reports the existing large MapLibre bundle warning (about 1.33 MB uncompressed).
- Python 3.12 is specified in `backend/environment.yml`; this local session used Python 3.13. Windows compatibility is configured through the cross-platform dependency set but has not been manually run here.

## Known Limitations

- Only one active DEM is managed by the current sidebar, and only single-band numeric elevation rasters are supported.
- Map imagery is a grayscale preview capped at 1024 pixels on its longest side; full-resolution DEM and hillshade files remain available from the backend but are not served as map tiles.
- Hillshade vertical units are converted when a common feet unit tag is present; absent elevation-unit metadata is treated as metres. Geographic-CRS horizontal resolution uses a center-latitude approximation.
- Unreferenced or identity-transform rasters are retained with a warning but cannot produce a geographically placed preview or hillshade.
- Storage is local disk with no authentication, quota management, or automatic retention policy. Configure `DEM_STORAGE_DIR` for deployment.
- Antimeridian-crossing datasets and unusual CRS distortion may need a tile-based visualization path for exact global rendering.
- The default OpenFreeMap basemap is an external public service with no SLA; review its terms and attribution requirements before deployment.

## Remaining Work

- Run the Python 3.12 environment and Windows CI checks in their target environments.
- Consider tiled raster delivery and persistent upload lifecycle controls before supporting large multi-user deployments.