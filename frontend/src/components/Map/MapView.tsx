import { useEffect, useRef } from "react";
import { Map as MapLibreMap, Marker, NavigationControl, setWorkerUrl } from "maplibre-gl";
import mapWorkerUrl from "maplibre-gl/dist/maplibre-gl-worker.mjs?url";
import type { GeographicCoordinates, MapState } from "../../types/api";

setWorkerUrl(mapWorkerUrl);

interface MapViewProps {
  styleUrl: string | null;
  configurationError: string | null;
  baseMapVisible: boolean;
  onMapStateChange: (state: MapState, detail?: string) => void;
  onZoomChange: (zoom: number) => void;
  onCursorChange: (coordinates: GeographicCoordinates | null) => void;
  onLocationSelect: (coordinates: GeographicCoordinates) => void;
}

function setBaseMapVisibility(map: MapLibreMap, visible: boolean) {
  map.getCanvas().style.opacity = visible ? "1" : "0";
}

export default function MapView({
  styleUrl,
  configurationError,
  baseMapVisible,
  onMapStateChange,
  onZoomChange,
  onCursorChange,
  onLocationSelect,
}: MapViewProps) {
  const containerRef = useRef<HTMLDivElement>(null);
  const mapRef = useRef<MapLibreMap | null>(null);
  const markerRef = useRef<Marker | null>(null);
  const baseMapVisibleRef = useRef(baseMapVisible);
  const callbacksRef = useRef({ onMapStateChange, onZoomChange, onCursorChange, onLocationSelect });

  useEffect(() => {
    callbacksRef.current = { onMapStateChange, onZoomChange, onCursorChange, onLocationSelect };
  }, [onMapStateChange, onZoomChange, onCursorChange, onLocationSelect]);

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
    callbacksRef.current.onMapStateChange("loading");

    map.on("load", () => {
      styleLoaded = true;
      setBaseMapVisibility(map, baseMapVisibleRef.current);
      callbacksRef.current.onMapStateChange("ready");
      callbacksRef.current.onZoomChange(map.getZoom());
    });
    map.on("error", (event) => {
      if (!styleLoaded) {
        callbacksRef.current.onMapStateChange("error", event.error.message || "Map style failed to load.");
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
    };
  }, [styleUrl, configurationError]);

  useEffect(() => {
    baseMapVisibleRef.current = baseMapVisible;
    const map = mapRef.current;
    if (map) setBaseMapVisibility(map, baseMapVisible);
  }, [baseMapVisible]);

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