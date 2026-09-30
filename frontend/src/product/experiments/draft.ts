import type { ExperimentConfiguration } from "./types";

export const EXPERIMENT_DRAFT_KEY = "quant.product.experiment-draft.v1";
export const DRAFT_RECOVERY_PREFIX =
  "quant.product.experiment-draft-recovery.v1.";
export const UNREADABLE_DRAFT_PREFIX =
  "quant.product.unreadable-experiment-draft.v1.";
// Rotate when this page starts another logical draft; older recovery stays intact.
let writerId = crypto.randomUUID();
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
  expectedUnreadableRaw?: string,
) {
  const storedRaw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
  if (
    expectedUnreadableRaw !== undefined &&
    storedRaw !== expectedUnreadableRaw
  )
    throw new Error("DRAFT_CHANGED_IN_ANOTHER_TAB");
  let stored: ExperimentDraft | null = null;
  try {
    stored =
      storedRaw === null ? null : parseExperimentDraft(JSON.parse(storedRaw));
  } catch {
    // Keep the exact original bytes; the user may still recover them.
  }
  if (storedRaw !== null && !stored) {
    if (storedRaw !== expectedUnreadableRaw)
      throw new Error("DRAFT_CHANGED_IN_ANOTHER_TAB");
    const backupKey = `${UNREADABLE_DRAFT_PREFIX}${crypto.randomUUID()}`;
    if (window.localStorage.getItem(backupKey) !== null)
      throw new Error("UNREADABLE_DRAFT_BACKUP_EXISTS");
    window.localStorage.setItem(backupKey, storedRaw);
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
  const currentRecoveryRaw = window.localStorage.getItem(
    `${DRAFT_RECOVERY_PREFIX}${writerId}`,
  );
  let currentRecovery: ExperimentDraft | null = null;
  try {
    currentRecovery = currentRecoveryRaw
      ? parseExperimentDraft(JSON.parse(currentRecoveryRaw))
      : null;
  } catch {
    // Preserve an unreadable page recovery under its existing key.
  }
  const nextWriterId =
    currentRecoveryRaw !== null &&
    currentRecovery?.idempotencyKey !== idempotencyKey
      ? crypto.randomUUID()
      : writerId;
  if (
    nextWriterId !== writerId &&
    window.localStorage.getItem(`${DRAFT_RECOVERY_PREFIX}${nextWriterId}`) !==
      null
  )
    throw new Error("DRAFT_RECOVERY_KEY_EXISTS");
  // Synchronous for beforeunload: preserve this page's latest values before any
  // shared-pointer write. Another tab can win the pointer without losing ours.
  window.localStorage.setItem(`${DRAFT_RECOVERY_PREFIX}${nextWriterId}`, raw);
  if (
    expectedUnreadableRaw !== undefined &&
    window.localStorage.getItem(EXPERIMENT_DRAFT_KEY) !== expectedUnreadableRaw
  )
    throw new Error("DRAFT_CHANGED_IN_ANOTHER_TAB");
  window.localStorage.setItem(EXPERIMENT_DRAFT_KEY, raw);
  writerId = nextWriterId;
}

export function readUnreadableDraftCopies(): {
  items: { id: string; raw: string }[];
  storageFailed: boolean;
} {
  try {
    const items: { id: string; raw: string }[] = [];
    for (let index = 0; index < window.localStorage.length; index++) {
      const key = window.localStorage.key(index);
      if (!key?.startsWith(UNREADABLE_DRAFT_PREFIX)) continue;
      const raw = window.localStorage.getItem(key);
      if (raw !== null)
        items.push({ id: key.slice(UNREADABLE_DRAFT_PREFIX.length), raw });
    }
    return {
      items: items.sort((a, b) => a.id.localeCompare(b.id)),
      storageFailed: false,
    };
  } catch {
    return { items: [], storageFailed: true };
  }
}

export function clearCompletedExperimentDraft(
  form: ExperimentConfiguration,
  idempotencyKey: string,
) {
  const matches = (raw: string | null) => {
    if (!raw) return false;
    try {
      const stored = parseExperimentDraft(JSON.parse(raw));
      return (
        stored?.idempotencyKey === idempotencyKey &&
        JSON.stringify(stored.form) === JSON.stringify(form)
      );
    } catch {
      return false;
    }
  };
  for (const key of [EXPERIMENT_DRAFT_KEY, DRAFT_RECOVERY_PREFIX + writerId]) {
    try {
      if (matches(window.localStorage.getItem(key)))
        window.localStorage.removeItem(key);
    } catch {
      // The server job is durable; browser storage may be unavailable.
    }
  }
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
