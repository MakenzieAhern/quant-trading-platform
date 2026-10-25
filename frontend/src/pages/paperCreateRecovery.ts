import type { CreatePaperSessionRequest } from "../types/paper";

export const PAPER_CREATE_PENDING_PREFIX =
  "quant.product.paper-create-pending.v1.";

export class PendingPaperCreateError extends Error {}

export interface PendingPaperCreate {
  version: 1;
  body: string;
  key: string;
  savedAt: string;
  confirmedSessionId?: string;
}

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
// ponytail: 1000 retained receipts fit a personal workstation; add explicit archive UI if this ceiling is reached.
const MAX_SAVED = 1000;
const MAX_PENDING = 20;
const CREATE_LOCK = "quant.product.paper-create.v1";

export function withPaperCreateLock<T>(work: () => Promise<T>): Promise<T> {
  if (!navigator.locks?.request)
    throw new Error("Browser cross-tab locking unavailable");
  return navigator.locks.request(CREATE_LOCK, work);
}

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
  if (keys.length > MAX_SAVED) throw new Error("Invalid saved paper requests");
  const saved = keys.map((storageKey) => {
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
      Number.isNaN(Date.parse(item.savedAt)) ||
      (item.confirmedSessionId !== undefined &&
        (typeof item.confirmedSessionId !== "string" ||
          !UUID.test(item.confirmedSessionId)))
    )
      throw new Error("Invalid saved paper requests");
    paperRequestFromBody(item.body);
    return item as unknown as PendingPaperCreate;
  });
  if (saved.filter((item) => !item.confirmedSessionId).length > MAX_PENDING)
    throw new Error("Too many unresolved paper requests");
  return saved;
}

export function preparePaperCreate(
  request: CreatePaperSessionRequest,
  createAnother = false,
): PendingPaperCreate {
  // All callers must hold CREATE_LOCK through the server response and receipt write.
  const body = JSON.stringify(request);
  paperRequestFromBody(body);
  const saved = readPendingPaperCreates();
  const matchingPending = saved.filter(
    (item) => item.body === body && !item.confirmedSessionId,
  );
  if (!createAnother && matchingPending.length === 1) return matchingPending[0];
  if (
    saved.some((item) => !item.confirmedSessionId) ||
    (saved.length && !createAnother)
  )
    throw new PendingPaperCreateError("Resolve saved paper request first");
  if (saved.length >= MAX_SAVED) throw new Error("Saved paper requests full");
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

export function confirmPaperCreate(
  intent: PendingPaperCreate,
  sessionId: string,
): void {
  if (!UUID.test(sessionId)) throw new Error("Invalid paper session ID");
  const saved = readPendingPaperCreates().find(
    (item) => item.body === intent.body && item.key === intent.key,
  );
  if (
    !saved ||
    (saved.confirmedSessionId && saved.confirmedSessionId !== sessionId)
  )
    throw new Error("Saved paper receipt changed");
  window.localStorage.setItem(
    `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
    JSON.stringify({ ...saved, confirmedSessionId: sessionId }),
  );
}

export function discardRejectedPaperCreate(intent: PendingPaperCreate): void {
  const saved = readPendingPaperCreates().find(
    (item) => item.body === intent.body && item.key === intent.key,
  );
  if (saved && !saved.confirmedSessionId)
    window.localStorage.removeItem(
      `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
    );
}
