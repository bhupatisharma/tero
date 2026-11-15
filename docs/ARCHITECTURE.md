# Architecture

## Overview

The application is split into independently runnable frontend and backend projects. The React client owns the interface, map interactions, and API requests. FastAPI exposes versioned, structured system endpoints and is the future home for geospatial services. No DEM, raster, vector, or routing behavior is included in Phase 1.

## Frontend

- `frontend/src/App.tsx`: application state, header, and workspace composition.
- `frontend/src/components/Map/`: MapLibre map lifecycle, controls, map events, marker, and resize observation.
- `frontend/src/components/Sidebar/`: map readouts and control composition.
- `frontend/src/components/LayerManager/`: base-map visibility and empty dataset state.
- `frontend/src/components/StatusPanel/`: frontend, backend, and map status.
- `frontend/src/services/`: backend URL validation and HTTP health-check service.
- `frontend/src/hooks/`: periodic health-check state.
- `frontend/src/types/`: shared frontend API and geographic value shapes.

Vite reads `VITE_API_BASE_URL` and `VITE_MAP_STYLE_URL` from frontend environment files. Invalid backend configuration is surfaced in the backend status; invalid map configuration is displayed over the map area. If no map style variable is supplied, the app uses the documented public demo style.

## Backend

- `backend/app/main.py`: FastAPI application, CORS configuration, and root API information.
- `backend/app/api/router.py`: `/api` route aggregation.
- `backend/app/api/routes/`: focused API route modules, currently the health endpoint.
- `backend/app/models.py`: Pydantic response models.
- `backend/tests/`: endpoint behavior tests.

`GET /api/health` returns backend status, application name, and API version. `GET /` returns API information. CORS defaults to the local Vite origins and can be overridden with comma-separated `CORS_ORIGINS` values.

## Map Integration

MapLibre GL JS renders a configurable style URL in the main workspace. The style supplies map sources and attribution; MapLibre supplies navigation controls, mouse/touch interaction, and map events. Clicks place a coordinate marker and update the sidebar readout. A `ResizeObserver` calls `map.resize()` when the map container changes dimensions.

The default style is OpenFreeMap Liberty (`https://tiles.openfreemap.org/styles/liberty`), an OpenStreetMap-derived vector basemap with roads, waterways, settlements, boundaries, and labels. It requires no API key. The style provides attribution, which MapLibre's attribution control displays automatically (© OpenMapTiles and OpenStreetMap contributors). Review [OpenFreeMap's terms](https://openfreemap.org/tos/); the public service currently offers no SLA. `VITE_MAP_STYLE_URL` keeps the style configurable without changing map behavior.

## Communication

The frontend health service sends `GET {VITE_API_BASE_URL}/api/health`, validates the response shape, reports network and HTTP errors, and repeats the check every 15 seconds. The backend allows the local Vite origin by default. Frontend and backend can be started and tested independently.