import { useState } from "react";
import MapView from "./components/Map/MapView";
import Sidebar from "./components/Sidebar/Sidebar";
import { useBackendHealth } from "./hooks/useBackendHealth";
import type { GeographicCoordinates, MapState } from "./types/api";

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
  const [sidebarOpen, setSidebarOpen] = useState(false);

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
            <strong>Terrain Planner</strong>
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
          isOpen={sidebarOpen}
        />
        <section className="map-workspace" aria-label="Map view">
          <MapView
            styleUrl={mapStyle.url}
            configurationError={mapStyle.error}
            baseMapVisible={baseMapVisible}
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