import type { HealthResponse } from "../types/health";
import { API_BASE_URL } from "./config";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, { signal });
  if (!response.ok) {
    throw new Error(`Health request failed with HTTP ${response.status}`);
  }
  const payload: unknown = await response.json();
  if (
    typeof payload !== "object" ||
    payload === null ||
    !("status" in payload) ||
    payload.status !== "ok" ||
    !("service" in payload) ||
    typeof payload.service !== "string" ||
    !("version" in payload) ||
    typeof payload.version !== "string" ||
    !("environment" in payload) ||
    typeof payload.environment !== "string" ||
    !("broker_mode" in payload) ||
    (payload.broker_mode !== "backtest" && payload.broker_mode !== "paper")
  ) {
    throw new Error("The health response did not match the expected contract.");
  }
  return payload as HealthResponse;
}

export function describeConnection(health: HealthResponse | null): string {
  return health
    ? `${health.environment} · ${health.broker_mode}`
    : "connecting";
}
