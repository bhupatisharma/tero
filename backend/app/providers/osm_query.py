from __future__ import annotations

from multiprocessing import get_context
from pathlib import Path
from tempfile import TemporaryDirectory
from threading import Lock

import geopandas as gpd
import osmnx as ox
from shapely import wkt
from shapely.geometry import Polygon


OSM_QUERY_TIMEOUT_SECONDS = 90
_query_lock = Lock()


def _query_worker(
    polygon_wkt: str,
    tags: dict[str, bool | str | list[str]],
    output_path: str,
    connection,
) -> None:
    try:
        ox.settings.overpass_rate_limit = False
        ox.settings.requests_timeout = 30
        ox.settings.overpass_settings = "[out:json][timeout:45]"
        features = ox.features_from_polygon(wkt.loads(polygon_wkt), tags)
        if features is None or features.empty:
            connection.send((0, None))
        else:
            features.to_file(output_path, driver="GeoJSON")
            connection.send((len(features), None))
    except Exception as error:
        connection.send((0, f"{type(error).__name__}: {error}"))
    finally:
        connection.close()


def query_osm_features(
    polygon: Polygon,
    tags: dict[str, bool | str | list[str]],
    label: str,
) -> gpd.GeoDataFrame:
    with TemporaryDirectory(prefix="tero-osm-") as directory:
        output_path = Path(directory) / "features.geojson"
        context = get_context("spawn")
        receiver, sender = context.Pipe(duplex=False)
        process = context.Process(
            target=_query_worker,
            args=(polygon.wkt, tags, str(output_path), sender),
        )
        with _query_lock:
            process.start()
            sender.close()
            process.join(OSM_QUERY_TIMEOUT_SECONDS)
            if process.is_alive():
                process.terminate()
                process.join(5)
                if process.is_alive():
                    process.kill()
                    process.join()
                receiver.close()
                raise TimeoutError(
                    f"OpenStreetMap {label} query timed out after "
                    f"{OSM_QUERY_TIMEOUT_SECONDS} seconds"
                )

        if not receiver.poll():
            receiver.close()
            raise RuntimeError(
                f"OpenStreetMap {label} query worker exited unexpectedly "
                f"(exit code {process.exitcode})"
            )
        feature_count, error = receiver.recv()
        receiver.close()
        if error:
            raise RuntimeError(f"OpenStreetMap {label} query failed: {error}")
        if not feature_count:
            raise ValueError(f"No {label} features were found in OpenStreetMap")

        frame = gpd.read_file(output_path)
        if frame.crs is None:
            frame = frame.set_crs("EPSG:4326")
        elif frame.crs.to_epsg() != 4326:
            frame = frame.to_crs("EPSG:4326")
        return frame
