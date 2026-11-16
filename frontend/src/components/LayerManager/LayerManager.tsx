import type { DemMetadata } from "../../types/api";

interface LayerManagerProps {
  baseMapVisible: boolean;
  onBaseMapVisibleChange: (visible: boolean) => void;
  dem: DemMetadata | null;
  demVisible: boolean;
  onDemVisibleChange: (visible: boolean) => void;
  hillshadeVisible: boolean;
  onHillshadeVisibleChange: (visible: boolean) => void;
  hillshadeOpacity: number;
  onHillshadeOpacityChange: (opacity: number) => void;
}

export default function LayerManager({
  baseMapVisible,
  onBaseMapVisibleChange,
  dem,
  demVisible,
  onDemVisibleChange,
  hillshadeVisible,
  onHillshadeVisibleChange,
  hillshadeOpacity,
  onHillshadeOpacityChange,
}: LayerManagerProps) {
  return (
    <section className="sidebar-section" aria-labelledby="layers-heading">
      <div className="section-heading">
        <div>
          <span className="section-kicker">01 / DATA</span>
          <h2 id="layers-heading">Layers</h2>
        </div>
        <span className="section-count">{dem?.geographic_bounds && dem.elevation.valid_pixel_count > 0 ? "03" : "01"}</span>
      </div>
      <label className="layer-row">
        <span className="layer-swatch" aria-hidden="true" />
        <span className="layer-name">
          <strong>Base map</strong>
          <small>MapLibre style</small>
        </span>
        <input
          aria-label="Show base map"
          type="checkbox"
          checked={baseMapVisible}
          onChange={(event) => onBaseMapVisibleChange(event.target.checked)}
        />
      </label>
      {dem?.geographic_bounds && dem.elevation.valid_pixel_count > 0 && (
        <>
          <label className="layer-row">
            <span className="layer-swatch layer-swatch--dem" aria-hidden="true" />
            <span className="layer-name">
              <strong>DEM · {dem.file_name}</strong>
              <small>Elevation preview</small>
            </span>
            <input
              aria-label="Show DEM layer"
              type="checkbox"
              checked={demVisible}
              onChange={(event) => onDemVisibleChange(event.target.checked)}
            />
          </label>
          <label className="layer-row">
            <span className="layer-swatch layer-swatch--hillshade" aria-hidden="true" />
            <span className="layer-name">
              <strong>Hillshade</strong>
              <small>Calculated from elevation</small>
            </span>
            <input
              aria-label="Show hillshade layer"
              type="checkbox"
              checked={hillshadeVisible}
              onChange={(event) => onHillshadeVisibleChange(event.target.checked)}
            />
          </label>
          <label className="opacity-control">
            <span>Hillshade opacity</span>
            <output>{Math.round(hillshadeOpacity * 100)}%</output>
            <input
              aria-label="Hillshade opacity"
              type="range"
              min="0"
              max="100"
              step="5"
              value={Math.round(hillshadeOpacity * 100)}
              onChange={(event) => onHillshadeOpacityChange(Number(event.target.value) / 100)}
            />
          </label>
        </>
      )}
    </section>
  );
}