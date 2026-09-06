import { API_BASE_URL } from "./config";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function safeErrorMessage(status: number, payload: unknown): string {
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = payload.detail;
    if (typeof detail === "string") return detail;
    if (
      typeof detail === "object" &&
      detail !== null &&
      "message" in detail &&
      typeof detail.message === "string"
    ) {
      return detail.message;
    }
  }
  if (status === 422) return "Please check the submitted values.";
  return `The API request failed (HTTP ${status}).`;
}

export async function apiRequest<T>(
  path: string,
  init: RequestInit = {},
  signal?: AbortSignal,
): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
    ...init,
    signal,
    headers: {
      Accept: "application/json",
      ...init.headers,
    },
  });
  if (!response.ok) {
    let payload: unknown;
    try {
      payload = await response.json();
    } catch {
      payload = null;
    }
    throw new ApiError(
      response.status,
      safeErrorMessage(response.status, payload),
    );
  }
  return (await response.json()) as T;
}
