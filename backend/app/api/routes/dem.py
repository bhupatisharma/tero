import re
import shutil
import uuid
from pathlib import Path

from fastapi import APIRouter, HTTPException, Request, UploadFile
from fastapi.responses import FileResponse
from starlette.concurrency import run_in_threadpool

from app.models import DemMetadata, SupportingLayerStatus, SupportingLayersResponse
from app.services.dem_processing import DemProcessingError, load_metadata, process_dem
from app.services.layer_cache import LAYER_FILES, fetched_directory, initialize_status, load_status
from app.services.layer_orchestration import fetch_one_layer, start_layer_fetches

router = APIRouter(prefix="/dem", tags=["dem"])
DEM_ID_PATTERN = re.compile(r"^[0-9a-f]{32}$")
UPLOAD_CHUNK_SIZE = 1024 * 1024
ALLOWED_EXTENSIONS = {".tif", ".tiff"}


def _dem_directory(request: Request, dem_id: str) -> Path:
    if not DEM_ID_PATTERN.fullmatch(dem_id):
        raise HTTPException(status_code=404, detail="DEM not found.")
    directory = Path(request.app.state.dem_storage_dir) / dem_id
    if not directory.is_dir():
        raise HTTPException(status_code=404, detail="DEM not found.")
    return directory


@router.post("/upload", response_model=DemMetadata, status_code=201)
async def upload_dem(request: Request, file: UploadFile) -> DemMetadata:
    file_name = Path(file.filename or "").name
    suffix = Path(file_name).suffix.lower()
    if suffix not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=415, detail="Only .tif and .tiff GeoTIFF files are supported.")

    max_upload_size = request.app.state.dem_max_upload_size
    dem_id = uuid.uuid4().hex
    directory = Path(request.app.state.dem_storage_dir) / dem_id
    directory.mkdir(parents=True, exist_ok=False)
    original_path = directory / f"original{suffix}"
    size = 0
    try:
        with original_path.open("wb") as destination:
            while chunk := await file.read(UPLOAD_CHUNK_SIZE):
                size += len(chunk)
                if size > max_upload_size:
                    raise HTTPException(status_code=413, detail="The uploaded file exceeds the configured size limit.")
                destination.write(chunk)
        if size == 0:
            raise HTTPException(status_code=400, detail="The uploaded file is empty.")

        metadata = await run_in_threadpool(
            process_dem, dem_id, file_name, original_path, size, directory
        )
        await run_in_threadpool(start_layer_fetches, directory)
        return metadata
    except DemProcessingError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except HTTPException:
        raise
    except Exception as error:
        raise HTTPException(status_code=500, detail="DEM processing failed.") from error
    finally:
        await file.close()
        if not (directory / "metadata.json").exists():
            shutil.rmtree(directory, ignore_errors=True)


@router.get("/{dem_id}", response_model=DemMetadata)
def get_dem(request: Request, dem_id: str) -> DemMetadata:
    directory = _dem_directory(request, dem_id)
    try:
        return load_metadata(directory)
    except DemProcessingError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error


@router.get("/{dem_id}/preview")
def get_dem_preview(request: Request, dem_id: str, layer: str = "dem") -> FileResponse:
    directory = _dem_directory(request, dem_id)
    if layer not in {"dem", "hillshade"}:
        raise HTTPException(status_code=400, detail="Layer must be 'dem' or 'hillshade'.")
    preview = directory / f"{layer}-preview.png"
    if not preview.is_file():
        raise HTTPException(status_code=409, detail="A map preview is unavailable for this DEM.")
    return FileResponse(preview, media_type="image/png")


@router.get("/{dem_id}/hillshade")
def get_hillshade(request: Request, dem_id: str) -> FileResponse:
    directory = _dem_directory(request, dem_id)
    hillshade = directory / "hillshade.tif"
    if not hillshade.is_file():
        raise HTTPException(status_code=409, detail="Hillshade is unavailable for this DEM.")
    return FileResponse(hillshade, media_type="image/tiff", filename="hillshade.tif")


@router.get("/{dem_id}/layers", response_model=SupportingLayersResponse)
def get_supporting_layers(request: Request, dem_id: str) -> SupportingLayersResponse:
    directory = _dem_directory(request, dem_id)
    status = initialize_status(directory)
    layers = {}
    for name, values in status.items():
        values = dict(values)
        values["name"] = name
        layers[name] = SupportingLayerStatus.model_validate(values)
    return SupportingLayersResponse(dem_id=dem_id, layers=layers)


@router.post("/{dem_id}/layers/{layer}/refresh", response_model=SupportingLayerStatus)
async def refresh_supporting_layer(request: Request, dem_id: str, layer: str) -> SupportingLayerStatus:
    directory = _dem_directory(request, dem_id)
    if layer not in LAYER_FILES:
        raise HTTPException(status_code=404, detail="Supporting layer not found.")
    await run_in_threadpool(fetch_one_layer, directory, layer, True)
    values = load_status(directory).get(layer, {})
    values = dict(values)
    values["name"] = layer
    return SupportingLayerStatus.model_validate(values)


@router.get("/{dem_id}/layers/{layer}/file")
def get_supporting_layer_file(request: Request, dem_id: str, layer: str) -> FileResponse:
    directory = _dem_directory(request, dem_id)
    if layer not in LAYER_FILES:
        raise HTTPException(status_code=404, detail="Supporting layer not found.")
    status = load_status(directory)
    if status.get(layer, {}).get("status") != "available":
        raise HTTPException(status_code=409, detail="Supporting layer is not available.")
    path = fetched_directory(directory) / LAYER_FILES[layer]
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Supporting layer file is unavailable.")
    media_type = "image/tiff" if path.suffix == ".tif" else "application/geo+json"
    return FileResponse(path, media_type=media_type, filename=path.name)


@router.get("/{dem_id}/layers/{layer}/preview")
def get_supporting_layer_preview(request: Request, dem_id: str, layer: str) -> FileResponse:
    directory = _dem_directory(request, dem_id)
    if layer not in {"vegetation", "landcover"}:
        raise HTTPException(status_code=404, detail="This layer has no raster preview.")
    status = load_status(directory)
    if status.get(layer, {}).get("status") != "available":
        raise HTTPException(status_code=409, detail="Supporting layer is not available.")
    raster = fetched_directory(directory) / LAYER_FILES[layer]
    preview = raster.with_suffix(".preview.png")
    if not preview.is_file():
        raise HTTPException(status_code=404, detail="Raster preview is unavailable.")
    return FileResponse(preview, media_type="image/png", filename=preview.name)

  
@router.delete("/{dem_id}", status_code=204)
def delete_dem(request: Request, dem_id: str) -> None:
    directory = _dem_directory(request, dem_id)
    shutil.rmtree(directory)