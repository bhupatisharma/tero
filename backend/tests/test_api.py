from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint_returns_structured_status() -> None:
    response = client.get("/api/health")

    assert response.status_code == 200
    assert response.json() == {
        "status": "ok",
        "application": "Terrain-Aware Route Planning and GIS Analysis System",
        "api_version": "1.0.0",
    }


def test_root_endpoint_returns_api_information() -> None:
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["docs_url"] == "/docs"