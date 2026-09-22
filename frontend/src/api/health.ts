import type { HealthResponse } from "../types/health";
import { apiRequest } from "./client";

export async function getHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const payload = await apiRequest<unknown>("/api/health", {}, signal);
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
