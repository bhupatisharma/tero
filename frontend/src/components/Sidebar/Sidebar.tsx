import LayerManager from "../LayerManager/LayerManager";
import DemUploadPanel from "./DemUploadPanel";
import StatusPanel from "../StatusPanel/StatusPanel";
import type { BackendHealth, DemMetadata, GeographicCoordinates, MapState, SupportingLayersResponse } from "../../types/api";

interface SidebarProps {
  backend: BackendHealth;
  mapState: MapState;
  mapDetail: string;
  zoom: number;
  selectedCoordinates: GeographicCoordinates | null;
  cursorCoordinates: GeographicCoordinates | null;
  baseMapVisible: boolean;
  onBaseMapVisibleChange: (visible: boolean) => void;
  dem: DemMetadata | null;
  demUploading: boolean;
  demProgress: number;
  demUploadError: string;
  demRemoveError: string;
  onDemUpload: (file: File) => void;
  onDemUploadCancel: () => void;
  onDemRemove: () => void;
  demVisible: boolean;
  onDemVisibleChange: (visible: boolean) => void;
  hillshadeVisible: boolean;
  onHillshadeVisibleChange: (visible: boolean) => void;
  hillshadeOpacity: number;
  onHillshadeOpacityChange: (opacity: number) => void;
  supportingLayers: SupportingLayersResponse | null;
  supportingVisibility: Record<string, boolean>;
  onSupportingVisibilityChange: (name: string, visible: boolean) => void;
  supportingOpacity: Record<string, number>;
  onSupportingOpacityChange: (name: string, opacity: number) => void;
  isOpen: boolean;
}

function CoordinateReadout({ coordinates }: { coordinates: GeographicCoordinates | null }) {
  if (!coordinates) return <span className="coordinate-value coordinate-value--empty">Click map to select</span>;
  return (
    <span className="coordinate-value">
      {Math.abs(coordinates.latitude).toFixed(5)}° {coordinates.latitude < 0 ? "S" : "N"},{" "}
      {Math.abs(coordinates.longitude).toFixed(5)}° {coordinates.longitude < 0 ? "W" : "E"}
    </span>
  );
}

export default function Sidebar(props: SidebarProps) {
  return (
    <aside className={`sidebar${props.isOpen ? " sidebar--open" : ""}`} aria-label="Map workspace controls">
      <section className="sidebar-section map-controls" aria-labelledby="map-controls-heading">
        <div className="section-heading">
          <div>
            <span className="section-kicker">00 / VIEW</span>
            <h2 id="map-controls-heading">Map controls</h2>
          </div>
          <span className="map-index">2D</span>
        </div>
        <div className="metric-row">
          <span>Current zoom</span>
          <strong>{props.zoom.toFixed(1)} <small>×</small></strong>
        </div>
        <div className="coordinate-block">
          <span className="field-label">Selected coordinates</span>
          <CoordinateReadout coordinates={props.selectedCoordinates} />
        </div>
        <div className="coordinate-block coordinate-block--cursor">
          <span className="field-label">Cursor position</span>
          <CoordinateReadout coordinates={props.cursorCoordinates} />
        </div>
      </section>
      <LayerManager
        baseMapVisible={props.baseMapVisible}
        onBaseMapVisibleChange={props.onBaseMapVisibleChange}
        dem={props.dem}
        demVisible={props.demVisible}
        onDemVisibleChange={props.onDemVisibleChange}
        hillshadeVisible={props.hillshadeVisible}
        onHillshadeVisibleChange={props.onHillshadeVisibleChange}
        hillshadeOpacity={props.hillshadeOpacity}
        onHillshadeOpacityChange={props.onHillshadeOpacityChange}
        supportingLayers={props.supportingLayers}
        supportingVisibility={props.supportingVisibility}
        onSupportingVisibilityChange={props.onSupportingVisibilityChange}
        supportingOpacity={props.supportingOpacity}
        onSupportingOpacityChange={props.onSupportingOpacityChange}
      />
      <DemUploadPanel
        dem={props.dem}
        isUploading={props.demUploading}
        progress={props.demProgress}
        uploadError={props.demUploadError}
        removeError={props.demRemoveError}
        onUpload={props.onDemUpload}
        onCancelUpload={props.onDemUploadCancel}
        onRemove={props.onDemRemove}
      />
      <StatusPanel backend={props.backend} mapState={props.mapState} mapDetail={props.mapDetail} />
      <div className="sidebar-footer">
        <span className="footer-rule" />
        <span>TERO / GEOGRAPHICAL DATA / PHASE 03</span>
      </div>
    </aside>
  );
}