import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { i18n } from "../i18n";
import { CommandPalette } from "./CommandPalette";
import { experimentApi } from "./experiments/api";
import { capabilities, job } from "./experiments/fixtures.test-data";
import { marketApi } from "./markets/api";
import { demo, watched } from "./markets/fixtures.test-data";
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
  vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
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
  it("searches older server records instead of filtering recent entries and preserves dataset links", async () => {
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
    await userEvent.click(watch);
    expect(close).toHaveBeenCalledOnce();
    expect(location.search).toContain(encodeURIComponent(demo.dataset_id));
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
    await userEvent.click(screen.getByRole("button", { name: "Try again" }));
    await waitFor(() => expect(experimentApi.list).toHaveBeenCalledTimes(2));
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
});
