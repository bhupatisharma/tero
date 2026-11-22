import { useEffect, useRef, useState } from "react";
import MapView from "./components/Map/MapView";
import Sidebar from "./components/Sidebar/Sidebar";
import { useBackendHealth } from "./hooks/useBackendHealth";
import { deleteDem, fetchSupportingLayers, uploadDem } from "./services/api";
import type { DemMetadata, GeographicCoordinates, MapState, SupportingLayersResponse } from "./types/api";

const DEFAULT_MAP_STYLE = "https://tiles.openfreemap.org/styles/liberty";

function resolveMapStyle(configuredStyle: string | undefined): { url: string | null; error: string | null } {
  const value = configuredStyle === undefined ? DEFAULT_MAP_STYLE : configuredStyle.trim();
  if (!value) return { url: null, error: "VITE_MAP_STYLE_URL is set but empty. Provide a valid style URL." };

  try {
    const url = new URL(value);
    if (url.protocol !== "http:" && url.protocol !== "https:") throw new Error("Invalid protocol");
    return { url: value, error: null };
  } catch {
    return { url: null, error: "VITE_MAP_STYLE_URL must be a valid http(s) URL." };
  }
}

const mapStyle = resolveMapStyle(import.meta.env.VITE_MAP_STYLE_URL);

export default function App() {
  const backend = useBackendHealth();
  const [mapState, setMapState] = useState<MapState>("loading");
  const [mapDetail, setMapDetail] = useState("");
  const [zoom, setZoom] = useState(3.5);
  const [selectedCoordinates, setSelectedCoordinates] = useState<GeographicCoordinates | null>(null);
  const [cursorCoordinates, setCursorCoordinates] = useState<GeographicCoordinates | null>(null);
  const [baseMapVisible, setBaseMapVisible] = useState(true);
  const [dem, setDem] = useState<DemMetadata | null>(null);
  const [demUploading, setDemUploading] = useState(false);
  const [demProgress, setDemProgress] = useState(0);
  const [demUploadError, setDemUploadError] = useState("");
  const [demRemoveError, setDemRemoveError] = useState("");
  const [demVisible, setDemVisible] = useState(true);
  const [hillshadeVisible, setHillshadeVisible] = useState(true);
  const [hillshadeOpacity, setHillshadeOpacity] = useState(0.55);
  const [supportingLayers, setSupportingLayers] = useState<SupportingLayersResponse | null>(null);
  const [supportingVisibility, setSupportingVisibility] = useState<Record<string, boolean>>({
    vegetation: true,
    landcover: true,
    rivers: true,
    water_bodies: true,
    roads: true,
  });
  const [supportingOpacity, setSupportingOpacity] = useState<Record<string, number>>({
    vegetation: 0.75,
    landcover: 0.65,
    rivers: 0.9,
    water_bodies: 0.75,
    roads: 0.9,
  });
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const uploadControllerRef = useRef<AbortController | null>(null);

  useEffect(() => {
    if (!dem) {
      setSupportingLayers(null);
      return;
    }
    let cancelled = false;
    const poll = async () => {
      try {
        const result = await fetchSupportingLayers(dem.dem_id);
        if (!cancelled) setSupportingLayers(result);
      } catch {
        if (!cancelled) setSupportingLayers(null);
      }
    };
    void poll();
    const interval = window.setInterval(() => {
      void poll();
    }, 3000);
    return () => {
      cancelled = true;
      window.clearInterval(interval);
    };
  }, [dem]);

  const handleDemUpload = async (file: File) => {
    uploadControllerRef.current?.abort();
    const controller = new AbortController();
    uploadControllerRef.current = controller;
    setDemUploadError("");
    setDemUploading(true);
    setDemProgress(0);
    try {
      const uploadedDem = await uploadDem(file, controller.signal, setDemProgress);
      const previousDem = dem;
      setDem(uploadedDem);
      if (previousDem) void deleteDem(previousDem.dem_id).catch(() => undefined);
      setDemVisible(true);
      setHillshadeVisible(true);
    } catch (error) {
      if (!(error instanceof DOMException && error.name === "AbortError")) {
        setDemUploadError(error instanceof Error ? error.message : "DEM upload failed.");
      }
    } finally {
      if (uploadControllerRef.current === controller) {
        uploadControllerRef.current = null;
        setDemUploading(false);
      }
    }
  };

  const handleDemRemove = async () => {
    if (!dem) return;
    setDemRemoveError("");
    try {
      await deleteDem(dem.dem_id);
      setDem(null);
    } catch (error) {
      setDemRemoveError(error instanceof Error ? error.message : "DEM removal failed.");
    }
  };

  const updateMapState = (state: MapState, detail = "") => {
    setMapState(state);
    setMapDetail(detail);
  };

  return (
    <main className="application-shell">
      <header className="topbar">
        <div className="brand-lockup">
          <button
            className="mobile-menu-button"
            type="button"
            aria-label={sidebarOpen ? "Close workspace controls" : "Open workspace controls"}
            aria-expanded={sidebarOpen}
            onClick={() => setSidebarOpen((open) => !open)}
          >
            <span /><span /><span />
          </button>
          <span className="brand-mark" aria-hidden="true"><span /></span>
          <div className="brand-text">
            <strong>TERO</strong>
            <span>GIS ANALYSIS WORKSPACE</span>
          </div>
        </div>
        <div className="topbar-meta">
          <span className="project-label">UNTITLED PROJECT</span>
          <span className={`connection-badge connection-badge--${backend.state}`}>
            <span className="status-dot" />
            {backend.state === "connected" ? "API CONNECTED" : backend.state === "offline" ? "API OFFLINE" : "CONNECTING"}
          </span>
        </div>
      </header>
      <div className="workspace">
        <Sidebar
          backend={backend}
          mapState={mapState}
          mapDetail={mapDetail}
          zoom={zoom}
          selectedCoordinates={selectedCoordinates}
          cursorCoordinates={cursorCoordinates}
          baseMapVisible={baseMapVisible}
          onBaseMapVisibleChange={setBaseMapVisible}
          dem={dem}
          demUploading={demUploading}
          demProgress={demProgress}
          demUploadError={demUploadError}
          demRemoveError={demRemoveError}
          onDemUpload={(file) => void handleDemUpload(file)}
          onDemUploadCancel={() => uploadControllerRef.current?.abort()}
          onDemRemove={() => void handleDemRemove()}
          demVisible={demVisible}
          onDemVisibleChange={setDemVisible}
          hillshadeVisible={hillshadeVisible}
          onHillshadeVisibleChange={setHillshadeVisible}
          hillshadeOpacity={hillshadeOpacity}
          onHillshadeOpacityChange={setHillshadeOpacity}
          supportingLayers={supportingLayers}
          supportingVisibility={supportingVisibility}
          onSupportingVisibilityChange={(name, visible) =>
            setSupportingVisibility((current) => ({ ...current, [name]: visible }))
          }
          supportingOpacity={supportingOpacity}
          onSupportingOpacityChange={(name, opacity) =>
            setSupportingOpacity((current) => ({ ...current, [name]: opacity }))
          }
          isOpen={sidebarOpen}
        />
        <section className="map-workspace" aria-label="Map view">
          <MapView
            styleUrl={mapStyle.url}
            configurationError={mapStyle.error}
            baseMapVisible={baseMapVisible}
            dem={dem}
            demVisible={demVisible}
            hillshadeVisible={hillshadeVisible}
            hillshadeOpacity={hillshadeOpacity}
            supportingLayers={supportingLayers}
            supportingVisibility={supportingVisibility}
            supportingOpacity={supportingOpacity}
            onMapStateChange={updateMapState}
            onZoomChange={setZoom}
            onCursorChange={setCursorCoordinates}
            onLocationSelect={setSelectedCoordinates}
          />
          <div className="map-readout" aria-live="polite">
            <span className="readout-icon" aria-hidden="true">+</span>
            {selectedCoordinates ? (
              <span>PIN <strong>{selectedCoordinates.latitude.toFixed(4)}, {selectedCoordinates.longitude.toFixed(4)}</strong></span>
            ) : (
              <span>CLICK MAP TO INSPECT COORDINATES</span>
            )}
          </div>
          <span className="map-corner-note">BASE LAYER / {baseMapVisible ? "ON" : "OFF"}</span>
        </section>
      </div>
    </main>
  );
}