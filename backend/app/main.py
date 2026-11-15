import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.models import ApiInfoResponse

APP_NAME = "Terrain-Aware Route Planning and GIS Analysis System"
API_VERSION = "1.0.0"

app = FastAPI(title=APP_NAME, version=API_VERSION)

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
    allow_methods=["GET"],
    allow_headers=["*"],
)

app.include_router(api_router)


@app.get("/", response_model=ApiInfoResponse)
def get_api_info() -> ApiInfoResponse:
    return ApiInfoResponse()