import { act, fireEvent, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { experimentApi } from "../experiments/api";
import { CreateExperimentPage } from "../experiments/CreateExperimentPage";
import {
  EXPERIMENT_DRAFT_KEY,
  DRAFT_RECOVERY_PREFIX,
  readExperimentDraft,
  saveExperimentDraft,
  type ExperimentDraft,
} from "../experiments/draft";
import { capabilities, configuration } from "../experiments/fixtures.test-data";
import { ConfigurationVersionsPanel } from "./ConfigurationVersionsPanel";
import {
  CONFIG_VERSION_PREFIX,
  readConfigurationVersions,
  saveConfigurationVersion,
} from "./storage";

const current: ExperimentDraft = {
  version: 1,
  form: configuration,
  step: 2,
  idempotencyKey: "current-key",
  savedAt: "2026-09-22T09:00:00Z",
};
beforeEach(async () => {
  for (const key of Object.keys(window.localStorage))
    if (
      key.startsWith(CONFIG_VERSION_PREFIX) ||
      key.startsWith(DRAFT_RECOVERY_PREFIX) ||
      key === EXPERIMENT_DRAFT_KEY
    )
      window.localStorage.removeItem(key);
  await i18n.changeLanguage("en-US");
  window.history.replaceState({}, "", "/research/new");
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value: function (this: HTMLDialogElement) {
        this.open = true;
      },
    },
    close: {
      configurable: true,
      value: function (this: HTMLDialogElement) {
        this.open = false;
      },
    },
  });
});
describe("configuration versions in the guided wizard", () => {
  it("rejects a recovery slot changed after preview and displays fractions in fraction fields", async () => {
    saveExperimentDraft(configuration, 2, current.idempotencyKey);
    const original = localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    const id = crypto.randomUUID();
    localStorage.setItem(
      DRAFT_RECOVERY_PREFIX + id,
      JSON.stringify({
        ...current,
        form: { ...configuration, name: "Preview this" },
      }),
    );
    const restore = vi.fn();
    render(
      <ConfigurationVersionsPanel current={current} onRestore={restore} />,
    );
    await userEvent.click(screen.getByText("Browser page recovery drafts"));
    await userEvent.click(
      screen.getByRole("button", {
        name: `Review recovery draft: Preview this ${id.slice(0, 8)}`,
      }),
    );
    const dialog = screen.getByRole("dialog");
    expect(
      within(dialog).getByText("Commission rate (decimal fraction)")
        .nextElementSibling,
    ).toHaveTextContent("0.0003");
    expect(
      within(dialog).getByText("Drawdown risk limit (negative fraction)")
        .nextElementSibling,
    ).toHaveTextContent("-0.2");
    localStorage.setItem(
      DRAFT_RECOVERY_PREFIX + id,
      JSON.stringify({
        ...current,
        form: { ...configuration, name: "Changed unseen", initial_cash: "1" },
      }),
    );
    await userEvent.click(
      within(dialog).getByRole("button", {
        name: "Back up current draft and restore",
      }),
    );
    expect(within(dialog).getByRole("alert")).toHaveTextContent(
      "changed after this preview opened",
    );
    expect(restore).not.toHaveBeenCalled();
    expect(localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(original);
  });
  it("offers orphaned page drafts as explicit recoveries without automatic submission", async () => {
    saveExperimentDraft(configuration, 2, current.idempotencyKey);
    const id = crypto.randomUUID();
    const other = {
      ...current,
      form: {
        ...configuration,
        name: "Recovered other page",
        initial_cash: "765432.000000000000000009",
      },
      idempotencyKey: "orphaned-intent",
    };
    localStorage.setItem(DRAFT_RECOVERY_PREFIX + id, JSON.stringify(other));
    const restore = vi.fn();
    render(
      <ConfigurationVersionsPanel current={current} onRestore={restore} />,
    );
    await userEvent.click(screen.getByText("Browser page recovery drafts"));
    await userEvent.click(
      screen.getByRole("button", {
        name: `Review recovery draft: Recovered other page ${id.slice(0, 8)}`,
      }),
    );
    expect(restore).not.toHaveBeenCalled();
    await userEvent.click(
      screen.getByRole("button", { name: "Back up current draft and restore" }),
    );
    expect(restore).toHaveBeenCalledWith(
      expect.objectContaining({ step: 0, form: other.form }),
    );
    expect(readExperimentDraft()?.idempotencyKey).not.toBe(
      other.idempotencyKey,
    );
  });
  it("keeps an entered version name across locale changes and saves exact browser-only values", async () => {
    const restore = vi.fn();
    render(
      <ConfigurationVersionsPanel current={current} onRestore={restore} />,
    );
    expect(screen.getByText(/not backed up to the server/)).toBeInTheDocument();
    await userEvent.type(
      screen.getByLabelText("Version name"),
      "My exact setup",
    );
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByLabelText("版本名称")).toHaveValue("My exact setup");
    await userEvent.click(screen.getByRole("button", { name: "保存命名版本" }));
    expect(readConfigurationVersions().items[0].draft.form.initial_cash).toBe(
      configuration.initial_cash,
    );
    expect(
      screen.getByText("配置版本已保存在此浏览器中。"),
    ).toBeInTheDocument();
    expect(restore).not.toHaveBeenCalled();
  });
  it("requires explicit confirmation, backs up current values and restores to step 1 without submitting", async () => {
    const target = saveConfigurationVersion("Original setup", {
      ...current,
      form: { ...configuration, initial_cash: "321000.000000000000000009" },
      idempotencyKey: "old-key",
    });
    saveExperimentDraft(configuration, 2, current.idempotencyKey);
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const create = vi.spyOn(experimentApi, "create");
    render(<CreateExperimentPage />);
    await screen.findByLabelText("Commission rate (decimal fraction)");
    const before = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    await userEvent.click(
      screen.getByRole("button", {
        name: "Review and restore: Original setup",
      }),
    );
    let dialog = screen.getByRole("dialog", {
      name: "Restore this saved configuration?",
    });
    expect(
      within(dialog).getByText("321,000.000000000000000009 CNY"),
    ).toBeInTheDocument();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Keep current draft" }),
    );
    expect(window.localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(before);
    await userEvent.click(
      screen.getByRole("button", {
        name: "Review and restore: Original setup",
      }),
    );
    dialog = screen.getByRole("dialog");
    await userEvent.click(
      within(dialog).getByRole("button", {
        name: "Back up current draft and restore",
      }),
    );
    expect(screen.getByRole("radio")).toBeChecked();
    expect(readExperimentDraft()).toMatchObject({
      form: target.draft.form,
      step: 0,
    });
    expect(readExperimentDraft()?.idempotencyKey).not.toBe("old-key");
    expect(readExperimentDraft()?.idempotencyKey).not.toBe(
      current.idempotencyKey,
    );
    expect(
      readConfigurationVersions().items.find(
        (entry) => entry.kind === "pre_restore_backup",
      )?.draft.form,
    ).toEqual(configuration);
    expect(create).not.toHaveBeenCalled();
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByLabelText("Starting capital (CNY)")).toHaveValue(
      target.draft.form.initial_cash,
    );
  });
  it("reports quota failure and retains the name, current form and draft", async () => {
    saveExperimentDraft(configuration, 2, current.idempotencyKey);
    const before = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    const restore = vi.fn();
    render(
      <ConfigurationVersionsPanel current={current} onRestore={restore} />,
    );
    await userEvent.type(
      screen.getByLabelText("Version name"),
      "Keep this name",
    );
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("full", "QuotaExceededError");
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Save named version" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "have not been replaced",
    );
    expect(screen.getByLabelText("Version name")).toHaveValue("Keep this name");
    expect(window.localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(before);
    expect(restore).not.toHaveBeenCalled();
  });
  it("refreshes separately stored cross-tab versions without changing current values", async () => {
    const restore = vi.fn();
    render(
      <ConfigurationVersionsPanel current={current} onRestore={restore} />,
    );
    await userEvent.type(
      screen.getByLabelText("Version name"),
      "Still editing",
    );
    act(() => {
      const created = saveConfigurationVersion("Other tab version", current);
      fireEvent(
        window,
        new StorageEvent("storage", {
          key: CONFIG_VERSION_PREFIX + created.id,
        }),
      );
    });
    expect(
      screen.getByRole("button", {
        name: "Review and restore: Other tab version",
      }),
    ).toBeInTheDocument();
    expect(screen.getByLabelText("Version name")).toHaveValue("Still editing");
    expect(restore).not.toHaveBeenCalled();
  });
  it("preserves the current wizard after restore storage fails", async () => {
    saveConfigurationVersion("Target", {
      ...current,
      form: { ...configuration, initial_cash: "12.3" },
    });
    saveExperimentDraft(configuration, 2, current.idempotencyKey);
    const restore = vi.fn();
    render(
      <ConfigurationVersionsPanel current={current} onRestore={restore} />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Review and restore: Target" }),
    );
    const write = Storage.prototype.setItem;
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(function (
      this: Storage,
      key,
      value,
    ) {
      if (key === EXPERIMENT_DRAFT_KEY)
        throw new DOMException("full", "QuotaExceededError");
      write.call(this, key, value);
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Back up current draft and restore" }),
    );
    expect(
      within(screen.getByRole("dialog")).getByRole("alert"),
    ).toHaveTextContent("have not been replaced");
    expect(readExperimentDraft()?.form).toEqual(configuration);
    expect(restore).not.toHaveBeenCalled();
  });
});
