from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str = "ok"
    application: str = "Terrain-Aware Route Planning and GIS Analysis System"
    api_version: str = "1.0.0"


class ApiInfoResponse(BaseModel):
    application: str = "Terrain-Aware Route Planning and GIS Analysis System"
    api_version: str = "1.0.0"
    docs_url: str = "/docs"