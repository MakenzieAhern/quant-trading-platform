import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, expect, it, vi } from "vitest";

import { paperApi } from "../api/paper";
import { i18n } from "../i18n";
import { jsonResponse } from "../test/fixtures";
import {
  PAPER_ID,
  paperCapabilities,
  paperCollection,
  paperSnapshot,
} from "../test/paperFixtures";
import { CreatePaperSessionPage } from "./CreatePaperSessionPage";
import { PaperSessionDetailPage } from "./PaperSessionDetailPage";
import { PaperSessionsPage } from "./PaperSessionsPage";

const stream = vi.hoisted(() => vi.fn());
vi.mock("../hooks/usePaperStream", () => ({ usePaperStream: stream }));

const messages = [
  [
    "SOURCE_CONTRACT_INTEGRITY_FAILED",
    "source references failed",
    "来源引用未通过",
  ],
  [
    "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED",
    "source integrity has not been verified",
    "来源完整性尚未验证",
  ],
  [
    "DATASET_CHANGED_SINCE_SUBMISSION",
    "data version changed after submission",
    "提交后数据版本发生变化",
  ],
] as const;

beforeEach(() => {
  // A later create/start check can reject a source that passed the read-only preflight.
  vi.spyOn(paperApi, "capabilities").mockResolvedValue(paperCapabilities());
  window.localStorage.clear();
  Object.defineProperty(window.navigator, "locks", {
    configurable: true,
    value: { request: (_: string, callback: () => unknown) => callback() },
  });
});
afterEach(() => {
  window.localStorage.clear();
  Reflect.deleteProperty(window.navigator, "locks");
});

it.each(["en-US", "zh-CN"])(
  "does not present a historical provider name as current audit approval (%s)",
  async (locale) => {
    await i18n.changeLanguage(locale);
    const saved = paperSnapshot("STOPPED").session;
    saved.provider_type = "historical_a_share";
    saved.dataset_id = "cn-a-research-20100101-20251231-v1";
    const before = JSON.stringify(saved);
    const read = vi.spyOn(paperApi, "list").mockResolvedValue({
      items: [saved],
      limit: 20,
      offset: 0,
      total: 1,
    });
    render(<PaperSessionsPage />);
    await screen.findByRole("link", {
      name: new RegExp(locale === "en-US" ? "Open session:" : "查看会话:"),
    });
    expect(document.body).not.toHaveTextContent(/audited|已审计/i);
    expect(document.body).toHaveTextContent(
      locale === "en-US" ? "current data admission" : "当前数据准入",
    );
    for (const key of [
      "createPage.historicalAShare",
      "createPage.historicalHint",
      "detail.marketSources.FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
    ]) {
      expect(i18n.exists(`paper:${key}`)).toBe(true);
      expect(i18n.t(`paper:${key}`)).not.toMatch(/audited|已审计/i);
    }
    expect(read).toHaveBeenCalledOnce();
    expect(JSON.stringify(saved)).toBe(before);
  },
);

it.each(messages)(
  "explains %s on historical paper creation and locale switch without resubmitting",
  async (code, en, zh) => {
    await i18n.changeLanguage("en-US");
    const fetch = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: code }, 422));
    vi.stubGlobal("fetch", fetch);
    window.history.replaceState({}, "", "/paper/new");
    await act(async () => render(<CreatePaperSessionPage />));
    fireEvent.change(screen.getByLabelText("Provider"), {
      target: { value: "historical_a_share" },
    });
    const cash = screen.getByLabelText("Initial cash");
    fireEvent.change(cash, { target: { value: "12345.000000000000001" } });
    const formBefore = Array.from(
      document.querySelectorAll<HTMLInputElement>("input[name]"),
      (item) => item.value,
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(en);
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByRole("alert")).toHaveTextContent(zh);
    expect(
      Array.from(
        document.querySelectorAll<HTMLInputElement>("input[name]"),
        (item) => item.value,
      ),
    ).toEqual(formBefore);
    expect(fetch).toHaveBeenCalledTimes(1);
    expect(fetch.mock.calls[0]![1].body).toContain("12345.000000000000001");
  },
);

it.each(messages)(
  "explains %s on resume while retaining the saved account and retry control",
  async (code, en, zh) => {
    await i18n.changeLanguage("en-US");
    const saved = paperSnapshot("PAUSED");
    saved.session.provider_type = "historical_a_share";
    saved.session.dataset_id = "cn-a-research-20100101-20251231-v1";
    const before = JSON.stringify(saved);
    stream.mockReturnValue({
      snapshot: saved,
      collectionSequence: 0,
      collectionsPending: false,
      fillAnnouncement: null,
      connection: "connected",
      error: null,
      acknowledge: vi.fn(),
      refresh: vi.fn(),
    });
    vi.spyOn(paperApi, "collection").mockImplementation(async (_id, kind) =>
      paperCollection(saved, kind),
    );
    const fetch = vi
      .fn()
      .mockResolvedValue(jsonResponse({ detail: code }, 422));
    vi.stubGlobal("fetch", fetch);
    render(<PaperSessionDetailPage sessionId={PAPER_ID} />);
    await userEvent.click(
      screen.getByRole("button", { name: "Resume replay" }),
    );
    expect(await screen.findByRole("alert")).toHaveTextContent(en);
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByRole("alert")).toHaveTextContent(zh);
    expect(screen.getByRole("button", { name: "继续回放" })).toHaveAttribute(
      "aria-disabled",
      "false",
    );
    expect(JSON.stringify(saved)).toBe(before);
    expect(fetch).toHaveBeenCalledTimes(1);
  },
);

it("keeps unrelated validation errors distinct from source integrity", async () => {
  await i18n.changeLanguage("en-US");
  vi.stubGlobal(
    "fetch",
    vi
      .fn()
      .mockResolvedValue(
        jsonResponse({ detail: "SOURCE_CONTRACT_INTEGRITY_FAILED_OTHER" }, 422),
      ),
  );
  window.history.replaceState({}, "", "/paper/new");
  await act(async () => render(<CreatePaperSessionPage />));
  await userEvent.click(
    screen.getByRole("button", { name: "Create paper session" }),
  );
  await waitFor(() =>
    expect(screen.getByRole("alert")).toHaveTextContent("Please check"),
  );
  expect(screen.getByRole("alert")).not.toHaveTextContent("source references");
});
