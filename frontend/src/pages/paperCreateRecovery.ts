import type { CreatePaperSessionRequest } from "../types/paper";

export const PAPER_CREATE_PENDING_PREFIX =
  "quant.product.paper-create-pending.v1.";

export class PendingPaperCreateError extends Error {}

export interface PendingPaperCreate {
  version: 1;
  body: string;
  key: string;
  savedAt: string;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
// ponytail: 20 unresolved intents fit a personal workstation; raise only with a recovery UI for larger queues.
const MAX_PENDING = 20;

export function paperRequestFromBody(body: string): CreatePaperSessionRequest {
  if (body.length > 8192) throw new Error("Invalid saved paper request");
  const value: unknown = JSON.parse(body);
  if (!value || typeof value !== "object" || Array.isArray(value))
    throw new Error("Invalid saved paper request");
  const request = value as Record<string, unknown>;
  const strategy = request.strategy;
  const risk = request.risk;
  if (
    !["replay", "simulated_a_share", "historical_a_share"].includes(
      String(request.provider_type),
    ) ||
    typeof request.dataset_id !== "string" ||
    typeof request.symbol !== "string" ||
    typeof request.initial_cash !== "string" ||
    typeof request.default_order_quantity !== "string" ||
    !strategy ||
    typeof strategy !== "object" ||
    Array.isArray(strategy) ||
    typeof (strategy as Record<string, unknown>).type !== "string" ||
    !risk ||
    typeof risk !== "object" ||
    Array.isArray(risk) ||
    JSON.stringify(value) !== body
  )
    throw new Error("Invalid saved paper request");
  return value as CreatePaperSessionRequest;
}

export function readPendingPaperCreates(): PendingPaperCreate[] {
  const keys = Array.from({ length: window.localStorage.length }, (_, index) =>
    window.localStorage.key(index),
  )
    .filter(
      (key): key is string =>
        key !== null && key.startsWith(PAPER_CREATE_PENDING_PREFIX),
    )
    .sort();
  if (keys.length > MAX_PENDING)
    throw new Error("Invalid saved paper requests");
  return keys.map((storageKey) => {
    const raw = window.localStorage.getItem(storageKey);
    if (raw === null || raw.length > 9000)
      throw new Error("Invalid saved paper requests");
    const value: unknown = JSON.parse(raw);
    if (!value || typeof value !== "object" || Array.isArray(value))
      throw new Error("Invalid saved paper requests");
    const item = value as Record<string, unknown>;
    if (
      item.version !== 1 ||
      typeof item.body !== "string" ||
      typeof item.key !== "string" ||
      !UUID.test(item.key) ||
      storageKey !== `${PAPER_CREATE_PENDING_PREFIX}${item.key}` ||
      typeof item.savedAt !== "string" ||
      Number.isNaN(Date.parse(item.savedAt))
    )
      throw new Error("Invalid saved paper requests");
    paperRequestFromBody(item.body);
    return item as unknown as PendingPaperCreate;
  });
}

export function preparePaperCreate(
  request: CreatePaperSessionRequest,
): PendingPaperCreate {
  // ponytail: localStorage is not atomic across tabs; add Web Locks and retained receipts before claiming cross-tab exactly-once creation.
  const body = JSON.stringify(request);
  paperRequestFromBody(body);
  const pending = readPendingPaperCreates();
  const matches = pending.filter((item) => item.body === body);
  if (matches.length === 1) return matches[0];
  if (matches.length > 1 || pending.length)
    throw new PendingPaperCreateError("Resolve saved paper request first");
  const intent: PendingPaperCreate = {
    version: 1,
    body,
    key: crypto.randomUUID(),
    savedAt: new Date().toISOString(),
  };
  window.localStorage.setItem(
    `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
    JSON.stringify(intent),
  );
  return intent;
}

export function confirmPaperCreate(intent: PendingPaperCreate): void {
  const pending = readPendingPaperCreates();
  if (
    pending.some((item) => item.body === intent.body && item.key === intent.key)
  )
    window.localStorage.removeItem(
      `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
    );
}
