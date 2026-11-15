import { afterEach, describe, expect, it, vi } from "vitest";
import { API_BASE_URL, fetchHealth } from "./api";

const healthPayload = {
  status: "ok",
  application: "Terrain-Aware Route Planning and GIS Analysis System",
  api_version: "1.0.0",
};

afterEach(() => vi.unstubAllGlobals());

describe("fetchHealth", () => {
  it("returns the structured backend health response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify(healthPayload), { status: 200 }),
    ));

    await expect(fetchHealth(new AbortController().signal)).resolves.toEqual(healthPayload);
    expect(fetch).toHaveBeenCalledWith(`${API_BASE_URL}/api/health`, expect.objectContaining({
      headers: { Accept: "application/json" },
    }));
  });

  it("reports an unsuccessful API response", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(new Response(null, { status: 503 })));

    await expect(fetchHealth(new AbortController().signal)).rejects.toThrow("HTTP 503");
  });

  it("rejects malformed health payloads", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(
      new Response(JSON.stringify({ status: "ok" }), { status: 200 }),
    ));

    await expect(fetchHealth(new AbortController().signal)).rejects.toThrow("invalid health response");
  });
});