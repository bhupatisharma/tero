import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import type { ComponentProps } from "react";
import { afterEach, describe, expect, it, vi } from "vitest";
import LayerManager from "../LayerManager/LayerManager";
import DemUploadPanel from "./DemUploadPanel";
import type { DemMetadata } from "../../types/api";

afterEach(cleanup);

const dem: DemMetadata = {
  dem_id: "8bcd1f45ba824278a7ed394740f68ab0",
  file_name: "ridge.tif",
  file_size_bytes: 728,
  format: "TIF",
  crs: "EPSG:32610",
  epsg: 32610,
  original_bounds: { west: 500000, south: 4199910, east: 500120, north: 4200000 },
  geographic_bounds: { west: -123.1, south: 37.8, east: -123, north: 37.9 },
  footprint: [[-123.1, 37.9], [-123, 37.9], [-123, 37.8], [-123.1, 37.8], [-123.1, 37.9]],
  transform: { a: 30, b: 0, c: 500000, d: 0, e: -30, f: 4200000 },
  pixel_resolution: [30, 30],
  resolution_units: "metre",
  width: 4,
  height: 3,
  band_count: 1,
  data_type: "int16",
  nodata: -9999,
  elevation: { minimum: 0, maximum: 90, mean: 40.9, valid_pixel_count: 11, units: "m" },
  geographic_coverage: "-123.1, 37.8 to -123, 37.9 (WGS84)",
  processing_status: "ready",
  warning: null,
};

function renderUploadPanel(overrides: Partial<ComponentProps<typeof DemUploadPanel>> = {}) {
  return render(
    <DemUploadPanel
      dem={null}
      isUploading={false}
      progress={0}
      uploadError=""
      removeError=""
      onUpload={vi.fn()}
      onCancelUpload={vi.fn()}
      onRemove={vi.fn()}
      {...overrides}
    />,
  );
}

describe("DEM upload and layer controls", () => {
  it("offers GeoTIFF file selection and sends a supported file", () => {
    const onUpload = vi.fn();
    renderUploadPanel({ onUpload });
    const file = new File(["terrain"], "ridge.tif", { type: "image/tiff" });

    fireEvent.change(screen.getByLabelText("Choose a DEM GeoTIFF"), { target: { files: [file] } });

    expect(onUpload).toHaveBeenCalledWith(file);
  });

  it("reports unsupported file extensions before upload", () => {
    const onUpload = vi.fn();
    renderUploadPanel({ onUpload });
    const file = new File(["data"], "terrain.png", { type: "image/png" });

    fireEvent.change(screen.getByLabelText("Choose a DEM GeoTIFF"), { target: { files: [file] } });

    expect(screen.getByRole("alert").textContent).toContain(".tif or .tiff");
    expect(onUpload).not.toHaveBeenCalled();
  });

  it("shows upload failure feedback", () => {
    renderUploadPanel({ uploadError: "The raster has no valid elevation pixels." });

    expect(screen.getByRole("alert").textContent).toContain("no valid elevation pixels");
  });

  it("shows transfer progress and exposes upload cancellation", () => {
    const onCancelUpload = vi.fn();
    renderUploadPanel({ isUploading: true, progress: 43, onCancelUpload });

    expect(screen.getByRole("progressbar", { name: "DEM upload progress" }).getAttribute("value")).toBe("43");
    fireEvent.click(screen.getByRole("button", { name: "Cancel upload" }));
    expect(onCancelUpload).toHaveBeenCalledOnce();
  });

  it("renders successful DEM metadata and CRS warnings separately", () => {
    renderUploadPanel({ dem });

    expect(screen.getByText("ridge.tif")).toBeTruthy();
    expect(screen.getByText("TIF · 728 B")).toBeTruthy();
    expect(screen.getByText("EPSG:32610")).toBeTruthy();
    expect(screen.getByText("40.9 m")).toBeTruthy();
    expect(screen.getByText("-9,999")).toBeTruthy();
  });

  it("exposes DEM visibility, hillshade visibility, and opacity controls", () => {
    const onDemVisibleChange = vi.fn();
    const onHillshadeVisibleChange = vi.fn();
    const onHillshadeOpacityChange = vi.fn();
    render(
      <LayerManager
        baseMapVisible
        onBaseMapVisibleChange={vi.fn()}
        dem={dem}
        demVisible
        onDemVisibleChange={onDemVisibleChange}
        hillshadeVisible
        onHillshadeVisibleChange={onHillshadeVisibleChange}
        hillshadeOpacity={0.55}
        onHillshadeOpacityChange={onHillshadeOpacityChange}
      />,
    );

    fireEvent.click(screen.getByLabelText("Show DEM layer"));
    fireEvent.click(screen.getByLabelText("Show hillshade layer"));
    fireEvent.change(screen.getByRole("slider", { name: "Hillshade opacity" }), { target: { value: "35" } });

    expect(onDemVisibleChange).toHaveBeenCalledWith(false);
    expect(onHillshadeVisibleChange).toHaveBeenCalledWith(false);
    expect(onHillshadeOpacityChange).toHaveBeenCalledWith(0.35);
  });
});
