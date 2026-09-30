import {
  EXPERIMENT_DRAFT_KEY,
  DRAFT_RECOVERY_PREFIX,
  parseExperimentDraft,
  saveExperimentDraft,
  type ExperimentDraft,
} from "../experiments/draft";
import type { ExperimentConfiguration } from "../experiments/types";

export const CONFIG_VERSION_PREFIX = "quant.product.configuration-version.v1.";
export interface ConfigurationVersion {
  schema: 1;
  id: string;
  name: string;
  createdAt: string;
  kind: "saved" | "pre_restore_backup";
  draft: ExperimentDraft;
}
export interface VersionLibrary {
  items: ConfigurationVersion[];
  unreadable: number;
  storageFailed: boolean;
}
const uuid = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
function parseVersion(value: unknown): ConfigurationVersion | null {
  if (!value || typeof value !== "object") return null;
  const entry = value as ConfigurationVersion;
  if (
    entry.schema !== 1 ||
    typeof entry.id !== "string" ||
    !uuid.test(entry.id) ||
    typeof entry.name !== "string" ||
    !entry.name.trim() ||
    entry.name.length > 80 ||
    typeof entry.createdAt !== "string" ||
    !Number.isFinite(Date.parse(entry.createdAt)) ||
    !["saved", "pre_restore_backup"].includes(entry.kind) ||
    !parseExperimentDraft(entry.draft)
  )
    return null;
  return entry;
}
export function readConfigurationVersions(): VersionLibrary {
  const items: ConfigurationVersion[] = [];
  let unreadable = 0;
  try {
    // Only enumerate this feature's own prefix; never clear or rewrite a shared collection.
    const keys = Array.from(
      { length: window.localStorage.length },
      (_, index) => window.localStorage.key(index),
    ).filter(
      (key): key is string =>
        key !== null && key.startsWith(CONFIG_VERSION_PREFIX),
    );
    for (const key of keys) {
      const raw = window.localStorage.getItem(key);
      if (raw === null) continue;
      try {
        const entry = parseVersion(JSON.parse(raw));
        if (!entry || key !== `${CONFIG_VERSION_PREFIX}${entry.id}`)
          unreadable += 1;
        else items.push(entry);
      } catch {
        unreadable += 1;
      }
    }
  } catch {
    return { items: [], unreadable, storageFailed: true };
  }
  return {
    items: items.sort(
      (a, b) =>
        b.createdAt.localeCompare(a.createdAt) || b.id.localeCompare(a.id),
    ),
    unreadable,
    storageFailed: false,
  };
}
export function saveConfigurationVersion(
  name: string,
  draft: ExperimentDraft,
  kind: ConfigurationVersion["kind"] = "saved",
): ConfigurationVersion {
  if (!name.trim() || name.trim().length > 80 || !parseExperimentDraft(draft))
    throw new Error("INVALID_CONFIGURATION_VERSION");
  const entry: ConfigurationVersion = {
    schema: 1,
    id: crypto.randomUUID(),
    name: name.trim(),
    createdAt: new Date().toISOString(),
    kind,
    draft,
  };
  const key = `${CONFIG_VERSION_PREFIX}${entry.id}`;
  if (window.localStorage.getItem(key) !== null)
    throw new Error("CONFIGURATION_VERSION_ALREADY_EXISTS");
  window.localStorage.setItem(key, JSON.stringify(entry));
  return entry;
}
export function restoreConfigurationVersion(
  id: string,
  current: ExperimentDraft,
  backupName: string,
): ExperimentDraft {
  if (!uuid.test(id)) throw new Error("INVALID_CONFIGURATION_VERSION");
  const target = parseVersion(
    JSON.parse(
      window.localStorage.getItem(`${CONFIG_VERSION_PREFIX}${id}`) ?? "null",
    ),
  );
  if (!target || target.id !== id)
    throw new Error("CONFIGURATION_VERSION_UNAVAILABLE");
  return restoreDraftSnapshot(target.draft, current, backupName);
}
export function restoreBrowserDraft(
  id: string,
  current: ExperimentDraft,
  backupName: string,
  expected: ExperimentDraft,
): ExperimentDraft {
  if (!uuid.test(id)) throw new Error("INVALID_CONFIGURATION_VERSION");
  const target = parseExperimentDraft(
    JSON.parse(localStorage.getItem(`${DRAFT_RECOVERY_PREFIX}${id}`) ?? "null"),
  );
  if (!target) throw new Error("CONFIGURATION_VERSION_UNAVAILABLE");
  if (JSON.stringify(target) !== JSON.stringify(expected))
    throw new Error("RECOVERY_DRAFT_CHANGED");
  return restoreDraftSnapshot(target, current, backupName);
}
export function startNewExperimentDraft(
  current: ExperimentDraft,
  form: ExperimentConfiguration,
  backupName: string,
): ExperimentDraft {
  return restoreDraftSnapshot({ ...current, form }, current, backupName);
}
function restoreDraftSnapshot(
  target: ExperimentDraft,
  current: ExperimentDraft,
  backupName: string,
): ExperimentDraft {
  const storedRaw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
  const stored =
    storedRaw === null ? null : parseExperimentDraft(JSON.parse(storedRaw));
  if (
    storedRaw !== null &&
    (!stored ||
      stored.idempotencyKey !== current.idempotencyKey ||
      stored.step !== current.step ||
      JSON.stringify(stored.form) !== JSON.stringify(current.form))
  )
    throw new Error("DRAFT_CHANGED_IN_ANOTHER_TAB");
  // Backup first. If either atomic storage write fails, the original draft is not erased.
  saveConfigurationVersion(backupName, current, "pre_restore_backup");
  const draft: ExperimentDraft = {
    version: 1,
    form: target.form,
    step: 0,
    idempotencyKey: crypto.randomUUID(),
    savedAt: new Date().toISOString(),
  };
  saveExperimentDraft(draft.form, draft.step, draft.idempotencyKey);
  return draft;
}
