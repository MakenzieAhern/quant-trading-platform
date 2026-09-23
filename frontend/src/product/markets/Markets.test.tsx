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
import { i18n } from "../../i18n";
import { writePresentationSetting } from "../../utils/presentationStorage";
import { PREFERENCES_KEY } from "../preferences";
import { ProductDataProvider } from "../ProductDataProvider";
import { useCurrentPageData } from "../dataContext";
import { marketApi } from "./api";
import { MarketsPage } from "./MarketsPage";
import {
  bars,
  dataset,
  demo,
  metadata,
  security,
  watched,
} from "./fixtures.test-data";
import type { WatchlistItem } from "./types";

beforeEach(async () => {
  await i18n.changeLanguage("en-US");
  writePresentationSetting(
    PREFERENCES_KEY,
    JSON.stringify({ priceView: "raw" }),
  );
  window.history.replaceState({}, "", "/markets");
  // jsdom does not implement the native modal API; browser focus/keyboard QA is separate.
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.setAttribute("open", "");
      },
    },
    close: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.removeAttribute("open");
      },
    },
  });
  vi.spyOn(marketApi, "datasets").mockResolvedValue([dataset, demo]);
  vi.spyOn(marketApi, "search").mockResolvedValue({
    items: [security],
    total: 1,
    limit: 20,
    offset: 0,
    metadata,
  });
  vi.spyOn(marketApi, "watchlist").mockResolvedValue({
    items: [],
    total: 0,
    limit: 20,
    offset: 0,
  });
  vi.spyOn(marketApi, "bars").mockResolvedValue(bars);
});
async function openSecurity() {
  await userEvent.click(
    await screen.findByRole("button", {
      name: `Inspect history: ${security.security_id}`,
    }),
  );
  return screen.getByRole("dialog");
}

describe("historical cache markets", () => {
  it("preserves explicit demo datasets and reacts to dataset query navigation without changing authority", async () => {
    window.history.replaceState(
      {},
      "",
      `/markets?dataset=${demo.dataset_id}&q=${encodeURIComponent(security.security_id)}`,
    );
    render(<MarketsPage />);
    expect(await screen.findByLabelText("Data source")).toHaveValue(
      demo.dataset_id,
    );
    await waitFor(() =>
      expect(marketApi.search).toHaveBeenLastCalledWith(
        demo.dataset_id,
        security.security_id,
        "ALL",
        0,
        expect.any(AbortSignal),
      ),
    );
    act(() => {
      window.history.pushState(
        {},
        "",
        `/markets?dataset=${dataset.dataset_id}&q=000001`,
      );
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(screen.getByLabelText("Data source")).toHaveValue(
      dataset.dataset_id,
    );
    await waitFor(() =>
      expect(marketApi.search).toHaveBeenLastCalledWith(
        dataset.dataset_id,
        "000001",
        "ALL",
        0,
        expect.any(AbortSignal),
      ),
    );
    act(() => {
      window.history.pushState(
        {},
        "",
        "/markets?dataset=unknown-source&q=600000",
      );
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(screen.getByLabelText("Data source")).toHaveValue("unknown-source");
    expect(
      screen.getByRole("option", {
        name: "Source unavailable · unknown-source",
      }),
    ).toHaveProperty("selected", true);
    expect(
      vi
        .mocked(marketApi.search)
        .mock.calls.some((call) => call[0] === "unknown-source"),
    ).toBe(false);
  });
  it("preserves the selected archive context when a detail opens and closes", async () => {
    function ContextReadout() {
      return (
        <output data-testid="source-context">
          {JSON.stringify(useCurrentPageData())}
        </output>
      );
    }
    render(
      <ProductDataProvider>
        <ContextReadout />
        <MarketsPage />
      </ProductDataProvider>,
    );
    await userEvent.selectOptions(
      await screen.findByLabelText("Data source"),
      demo.dataset_id,
    );
    const expected = JSON.stringify({
      mode: demo.mode,
      asOf: demo.as_of,
      dateKind: "snapshot",
    });
    expect(screen.getByTestId("source-context")).toHaveTextContent(expected);
    const dialog = await openSecurity();
    expect(screen.getByTestId("source-context")).toHaveTextContent(expected);
    expect(
      screen.getByRole("cell", { name: "Shanghai Main Board" }),
    ).toBeInTheDocument();
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Close" }),
    );
    expect(screen.getByTestId("source-context")).toHaveTextContent(expected);
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByRole("cell", { name: "沪市主板" })).toBeInTheDocument();
  });

  it("keeps an uncertain suspension boundary explicitly unknown in both languages", async () => {
    vi.mocked(marketApi.bars).mockResolvedValue({
      ...bars,
      total: 1,
      items: [
        {
          ...bars.items[1],
          status: "SUSPENSION_BOUNDARY_UNCERTAIN",
          execution_open_blocked: null,
          suspension_evidence: [
            {
              suspended_at: "2024/2/28 13:00",
              source_sha256_json: '["source-hash"]',
            },
          ],
        },
      ],
      metadata: {
        ...metadata,
        status_counts: { SUSPENSION_BOUNDARY_UNCERTAIN: 1 },
      },
    });
    render(<MarketsPage />);
    const dialog = await openSecurity();
    await within(dialog).findByLabelText("Inspect trading date");
    expect(
      within(dialog).getAllByText("Suspension boundary timing unknown").length,
    ).toBeGreaterThan(0);
    await userEvent.click(
      within(dialog).getByText("Exact observations", { selector: "summary" }),
    );
    const row = within(dialog).getByRole("row", { name: /2024-02-28/ });
    expect(within(row).getAllByRole("cell").at(-1)).toHaveTextContent(
      "Unknown",
    );
    await userEvent.click(
      within(dialog).getByText("Original suspension evidence", {
        selector: "summary",
      }),
    );
    expect(
      within(dialog).getByText(/source-hash/, { selector: "pre" }),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      within(dialog).getAllByText("停复牌边界时点未知").length,
    ).toBeGreaterThan(0);
    expect(within(row).getAllByRole("cell").at(-1)).toHaveTextContent("未知");
  });

  it("shows pending and failed detail reads with retry, and does not invent bars for an empty window", async () => {
    let reject: ((error: Error) => void) | undefined;
    vi.mocked(marketApi.bars)
      .mockImplementationOnce(
        () =>
          new Promise((_done, fail) => {
            reject = fail;
          }),
      )
      .mockResolvedValueOnce({
        ...bars,
        items: [],
        total: 0,
        metadata: { ...metadata, status_counts: {} },
      });
    render(<MarketsPage />);
    const dialog = await openSecurity();
    expect(within(dialog).getByRole("status")).toHaveTextContent(
      "Loading saved data",
    );
    await act(async () => {
      reject?.(new Error("unavailable"));
    });
    expect(within(dialog).getByRole("alert")).toHaveTextContent(
      "could not be loaded",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Retry reading cache" }),
    );
    expect(
      await within(dialog).findByText(/no prices have been filled in/),
    ).toBeInTheDocument();
    expect(within(dialog).queryByRole("img")).not.toBeInTheDocument();
    expect(marketApi.bars).toHaveBeenCalledTimes(2);
  });

  it("applies search/exchange with bounded paging and responds to global query navigation", async () => {
    vi.mocked(marketApi.search).mockImplementation(
      async (_dataset, _q, _exchange, offset) => ({
        items: [security],
        total: 45,
        limit: 20,
        offset: offset ?? 0,
        metadata,
      }),
    );
    render(<MarketsPage />);
    await screen.findByRole("button", {
      name: `Inspect history: ${security.security_id}`,
    });
    await userEvent.type(
      screen.getByLabelText("Symbol, code or source-observed name"),
      "600000",
    );
    await userEvent.selectOptions(screen.getByLabelText("Exchange"), "SSE");
    await userEvent.click(
      screen.getByRole("button", { name: "Search securities" }),
    );
    await waitFor(() =>
      expect(marketApi.search).toHaveBeenLastCalledWith(
        dataset.dataset_id,
        "600000",
        "SSE",
        0,
        expect.any(AbortSignal),
      ),
    );
    const catalog = screen.getByRole("region", { name: "Search securities" });
    await userEvent.click(
      within(catalog).getByRole("button", { name: "Next" }),
    );
    await waitFor(() =>
      expect(vi.mocked(marketApi.search).mock.calls.at(-1)?.[3]).toBe(20),
    );
    act(() => {
      window.history.pushState({}, "", "/markets?q=Observed");
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    await waitFor(() =>
      expect(marketApi.search).toHaveBeenLastCalledWith(
        dataset.dataset_id,
        "Observed",
        "SSE",
        0,
        expect.any(AbortSignal),
      ),
    );
    expect(
      screen.getByLabelText("Symbol, code or source-observed name"),
    ).toHaveValue("Observed");
  });

  it("saves once while pending and reopens the database-backed watchlist, then removes it", async () => {
    let stored: WatchlistItem[] = [];
    vi.mocked(marketApi.watchlist).mockImplementation(async () => ({
      items: stored,
      total: stored.length,
      limit: 20,
      offset: 0,
    }));
    let resolve: ((value: WatchlistItem) => void) | undefined;
    const add = vi.spyOn(marketApi, "add").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const remove = vi
      .spyOn(marketApi, "remove")
      .mockImplementation(async () => {
        stored = [];
      });
    const first = render(<MarketsPage />);
    await userEvent.dblClick(
      await screen.findByRole("button", { name: "Save to watchlist" }),
    );
    expect(add).toHaveBeenCalledTimes(1);
    expect(screen.getByRole("button", { name: "Saving…" })).toBeDisabled();
    await act(async () => {
      stored = [watched];
      resolve?.(watched);
    });
    await screen.findByText("Saved to your watchlist.");
    first.unmount();
    render(<MarketsPage />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Remove from watchlist" }),
    );
    expect(remove).toHaveBeenCalledWith(
      dataset.dataset_id,
      security.security_id,
    );
    expect(
      await screen.findByText(
        "Your watchlist is empty. Save a security from the search results.",
      ),
    ).toBeInTheDocument();
  });

  it("uses the stored price-view default while preserving exact strings, gaps and dates across locale changes", async () => {
    writePresentationSetting(
      PREFERENCES_KEY,
      JSON.stringify({ priceView: "adjusted" }),
    );
    render(<MarketsPage />);
    const dialog = await openSecurity();
    expect(within(dialog).getByLabelText("Price view")).toHaveValue("adjusted");
    await userEvent.selectOptions(
      within(dialog).getByLabelText("Inspect trading date"),
      "2024-02-27",
    );
    expect(
      within(dialog).getByText("20.246913578024691356", { selector: "dd" }),
    ).toBeInTheDocument();
    await userEvent.selectOptions(
      within(dialog).getByLabelText("Price view"),
      "raw",
    );
    expect(
      within(dialog).getByText("10.123456789012345678", { selector: "dd" }),
    ).toBeInTheDocument();
    expect(
      within(dialog).getByText("100,000.000000000000000001", {
        selector: "dd",
      }),
    ).toBeInTheDocument();
    const path = dialog.querySelector(".marketPriceLine")?.getAttribute("d");
    expect(path?.match(/M/g)).toHaveLength(2);
    expect(path).not.toContain("L");
    await userEvent.selectOptions(
      within(dialog).getByLabelText("Inspect trading date"),
      "2024-02-29",
    );
    expect(
      within(dialog).getByText("12.000000000000000001", { selector: "dd" }),
    ).toBeInTheDocument();
    expect(within(dialog).getAllByText("N/A").length).toBeGreaterThan(1);
    expect(
      within(dialog).getByText(/not complete, executable OHLCV bars/),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(within(dialog).getByLabelText("开始日期")).toHaveValue("2024-02-27");
    expect(within(dialog).getByLabelText("结束日期")).toHaveValue("2024-02-29");
    expect(within(dialog).getByLabelText("价格视图")).toHaveValue("raw");
    expect(marketApi.bars).toHaveBeenCalledTimes(1);
  });

  it("rejects an overlong date window without silently clipping it and restores trigger focus", async () => {
    render(<MarketsPage />);
    const trigger = await screen.findByRole("button", {
      name: `Inspect history: ${security.security_id}`,
    });
    await userEvent.click(trigger);
    const dialog = screen.getByRole("dialog");
    await within(dialog).findByLabelText("Inspect trading date");
    fireEvent.change(within(dialog).getByLabelText("First date"), {
      target: { value: "2023-01-01" },
    });
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Read this date window" }),
    );
    expect(within(dialog).getByRole("alert")).toHaveTextContent(
      "Dates have not been changed",
    );
    expect(within(dialog).getByLabelText("First date")).toHaveValue(
      "2023-01-01",
    );
    expect(marketApi.bars).toHaveBeenCalledTimes(1);
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Close" }),
    );
    expect(trigger).toHaveFocus();
    await userEvent.click(trigger);
    expect(screen.getByLabelText("First date")).toHaveValue("2023-01-01");
  });

  it("keeps unavailable historical records removable while clearly labeling the demo", async () => {
    vi.mocked(marketApi.datasets).mockResolvedValue([
      {
        ...dataset,
        available: false,
        reason_code: "DATASET_NOT_MOUNTED",
        as_of: null,
        sha256: null,
      },
      demo,
    ]);
    vi.mocked(marketApi.watchlist).mockResolvedValue({
      items: [
        {
          ...watched,
          source_available: false,
          source_reason_code: "DATASET_NOT_MOUNTED",
        },
      ],
      total: 1,
      limit: 20,
      offset: 0,
    });
    const remove = vi.spyOn(marketApi, "remove").mockResolvedValue(undefined);
    render(<MarketsPage />);
    expect(
      await screen.findByText(
        "Synthetic prices demonstrate the interface only. They are not market prices or investment evidence.",
      ),
    ).toBeInTheDocument();
    expect(
      await screen.findByRole("button", { name: "Inspect history" }),
    ).toBeDisabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Remove from watchlist" }),
    );
    expect(remove).toHaveBeenCalledWith(
      dataset.dataset_id,
      security.security_id,
    );
    await userEvent.selectOptions(
      screen.getByLabelText("Data source"),
      dataset.dataset_id,
    );
    expect(
      await screen.findByText(
        /Optional historical archives must already be mounted/,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Search securities" }),
    ).toBeDisabled();
  });

  it("shows honest empty and failed cache reads and provides retry", async () => {
    vi.mocked(marketApi.search)
      .mockRejectedValueOnce(new Error("offline"))
      .mockResolvedValue({
        items: [],
        total: 0,
        limit: 20,
        offset: 0,
        metadata,
      });
    render(<MarketsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "saved data could not be loaded",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Retry reading cache" }),
    );
    expect(
      await screen.findByText(
        "No securities match these filters. Try another code or exchange.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("link", { name: "Open data center" }),
    ).toHaveAttribute("href", "/data");
  });
});
