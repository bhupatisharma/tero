interface LayerManagerProps {
  baseMapVisible: boolean;
  onBaseMapVisibleChange: (visible: boolean) => void;
}

export default function LayerManager({ baseMapVisible, onBaseMapVisibleChange }: LayerManagerProps) {
  return (
    <section className="sidebar-section" aria-labelledby="layers-heading">
      <div className="section-heading">
        <div>
          <span className="section-kicker">01 / DATA</span>
          <h2 id="layers-heading">Layers</h2>
        </div>
        <span className="section-count">01</span>
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
      <div className="layer-empty">
        <span className="empty-mark" aria-hidden="true">+</span>
        <p>No geographical datasets uploaded</p>
        <small>Raster and vector layers will appear here.</small>
      </div>
    </section>
  );
}