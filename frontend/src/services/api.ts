import type { DemMetadata, HealthResponse } from "../types/api";

const DEFAULT_API_URL = "http://127.0.0.1:8000";

function resolveApiUrl(configuredUrl: string | undefined): string {
  const value = configuredUrl?.trim() || DEFAULT_API_URL;

  try {
    const url = new URL(value);
    if (url.protocol !== "http:" && url.protocol !== "https:") {
      throw new Error("Use an http or https URL.");
    }
    return url.toString().replace(/\/$/, "");
  } catch {
    throw new Error("Backend URL is invalid. Set VITE_API_BASE_URL to an http(s) URL.");
  }
}

let apiBaseUrl = "";
let apiConfigurationError: string | null = null;
try {
  apiBaseUrl = resolveApiUrl(import.meta.env.VITE_API_BASE_URL);
} catch (error) {
  apiConfigurationError = error instanceof Error ? error.message : "Backend URL is invalid.";
}
export const API_BASE_URL = apiBaseUrl;

function isHealthResponse(value: unknown): value is HealthResponse {
  if (typeof value !== "object" || value === null) return false;
  const response = value as Record<string, unknown>;
  return (
    typeof response.status === "string" &&
    typeof response.application === "string" &&
    typeof response.api_version === "string"
  );
}

export async function fetchHealth(signal: AbortSignal): Promise<HealthResponse> {
  if (apiConfigurationError) throw new Error(apiConfigurationError);

  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}/api/health`, {
      headers: { Accept: "application/json" },
      signal,
    });
  } catch (error) {
    if (error instanceof DOMException && error.name === "AbortError") throw error;
    throw new Error(`Cannot reach the backend at ${API_BASE_URL}.`);
  }

  if (!response.ok) {
    throw new Error(`Backend health check failed (HTTP ${response.status}).`);
  }

  const body: unknown = await response.json();
  if (!isHealthResponse(body) || body.status !== "ok") {
    throw new Error("Backend returned an invalid health response.");
  }
  return body;
}

function isDemMetadata(value: unknown): value is DemMetadata {
  if (typeof value !== "object" || value === null) return false;
  const metadata = value as Partial<DemMetadata>;
  return (
    typeof metadata.dem_id === "string" &&
    typeof metadata.file_name === "string" &&
    typeof metadata.width === "number" &&
    typeof metadata.height === "number" &&
    typeof metadata.elevation === "object" &&
    metadata.elevation !== null
  );
}

export function uploadDem(
  file: File,
  signal: AbortSignal,
  onProgress: (progress: number) => void,
): Promise<DemMetadata> {
  if (apiConfigurationError) return Promise.reject(new Error(apiConfigurationError));

  return new Promise((resolve, reject) => {
    const request = new XMLHttpRequest();
    const formData = new FormData();
    formData.append("file", file);
    request.open("POST", `${API_BASE_URL}/api/dem/upload`);
    request.setRequestHeader("Accept", "application/json");
    request.upload.addEventListener("progress", (event) => {
      if (event.lengthComputable) onProgress(Math.round((event.loaded / event.total) * 100));
    });
    request.addEventListener("load", () => {
      let body: unknown;
      try {
        body = JSON.parse(request.responseText);
      } catch {
        reject(new Error("Backend returned an invalid DEM response."));
        return;
      }
      if (request.status < 200 || request.status >= 300) {
        const detail = typeof body === "object" && body !== null && "detail" in body
          ? String((body as { detail: unknown }).detail)
          : `DEM upload failed (HTTP ${request.status}).`;
        reject(new Error(detail));
        return;
      }
      if (!isDemMetadata(body)) {
        reject(new Error("Backend returned incomplete DEM metadata."));
        return;
      }
      resolve(body);
    });
    request.addEventListener("error", () => reject(new Error("Cannot reach the backend.")));
    request.addEventListener("abort", () => reject(new DOMException("Upload cancelled.", "AbortError")));
    signal.addEventListener("abort", () => request.abort(), { once: true });
    request.send(formData);
  });
}

export async function deleteDem(demId: string): Promise<void> {
  if (apiConfigurationError) throw new Error(apiConfigurationError);
  const response = await fetch(`${API_BASE_URL}/api/dem/${encodeURIComponent(demId)}`, {
    method: "DELETE",
    headers: { Accept: "application/json" },
  });
  if (!response.ok) throw new Error(`DEM removal failed (HTTP ${response.status}).`);
}

export function demPreviewUrl(demId: string, layer: "dem" | "hillshade"): string {
  return `${API_BASE_URL}/api/dem/${encodeURIComponent(demId)}/preview?layer=${layer}`;
}