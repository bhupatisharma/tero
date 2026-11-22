from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

import geopandas as gpd
import numpy as np
import pytest
import rasterio
from rasterio.transform import from_origin
from shapely.geometry import LineString, box

from app.providers import hydrography, osm_query, roads, vegetation
from app.services.layer_cache import initialize_status, load_status, status_path, update_status
from app.services.layer_orchestration import fetch_one_layer


def write_raster(
    path: Path,
    values: np.ndarray,
    *,
    nodata: int | float | None = None,
) -> None:
    with rasterio.open(
        path,
        "w",
        driver="GTiff",
        width=values.shape[1],
        height=values.shape[0],
        count=1,
        dtype=values.dtype,
        crs="EPSG:4326",
        transform=from_origin(73.0, 20.0, 0.01, 0.01),
        nodata=nodata,
    ) as dataset:
        dataset.write(values, 1)


def test_ndvi_writes_georeferenced_data_and_masks_nonclear_scl(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dem = tmp_path / "dem.tif"
    red = tmp_path / "red.tif"
    nir = tmp_path / "nir.tif"
    scl = tmp_path / "scl.tif"
    output = tmp_path / "ndvi.tif"
    write_raster(dem, np.ones((4, 4), dtype=np.int16))
    write_raster(red, np.full((4, 4), 1000, dtype=np.uint16), nodata=0)
    write_raster(nir, np.full((4, 4), 3000, dtype=np.uint16), nodata=0)
    scl_values = np.full((4, 4), 4, dtype=np.uint8)
    scl_values[0, 1] = 9
    scl_values[0, 2] = 0
    write_raster(scl, scl_values, nodata=0)

    item = SimpleNamespace(
        id="local-test-scene",
        assets={
            "B04": SimpleNamespace(href=str(red)),
            "B08": SimpleNamespace(href=str(nir)),
            "SCL": SimpleNamespace(href=str(scl)),
        },
    )

    class Search:
        def items(self):
            return iter([item])

    class Catalog:
        def search(self, **kwargs):
            assert kwargs["max_items"] == vegetation.MAX_SCENES
            return Search()

    def open_catalog(url, stac_io):
        assert url == vegetation.STAC_URL
        assert stac_io.timeout == (5, 20)
        return Catalog()

    monkeypatch.setattr(vegetation.Client, "open", open_catalog)
    monkeypatch.setattr(vegetation.planetary_computer, "sign", lambda value: value)

    metadata = vegetation.fetch_ndvi(dem, output)

    assert output.is_file()
    assert metadata["scene_count"] == 1
    assert metadata["crs"] == "EPSG:4326"
    with rasterio.open(output) as dataset:
        values = dataset.read(1)
        assert dataset.crs.to_epsg() == 4326
        assert dataset.bounds == rasterio.coords.BoundingBox(73.0, 19.96, 73.04, 20.0)
        assert np.isclose(values[0, 0], 0.5)
        assert values[0, 1] == dataset.nodata
        assert values[0, 2] == dataset.nodata


def test_osm_providers_query_full_footprint_and_write_geojson(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dem = tmp_path / "dem.tif"
    write_raster(dem, np.ones((4, 4), dtype=np.int16))
    footprint = box(73.0, 19.96, 73.04, 20.0)
    line = LineString([(73.005, 19.98), (73.035, 19.98)])
    frames = gpd.GeoDataFrame(
        {"name": ["interior river"], "geometry": [line]},
        crs="EPSG:4326",
    )
    calls = []

    def fake_query(*query):
        calls.append(query)
        return frames

    monkeypatch.setattr(hydrography, "query_osm_features", fake_query)
    output = tmp_path / "rivers.geojson"

    metadata = hydrography.fetch_rivers(dem, output)

    assert len(calls) == 1
    assert calls[0][0].bounds == footprint.bounds
    assert calls[0][2] == "river"
    assert output.is_file()
    assert metadata["crs"] == "EPSG:4326"
    assert metadata["feature_count"] == 1
    result = gpd.read_file(output)
    assert result.crs.to_epsg() == 4326
    assert result.total_bounds[0] <= 73.005
    assert result.total_bounds[2] >= 73.035
    assert result.geometry.iloc[0].intersects(box(73.019, 19.97, 73.021, 19.99))


def test_roads_reuse_complete_footprint_query(tmp_path: Path, monkeypatch) -> None:
    dem = tmp_path / "dem.tif"
    write_raster(dem, np.ones((4, 4), dtype=np.int16))
    frames = gpd.GeoDataFrame(
        {"highway": ["residential"], "geometry": [LineString([(73.01, 19.97), (73.03, 19.99)])]},
        crs="EPSG:4326",
    )
    calls = []
    monkeypatch.setattr(
        hydrography,
        "query_osm_features",
        lambda polygon, tags, label: calls.append((polygon, tags, label)) or frames,
    )
    output = tmp_path / "roads.geojson"

    metadata = roads.fetch_roads(dem, output)

    assert calls[0][0].bounds == (73.0, 19.96, 73.04, 20.0)
    assert calls[0][1] == {"highway": True}
    assert calls[0][2] == "road"
    assert metadata["feature_count"] == 1
    assert gpd.read_file(output).crs.to_epsg() == 4326


def test_water_bodies_write_valid_geojson(tmp_path: Path, monkeypatch) -> None:
    dem = tmp_path / "dem.tif"
    write_raster(dem, np.ones((4, 4), dtype=np.int16))
    frames = gpd.GeoDataFrame(
        {"natural": ["water"], "geometry": [box(73.01, 19.97, 73.03, 19.99)]},
        crs="EPSG:4326",
    )
    calls = []
    monkeypatch.setattr(
        hydrography,
        "query_osm_features",
        lambda *query: calls.append(query) or frames,
    )
    output = tmp_path / "water_bodies.geojson"

    metadata = hydrography.fetch_water_bodies(dem, output)

    assert calls[0][0].bounds == (73.0, 19.96, 73.04, 20.0)
    assert calls[0][2] == "water-body"
    assert metadata["feature_count"] == 1
    result = gpd.read_file(output)
    assert result.crs.to_epsg() == 4326
    assert result.geometry.iloc[0].area > 0


def test_osm_worker_returns_provider_error(monkeypatch, tmp_path: Path) -> None:
    class Connection:
        message = None

        def send(self, value):
            self.message = value

        def close(self):
            pass

    def fail_query(polygon, tags):
        raise ConnectionError(f"network unreachable for {polygon.area} area and {len(tags)} tag")

    connection = Connection()
    monkeypatch.setattr(osm_query.ox.settings, "overpass_rate_limit", True)
    monkeypatch.setattr(osm_query.ox.settings, "requests_timeout", 180)
    monkeypatch.setattr(osm_query.ox.settings, "overpass_settings", "[out:json][timeout:180]")
    monkeypatch.setattr(osm_query.ox, "features_from_polygon", fail_query)

    osm_query._query_worker(
        box(73.0, 19.96, 73.04, 20.0).wkt,
        {"highway": True},
        str(tmp_path / "roads.geojson"),
        connection,
    )

    assert connection.message[0] == 0
    assert connection.message[1].startswith("ConnectionError: network unreachable")


def test_osm_worker_serializes_geojson_with_crs(monkeypatch, tmp_path: Path) -> None:
    class Connection:
        message = None

        def send(self, value):
            self.message = value

        def close(self):
            pass

    frames = gpd.GeoDataFrame(
        {"highway": ["residential"], "geometry": [LineString([(73.01, 19.97), (73.03, 19.99)])]},
        crs="EPSG:4326",
    )

    def return_features(polygon, tags):
        assert polygon.is_valid
        assert tags == {"highway": True}
        return frames

    monkeypatch.setattr(osm_query.ox.settings, "overpass_rate_limit", True)
    monkeypatch.setattr(osm_query.ox.settings, "requests_timeout", 180)
    monkeypatch.setattr(osm_query.ox.settings, "overpass_settings", "[out:json][timeout:180]")
    monkeypatch.setattr(osm_query.ox, "features_from_polygon", return_features)
    output = tmp_path / "roads.geojson"
    connection = Connection()

    osm_query._query_worker(
        box(73.0, 19.96, 73.04, 20.0).wkt,
        {"highway": True},
        str(output),
        connection,
    )

    assert connection.message == (1, None)
    result = gpd.read_file(output)
    assert result.crs.to_epsg() == 4326
    assert result.geometry.iloc[0].length > 0


def test_osm_query_timeout_terminates_worker(monkeypatch) -> None:
    class Connection:
        def close(self):
            pass

        def poll(self):
            return False

    class Process:
        alive = True
        terminated = False

        def start(self):
            pass

        def join(self, timeout=None):
            self.join_timeouts.append(timeout)

        def is_alive(self):
            return self.alive

        def terminate(self):
            self.terminated = True
            self.alive = False

        def kill(self):
            self.alive = False

    class Context:
        def Pipe(self, duplex):
            assert duplex is False
            return Connection(), Connection()

        def Process(self, **kwargs):
            assert kwargs["target"] is osm_query._query_worker
            return process

    process = Process()
    process.join_timeouts = []

    def get_context(method):
        assert method == "spawn"
        return Context()

    monkeypatch.setattr(osm_query, "get_context", get_context)
    monkeypatch.setattr(osm_query, "OSM_QUERY_TIMEOUT_SECONDS", 1)

    with pytest.raises(TimeoutError, match="timed out after 1 seconds"):
        osm_query.query_osm_features(
            box(73.0, 19.96, 73.04, 20.0),
            {"highway": True},
            "road",
        )

    assert process.terminated
    assert process.join_timeouts == [1, 5]


def test_interrupted_layer_work_is_reported_as_failed(tmp_path: Path) -> None:
    fetched = tmp_path / "fetched"
    fetched.mkdir()
    status_path(tmp_path).write_text(
        '{"vegetation":{"name":"vegetation","status":"processing","source":"Sentinel-2"}}',
        encoding="utf-8",
    )

    status = initialize_status(tmp_path)

    assert status["vegetation"]["status"] == "failed"
    assert "interrupted" in status["vegetation"]["error"]


def test_provider_network_error_transitions_to_failed(
    tmp_path: Path,
    monkeypatch,
) -> None:
    dem = tmp_path / "dem"
    dem.mkdir()
    write_raster(dem / "original.tif", np.ones((4, 4), dtype=np.int16))

    def fail_fetch(*_args):
        assert _args[0].name == "original.tif"
        assert _args[1].name == "ndvi.tif"
        raise ConnectionError("network unreachable")

    monkeypatch.setattr("app.services.layer_orchestration.fetch_ndvi", fail_fetch)

    result = fetch_one_layer(dem, "vegetation")

    assert result["status"] == "failed"
    assert result["error"] == "ConnectionError: network unreachable"
    assert result["file_name"] is None


def test_corrupt_cached_metadata_transitions_to_failed(tmp_path: Path) -> None:
    directory = tmp_path / "dem"
    fetched = directory / "fetched"
    fetched.mkdir(parents=True)
    (directory / "original.tif").touch()
    (fetched / "ndvi.tif").touch()
    (fetched / "ndvi.tif.json").write_text("{invalid", encoding="utf-8")

    result = fetch_one_layer(directory, "vegetation")

    assert result["status"] == "failed"
    assert result["error"].startswith("JSONDecodeError:")


def test_concurrent_status_updates_do_not_overwrite_each_other(tmp_path: Path) -> None:
    from concurrent.futures import ThreadPoolExecutor

    initialize_status(tmp_path)
    with ThreadPoolExecutor(max_workers=5) as executor:
        list(
            executor.map(
                lambda name: update_status(tmp_path, name, status="failed", error=name),
                ("vegetation", "landcover", "rivers", "water_bodies", "roads"),
            )
        )

    status = load_status(tmp_path)
    assert all(status[name]["error"] == name for name in status)
