import numpy as np
import rasterio
import pytest
from fastapi.testclient import TestClient
from rasterio.io import MemoryFile
from affine import Affine
from rasterio.transform import from_origin

from app.main import app


def make_dem(
    crs: str | None = "EPSG:32610",
    data: np.ndarray | None = None,
    transform=None,
) -> bytes:
    values = data if data is not None else np.array(
        [[0, 20, 40, 60], [10, 30, 60, 90], [20, 45, 75, -9999]],
        dtype=np.int16,
    )
    with MemoryFile() as memory_file:
        with memory_file.open(
            driver="GTiff",
            width=values.shape[1],
            height=values.shape[0],
            count=1,
            dtype=values.dtype,
            crs=crs,
            transform=transform or from_origin(500000, 4200000, 30, 30),
            nodata=-9999,
        ) as dataset:
            dataset.write(values, 1)
        return memory_file.read()


def create_client(tmp_path, monkeypatch) -> TestClient:
    app.state.dem_storage_dir = tmp_path / "dems"
    app.state.dem_storage_dir.mkdir()
    app.state.dem_max_upload_size = 1024 * 1024
    monkeypatch.setattr("app.api.routes.dem.start_layer_fetches", lambda _: None)
    return TestClient(app)


def upload(client: TestClient, content: bytes, filename: str = "terrain.tif"):
    return client.post("/api/dem/upload", files={"file": (filename, content)})


def test_upload_extracts_projected_metadata_and_nodata_statistics(tmp_path, monkeypatch) -> None:
    with create_client(tmp_path, monkeypatch) as client:
        response = upload(client, make_dem())

        assert response.status_code == 201
        metadata = response.json()
        assert metadata["epsg"] == 32610
        assert metadata["width"] == 4
        assert metadata["height"] == 3
        assert metadata["band_count"] == 1
        assert metadata["original_bounds"] == {
            "west": 500000.0,
            "south": 4199910.0,
            "east": 500120.0,
            "north": 4200000.0,
        }
        assert metadata["geographic_bounds"]["west"] < -123
        assert metadata["geographic_bounds"]["west"] > -124
        assert metadata["elevation"] == {
            "minimum": 0.0,
            "maximum": 90.0,
            "mean": 40.90909090909091,
            "valid_pixel_count": 11,
            "units": None,
        }
        assert len(metadata["footprint"]) >= 4
        assert metadata["processing_status"] == "ready"

        dem_id = metadata["dem_id"]
        assert client.get(f"/api/dem/{dem_id}").json() == metadata
        assert client.get(f"/api/dem/{dem_id}/preview").headers["content-type"] == "image/png"
        hillshade_response = client.get(f"/api/dem/{dem_id}/hillshade")
        assert hillshade_response.headers["content-type"] == "image/tiff"
        with MemoryFile(hillshade_response.content) as hillshade_file:
            with hillshade_file.open() as hillshade:
                assert hillshade.crs.to_epsg() == 32610
                assert hillshade.transform == from_origin(500000, 4200000, 30, 30)
                assert hillshade.count == 1
                assert hillshade.dtypes == ("uint8",)
                shade = hillshade.read(1)
                assert np.unique(shade).size > 1
                assert hillshade.read_masks(1)[2, 3] == 0

            assert (app.state.dem_storage_dir / dem_id / "original.tif").read_bytes() == make_dem()


def test_geographic_crs_and_geographic_bounds(tmp_path, monkeypatch) -> None:
    transform = from_origin(-123.0, 49.0, 0.01, 0.01)
    with create_client(tmp_path, monkeypatch) as client:
        metadata = upload(client, make_dem("EPSG:4326", transform=transform)).json()

        assert metadata["epsg"] == 4326
        assert metadata["geographic_bounds"] == {
            "west": -123.0,
            "south": 48.97,
            "east": -122.96,
            "north": 49.0,
        }


def test_rotated_geotransform_is_preserved_in_footprint_and_hillshade(tmp_path, monkeypatch) -> None:
    transform = Affine.translation(500000, 4200000) @ Affine.rotation(15) @ Affine.scale(30, -30)
    with create_client(tmp_path, monkeypatch) as client:
        metadata = upload(client, make_dem(transform=transform)).json()
        hillshade_response = client.get(f"/api/dem/{metadata['dem_id']}/hillshade")

        assert metadata["transform"]["b"] != 0
        assert metadata["transform"]["d"] != 0
        assert metadata["footprint"][0] == metadata["footprint"][-1]
        with MemoryFile(hillshade_response.content) as hillshade_file:
            with hillshade_file.open() as hillshade:
                assert hillshade.transform == transform
                assert hillshade.crs.to_epsg() == 32610


def test_rejects_bad_extensions_empty_and_corrupted_rasters(tmp_path, monkeypatch) -> None:
    with create_client(tmp_path, monkeypatch) as client:
        assert upload(client, b"not a raster", "terrain.img").status_code == 415
        assert upload(client, b"", "empty.tif").status_code == 400
        assert upload(client, b"not a raster", "broken.tif").status_code == 422


def test_rejects_uploads_over_configured_limit(tmp_path, monkeypatch) -> None:
    with create_client(tmp_path, monkeypatch) as client:
        app.state.dem_max_upload_size = 10
        assert upload(client, make_dem()).status_code == 413


def test_missing_crs_is_reported_without_map_placement(tmp_path, monkeypatch) -> None:
    with create_client(tmp_path, monkeypatch) as client:
        response = upload(client, make_dem(crs=None))

        assert response.status_code == 201
        metadata = response.json()
        assert metadata["crs"] is None
        assert metadata["geographic_bounds"] is None
        assert metadata["processing_status"] == "warning"
        assert "no CRS" in metadata["warning"]
        assert client.get(f"/api/dem/{metadata['dem_id']}/preview").status_code == 409


def test_missing_geotransform_is_reported_without_map_placement(tmp_path, monkeypatch) -> None:
    with create_client(tmp_path, monkeypatch) as client:
        with pytest.warns(rasterio.errors.NotGeoreferencedWarning):
            response = upload(client, make_dem(transform=Affine.identity()))
        metadata = response.json()

        assert metadata["crs"] == "EPSG:32610"
        assert metadata["original_bounds"] is None
        assert metadata["geographic_bounds"] is None
        assert "no usable geotransform" in metadata["warning"]


def test_all_nodata_pixels_produce_warning_without_previews(tmp_path, monkeypatch) -> None:
    values = np.full((3, 4), -9999, dtype=np.int16)
    with create_client(tmp_path, monkeypatch) as client:
        response = upload(client, make_dem(data=values))

        assert response.status_code == 201
        metadata = response.json()
        assert metadata["elevation"]["minimum"] is None
        assert metadata["elevation"]["maximum"] is None
        assert metadata["processing_status"] == "warning"
        assert "no valid elevation pixels" in metadata["warning"]
        assert client.get(f"/api/dem/{metadata['dem_id']}/preview").status_code == 409


def test_rejects_multiband_ambiguous_raster(tmp_path, monkeypatch) -> None:
    values = np.ones((2, 4, 4), dtype=np.uint8)
    with MemoryFile() as memory_file:
        with memory_file.open(
            driver="GTiff", width=4, height=4, count=2, dtype="uint8",
            crs="EPSG:4326", transform=from_origin(0, 4, 1, 1),
        ) as dataset:
            dataset.write(values)
        content = memory_file.read()

    with create_client(tmp_path, monkeypatch) as client:
        response = upload(client, content)
        assert response.status_code == 422
        assert "single-band" in response.json()["detail"]


def test_delete_removes_original_and_generated_files(tmp_path, monkeypatch) -> None:
    with create_client(tmp_path, monkeypatch) as client:
        metadata = upload(client, make_dem()).json()
        dem_directory = app.state.dem_storage_dir / metadata["dem_id"]
        assert (dem_directory / "original.tif").is_file()
        assert (dem_directory / "hillshade.tif").is_file()

        response = client.delete(f"/api/dem/{metadata['dem_id']}")
        assert response.status_code == 204
        assert not dem_directory.exists()
        assert client.get(f"/api/dem/{metadata['dem_id']}").status_code == 404