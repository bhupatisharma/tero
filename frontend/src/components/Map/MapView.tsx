import { useEffect, useRef } from "react";
import { Map as MapLibreMap, Marker, NavigationControl, setWorkerUrl } from "maplibre-gl";
import mapWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import { demPreviewUrl } from "../../services/api";
import type { DemMetadata, GeographicCoordinates, MapState } from "../../types/api";

setWorkerUrl(mapWorkerUrl);

interface MapViewProps {
  styleUrl: string | null;
  configurationError: string | null;
  baseMapVisible: boolean;
  dem: DemMetadata | null;
  demVisible: boolean;
  hillshadeVisible: boolean;
  hillshadeOpacity: number;
  onMapStateChange: (state: MapState, detail?: string) => void;
  onZoomChange: (zoom: number) => void;
  onCursorChange: (coordinates: GeographicCoordinates | null) => void;
  onLocationSelect: (coordinates: GeographicCoordinates) => void;
}

function setBaseMapVisibility(map: MapLibreMap, visible: boolean) {
  const managedLayers = new Set(["dem-raster", "hillshade-raster", "dem-footprint"]);
  for (const layer of map.getStyle()?.layers ?? []) {
    if (!managedLayers.has(layer.id)) {
      map.setLayoutProperty(layer.id, "visibility", visible ? "visible" : "none");
    }
  }
}

function removeDemLayers(map: MapLibreMap) {
  for (const layerId of ["dem-footprint", "hillshade-raster", "dem-raster"]) {
    if (map.getLayer(layerId)) map.removeLayer(layerId);
  }
  for (const sourceId of ["hillshade-image", "dem-image", "dem-footprint-data"]) {
    if (map.getSource(sourceId)) map.removeSource(sourceId);
  }
}

function addDemLayers(map: MapLibreMap, dem: DemMetadata | null) {
  removeDemLayers(map);
  if (
    !dem?.geographic_bounds ||
    !dem.footprint ||
    dem.footprint.length < 4 ||
    dem.elevation.valid_pixel_count === 0
  ) return false;

  const bounds = dem.geographic_bounds;
  const coordinates: [[number, number], [number, number], [number, number], [number, number]] = [
    [bounds.west, bounds.north],
    [bounds.east, bounds.north],
    [bounds.east, bounds.south],
    [bounds.west, bounds.south],
  ];
  map.addSource("dem-image", {
    type: "image",
    url: demPreviewUrl(dem.dem_id, "dem"),
    coordinates,
  });
  map.addLayer({
    id: "dem-raster",
    type: "raster",
    source: "dem-image",
    paint: { "raster-opacity": 0.48, "raster-resampling": "linear" },
  });
  map.addSource("hillshade-image", {
    type: "image",
    url: demPreviewUrl(dem.dem_id, "hillshade"),
    coordinates,
  });
  map.addLayer({
    id: "hillshade-raster",
    type: "raster",
    source: "hillshade-image",
    paint: { "raster-opacity": 0.55, "raster-resampling": "linear" },
  });
  map.addSource("dem-footprint-data", {
    type: "geojson",
    data: {
      type: "Feature",
      properties: {},
      geometry: { type: "Polygon", coordinates: [dem.footprint] },
    },
  });
  map.addLayer({
    id: "dem-footprint",
    type: "line",
    source: "dem-footprint-data",
    paint: { "line-color": "#d85d3e", "line-width": 2 },
  });
  map.fitBounds(
    [[bounds.west, bounds.south], [bounds.east, bounds.north]],
    { padding: 48, maxZoom: 12, duration: 700 },
  );
  return true;
}

function applyDemVisibility(
  map: MapLibreMap,
  demVisible: boolean,
  hillshadeVisible: boolean,
  hillshadeOpacity: number,
) {
  if (map.getLayer("dem-raster")) {
    map.setLayoutProperty("dem-raster", "visibility", demVisible ? "visible" : "none");
  }
  if (map.getLayer("hillshade-raster")) {
    map.setLayoutProperty("hillshade-raster", "visibility", hillshadeVisible ? "visible" : "none");
    map.setPaintProperty("hillshade-raster", "raster-opacity", hillshadeOpacity);
  }
  if (map.getLayer("dem-footprint")) {
    map.setLayoutProperty("dem-footprint", "visibility", demVisible ? "visible" : "none");
  }
}

export default function MapView({
  styleUrl,
  configurationError,
  baseMapVisible,
  dem,
  demVisible,
  hillshadeVisible,
  hillshadeOpacity,
  onMapStateChange,
  onZoomChange,
  onCursorChange,
  onLocationSelect,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const baseMapVisibleRef = useRef(baseMapVisible);
  const demRef = useRef(dem);
  const demVisibleRef = useRef(demVisible);
  const hillshadeVisibleRef = useRef(hillshadeVisible);
  const hillshadeOpacityRef = useRef(hillshadeOpacity);
  const styleLoadedRef = useRef(false);
  const callbacksRef = useRef({ onMapStateChange, onZoomChange, onCursorChange, onLocationSelect });

  useEffect(() => {
    callbacksRef.current = { onMapStateChange, onZoomChange, onCursorChange, onLocationSelect };
  }, [onMapStateChange, onZoomChange, onCursorChange, onLocationSelect]);

  useEffect(() => {
    demRef.current = dem;
    demVisibleRef.current = demVisible;
    hillshadeVisibleRef.current = hillshadeVisible;
    hillshadeOpacityRef.current = hillshadeOpacity;
  }, [dem, demVisible, hillshadeVisible, hillshadeOpacity]);

  useEffect(() => {
    const container = containerRef.current;
    if (!container) return;

    if (configurationError || !styleUrl) {
      callbacksRef.current.onMapStateChange("error", configurationError ?? "Map style is not configured.");
      return;
    }

    let map: MapLibreMap;
    try {
      map = new MapLibreMap({
        container,
        style: styleUrl,
        center: [-98.5, 39.5],
        zoom: 3.5,
        minZoom: 1,
        maxZoom: 18,
        cooperativeGestures: true,
      });
      map.addControl(new NavigationControl({ showCompass: true }), "top-right");
      mapRef.current = map;
    } catch (error) {
      const detail = error instanceof Error ? error.message : "Map initialization failed.";
      callbacksRef.current.onMapStateChange("error", detail);
      return;
    }

    let styleLoaded = false;
    styleLoadedRef.current = false;
    callbacksRef.current.onMapStateChange("loading");

    map.on("load", () => {
      styleLoaded = true;
      styleLoadedRef.current = true;
      setBaseMapVisibility(map, baseMapVisibleRef.current);
      addDemLayers(map, demRef.current);
      applyDemVisibility(map, demVisibleRef.current, hillshadeVisibleRef.current, hillshadeOpacityRef.current);
      callbacksRef.current.onMapStateChange("ready");
      callbacksRef.current.onZoomChange(map.getZoom());
    });
    map.on("error", (event) => {
      if (!styleLoaded) {
        callbacksRef.current.onMapStateChange("error", event.error.message || "Map style failed to load.");
      } else if (
        "sourceId" in event &&
        (event.sourceId === "dem-image" || event.sourceId === "hillshade-image")
      ) {
        callbacksRef.current.onMapStateChange("error", "A DEM map preview failed to load.");
      }
    });
    map.on("mousemove", (event) => {
      callbacksRef.current.onCursorChange({
        longitude: event.lngLat.lng,
        latitude: event.lngLat.lat,
      });
    });
    map.on("mouseout", () => callbacksRef.current.onCursorChange(null));
    map.on("click", (event) => {
      const coordinates = { longitude: event.lngLat.lng, latitude: event.lngLat.lat };
      callbacksRef.current.onLocationSelect(coordinates);
      markerRef.current?.remove();
      markerRef.current = new Marker({ color: "#d85d3e" })
        .setLngLat([coordinates.longitude, coordinates.latitude])
        .addTo(map);
    });
    map.on("zoomend", () => callbacksRef.current.onZoomChange(map.getZoom()));

    const resizeObserver = new ResizeObserver(() => map.resize());
    resizeObserver.observe(container);

    return () => {
      resizeObserver.disconnect();
      markerRef.current?.remove();
      markerRef.current = null;
      map.remove();
      mapRef.current = null;
      styleLoadedRef.current = false;
    };
  }, [styleUrl, configurationError]);

  useEffect(() => {
    baseMapVisibleRef.current = baseMapVisible;
    const map = mapRef.current;
    if (map) setBaseMapVisibility(map, baseMapVisible);
  }, [baseMapVisible]);

  useEffect(() => {
    const map = mapRef.current;
    if (!map || !styleLoadedRef.current) return;
    addDemLayers(map, dem);
    applyDemVisibility(map, demVisible, hillshadeVisible, hillshadeOpacity);
  }, [dem]);

  useEffect(() => {
    const map = mapRef.current;
    if (map && styleLoadedRef.current) {
      applyDemVisibility(map, demVisible, hillshadeVisible, hillshadeOpacity);
    }
  }, [demVisible, hillshadeVisible, hillshadeOpacity]);

  return (
    <div className="map-frame" aria-label="Interactive map">
      <div className="map-canvas" ref={containerRef} />
      {configurationError && (
        <div className="map-message map-message--error" role="alert">
          <strong>Map configuration issue</strong>
          <span>{configurationError}</span>
        </div>
      )}
    </div>
  );
}