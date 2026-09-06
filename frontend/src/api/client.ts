import { API_BASE_URL } from "./config";

export const REQUEST_TIMEOUT_MS = 15_000;

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
  parse?: (payload: unknown) => T,
): Promise<T> {
  const timeoutController = new AbortController();
  const timeout = window.setTimeout(
    () => timeoutController.abort(),
    REQUEST_TIMEOUT_MS,
  );
  const requestSignal = signal
    ? AbortSignal.any([signal, timeoutController.signal])
    : timeoutController.signal;
  let response: Response;
  try {
    response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      signal: requestSignal,
      headers: {
        Accept: "application/json",
        ...init.headers,
      },
    });
  } catch (reason) {
    if (timeoutController.signal.aborted && !signal?.aborted) {
      throw new ApiError(408, "The API request timed out.");
    }
    throw reason;
  } finally {
    window.clearTimeout(timeout);
  }
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
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError(502, "The API returned an invalid JSON response.");
  }
  return parse ? parse(payload) : (payload as T);
}
