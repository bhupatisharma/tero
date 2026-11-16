# Terrain-Aware Route Planning and GIS Analysis System

A GIS workspace with a React and TypeScript frontend, an interactive MapLibre 2D map, GeoTIFF DEM inspection, computed hillshade, and a FastAPI backend.

## Technology

- Frontend: React 19, TypeScript, Vite, MapLibre GL JS
- Backend: Python 3.12, FastAPI, Pydantic, Rasterio, PyProj, NumPy, Pillow, Uvicorn
- Tests: Vitest and pytest

Frontend and backend dependencies are managed separately in `frontend/package.json` and `backend/requirements.txt`.

## Prerequisites

- Node.js 22 LTS and npm
- Python 3.12
- Conda with conda-forge is recommended for the backend geospatial stack.

## Configure

Copy the frontend environment example to `frontend/.env.local`.

On Linux:

```sh
cp frontend/.env.example frontend/.env.local
```

On Windows PowerShell:

```powershell
Copy-Item frontend/.env.example frontend/.env.local
```

Set `VITE_API_BASE_URL` to the FastAPI origin and `VITE_MAP_STYLE_URL` to a MapLibre style JSON URL. The example uses `http://127.0.0.1:8000` and OpenFreeMap's Liberty style. The backend's optional `CORS_ORIGINS` variable is a comma-separated list of allowed frontend origins; its defaults include the local Vite origin on port 5173.

The default style uses [OpenFreeMap Liberty](https://tiles.openfreemap.org/styles/liberty), a detailed OpenStreetMap-derived vector basemap that requires no API key. MapLibre displays the style's required attribution, including © OpenMapTiles and OpenStreetMap contributors. Review the [OpenFreeMap terms](https://openfreemap.org/tos/) before deployment; its public service currently has no SLA. Use `VITE_MAP_STYLE_URL` to select another compatible style when needed.

## Start the Backend

Recommended geospatial environment, from the repository root:

```sh
conda env create -f backend/environment.yml
conda activate terrain-gis
```

The environment uses conda-forge for Rasterio, PyProj, and their GDAL dependencies. Alternatively, use the Python virtual-environment steps below; `backend/requirements.txt` lists the matching PyPI dependencies.

Create and activate a virtual environment from the repository root.

Linux:

```sh
python3.12 -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Windows PowerShell:

```powershell
py -3.12 -m venv .venv
.venv\Scripts\Activate.ps1
python -m pip install -r backend\requirements.txt
```

Start the API from the repository root:

```sh
python -m uvicorn app.main:app --app-dir backend --reload
```

The API is available at `http://127.0.0.1:8000`. Check `http://127.0.0.1:8000/api/health` or open the interactive API docs at `http://127.0.0.1:8000/docs`.

DEM uploads accept single-band `.tif` and `.tiff` rasters that Rasterio can open. The API validates the raster contents, extracts CRS and elevation statistics, stores the original, creates a georeferenced hillshade, and serves downsampled map previews. Uploads are limited to 512 MB by default. Configure `DEM_MAX_UPLOAD_SIZE_MB` to change the limit and `DEM_STORAGE_DIR` to change the local storage directory. The default storage directory is `backend/data/dems`.

The DEM endpoints are `POST /api/dem/upload`, `GET /api/dem/{dem_id}`, `GET /api/dem/{dem_id}/preview?layer=dem|hillshade`, `GET /api/dem/{dem_id}/hillshade`, and `DELETE /api/dem/{dem_id}`. A raster with missing CRS or geotransform is retained with a warning but is not placed on the map.

## Start the Frontend

In a second terminal:

```sh
cd frontend
npm install
npm run dev
```

Open the Vite URL shown in the terminal (by default `http://127.0.0.1:5173`). The app checks the API on launch and every 15 seconds. The map supports mouse drag panning, wheel/touch zoom, navigation controls, and click-to-select coordinates. Use the sidebar to upload a DEM, inspect its metadata, toggle its footprint/elevation preview and hillshade, and adjust hillshade opacity.

## Checks

Frontend, from `frontend/`:

```sh
npm ci
npm test
npm run check
npm run build
```

Backend, from the repository root after installing its requirements:

```sh
python -m pytest backend/tests
```

GitHub Actions runs frontend and backend checks on Ubuntu and Windows. Windows is configured in CI; it has not been manually verified as part of this implementation.

## Scope

Phase 2 provides single-band GeoTIFF ingestion, metadata and statistics, geographic coverage, a computed hillshade, and bounded map previews. Route planning, cost surfaces, constraints, multi-band DEM interpretation, and 3D terrain rendering remain out of scope. See [docs/IMPLEMENTATION_STATUS.md](docs/IMPLEMENTATION_STATUS.md) for completed work and limitations.