import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.models import ApiInfoResponse

APP_NAME = "TERO"
API_VERSION = "1.0.0"

app = FastAPI(title=APP_NAME, version=API_VERSION)
app.state.dem_storage_dir = Path(os.getenv("DEM_STORAGE_DIR", "backend/data/dems"))
app.state.dem_max_upload_size = int(os.getenv("DEM_MAX_UPLOAD_SIZE_MB", "512")) * 1024 * 1024

allowed_origins = [
    origin.strip()
    for origin in os.getenv(
        "CORS_ORIGINS", "http://localhost:5173,http://127.0.0.1:5173"
    ).split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST", "DELETE"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", response_model=ApiInfoResponse)
def get_api_info() -> ApiInfoResponse:
    return ApiInfoResponse()