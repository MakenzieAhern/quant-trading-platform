import { beforeEach, describe, expect, it, vi } from "vitest";
import {
  EXPERIMENT_DRAFT_KEY,
  DRAFT_RECOVERY_PREFIX,
  readBrowserDraftRecoveries,
  parseExperimentDraft,
  readExperimentDraft,
  saveExperimentDraft,
  type ExperimentDraft,
} from "../experiments/draft";
import { configuration } from "../experiments/fixtures.test-data";
import {
  CONFIG_VERSION_PREFIX,
  readConfigurationVersions,
  restoreConfigurationVersion,
  saveConfigurationVersion,
  startNewExperimentDraft,
} from "./storage";

const current: ExperimentDraft = {
  version: 1,
  form: configuration,
  step: 2,
  idempotencyKey: "current-intent",
  savedAt: "2026-09-22T09:00:00Z",
};
beforeEach(() => {
  for (const key of Object.keys(window.localStorage))
    if (
      key.startsWith(CONFIG_VERSION_PREFIX) ||
      key.startsWith(DRAFT_RECOVERY_PREFIX) ||
      key === EXPERIMENT_DRAFT_KEY
    )
      window.localStorage.removeItem(key);
});
describe("immutable browser configuration versions", () => {
  it("keeps the saved time for an unchanged autosave, but dates a real edit", () => {
    const original = JSON.stringify(current);
    localStorage.setItem(EXPERIMENT_DRAFT_KEY, original);
    saveExperimentDraft(
      { ...configuration },
      current.step,
      current.idempotencyKey,
    );
    expect(localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(original);
    expect(readBrowserDraftRecoveries().items[0].draft.savedAt).toBe(
      current.savedAt,
    );

    saveExperimentDraft(
      { ...configuration, name: "Edited configuration" },
      current.step,
      current.idempotencyKey,
    );
    expect(readExperimentDraft()?.form.name).toBe("Edited configuration");
    expect(readExperimentDraft()?.savedAt).not.toBe(current.savedAt);
  });
  it("keeps another tab's draft when it arrives during backup publication", async () => {
    saveExperimentDraft(configuration, current.step, current.idempotencyKey);
    const target = saveConfigurationVersion("Target", {
      ...current,
      form: { ...configuration, name: "Restore target" },
    });
    vi.resetModules();
    const otherPage = await import("../experiments/draft");
    const otherForm = {
      ...configuration,
      name: "Other tab concurrent edit",
      initial_cash: "123456.000000000000000007",
    };
    const original = Storage.prototype.setItem;
    let interleaved = false;
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key,
      value,
    ) {
      if (!interleaved && key.startsWith(CONFIG_VERSION_PREFIX)) {
        interleaved = true;
        otherPage.saveExperimentDraft(otherForm, 1, "other-tab-new-intent");
      }
      original.call(this, key, value);
    });
    expect(() =>
      restoreConfigurationVersion(target.id, current, "Before restore"),
    ).toThrow("DRAFT_CHANGED_IN_ANOTHER_TAB");
    expect(interleaved).toBe(true);
    expect(readExperimentDraft()?.form).toEqual(otherForm);
    const preserved = readBrowserDraftRecoveries().items.find(
      (entry) => entry.draft.idempotencyKey === "other-tab-new-intent",
    );
    expect(preserved?.draft.form).toEqual(otherForm);
    expect(readBrowserDraftRecoveries().items).toHaveLength(3);
    expect(
      readBrowserDraftRecoveries().items.some(
        (entry) => entry.draft.form.name === "Restore target",
      ),
    ).toBe(true);
    expect(
      readConfigurationVersions().items.some(
        (entry) =>
          entry.kind === "pre_restore_backup" &&
          entry.draft.idempotencyKey === current.idempotencyKey,
      ),
    ).toBe(true);
  });
  it("keeps one page recovery through ordinary edits, rotating only for an explicit new draft", () => {
    saveExperimentDraft(configuration, 1, "first-intent");
    for (let index = 0; index < 20; index++)
      saveExperimentDraft(
        { ...configuration, name: `Edit ${index}` },
        1,
        `edit-${index}`,
      );
    expect(readBrowserDraftRecoveries().items).toHaveLength(1);
    expect(readBrowserDraftRecoveries().items[0].draft.form.name).toBe(
      "Edit 19",
    );
    startNewExperimentDraft(
      readExperimentDraft()!,
      { ...configuration, name: "New intent" },
      "Before new draft",
    );
    expect(readBrowserDraftRecoveries().items).toHaveLength(2);
  });
  it("never changes the shared draft if its own recovery slot cannot be persisted", () => {
    saveExperimentDraft(configuration, 2, current.idempotencyKey);
    const raw = localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    const original = Storage.prototype.setItem;
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key,
      value,
    ) {
      if (key.startsWith(DRAFT_RECOVERY_PREFIX))
        throw new DOMException("full", "QuotaExceededError");
      original.call(this, key, value);
    });
    expect(() =>
      saveExperimentDraft(
        { ...configuration, name: "New unpersisted form" },
        1,
        "different-key",
      ),
    ).toThrow();
    expect(localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(raw);
  });
  it("stores each exact snapshot independently and never overwrites an earlier version", () => {
    const first = saveConfigurationVersion("Original", current);
    const second = saveConfigurationVersion("Original", {
      ...current,
      form: { ...configuration, initial_cash: "99999.999999999999999999" },
    });
    expect(first.id).not.toBe(second.id);
    expect(readConfigurationVersions().items).toHaveLength(2);
    expect(
      JSON.parse(
        window.localStorage.getItem(CONFIG_VERSION_PREFIX + first.id)!,
      ),
    ).toMatchObject({ draft: current });
    expect(
      JSON.parse(
        window.localStorage.getItem(CONFIG_VERSION_PREFIX + second.id)!,
      ),
    ).toMatchObject({
      draft: { form: { initial_cash: "99999.999999999999999999" } },
    });
  });
  it("reuses the draft shape validator without rejecting unfinished draft values", () => {
    const unfinished = {
      ...current,
      form: {
        ...configuration,
        initial_cash: "",
        end_date: "",
        costs: { commission_rate: "-", minimum_commission: "" },
      },
    };
    saveExperimentDraft(
      unfinished.form,
      unfinished.step,
      unfinished.idempotencyKey,
    );
    expect(parseExperimentDraft(readExperimentDraft())).toEqual(
      readExperimentDraft(),
    );
    expect(saveConfigurationVersion("Unfinished", unfinished).draft).toEqual(
      unfinished,
    );
    for (const broken of [
      null,
      {},
      { ...current, step: 4 },
      { ...current, form: { ...configuration, costs: null } },
      { ...current, form: { ...configuration, initial_cash: 100000 } },
    ]) {
      window.localStorage.setItem(EXPERIMENT_DRAFT_KEY, JSON.stringify(broken));
      expect(readExperimentDraft()).toBeNull();
      expect(parseExperimentDraft(broken)).toBeNull();
    }
  });
  it("retains corrupt records and distinguishes blocked storage from an empty library", () => {
    const key = CONFIG_VERSION_PREFIX + crypto.randomUUID();
    window.localStorage.setItem(key, "{broken");
    window.localStorage.setItem("unrelated-preference", "kept");
    expect(readConfigurationVersions()).toMatchObject({
      items: [],
      unreadable: 1,
      storageFailed: false,
    });
    expect(window.localStorage.getItem(key)).toBe("{broken");
    const get = vi
      .spyOn(Storage.prototype, "getItem")
      .mockImplementation(() => {
        throw new DOMException("blocked", "SecurityError");
      });
    expect(readConfigurationVersions().storageFailed).toBe(true);
    get.mockRestore();
    expect(window.localStorage.getItem("unrelated-preference")).toBe("kept");
    window.localStorage.removeItem("unrelated-preference");
  });
  it("backs up the current draft, restores exact values at step 1 and creates a fresh intent", () => {
    saveExperimentDraft(configuration, current.step, current.idempotencyKey);
    const version = saveConfigurationVersion("Target", {
      ...current,
      idempotencyKey: "old-intent",
      form: { ...configuration, initial_cash: "345678.000000000000000001" },
    });
    const restored = restoreConfigurationVersion(version.id, current, "Backup");
    expect(restored.step).toBe(0);
    expect(restored.idempotencyKey).not.toBe(current.idempotencyKey);
    expect(restored.idempotencyKey).not.toBe(version.draft.idempotencyKey);
    expect(restored.form).toEqual(version.draft.form);
    expect(readExperimentDraft()).toMatchObject({
      step: 0,
      form: version.draft.form,
      idempotencyKey: restored.idempotencyKey,
    });
    expect(
      readConfigurationVersions().items.find(
        (entry) => entry.kind === "pre_restore_backup",
      )?.draft,
    ).toEqual(current);
  });
  it.each(["backup", "primary"])(
    "preserves the original draft when %s storage write fails",
    (failure) => {
      saveExperimentDraft(configuration, current.step, current.idempotencyKey);
      const raw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
      const version = saveConfigurationVersion("Target", current);
      const write = Storage.prototype.setItem;
      vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
        this: Storage,
        key,
        value,
      ) {
        if (
          (failure === "backup" && key.startsWith(CONFIG_VERSION_PREFIX)) ||
          (failure === "primary" && key === EXPERIMENT_DRAFT_KEY)
        )
          throw new DOMException("full", "QuotaExceededError");
        write.call(this, key, value);
      });
      expect(() =>
        restoreConfigurationVersion(version.id, current, "Backup"),
      ).toThrow();
      expect(window.localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(raw);
      expect(readConfigurationVersions().items).toHaveLength(
        failure === "backup" ? 1 : 2,
      );
    },
  );
  it("refuses to replace a different draft written by another tab", () => {
    const version = saveConfigurationVersion("Target", current);
    saveExperimentDraft(
      { ...configuration, name: "Other tab" },
      1,
      "other-tab-intent",
    );
    const raw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    expect(() =>
      restoreConfigurationVersion(version.id, current, "Backup"),
    ).toThrow("DRAFT_CHANGED_IN_ANOTHER_TAB");
    expect(window.localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(raw);
    expect(readConfigurationVersions().items).toHaveLength(1);
  });
  it("refuses a fresh start when another tab advanced the same draft", () => {
    saveExperimentDraft(configuration, current.step, current.idempotencyKey);
    saveExperimentDraft(configuration, 3, current.idempotencyKey);
    const raw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    expect(() =>
      startNewExperimentDraft(
        current,
        { ...configuration, name: "Fresh start" },
        "Before new backtest",
      ),
    ).toThrow("DRAFT_CHANGED_IN_ANOTHER_TAB");
    expect(window.localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(raw);
    expect(readConfigurationVersions().items).toHaveLength(0);
  });
});
