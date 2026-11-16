import { useState } from "react";
import type { DemMetadata } from "../../types/api";

const MAX_UPLOAD_BYTES = 512 * 1024 * 1024;

interface DemUploadPanelProps {
  dem: DemMetadata | null;
  isUploading: boolean;
  progress: number;
  uploadError: string;
  removeError: string;
  onUpload: (file: File) => void;
  onCancelUpload: () => void;
  onRemove: () => void;
}

function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} B`;
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
  return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
}

function formatNumber(value: number | null, units = ""): string {
  if (value === null) return "Unavailable";
  return `${value.toLocaleString(undefined, { maximumFractionDigits: 2 })}${units ? ` ${units}` : ""}`;
}

function formatBounds(bounds: DemMetadata["geographic_bounds"]): string {
  if (!bounds) return "Unavailable";
  return `${bounds.west.toFixed(5)}, ${bounds.south.toFixed(5)} to ${bounds.east.toFixed(5)}, ${bounds.north.toFixed(5)}`;
}

export default function DemUploadPanel({
  dem,
  isUploading,
  progress,
  uploadError,
  removeError,
  onUpload,
  onCancelUpload,
  onRemove,
}: DemUploadPanelProps) {
  const [validationError, setValidationError] = useState("");
  const [dragging, setDragging] = useState(false);

  const acceptFile = (file?: File) => {
    if (!file) return;
    setValidationError("");
    const extension = file.name.split(".").pop()?.toLowerCase();
    if (extension !== "tif" && extension !== "tiff") {
      setValidationError("Choose a .tif or .tiff GeoTIFF file.");
      return;
    }
    if (file.size === 0) {
      setValidationError("This file is empty.");
      return;
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setValidationError("The maximum upload size is 512 MB.");
      return;
    }
    onUpload(file);
  };

  return (
    <section className="sidebar-section dem-section" aria-labelledby="dem-heading">
      <div className="section-heading">
        <div>
          <span className="section-kicker">02 / TERRAIN</span>
          <h2 id="dem-heading">DEM upload &amp; info</h2>
        </div>
        {dem && <span className={`dem-state dem-state--${dem.processing_status}`}>{dem.processing_status}</span>}
      </div>

      {!isUploading && (
        <label
          className={`dem-dropzone${dragging ? " dem-dropzone--active" : ""}`}
          onDragOver={(event) => { event.preventDefault(); setDragging(true); }}
          onDragLeave={() => setDragging(false)}
          onDrop={(event) => {
            event.preventDefault();
            setDragging(false);
            acceptFile(event.dataTransfer.files[0]);
          }}
        >
          <input
            aria-label="Choose a DEM GeoTIFF"
            type="file"
            accept=".tif,.tiff,image/tiff"
            onChange={(event) => {
              acceptFile(event.target.files?.[0]);
              event.currentTarget.value = "";
            }}
          />
          <span className="dem-upload-mark" aria-hidden="true">↑</span>
          <strong>{dem ? "Drop a GeoTIFF to replace this DEM" : "Drop a GeoTIFF here"}</strong>
          <small>or browse files · .tif / .tiff · up to 512 MB</small>
        </label>
      )}

      {isUploading && (
        <div className="dem-progress" role="status" aria-live="polite">
          <div className="dem-progress-copy">
            <strong>{progress < 100 ? "Uploading DEM" : "Inspecting raster and generating hillshade"}</strong>
            <span>{progress < 100 ? `${progress}%` : "Processing"}</span>
          </div>
          <progress aria-label="DEM upload progress" max="100" value={progress} />
          <button type="button" className="text-button" onClick={onCancelUpload}>Cancel upload</button>
        </div>
      )}

      {(validationError || uploadError || removeError) && (
        <p className="dem-error" role="alert">{validationError || uploadError || removeError}</p>
      )}

      {dem && (
        <>
          <div className="dem-file-row">
            <div className="dem-file-icon" aria-hidden="true">TIF</div>
            <div className="dem-file-copy">
              <strong title={dem.file_name}>{dem.file_name}</strong>
              <small>{dem.format} · {formatBytes(dem.file_size_bytes)}</small>
            </div>
            <button type="button" className="text-button" onClick={onRemove} aria-label="Remove uploaded DEM">Remove</button>
          </div>

          {dem.warning && <p className="dem-warning" role="status">{dem.warning}</p>}

          <div className="dem-metadata-group">
            <h3>Geographic information</h3>
            <dl>
              <div><dt>CRS</dt><dd>{dem.crs ?? "Unavailable"}</dd></div>
              <div><dt>EPSG</dt><dd>{dem.epsg ?? "Unavailable"}</dd></div>
              <div><dt>WGS84 bounds</dt><dd>{formatBounds(dem.geographic_bounds)}</dd></div>
              <div><dt>Original bounds</dt><dd>{formatBounds(dem.original_bounds)}</dd></div>
              <div><dt>Pixel resolution</dt><dd>{dem.pixel_resolution ? `${formatNumber(dem.pixel_resolution[0])} × ${formatNumber(dem.pixel_resolution[1])} ${dem.resolution_units ?? "CRS units"}` : "Unavailable"}</dd></div>
            </dl>
          </div>

          <div className="dem-metadata-group">
            <h3>Elevation &amp; raster</h3>
            <dl>
              <div><dt>Minimum</dt><dd>{formatNumber(dem.elevation.minimum, dem.elevation.units ?? "")}</dd></div>
              <div><dt>Maximum</dt><dd>{formatNumber(dem.elevation.maximum, dem.elevation.units ?? "")}</dd></div>
              <div><dt>Mean</dt><dd>{formatNumber(dem.elevation.mean, dem.elevation.units ?? "")}</dd></div>
              <div><dt>Dimensions</dt><dd>{dem.width.toLocaleString()} × {dem.height.toLocaleString()}</dd></div>
              <div><dt>NoData</dt><dd>{dem.nodata === null ? "Unavailable" : formatNumber(dem.nodata)}</dd></div>
            </dl>
          </div>
        </>
      )}
    </section>
  );
}
