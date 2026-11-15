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