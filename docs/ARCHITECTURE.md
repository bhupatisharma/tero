# Architecture

## Overview

The application is split into independently runnable frontend and backend projects. The React client owns the interface, map interactions, and API requests. FastAPI owns DEM validation, metadata extraction, coordinate transformations, hillshade generation, and map-preview generation. Routing and analysis beyond DEM recognition are not included in Phase 2.

## Frontend

- `frontend/src/App.tsx`: application state, header, and workspace composition.
- `frontend/src/components/Map/`: MapLibre map lifecycle, controls, map events, marker, and resize observation.
- `frontend/src/components/Sidebar/`: map readouts, DEM upload/metadata panel, and control composition.
- `frontend/src/components/LayerManager/`: base-map, DEM, and hillshade visibility plus hillshade opacity.
- `frontend/src/components/StatusPanel/`: frontend, backend, and map status.
- `frontend/src/services/`: backend URL validation, health checks, and DEM upload/removal requests.
- `frontend/src/hooks/`: periodic health-check state.
- `frontend/src/types/`: shared frontend API and geographic value shapes.

Vite reads `VITE_API_BASE_URL` and `VITE_MAP_STYLE_URL` from frontend environment files. Invalid backend configuration is surfaced in the backend status; invalid map configuration is displayed over the map area. If no map style variable is supplied, the app uses the documented public demo style.

## Backend

- `backend/app/main.py`: FastAPI application, CORS configuration, and root API information.
- `backend/app/api/router.py`: `/api` route aggregation.
- `backend/app/api/routes/`: focused health and DEM route modules.
- `backend/app/services/dem_processing.py`: Rasterio/PyProj processing, statistics, hillshade, and preview creation.
- `backend/app/models.py`: Pydantic response models, including DEM metadata.
- `backend/tests/`: endpoint behavior tests.

`GET /api/health` returns backend status, application name, and API version. `GET /` returns API information. DEM originals and generated files are stored under `DEM_STORAGE_DIR` (default `backend/data/dems`); `DEM_MAX_UPLOAD_SIZE_MB` configures the streamed upload limit (default 512). CORS defaults to the local Vite origins and can be overridden with comma-separated `CORS_ORIGINS` values.

### DEM Processing

`POST /api/dem/upload` streams an allowed `.tif`/`.tiff` file to a generated per-DEM directory. Rasterio must successfully open it, and Phase 2 accepts a single real-numeric band rather than interpreting multiband or palette data as elevation. Statistics are accumulated in fixed-size windows with masked and non-finite pixels excluded. The original file is never rewritten.

PyProj identifies the source CRS and transforms a densified raster perimeter from the actual affine transform (including rotation/shear) to WGS84. Responses keep original-CRS bounds separate from WGS84 bounds and footprint. If CRS or usable geotransform is absent, metadata is returned with a warning and no geographic footprint or map preview is produced.

The processing service creates a single-band, georeferenced hillshade GeoTIFF using elevation gradients transformed through the full affine geotransform, horizontal CRS units, elevation unit tags when present, and default 315-degree azimuth / 45-degree altitude. It writes in windows and masks NoData edges. A separate DEM and hillshade PNG preview is reprojected to WGS84 and capped at 1024 pixels on its longest side; the original and full-resolution hillshade remain on disk. The preview endpoints serve these bounded images, not raw raster arrays.

MapLibre adds the previews as independent image sources over the WGS84 bounds and draws the transformed footprint as a line. Uploading a located DEM fits the map to its extent. DEM and hillshade visibility are separate, hillshade opacity is adjustable, and base-map visibility changes only the basemap style layers. The map layer UI never assigns a location to an unreferenced dataset.

DEM API: `POST /api/dem/upload`, `GET /api/dem/{dem_id}`, `GET /api/dem/{dem_id}/preview?layer=dem|hillshade`, `GET /api/dem/{dem_id}/hillshade`, and `DELETE /api/dem/{dem_id}`. Responses use Pydantic models; file responses expose generated raster/image content without exposing server paths.

## Map Integration

MapLibre GL JS renders a configurable style URL in the main workspace. The style supplies map sources and attribution; MapLibre supplies navigation controls, mouse/touch interaction, and map events. Clicks place a coordinate marker and update the sidebar readout. A `ResizeObserver` calls `map.resize()` when the map container changes dimensions.

The default style is OpenFreeMap Liberty (`https://tiles.openfreemap.org/styles/liberty`), an OpenStreetMap-derived vector basemap with roads, waterways, settlements, boundaries, and labels. It requires no API key. The style provides attribution, which MapLibre's attribution control displays automatically (© OpenMapTiles and OpenStreetMap contributors). Review [OpenFreeMap's terms](https://openfreemap.org/tos/); the public service currently offers no SLA. `VITE_MAP_STYLE_URL` keeps the style configurable without changing map behavior.

## Communication

The frontend health service sends `GET {VITE_API_BASE_URL}/api/health`, validates the response shape, reports network and HTTP errors, and repeats the check every 15 seconds. DEM uploads use a cancellable multipart request with upload progress; the backend performs processing without blocking the frontend. The backend allows the local Vite origin by default. Frontend and backend can be started and tested independently.