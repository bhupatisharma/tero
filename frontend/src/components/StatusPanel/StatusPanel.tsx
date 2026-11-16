import type { BackendHealth, MapState } from "../../types/api";

interface StatusPanelProps {
  backend: BackendHealth;
  mapState: MapState;
  mapDetail: string;
}

function StatusIndicator({ state, label }: { state: "ready" | "loading" | "error"; label: string }) {
  return (
    <span className={`status-indicator status-indicator--${state}`}>
      <span className="status-dot" />
      {label}
    </span>
  );
}

export default function StatusPanel({ backend, mapState, mapDetail }: StatusPanelProps) {
  const backendState = backend.state === "connected" ? "ready" : backend.state === "offline" ? "error" : "loading";
  const backendLabel = backend.state === "connected" ? "Connected" : backend.state === "offline" ? "Unavailable" : "Checking";

  return (
    <section className="sidebar-section status-section" aria-labelledby="status-heading">
      <div className="section-heading">
        <div>
          <span className="section-kicker">03 / SYSTEM</span>
          <h2 id="status-heading">Project status</h2>
        </div>
      </div>
      <div className="status-list">
        <div className="status-row">
          <span>Frontend</span>
          <StatusIndicator state="ready" label="Online" />
        </div>
        <div className="status-row" title={backend.detail}>
          <span>Backend API</span>
          <StatusIndicator state={backendState} label={backendLabel} />
        </div>
        <div className="status-row" title={mapDetail || undefined}>
          <span>Map renderer</span>
          <StatusIndicator state={mapState} label={mapState === "ready" ? "Ready" : mapState === "error" ? "Error" : "Loading"} />
        </div>
      </div>
      {backend.state === "offline" && <p className="status-detail" role="status">{backend.detail}</p>}
      {mapState === "error" && <p className="status-detail status-detail--error" role="alert">{mapDetail}</p>}
    </section>
  );
}