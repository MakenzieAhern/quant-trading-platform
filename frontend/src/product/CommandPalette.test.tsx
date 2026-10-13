import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { StrictMode, useState } from "react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { CommandPalette } from "./CommandPalette";
import { HelpPage } from "./ProductPages";
import { experimentApi } from "./experiments/api";
import { capabilities, job } from "./experiments/fixtures.test-data";
import { marketApi } from "./markets/api";
import { dataset, demo, watched } from "./markets/fixtures.test-data";
import type { Experiment, Page } from "./experiments/types";

beforeEach(async () => {
  await i18n.changeLanguage("en-US");
  window.history.replaceState({}, "", "/");
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
  vi.spyOn(experimentApi, "capabilities").mockResolvedValue({
    ...capabilities,
    datasets: [dataset, demo],
  });
  vi.spyOn(experimentApi, "list").mockResolvedValue({
    items: [],
    total: 0,
    limit: 20,
    offset: 0,
  });
  vi.spyOn(marketApi, "watchlist").mockResolvedValue({
    items: [],
    total: 0,
    limit: 20,
    offset: 0,
  });
});
describe("bounded server command search", () => {
  it.each([
    ["drawdown", "What is maximum drawdown?"],
    ["benchmark", "Why compare with a benchmark?"],
  ])(
    "reveals %s after closing a real same-page search dialog",
    async (topic, question) => {
      window.history.replaceState({}, "", "/help#help-drawdown");
      function HelpSearch() {
        const [open, setOpen] = useState(false);
        return (
          <>
            <button onClick={() => setOpen(true)}>Search</button>
            <HelpPage />
            {open && <CommandPalette onClose={() => setOpen(false)} />}
          </>
        );
      }
      render(<HelpSearch />);
      const drawdown = screen.getByText("What is maximum drawdown?");
      await waitFor(() => expect(drawdown).toHaveFocus());
      fireEvent.click(drawdown);
      expect(drawdown.closest("details")).not.toHaveAttribute("open");
      await userEvent.click(screen.getByRole("button", { name: "Search" }));
      fireEvent.change(screen.getByRole("searchbox"), {
        target: { value: topic },
      });
      const command = await screen.findByRole("link", { name: question });
      command.focus();
      await userEvent.keyboard("{Enter}");
      await waitFor(() =>
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
      );
      const answer = screen.getByText(question);
      expect(answer.closest("details")).toHaveAttribute("open");
      await waitFor(() => expect(answer).toHaveFocus());
      expect(location.hash).toBe(`#help-${topic}`);
    },
  );

  it.each([
    [
      "en-US",
      "local-app",
      "GitHub",
      "Can I use the local app while GitHub CI/CD is unavailable?",
    ],
    ["zh-CN", "local-app", "GitHub", "GitHub CI/CD 暂停时，本地平台还能用吗？"],
    ["en-US", "backtest", "backtest", "What is a backtest?"],
    ["en-US", "drawdown", "drawdown", "What is maximum drawdown?"],
    [
      "en-US",
      "win",
      "win rate",
      "Is a high win rate the same as a good return?",
    ],
    ["en-US", "benchmark", "benchmark", "Why compare with a benchmark?"],
    ["zh-CN", "backtest", "回测", "什么是回测？"],
    ["zh-CN", "drawdown", "回撤", "什么是最大回撤？"],
    ["zh-CN", "win", "胜率", "胜率高，收益就好吗？"],
    ["zh-CN", "benchmark", "基准", "为什么要看基准？"],
  ])(
    "finds the %s %s help answer without a task submission",
    async (locale, topic, query, question) => {
      await i18n.changeLanguage(locale);
      const create = vi.spyOn(experimentApi, "create");
      const close = vi.fn();
      render(<CommandPalette onClose={close} />);
      fireEvent.change(screen.getByRole("searchbox"), {
        target: { value: query },
      });
      const answer = await screen.findByRole("link", { name: question });
      expect(answer).toHaveAttribute("href", `/help#help-${topic}`);
      answer.focus();
      await userEvent.keyboard("{Enter}");
      expect(location.pathname).toBe("/help");
      expect(location.hash).toBe(`#help-${topic}`);
      expect(close).toHaveBeenCalledOnce();
      expect(create).not.toHaveBeenCalled();
    },
  );

  it.each([
    [
      "en-US",
      "Matching personal studies — Pagination",
      "Matching watchlist entries — Pagination",
    ],
    ["zh-CN", "匹配的个人研究 — 分页", "匹配的自选记录 — 分页"],
  ])(
    "distinguishes both %s result pagers",
    async (language, studies, watchlist) => {
      await i18n.changeLanguage(language);
      render(<CommandPalette onClose={() => undefined} />);
      expect(screen.getByRole("group", { name: studies })).toBeInTheDocument();
      expect(
        screen.getByRole("group", { name: watchlist }),
      ).toBeInTheDocument();
    },
  );

  it("sends the new-study command to the explicit fresh-start choice", () => {
    render(<CommandPalette onClose={() => undefined} />);
    expect(
      screen.getByRole("link", { name: "Start guided backtest" }),
    ).toHaveAttribute("href", "/research/new?new=1");
  });

  it("does not offer same-route new navigation while a wizard is already open", () => {
    window.history.replaceState({}, "", "/research/new");
    render(<CommandPalette onClose={() => undefined} />);
    expect(
      screen.queryByRole("link", { name: "Start guided backtest" }),
    ).toBeNull();
  });

  it("focuses search on opening and returns to the original trigger on closing", () => {
    const view = render(
      <>
        <button>Open command search</button>
      </>,
    );
    const trigger = screen.getByRole("button", { name: "Open command search" });
    trigger.focus();
    view.rerender(
      <>
        <button>Open command search</button>
        <StrictMode>
          <CommandPalette onClose={() => undefined} />
        </StrictMode>
      </>,
    );
    expect(screen.getByRole("searchbox")).toHaveFocus();
    view.rerender(
      <>
        <button>Open command search</button>
      </>,
    );
    expect(trigger).toHaveFocus();
  });

  it("closes on the first Escape even when the native search field has text", async () => {
    const close = vi.fn();
    render(<CommandPalette onClose={close} />);
    const search = screen.getByRole("searchbox");
    fireEvent.change(search, { target: { value: "saved study" } });
    fireEvent.keyDown(search, { key: "Escape" });
    expect(close).toHaveBeenCalledOnce();
  });

  it("keeps each category's empty message accurate when the other has a match", async () => {
    vi.mocked(marketApi.watchlist).mockResolvedValue({
      items: [watched],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<CommandPalette onClose={() => undefined} />);
    expect(
      await screen.findByText(
        "No personal studies match. Try a different name or ID.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(
        "No saved securities match. Try a symbol or security ID.",
      ),
    ).not.toBeInTheDocument();
  });
  it("searches older server records and opens the exact saved security", async () => {
    vi.mocked(experimentApi.list).mockImplementation(
      async (_signal, _limit, offset, q) => ({
        items:
          q === "Older"
            ? [{ ...job, name: "Older result outside recent page" }]
            : [],
        total: q === "Older" ? 1 : 0,
        limit: 20,
        offset: offset ?? 0,
      }),
    );
    vi.mocked(marketApi.watchlist).mockImplementation(
      async (offset, _signal, q) => ({
        items:
          q === "Older"
            ? [
                {
                  ...watched,
                  dataset_id: demo.dataset_id,
                  security: { ...watched.security, name: "Older demo" },
                },
              ]
            : [],
        total: q === "Older" ? 1 : 0,
        limit: 20,
        offset: offset ?? 0,
      }),
    );
    const close = vi.fn();
    render(<CommandPalette onClose={close} />);
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Older" },
    });
    const found = await screen.findByRole("link", {
      name: /Older result outside recent page/,
    });
    expect(found).toHaveAttribute("href", `/experiments/${job.job_id}`);
    expect(experimentApi.list).toHaveBeenLastCalledWith(
      expect.any(AbortSignal),
      20,
      0,
      "Older",
    );
    const watch = screen.getByRole("link", { name: /Older demo/ });
    const url = new URL(watch.getAttribute("href")!, "http://local");
    expect(url.searchParams.get("dataset")).toBe(demo.dataset_id);
    expect(url.searchParams.get("q")).toBe(watched.security_id);
    const detail = new URLSearchParams(url.hash.slice(1));
    expect(detail.get("dataset")).toBe(demo.dataset_id);
    expect(detail.get("security")).toBe(watched.security_id);
    await userEvent.click(watch);
    expect(close).toHaveBeenCalledOnce();
    expect(location.search).toContain(encodeURIComponent(demo.dataset_id));
    expect(location.hash).toBe(url.hash);
  });
  it.each([
    {
      reason: "changed source rejected by the server",
      item: {
        ...watched,
        dataset_sha256: "0".repeat(64),
        source_available: false,
      },
      source: dataset,
    },
    {
      reason: "current source SHA mismatch",
      item: { ...watched, dataset_sha256: "0".repeat(64) },
      source: dataset,
    },
    {
      reason: "missing server source authority",
      item: { ...watched, source_available: undefined },
      source: dataset,
    },
    {
      reason: "unavailable current source",
      item: watched,
      source: { ...dataset, available: false },
    },
    {
      reason: "missing current source",
      item: watched,
      source: undefined,
    },
    {
      reason: "different current source identity",
      item: watched,
      source: { ...dataset, dataset_id: "another-dataset" },
    },
    {
      reason: "unknown current source SHA",
      item: watched,
      source: { ...dataset, sha256: null },
    },
  ])(
    "blocks saved-source navigation for $reason without hiding the entry",
    async ({ item, source }) => {
      vi.mocked(experimentApi.capabilities).mockResolvedValue({
        ...capabilities,
        datasets: source ? [source] : [],
      });
      vi.mocked(marketApi.watchlist).mockResolvedValue({
        items: [item],
        total: 1,
        limit: 20,
        offset: 0,
      });
      const close = vi.fn();
      render(<CommandPalette onClose={close} />);
      const result = await screen.findByRole("button", {
        name: /Observed Bank.*600000/,
      });
      expect(result).toBeDisabled();
      expect(result).toHaveTextContent("saved data source unavailable");
      expect(screen.queryByRole("link", { name: /600000/ })).toBeNull();
      await userEvent.click(result);
      expect(close).not.toHaveBeenCalled();
      expect(location.pathname).toBe("/");
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(result).toHaveTextContent("保存的数据来源不可用");
      expect(result).toBeDisabled();
    },
  );
  it("opens a matching source for read-only inspection when execution is unavailable", async () => {
    vi.mocked(experimentApi.capabilities).mockResolvedValue({
      ...capabilities,
      datasets: [{ ...dataset, execution_available: false }],
    });
    vi.mocked(marketApi.watchlist).mockResolvedValue({
      items: [watched],
      total: 1,
      limit: 20,
      offset: 0,
    });
    const close = vi.fn();
    render(<CommandPalette onClose={close} />);
    const result = await screen.findByRole("link", {
      name: /Observed Bank.*600000/,
    });
    result.focus();
    await userEvent.keyboard("{Enter}");
    expect(close).toHaveBeenCalledOnce();
    expect(location.pathname).toBe("/markets");
    const detail = new URLSearchParams(location.hash.slice(1));
    expect(detail.get("dataset")).toBe(watched.dataset_id);
    expect(detail.get("security")).toBe(watched.security_id);
  });
  it("loads the next bounded page with unchanged query instead of downloading all results", async () => {
    vi.mocked(experimentApi.list).mockImplementation(
      async (_signal, _limit, offset = 0, q) => ({
        items: q ? [{ ...job, name: `Match at ${offset}` }] : [],
        total: q ? 42 : 0,
        limit: 20,
        offset,
      }),
    );
    render(<CommandPalette onClose={() => undefined} />);
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Match" },
    });
    await screen.findByRole("link", { name: /Match at 0/ });
    const group = screen.getByRole("region", {
      name: "Matching personal studies",
    });
    expect(
      within(group).getByText(/More matches are available/),
    ).toBeInTheDocument();
    await userEvent.click(within(group).getByRole("button", { name: "Next" }));
    expect(
      await screen.findByRole("link", { name: /Match at 20/ }),
    ).toBeInTheDocument();
    expect(experimentApi.list).toHaveBeenLastCalledWith(
      expect.any(AbortSignal),
      20,
      20,
      "Match",
    );
  });
  it("debounces, aborts obsolete server requests and ignores late old responses", async () => {
    let oldSignal: AbortSignal | undefined;
    let oldResolve: ((page: Page<Experiment>) => void) | undefined;
    vi.mocked(experimentApi.list).mockImplementation(
      (signal, _limit, offset = 0, q) => {
        if (q === "old") {
          oldSignal = signal;
          return new Promise((resolve) => {
            oldResolve = resolve;
          });
        }
        return Promise.resolve({
          items: q === "new" ? [{ ...job, name: "Newest match" }] : [],
          total: q === "new" ? 1 : 0,
          limit: 20,
          offset,
        });
      },
    );
    render(<CommandPalette onClose={() => undefined} />);
    fireEvent.change(screen.getByRole("searchbox"), { target: { value: "o" } });
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "old" },
    });
    await waitFor(() => expect(oldSignal).toBeDefined());
    expect(
      vi.mocked(experimentApi.list).mock.calls.some((call) => call[3] === "o"),
    ).toBe(false);
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "new" },
    });
    expect(
      await screen.findByRole("link", { name: /Newest match/ }),
    ).toBeInTheDocument();
    expect(oldSignal?.aborted).toBe(true);
    await act(async () =>
      oldResolve?.({
        items: [{ ...job, name: "Obsolete match" }],
        total: 1,
        limit: 20,
        offset: 0,
      }),
    );
    expect(
      screen.queryByRole("link", { name: /Obsolete match/ }),
    ).not.toBeInTheDocument();
  });
  it("shows failures distinctly from empty results, retries and preserves a bounded query across locale", async () => {
    vi.mocked(experimentApi.list).mockRejectedValueOnce(new Error("offline"));
    render(<CommandPalette onClose={() => undefined} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "not an empty-results claim",
    );
    const retry = screen.getByRole("button", { name: "Try again" });
    retry.focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() => expect(experimentApi.list).toHaveBeenCalledTimes(2));
    await waitFor(() =>
      expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
    );
    expect(screen.getByRole("searchbox")).toHaveFocus();
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "界".repeat(90) },
    });
    expect(screen.getByRole("searchbox")).toHaveValue("界".repeat(80));
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByRole("searchbox")).toHaveValue("界".repeat(80));
    await waitFor(() =>
      expect(experimentApi.list).toHaveBeenLastCalledWith(
        expect.any(AbortSignal),
        20,
        0,
        "界".repeat(80),
      ),
    );
  });
  it.each([
    {
      language: "en-US",
      error: new ApiError(403, "denied"),
      expected: "Access was denied",
    },
    {
      language: "zh-CN",
      error: new ApiError(403, "denied"),
      expected: "访问被拒绝",
    },
    {
      language: "en-US",
      error: new ApiError(408, "timeout"),
      expected: "request timed out",
    },
    {
      language: "zh-CN",
      error: new ApiError(408, "timeout"),
      expected: "请求超时",
    },
    {
      language: "en-US",
      error: new TypeError("offline"),
      expected: "service is unavailable",
    },
    {
      language: "zh-CN",
      error: new TypeError("offline"),
      expected: "服务暂时无法连接",
    },
  ])(
    "explains $language search failure without hiding successful sources",
    async ({ language, error, expected }) => {
      await i18n.changeLanguage(language);
      vi.mocked(experimentApi.list).mockRejectedValue(error);
      vi.mocked(marketApi.watchlist).mockResolvedValue({
        items: [watched],
        total: 1,
        limit: 20,
        offset: 0,
      });
      render(<CommandPalette onClose={() => undefined} />);
      expect(await screen.findByRole("alert")).toHaveTextContent(expected);
      expect(screen.getByRole("link", { name: /600000/ })).toBeInTheDocument();
      expect(experimentApi.list).toHaveBeenCalledTimes(1);
    },
  );
});
