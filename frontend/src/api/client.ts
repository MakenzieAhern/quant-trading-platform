import { API_BASE_URL } from "./config";

export const REQUEST_TIMEOUT_MS = 15_000;

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    message: string,
    public readonly code?: string | null,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function safeError(
  status: number,
  payload: unknown,
): { message: string; code: string | null } {
  if (typeof payload === "object" && payload !== null && "code" in payload) {
    const code = typeof payload.code === "string" ? payload.code : null;
    const message =
      "message" in payload && typeof payload.message === "string"
        ? payload.message
        : `The API request failed (HTTP ${status}).`;
    return { message, code };
  }
  if (typeof payload === "object" && payload !== null && "detail" in payload) {
    const detail = payload.detail;
    if (typeof detail === "string") return { message: detail, code: null };
    if (
      typeof detail === "object" &&
      detail !== null &&
      "message" in detail &&
      typeof detail.message === "string"
    ) {
      return { message: detail.message, code: null };
    }
  }
  if (status === 422)
    return { message: "Please check the submitted values.", code: null };
  return { message: `The API request failed (HTTP ${status}).`, code: null };
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
    const error = safeError(response.status, payload);
    throw new ApiError(response.status, error.message, error.code);
  }
  let payload: unknown;
  try {
    payload = await response.json();
  } catch {
    throw new ApiError(502, "The API returned an invalid JSON response.");
  }
  return parse ? parse(payload) : (payload as T);
}
