import type { HealthResponse } from "../types/health";
import { API_BASE_URL } from "./config";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_BASE_URL}/api/health`, { signal });
  if (!response.ok) {
    throw new Error(`Health request failed with HTTP ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}

export function describeConnection(health: HealthResponse | null): string {
  return health
    ? `${health.environment} · ${health.broker_mode}`
    : "connecting";
}
