export interface HealthResponse {
  status: string;
  application: string;
  api_version: string;
}

export type ConnectionState = "checking" | "connected" | "offline";

export interface BackendHealth {
  state: ConnectionState;
  detail: string;
  application?: string;
  apiVersion?: string;
}

export interface GeographicCoordinates {
  longitude: number;
  latitude: number;
}

export type MapState = "loading" | "ready" | "error";

export interface DemBounds {
  west: number;
  south: number;
  east: number;
  north: number;
}

export interface DemMetadata {
  dem_id: string;
  file_name: string;
  file_size_bytes: number;
  format: string;
  crs: string | null;
  epsg: number | null;
  original_bounds: DemBounds | null;
  geographic_bounds: DemBounds | null;
  footprint: [number, number][] | null;
  transform: { a: number; b: number; c: number; d: number; e: number; f: number } | null;
  pixel_resolution: [number, number] | null;
  resolution_units: string | null;
  width: number;
  height: number;
  band_count: number;
  data_type: string;
  nodata: number | null;
  elevation: {
    minimum: number | null;
    maximum: number | null;
    mean: number | null;
    valid_pixel_count: number;
    units: string | null;
  };
  geographic_coverage: string | null;
  processing_status: "ready" | "warning";
  warning: string | null;
}

export type SupportingLayerStatusName =
  | "pending" | "fetching" | "processing" | "available" | "partial" | "unavailable" | "failed";

export interface SupportingLayerStatus {
  name: string;
  status: SupportingLayerStatusName;
  source: string;
  licence?: string | null;
  fetched_at?: string | null;
  crs?: string | null;
  bounds?: number[] | null;
  feature_count?: number | null;
  scene_count?: number | null;
  file_name?: string | null;
  metadata?: Record<string, unknown> | null;
  error?: string | null;
}

export interface SupportingLayersResponse {
  dem_id: string;
  layers: Record<string, SupportingLayerStatus>;
}