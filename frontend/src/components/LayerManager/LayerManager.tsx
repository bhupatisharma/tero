import { useState } from "react";
import { refreshSupportingLayer } from "../../services/api";
import type { DemMetadata, SupportingLayersResponse } from "../../types/api";

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
  supportingLayers?: SupportingLayersResponse | null;
  supportingVisibility?: Record<string, boolean>;
  onSupportingVisibilityChange?: (name: string, visible: boolean) => void;
  supportingOpacity?: Record<string, number>;
  onSupportingOpacityChange?: (name: string, opacity: number) => void;
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
  supportingLayers = null,
  supportingVisibility = {},
  onSupportingVisibilityChange = () => undefined,
  supportingOpacity = {},
  onSupportingOpacityChange = () => undefined,
}: LayerManagerProps) {
  const [refreshing, setRefreshing] = useState<string | null>(null);
  const labels: Record<string, string> = {
    vegetation: "Vegetation (NDVI)",
    landcover: "Land cover",
    rivers: "Rivers",
    water_bodies: "Water bodies",
    roads: "Roads",
  };
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
          {supportingLayers && Object.entries(supportingLayers.layers).map(([name, layer]) => (
            <div className="supporting-layer" key={name}>
              <label className="layer-row">
                <span className={`layer-swatch layer-swatch--${name}`} aria-hidden="true" />
                <span className="layer-name">
                  <strong>{labels[name] ?? name}</strong>
                  <small>{layer.status === "available" ? layer.source : `${layer.status}${layer.error ? ` · ${layer.error}` : ""}`}</small>
                </span>
                <input
                  aria-label={`Show ${labels[name] ?? name} layer`}
                  type="checkbox"
                  checked={supportingVisibility[name] ?? true}
                  disabled={layer.status !== "available"}
                  onChange={(event) => onSupportingVisibilityChange(name, event.target.checked)}
                />
              </label>
              {layer.status === "available" && (
                <>
                  <label className="opacity-control">
                    <span>{labels[name]} opacity</span>
                    <output>{Math.round((supportingOpacity[name] ?? 0.75) * 100)}%</output>
                    <input
                      aria-label={`${labels[name]} opacity`}
                      type="range"
                      min="0"
                      max="100"
                      step="5"
                      value={Math.round((supportingOpacity[name] ?? 0.75) * 100)}
                      onChange={(event) => onSupportingOpacityChange(name, Number(event.target.value) / 100)}
                    />
                  </label>
                  <details className="layer-metadata">
                    <summary>Metadata</summary>
                    <span>CRS: {layer.crs ?? "unknown"}</span>
                    {layer.feature_count != null && <span>Features: {layer.feature_count}</span>}
                    {layer.scene_count != null && <span>Scenes: {layer.scene_count}</span>}
                    {layer.fetched_at && <span>Fetched: {layer.fetched_at}</span>}
                    {layer.licence && <span>Licence: {layer.licence}</span>}
                  </details>
                </>
              )}
              <button
                className="layer-refresh"
                type="button"
                disabled={refreshing === name}
                onClick={() => {
                  if (!dem) return;
                  setRefreshing(name);
                  void refreshSupportingLayer(dem.dem_id, name)
                    .finally(() => setRefreshing(null));
                }}
              >
                {refreshing === name ? "Refreshing..." : "Refresh"}
              </button>
            </div>
          ))}
        </>
      )}
    </section>
  );
}