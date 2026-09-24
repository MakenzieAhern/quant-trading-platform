import type { ExperimentConfiguration } from "./types";

export const EXPERIMENT_DRAFT_KEY = "quant.product.experiment-draft.v1";
export const DRAFT_RECOVERY_PREFIX =
  "quant.product.experiment-draft-recovery.v1.";
// A page owns only this recovery slot. Never reuse a writer ID from shared storage.
const writerId = crypto.randomUUID();
export interface BrowserDraftRecovery {
  id: string;
  draft: ExperimentDraft;
}
export interface ExperimentDraft {
  version: 1;
  form: ExperimentConfiguration;
  step: number;
  idempotencyKey: string;
  savedAt: string;
}
export function readExperimentDraft(): ExperimentDraft | null {
  try {
    const raw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    if (!raw) return null;
    return parseExperimentDraft(JSON.parse(raw));
  } catch {
    return null;
  }
}
export function parseExperimentDraft(input: unknown): ExperimentDraft | null {
  try {
    const value = input as ExperimentDraft;
    if (
      value.version !== 1 ||
      !Number.isInteger(value.step) ||
      value.step < 0 ||
      value.step > 3 ||
      typeof value.idempotencyKey !== "string" ||
      typeof value.savedAt !== "string"
    )
      return null;
    // Drafts can contain unfinished values. Validate shape, not run eligibility.
    const form = value.form;
    if (
      !form ||
      [
        form.name,
        form.dataset_id,
        form.strategy_id,
        form.start_date,
        form.end_date,
        form.initial_cash,
        form.universe,
        form.costs?.commission_rate,
        form.costs?.minimum_commission,
        form.risk?.max_drawdown,
        form.risk?.max_position_weight,
      ].some((field) => typeof field !== "string") ||
      !Number.isSafeInteger(form.strategy?.rebalance_sessions) ||
      !Number.isSafeInteger(form.strategy?.maximum_holdings)
    )
      return null;
    return value;
  } catch {
    return null;
  }
}
export function saveExperimentDraft(
  form: ExperimentConfiguration,
  step: number,
  idempotencyKey: string,
) {
  let storedRaw: string | null = null;
  let stored: ExperimentDraft | null = null;
  try {
    storedRaw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    stored = storedRaw ? parseExperimentDraft(JSON.parse(storedRaw)) : null;
  } catch {
    // Corrupt or unreadable storage must not prevent writing the current draft.
  }
  const unchanged =
    stored &&
    stored.step === step &&
    stored.idempotencyKey === idempotencyKey &&
    JSON.stringify(stored.form) === JSON.stringify(form);
  const raw =
    unchanged && storedRaw
      ? storedRaw
      : JSON.stringify({
          version: 1,
          form,
          step,
          idempotencyKey,
          savedAt: new Date().toISOString(),
        } satisfies ExperimentDraft);
  // Synchronous for beforeunload: preserve this page's latest values before any
  // shared-pointer write. Another tab can win the pointer without losing ours.
  window.localStorage.setItem(`${DRAFT_RECOVERY_PREFIX}${writerId}`, raw);
  window.localStorage.setItem(EXPERIMENT_DRAFT_KEY, raw);
}

export function readBrowserDraftRecoveries(): {
  items: BrowserDraftRecovery[];
  unreadable: number;
  storageFailed: boolean;
} {
  const items: BrowserDraftRecovery[] = [];
  let unreadable = 0;
  try {
    const keys = Array.from({ length: localStorage.length }, (_, index) =>
      localStorage.key(index),
    ).filter(
      (key): key is string =>
        key !== null && key.startsWith(DRAFT_RECOVERY_PREFIX),
    );
    for (const key of keys) {
      const raw = localStorage.getItem(key);
      if (raw === null) continue;
      try {
        const draft = parseExperimentDraft(JSON.parse(raw));
        const id = key.slice(DRAFT_RECOVERY_PREFIX.length);
        if (
          !draft ||
          !/^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i.test(
            id,
          )
        )
          unreadable++;
        else items.push({ id, draft });
      } catch {
        unreadable++;
      }
    }
  } catch {
    return { items: [], unreadable, storageFailed: true };
  }
  return {
    items: items.sort(
      (a, b) =>
        b.draft.savedAt.localeCompare(a.draft.savedAt) ||
        b.id.localeCompare(a.id),
    ),
    unreadable,
    storageFailed: false,
  };
}
