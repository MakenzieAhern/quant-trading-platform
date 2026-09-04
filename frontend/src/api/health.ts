import type { HealthResponse } from "../types/health";

const API_URL = import.meta.env.VITE_API_URL ?? "http://localhost:8000";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${API_URL}/api/health`, { signal });
  if (!response.ok) {
    throw new Error(`Health request failed with HTTP ${response.status}`);
  }
  return (await response.json()) as HealthResponse;
}

export function describeConnection(health: HealthResponse | null): string {
  return health ? `${health.environment} · ${health.broker_mode}` : "connecting";
}
