import json
from datetime import datetime, timezone
from pathlib import Path
from threading import RLock
from uuid import uuid4


_STATUS_LOCK = RLock()
_PROCESS_INSTANCE_ID = uuid4().hex
_IN_PROGRESS_STATUSES = {"fetching", "processing"}

LAYER_FILES = {
    "vegetation": "ndvi.tif",
    "landcover": "landcover.tif",
    "rivers": "rivers.geojson",
    "water_bodies": "water_bodies.geojson",
    "roads": "roads.geojson",
}


def fetched_directory(dem_directory: Path) -> Path:
    return dem_directory / "fetched"


def status_path(dem_directory: Path) -> Path:
    return fetched_directory(dem_directory) / "status.json"


def initialize_status(dem_directory: Path) -> dict:
    directory = fetched_directory(dem_directory)
    directory.mkdir(parents=True, exist_ok=True)
    with _STATUS_LOCK:
        current = load_status(dem_directory)
        sources = {
            "vegetation": "Sentinel-2 L2A",
            "landcover": "ESA WorldCover",
            "rivers": "OpenStreetMap",
            "water_bodies": "OpenStreetMap",
            "roads": "OpenStreetMap",
        }
        for name, source in sources.items():
            row = current.setdefault(name, {"name": name, "status": "pending", "source": source})
            row.setdefault("name", name)
            row["source"] = source
            if (
                row.get("status") in _IN_PROGRESS_STATUSES
                and row.get("worker_instance") != _PROCESS_INSTANCE_ID
            ):
                row.update(
                    status="failed",
                    error="The previous fetch was interrupted; refresh this layer to retry.",
                    file_name=None,
                    licence=None,
                    fetched_at=None,
                    crs=None,
                    bounds=None,
                    feature_count=None,
                    scene_count=None,
                    metadata=None,
                    worker_instance=None,
                    updated_at=datetime.now(timezone.utc).isoformat(),
                )
        save_status(dem_directory, current)
        return current


def load_status(dem_directory: Path) -> dict:
    path = status_path(dem_directory)
    if not path.is_file():
        return {}
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
        return value if isinstance(value, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def save_status(dem_directory: Path, status: dict) -> None:
    path = status_path(dem_directory)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary_path = path.with_suffix(path.suffix + ".tmp")
    with _STATUS_LOCK:
        temporary_path.write_text(json.dumps(status, indent=2), encoding="utf-8")
        temporary_path.replace(path)


def update_status(dem_directory: Path, name: str, **values) -> dict:
    with _STATUS_LOCK:
        status = load_status(dem_directory)
        status.setdefault(name, {"name": name, "status": "pending", "source": name})
        layer_status = values.get("status")
        if layer_status in _IN_PROGRESS_STATUSES:
            values.setdefault("worker_instance", _PROCESS_INSTANCE_ID)
        elif layer_status:
            values.setdefault("worker_instance", None)
        values.setdefault("updated_at", datetime.now(timezone.utc).isoformat())
        status[name].update(values)
        save_status(dem_directory, status)
        return status
