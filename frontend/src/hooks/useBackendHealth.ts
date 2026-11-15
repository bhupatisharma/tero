import { useEffect, useState } from "react";
import { fetchHealth } from "../services/api";
import type { BackendHealth } from "../types/api";

const INITIAL_HEALTH: BackendHealth = {
  state: "checking",
  detail: "Checking backend connection",
};

export function useBackendHealth(): BackendHealth {
  const [health, setHealth] = useState(INITIAL_HEALTH);

  useEffect(() => {
    const controller = new AbortController();
    let active = true;

    const check = async () => {
      try {
        const result = await fetchHealth(controller.signal);
        if (active) {
          setHealth({
            state: "connected",
            detail: "Connected",
            application: result.application,
            apiVersion: result.api_version,
          });
        }
      } catch (error) {
        if (!active || (error instanceof DOMException && error.name === "AbortError")) return;
        setHealth({
          state: "offline",
          detail: error instanceof Error ? error.message : "Backend request failed.",
        });
      }
    };

    void check();
    const intervalId = window.setInterval(() => void check(), 15000);

    return () => {
      active = false;
      controller.abort();
      window.clearInterval(intervalId);
    };
  }, []);

  return health;
}