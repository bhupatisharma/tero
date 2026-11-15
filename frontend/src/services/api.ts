import type { HealthResponse } from "../types/api";

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