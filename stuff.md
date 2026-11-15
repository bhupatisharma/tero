# MASTER PROJECT SPECIFICATION
# TERRAIN-AWARE ROUTE PLANNING AND GIS ANALYSIS SYSTEM

## 1. PROJECT OVERVIEW

### 1.1 Project objective

Develop a modular, interactive, GIS-based Terrain-Aware Route Planning System.

The application will allow users to upload Digital Elevation Models (DEMs), load additional geographical datasets, analyse terrain characteristics, generate a combined weighted cost map, select geographical start and destination points, and calculate routes based on terrain and user-defined geographical constraints.

The system should provide multiple route alternatives, detailed route statistics, interactive 2D mapping, and 3D terrain visualisation.

The application must be designed iteratively, with each feature implemented, tested, documented, and committed before proceeding to the next phase.

### 1.2 Main objectives

1. Accept user-uploaded DEM files.
2. Automatically read and interpret geospatial metadata.
3. Correctly position uploaded geographical data on an interactive world map.
4. Support multiple geographical data layers.
5. Combine terrain and environmental information into a cost surface.
6. Allow users to dynamically configure the weights of supported cost factors.
7. Allow users to select start and destination points directly on the map.
8. Generate routes using the A* algorithm.
9. Support general user-defined geographical restrictions.
10. Generate multiple alternative routes.
11. Compare route lengths, costs, elevation and terrain characteristics.
12. Display results in both 2D and 3D.
13. Support large geographical datasets as far as available hardware permits.
14. Work on both Linux and Windows.

### 1.3 Intended application

The application is a general-purpose terrain-aware GIS analysis and route-planning platform.

It should be modular enough to support different geographical analysis scenarios without being tied to one particular dataset or geographical location.

---

# 2. CORE FUNCTIONAL REQUIREMENTS

## 2.1 DEM UPLOAD AND RECOGNITION

Users should be able to upload their own Digital Elevation Models.

Initial supported format:
- GeoTIFF (.tif)
- GeoTIFF (.tiff)

The application must automatically inspect uploaded DEM files.

Extract the following metadata:
- Coordinate Reference System (CRS).
- EPSG identifier, where available.
- Geographic bounds.
- Raster width and height.
- Pixel resolution.
- Number of bands.
- Elevation values.
- Minimum and maximum elevation.
- NoData values.
- Geotransform information.
- Geographic coverage.

The system must use the actual georeferencing metadata to position the DEM correctly.

It must not assume every DEM uses latitude and longitude coordinates.

Support coordinate transformations between different CRS systems.

If the uploaded DEM lacks valid georeferencing:
- Display a warning.
- Explain which metadata is missing.
- Do not silently place it at an arbitrary location.
- Allow the user to supply additional georeferencing information if feasible.

Display a DEM information panel containing the extracted metadata.

Allow users to see the geographical coverage of the uploaded DEM on the map.

Important: The application should recognise a DEM's geographical coverage from its geospatial metadata. It should not claim to identify an unknown location perfectly from an unreferenced elevation image.

## 2.2 INTERACTIVE 2D MAP

Provide a full-screen interactive map.

Features:
- Zoom in and out.
- Pan around the map.
- Display latitude and longitude.
- Display coordinates when clicking the map.
- Display uploaded geographical datasets.
- Toggle individual layers.
- Control layer opacity.
- Display geographical boundaries.
- Display route start and destination markers.
- Display generated routes.
- Display restricted-area overlays.
- Display legends for raster layers.
- Support different base-map styles where available.

The map should remain responsive when datasets are uploaded or changed.

## 2.3 GEOGRAPHICAL DATA LAYERS

The application should support multiple geographical datasets.

Initial required layers:

1. DEM / elevation data.
2. Vegetation data.
3. Land-cover data.
4. River data.
5. Water-body data.
6. Road-network data.
7. Derived slope data.
8. Derived hillshade data.

Each layer should be independently managed.

Required functionality:
- Upload a dataset.
- Read its metadata.
- Display it on the map.
- Enable or disable visibility.
- Adjust opacity.
- Inspect its properties.
- Remove it from the current project.
- Check whether it covers the selected geographical region.

Support raster and vector data separately.

Initial formats:
- GeoTIFF for raster datasets.
- GeoJSON for vector datasets.

Additional formats may be introduced later.

## 2.4 GEOSPATIAL DATA PROCESSING

Different datasets may have:
- Different coordinate systems.
- Different spatial resolutions.
- Different geographical extents.
- Different pixel dimensions.
- Different data types.

The application must process these differences correctly.

Required functionality:
- CRS detection.
- Reprojection.
- Raster resampling.
- Vector reprojection.
- Raster alignment.
- Vector-to-raster conversion where necessary.
- NoData handling.
- Extent validation.
- Resolution validation.
- Common analysis-grid generation.

Select an appropriate reference grid for analysis.

Do not blindly resample every dataset to an arbitrarily high resolution.

Preserve original uploaded datasets separately.

All processing should produce new derived datasets without overwriting the original inputs.

## 2.5 COST MAP GENERATION

Generate a combined geographical cost surface from the available geographical layers.

Initial cost factors:
- Slope.
- Vegetation density.
- Land-cover characteristics.
- Water features.
- Road-network characteristics.
- Other supported environmental factors.

Each factor should be converted into a suitable cost raster.

The application must:
1. Generate individual cost layers.
2. Normalize their values.
3. Align them to the common analysis grid.
4. Apply user-defined weights.
5. Combine the layers into a final cost surface.
6. Display the resulting cost map.

Use a configurable weighted cost model.

Conceptual example:

C(x,y) = w1*S(x,y) + w2*V(x,y) + w3*L(x,y) + w4*H(x,y)

Where:
- S = slope-related cost.
- V = vegetation-related cost.
- L = land-cover-related cost.
- H = environmental hazard-related cost.
- w = user-defined weight.

The actual model must be documented and implemented consistently.

The interface should provide:
- Individual weight sliders.
- Numerical weight values.
- Reset button.
- Enable/disable controls for cost factors.
- Cost-map visibility toggle.
- Colour legend.
- Cost-layer inspection.

Changing a weight must update the combined cost surface and subsequent route calculations.

Keep individual cost layers separate so that they can be recalculated without re-uploading the original datasets.

Define appropriate behaviour for missing or unavailable layers.

## 2.6 START AND DESTINATION SELECTION

Users should select the starting and ending points directly on the map.

Required functionality:
- Start-point selection mode.
- Destination-selection mode.
- Display selected coordinates.
- Display markers.
- Allow points to be moved.
- Allow points to be cleared and selected again.
- Convert geographic coordinates into raster coordinates.
- Validate whether points fall inside the DEM coverage.
- Validate whether points fall on usable data.
- Warn when a point falls inside an inaccessible or restricted region.

The system must not attempt route calculation using invalid coordinates or missing raster cells.

## 2.7 ROUTE PLANNING

Implement the A* pathfinding algorithm.

The routing engine should operate independently of the frontend.

The algorithm should use the processed cost surface.

A* evaluation:

f(n) = g(n) + h(n)

Where:
- g(n) = accumulated cost from the start.
- h(n) = estimated remaining cost.
- f(n) = estimated total cost.

Required functionality:
- Grid-based graph representation.
- Horizontal movement.
- Vertical movement.
- Diagonal movement.
- Appropriate movement-distance calculation.
- Cost accumulation.
- Invalid-cell handling.
- NoData handling.
- Route reconstruction.
- Conversion from raster coordinates to geographic coordinates.

The heuristic must be compatible with the cost model and must not overestimate the remaining cost if optimality is being claimed.

Avoid unnecessary assumptions about the relationship between distance and terrain cost.

The routing module should be independently testable.

## 2.8 USER-DEFINED GEOGRAPHICAL CONSTRAINTS

Allow users to define geographical areas that should be excluded or treated as higher-cost areas in general-purpose route planning.

Features:
- Draw polygons on the map.
- Create circular geographical regions.
- Specify the size and position of a region.
- Import restricted-area polygons using GeoJSON.
- Edit existing regions.
- Move or resize regions.
- Delete regions.
- Enable or disable individual regions.
- Display regions as map overlays.

Support two constraint types:

HARD CONSTRAINT:
- The route must not cross the specified area.

SOFT CONSTRAINT:
- The area remains traversable but incurs an additional cost.

Validate start and destination points against active hard restrictions.

Provide appropriate warnings when a route cannot be calculated because of conflicting constraints.

Keep the restriction module independent from the original uploaded datasets and base cost layers.

## 2.9 MULTIPLE ALTERNATIVE ROUTES

The application should generate multiple route alternatives rather than returning only one route.

Initial approach:
- Generate an initial A* route.
- Preserve the original cost surface.
- Apply controlled temporary penalties to previously used route cells.
- Recalculate alternative routes.
- Repeat as required.
- Identify duplicate or nearly identical routes.
- Retain meaningfully different alternatives.

Important: Penalized repeated A* calculations are a heuristic alternative-generation method. Do not describe them as guaranteed K-shortest-path solutions.

Display alternative routes using distinguishable colours and allow users to select individual routes.

Each alternative should have its own statistics.

## 2.10 ROUTE COMPARISON AND STATISTICS

For every route, calculate and display:

- Total geographical length.
- Accumulated cost.
- Average slope.
- Maximum slope.
- Minimum elevation.
- Maximum elevation.
- Total elevation gain.
- Total elevation loss.
- Average elevation.
- Vegetation statistics, where available.
- Environmental hazard statistics, where available.
- Route geometry.

Include an elevation-profile graph.

Provide a comparison panel for alternative routes.

Clearly distinguish physical distance from accumulated cost.

Explain that the lowest-cost route does not necessarily have the shortest geographical distance.

## 2.11 2D AND 3D VISUALISATION

Provide both 2D and 3D map interfaces.

2D:
- Interactive map.
- DEM coverage.
- Geographical layers.
- Cost-map overlay.
- Start and destination markers.
- Generated routes.
- Restricted-area overlays.
- Route selection and comparison.

3D:
- Terrain surface generated from DEM elevation data.
- Satellite or aerial imagery draped over the terrain.
- Terrain shading.
- Route displayed over the 3D surface.
- Start and destination markers.
- Relevant geographical overlays.
- Camera rotation.
- Camera tilt.
- Zoom.
- Terrain inspection.

Allow users to switch between 2D and 3D.

Route selection should remain synchronized between both views.

Important:
A DEM contains elevation information, not satellite imagery. A separate imagery source is required to obtain the detailed satellite appearance.

Use imagery sources with appropriate access permissions, coverage and licensing.

## 2.12 PROJECT MANAGEMENT AND EXPORT

Allow users to save and reopen their analysis projects.

Store:
- Project configuration.
- Uploaded dataset references.
- Dataset metadata.
- Layer visibility settings.
- Cost-factor configuration.
- Weight values.
- Selected start and destination points.
- User-defined restrictions.
- Generated route information.

Support:
- Export route as GeoJSON.
- Export route statistics.
- Save project configuration.
- Reopen saved projects.

Avoid embedding unnecessarily large raster files inside project configuration files. Store dataset references and metadata separately.

---

# 3. TECHNOLOGY STACK

The complete application must work on Linux and Windows.

Do not introduce operating-system-specific dependencies unless absolutely necessary.

## 3.1 FRONTEND

React:
- Main application framework.
- Component-based interface.
- State management.

TypeScript:
- Type safety.
- Structured geographic data models.
- Better maintainability.

Vite:
- Frontend development server.
- Build system.

MapLibre GL JS:
- Interactive 2D mapping.
- Raster and vector overlays.
- Markers and route visualisation.
- Geographic interaction.

CesiumJS:
- 3D terrain rendering.
- Terrain visualisation from DEM data.
- Satellite and aerial imagery.
- 3D route overlays.

## 3.2 BACKEND

Python 3.12:
- Main backend language.
- Geospatial processing.
- Cost calculations.
- Routing implementation.

FastAPI:
- API framework.
- Upload endpoints.
- Processing endpoints.
- Route calculation endpoints.
- Project management endpoints.

Uvicorn:
- ASGI server.

Pydantic:
- Data validation.
- API request and response models.

## 3.3 GEOSPATIAL PROCESSING

Rasterio:
- Read and write raster datasets.
- DEM metadata extraction.
- Raster processing.

GDAL:
- Geospatial raster operations.
- Reprojection.
- Raster format support.

GeoPandas:
- Vector data management.
- Geographical data processing.

Shapely:
- Geometrical operations.
- Polygon and line processing.
- Spatial intersection checks.

PyProj:
- CRS recognition.
- Coordinate transformations.

## 3.4 NUMERICAL PROCESSING

NumPy:
- Raster calculations.
- Cost arrays.
- Numerical operations.

SciPy:
- Numerical processing.
- Filtering.
- Selected raster operations.

## 3.5 ROUTING

Python implementation of:
- A* algorithm.
- Grid-based graph representation.
- Alternative-route generation.

Keep the routing algorithm separate from the GIS upload and visualisation code.

## 3.6 TESTING

Backend:
- Pytest.

Frontend:
- Vitest.
- React Testing Library.

Cross-platform:
- GitHub Actions.
- Linux and Windows CI environments.

## 3.7 DATA FORMATS

Initial supported formats:
- GeoTIFF for raster data.
- GeoJSON for vector data.

Additional formats can be considered after the initial pipeline works.

---

# 4. CROSS-PLATFORM REQUIREMENTS

Linux and Windows support are mandatory.

Target environments:
- Linux distributions such as Fedora and Ubuntu.
- Windows 10 and Windows 11.

The application must not depend on Linux-only commands or directory conventions.

Use Python pathlib for filesystem operations.

Avoid hardcoded filesystem paths.

Do not assume that every operating system has the same installed geospatial libraries.

Use Miniforge and conda-forge for the Python geospatial environment.

Use a shared environment specification.

Initial environment:

environment.yml

name: terrain-planner

channels:
  - conda-forge

dependencies:
  - python=3.12
  - numpy
  - scipy
  - rasterio
  - gdal
  - geopandas
  - shapely
  - pyproj
  - pandas
  - pip
  - pip:
      - fastapi
      - uvicorn[standard]
      - python-multipart
      - pydantic
      - pytest

This is the initial environment specification. After successful installation on both platforms, test and lock exact dependency versions.

Do not independently install conflicting GDAL versions.

Keep frontend dependencies separate through package.json and the package lockfile.

Every phase must be tested on Linux and Windows before being marked complete.

---

# 5. APPLICATION ARCHITECTURE

Use a modular frontend/backend architecture.

Frontend responsibilities:
- User interface.
- Map interactions.
- Dataset upload interface.
- Layer controls.
- Cost configuration.
- Route selection.
- Results presentation.
- 2D and 3D rendering.

Backend responsibilities:
- File validation.
- DEM processing.
- Metadata extraction.
- Coordinate transformations.
- Raster processing.
- Vector processing.
- Cost-map generation.
- Route calculation.
- Route statistics.
- Project management.
- Export functionality.

Keep the following modules separate:

1. API module.
2. DEM-processing module.
3. Coordinate-transformation module.
4. Raster-processing module.
5. Vector-processing module.
6. Cost-map module.
7. Routing module.
8. Constraint-management module.
9. Route-statistics module.
10. Project-management module.

The frontend should not perform heavy raster calculations.

The backend should return structured metadata and geographic results.

Use GeoJSON for route geometries and vector results.

Use appropriate raster files or rendered raster tiles for raster visualisation.

---

# 6. DEVELOPMENT PHASES

Development must follow the sequence below.

Do not attempt to implement every feature simultaneously.

Each phase should have:
- A defined scope.
- Small implementation tasks.
- Tests.
- Documentation.
- A working milestone.
- A GitHub commit.

A later phase must not break functionality completed in an earlier phase.

---

## PHASE 1 — PROJECT SETUP AND BASIC MAP INTERFACE

### Objective

Establish the application foundation and display an interactive map.

### Features

1. Create the GitHub repository.
2. Set up the React frontend.
3. Set up TypeScript.
4. Set up Vite.
5. Set up the Python backend.
6. Set up FastAPI.
7. Configure frontend/backend communication.
8. Integrate MapLibre GL JS.
9. Create the main application layout.
10. Create a full-screen map.
11. Create a sidebar.
12. Add zoom and pan.
13. Display map coordinates.
14. Add basic layer-management UI.
15. Add an initial status panel.
16. Create basic error handling.
17. Create the initial documentation.

### Cross-platform requirements

- Verify frontend installation on Linux and Windows.
- Verify backend installation on Linux and Windows.
- Verify that both services start.
- Verify API communication.

### Completion criteria

A working browser application with an interactive 2D map and a functioning backend.

---

## PHASE 2 — DEM UPLOAD AND GEOSPATIAL RECOGNITION

### Objective

Allow users to upload a DEM and automatically interpret its geographical information.

### Features

1. Implement DEM file upload.
2. Support GeoTIFF.
3. Validate file type.
4. Validate file integrity.
5. Read metadata using Rasterio.
6. Extract CRS.
7. Extract EPSG identifier where available.
8. Extract geographical bounds.
9. Extract raster dimensions.
10. Extract resolution.
11. Extract elevation values.
12. Extract minimum and maximum elevation.
13. Handle NoData values.
14. Handle missing georeferencing.
15. Convert coordinates where necessary.
16. Position the DEM correctly on the 2D map.
17. Display DEM coverage.
18. Create a DEM metadata panel.
19. Generate hillshade.
20. Display hillshade over the map.

### Completion criteria

A user can upload a GeoTIFF, inspect its metadata, see its geographical coverage and view its hillshade in the correct location.

This is the first major project milestone.

---

## PHASE 3 — GEOGRAPHICAL DATA LAYERS

### Objective

Allow users to upload and manage supporting geographical datasets.

### Features

1. Vegetation data upload.
2. Land-cover data upload.
3. River data upload.
4. Water-body data upload.
5. Road-network data upload.
6. Vector data upload.
7. Raster data upload.
8. Individual layer visibility.
9. Layer opacity controls.
10. Layer metadata.
11. CRS validation.
12. Dataset extent validation.
13. Coordinate reprojection.
14. Initial raster/vector alignment.
15. Layer removal.
16. Layer status display.

### Completion criteria

Multiple geographical datasets can be loaded and independently displayed in the correct geographical positions.

---

## PHASE 4 — RASTER PROCESSING AND COST MAP GENERATION

### Objective

Convert the geographical datasets into compatible cost layers and combine them.

### Features

1. Define the analysis grid.
2. Choose reference resolution.
3. Reproject compatible datasets.
4. Resample raster datasets.
5. Rasterize applicable vector datasets.
6. Handle NoData values.
7. Generate slope raster.
8. Generate vegetation cost raster.
9. Generate land-cover cost raster.
10. Generate applicable water-related cost raster.
11. Generate applicable road-related cost raster.
12. Normalize individual cost layers.
13. Create configurable weights.
14. Implement weighted cost calculation.
15. Generate combined cost raster.
16. Preserve individual cost layers.
17. Add dynamic weight controls.
18. Recalculate cost map after weight changes.
19. Display cost map.
20. Add colour legend.
21. Add cost-layer visibility controls.
22. Validate the output.

### Completion criteria

The application generates a combined cost surface and updates it when the user changes the configuration.

---

## PHASE 5 — START/DESTINATION SELECTION AND A* ROUTING

### Objective

Implement the first complete route-planning workflow.

### Features

1. Start-point selection.
2. Destination selection.
3. Map markers.
4. Coordinate display.
5. Raster-coordinate conversion.
6. Start-point validation.
7. Destination validation.
8. Grid-based graph construction.
9. A* implementation.
10. Horizontal movement.
11. Vertical movement.
12. Diagonal movement.
13. Movement-distance calculation.
14. Cost accumulation.
15. Admissible heuristic.
16. NoData handling.
17. Inaccessible-cell handling.
18. Route reconstruction.
19. Geographic coordinate conversion.
20. Route display on 2D map.
21. Route length calculation.
22. Accumulated cost calculation.
23. Routing error handling.

### Completion criteria

The user can select two valid points and receive a route calculated from the generated cost map.

---

## PHASE 6 — USER-DEFINED GEOGRAPHICAL CONSTRAINTS

### Objective

Allow users to define geographical areas that influence or restrict general-purpose routing.

### Features

1. Polygon drawing.
2. Circular-area creation.
3. Radius configuration.
4. GeoJSON restriction import.
5. Restriction editing.
6. Restriction movement.
7. Restriction resizing.
8. Restriction deletion.
9. Enable/disable controls.
10. Hard constraints.
11. Soft constraints.
12. Map overlays.
13. Start-point validation.
14. Destination validation.
15. Conflict detection.
16. Route recalculation after constraint changes.

### Completion criteria

Users can create, edit and manage geographical restrictions, and the routing engine correctly respects the selected constraint type.

---

## PHASE 7 — MULTIPLE ALTERNATIVE ROUTES

### Objective

Generate and compare multiple distinct route alternatives.

### Features

1. Generate initial A* route.
2. Preserve original cost surface.
3. Implement temporary route penalties.
4. Recalculate alternative routes.
5. Generate multiple alternatives.
6. Detect duplicates.
7. Detect nearly identical routes.
8. Compare route lengths.
9. Compare accumulated costs.
10. Compare terrain characteristics.
11. Calculate route statistics.
12. Display routes with different colours.
13. Allow route selection.
14. Highlight selected alternative.
15. Display comparison panel.

### Completion criteria

The application displays several meaningfully different routes and provides a comparison of their characteristics.

---

## PHASE 8 — 3D TERRAIN VISUALISATION

### Objective

Provide a detailed 3D geographical representation.

### Features

1. Integrate CesiumJS.
2. Load terrain generated from DEM data.
3. Display 3D elevation.
4. Load suitable satellite or aerial imagery.
5. Apply imagery to terrain.
6. Add terrain shading.
7. Render route geometry in 3D.
8. Display start marker.
9. Display destination marker.
10. Display applicable geographical layers.
11. Display geographical restrictions.
12. Implement zoom.
13. Implement rotation.
14. Implement camera tilt.
15. Implement terrain inspection.
16. Add 2D/3D switching.
17. Synchronize selected route between views.

### Completion criteria

Users can inspect the geographical region in 3D and see the generated routes over the terrain.

---

## PHASE 9 — ROUTE ANALYSIS AND STATISTICS

### Objective

Provide detailed information about the generated routes.

### Features

1. Route distance.
2. Accumulated cost.
3. Average slope.
4. Maximum slope.
5. Minimum elevation.
6. Maximum elevation.
7. Average elevation.
8. Elevation gain.
9. Elevation loss.
10. Elevation profile graph.
11. Vegetation statistics.
12. Environmental statistics.
13. Alternative-route comparison.
14. Cost-factor contribution.
15. Route information panel.
16. Export statistics.

### Completion criteria

Users can inspect and compare the characteristics of each route.

---

## PHASE 10 — PROJECT MANAGEMENT, EXPORT AND FINAL TESTING

### Objective

Make the application reliable and ready for demonstration.

### Features

1. Save projects.
2. Reopen projects.
3. Store dataset metadata.
4. Store dataset references.
5. Store layer configuration.
6. Store weight settings.
7. Store selected points.
8. Store geographical restrictions.
9. Store generated route information.
10. Export routes as GeoJSON.
11. Export route statistics.
12. Implement application-wide error handling.
13. Test large raster datasets.
14. Test different CRS systems.
15. Test missing geospatial metadata.
16. Test different raster resolutions.
17. Test cost-map accuracy.
18. Test routing correctness.
19. Test alternative-route uniqueness.
20. Test 2D and 3D visualisation.
21. Test Linux compatibility.
22. Test Windows compatibility.
23. Optimise performance.
24. Complete README.
25. Complete architecture documentation.
26. Prepare final demonstration.
27. Prepare project presentation.

### Completion criteria

The entire application runs on Linux and Windows, passes its essential tests and can demonstrate the complete data-to-route workflow.

---

# 7. DEMONSTRATION DATA REQUIREMENTS

The final demonstration should use a real, publicly available mountainous DEM.

The demonstration dataset should:

- Cover a clearly identifiable mountainous region.
- Have valid geospatial metadata.
- Have sufficient resolution for a meaningful demonstration.
- Have usable elevation values.
- Be available in GeoTIFF format where possible.
- Have a clear licence or permitted usage.
- Be compatible with the supporting imagery source.

For a mountainous-region demonstration, select a suitable non-sensitive public dataset.

Potential data sources to investigate:
- Copernicus DEM.
- NASA SRTM.
- USGS EarthExplorer, where applicable.
- OpenTopography, subject to dataset access and licence conditions.

Remember:

DEM and satellite imagery are different datasets.

The DEM provides elevation and terrain geometry.

Satellite or aerial imagery provides the visual surface.

The final demonstration should show:
1. DEM upload.
2. Automatic metadata recognition.
3. Correct map positioning.
4. Hillshade generation.
5. Additional geographical layers.
6. Cost-map generation.
7. Dynamic cost configuration.
8. Start and destination selection.
9. Route calculation.
10. Alternative routes.
11. Route statistics.
12. 2D and 3D visualisation.

Do not claim that a DEM has satellite-level visual detail by itself.

---

# 8. PROJECT DIRECTORY STRUCTURE

Use a modular structure similar to the following:

terrain-route-planner/

    frontend/
        src/
            components/
                Map/
                Sidebar/
                LayerManager/
                DEMUpload/
                CostControls/
                RouteResults/
                RouteComparison/
                Map3D/

            pages/
            services/
            hooks/
            types/

        public/
        package.json
        vite.config.ts

    backend/
        app/
            api/

            geospatial/
                dem.py
                reprojection.py
                raster_processing.py
                vector_processing.py
                hillshade.py

            cost/
                normalization.py
                cost_surface.py
                cost_layers.py

            routing/
                astar.py
                graph.py
                alternatives.py

            constraints/
                geometry.py
                validation.py

            analysis/
                route_statistics.py
                elevation_profile.py

            projects/
                project_manager.py
                export.py

            services/
            main.py

        tests/
        requirements/

    data/
        uploads/
        processed/
        test_data/

    docs/
        MASTER_PROJECT_SPEC.md
        ARCHITECTURE.md
        IMPLEMENTATION_STATUS.md
        DATA_FORMATS.md

    environment.yml
    .gitignore
    README.md

The exact directory structure can be adjusted as implementation progresses, but maintain clear separation between frontend, backend, geospatial processing, cost calculations and routing.

---

# 9. COPILOT IMPLEMENTATION RULES

Copilot will assist with implementation.

It must not be instructed to generate the entire application in one operation.

Use the following workflow for every phase.

### Step 1: Understand the project

Before implementing anything, inspect:
- MASTER_PROJECT_SPEC.md
- ARCHITECTURE.md
- IMPLEMENTATION_STATUS.md

Understand the existing project structure and completed features.

### Step 2: Plan

Ask Copilot to:
- Identify the feature to implement.
- Identify the files that need modification.
- Identify new dependencies.
- Identify potential compatibility problems.
- Explain how the feature will interact with existing modules.

Do not immediately generate code.

### Step 3: Implement incrementally

Implement one small feature at a time.

Avoid rewriting working modules unnecessarily.

Avoid modifying unrelated files.

### Step 4: Test

Test the feature using actual datasets where appropriate.

Check:
- Expected output.
- Error handling.
- Invalid input.
- Existing functionality.
- Linux compatibility.
- Windows compatibility.

### Step 5: Document

Update:
- IMPLEMENTATION_STATUS.md
- ARCHITECTURE.md, if architecture changes.
- README.md, where appropriate.

### Step 6: Commit

Commit working changes to GitHub.

Only proceed after the feature works.

---

# 10. CROSS-PLATFORM DEVELOPMENT REQUIREMENTS

Every feature must work on both Linux and Windows.

Use:
- Python pathlib for file paths.
- Cross-platform Python libraries.
- Conda-forge for geospatial dependencies.
- Separate frontend and backend environments.
- Environment variables for configurable paths and settings.
- GitHub Actions for automated testing.

Avoid:
- Hardcoded Linux paths.
- Hardcoded Windows paths.
- Linux-only shell commands.
- OS-specific assumptions.
- Conflicting GDAL installations.
- Unnecessary platform-specific dependencies.

Use GitHub Actions to run backend and frontend tests on Linux and Windows.

A feature is not complete until it has passed the applicable cross-platform tests.

---

# 11. PERFORMANCE AND DATA-HANDLING REQUIREMENTS

The application should be designed to handle reasonably large geographical datasets.

Important requirements:

1. Avoid loading unnecessarily large rasters entirely into memory.
2. Use raster windows and block-based processing where appropriate.
3. Preserve source datasets.
4. Cache derived layers when appropriate.
5. Avoid regenerating unchanged cost layers.
6. Recalculate only affected outputs when possible.
7. Validate raster dimensions before processing.
8. Display progress for long-running operations.
9. Handle cancelled processing tasks.
10. Handle insufficient memory and disk space gracefully.
11. Avoid blocking the frontend while backend calculations run.
12. Keep the UI responsive during processing.
13. Use efficient route graph representations.
14. Avoid unnecessarily expensive coordinate transformations.

The system should report the analysis resolution and relevant dataset limitations to the user.

---

# 12. DEVELOPMENT TIMELINE

Suggested initial schedule:

Week 1:
- Phase 1.
- Phase 2.

Week 2:
- Phase 3.

Week 3:
- Phase 4.

Week 4:
- Phase 5.
- Phase 6.

Week 5:
- Phase 7.

Week 6:
- Phase 8.

Week 7:
- Phase 9.
- Phase 10.

This is an approximate schedule. Extend individual phases if the tests reveal issues.

Do not sacrifice correctness to meet the schedule.

---

# 13. FINAL PROJECT DELIVERABLE

The completed project should be a working desktop-browser-accessible web application.

A user should be able to:

1. Open the application.
2. Upload a DEM.
3. Have the application inspect its geographical metadata.
4. See the DEM correctly positioned on the world map.
5. View its elevation and hillshade.
6. Upload vegetation, land-cover, river, water-body and road datasets.
7. Inspect and toggle individual layers.
8. Generate individual cost layers.
9. Combine them into a weighted cost map.
10. Dynamically adjust cost weights.
11. Select starting and ending points.
12. Generate a route using A*.
13. Create and manage geographical restrictions.
14. Generate multiple route alternatives.
15. Compare routes using statistics.
16. View elevation profiles.
17. Switch between 2D and 3D.
18. Inspect the route over detailed terrain and suitable imagery.
19. Save and reopen projects.
20. Export routes and results.

The application must run on both Linux and Windows.

---

# 14. FINAL DEVELOPMENT PRINCIPLES

1. Build incrementally.
2. Prioritise working functionality over visual polish.
3. Validate geographical correctness.
4. Keep source data unchanged.
5. Keep modules independent.
6. Test every phase.
7. Maintain cross-platform compatibility.
8. Document implementation decisions.
9. Commit working milestones to GitHub.
10. Never claim a feature works without testing it.
11. Do not introduce unnecessary technologies.
12. Do not implement future-phase functionality prematurely.
13. Preserve all previously working functionality.
14. Prefer reliable and understandable implementations over unnecessarily complicated algorithms.

The first development milestone is:

UPLOAD A GEOTIFF DEM → READ ITS METADATA → IDENTIFY ITS GEOGRAPHICAL COVERAGE → DISPLAY IT CORRECTLY ON THE 2D MAP → GENERATE AND DISPLAY HILLSHADE.

Everything else should build on this working foundation.
