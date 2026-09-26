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
import { ApiError } from "../../api/client";
import { i18n } from "../../i18n";
import { marketUpdateApi } from "./api";
import { MarketUpdatesPanel } from "./MarketUpdatesPanel";
import { caps, job, observations, receipt } from "./fixtures.test-data";
import { UPDATE_DRAFT_KEY } from "./intent";
import type { UpdateJob } from "./types";

beforeEach(async () => {
  localStorage.removeItem(UPDATE_DRAFT_KEY);
  window.history.replaceState({}, "", "/data");
  await i18n.changeLanguage("en-US");
  vi.spyOn(marketUpdateApi, "capabilities").mockResolvedValue(caps);
  vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
    items: [job],
    total: 1,
    limit: 20,
    offset: 0,
  });
  vi.spyOn(marketUpdateApi, "get").mockResolvedValue(job);
  vi.spyOn(marketUpdateApi, "receipts").mockResolvedValue({
    items: [receipt],
    total: 1,
    limit: 20,
    offset: 0,
  });
  vi.spyOn(marketUpdateApi, "observations").mockResolvedValue(observations);
});
async function fill() {
  await screen.findByLabelText("Security IDs (1–20)");
  fireEvent.change(screen.getByLabelText("Security IDs (1–20)"), {
    target: { value: "CN-A:SSE:600000" },
  });
  fireEvent.input(screen.getByLabelText("Start date"), {
    target: { value: "2026-01-05" },
  });
  fireEvent.input(screen.getByLabelText("End date"), {
    target: { value: "2026-01-06" },
  });
  await userEvent.click(screen.getByRole("checkbox"));
}
describe("explicit incremental request workflow", () => {
  it("names native candidate observations and its translated scroll region without acquiring data", async () => {
    const create = vi.spyOn(marketUpdateApi, "create");
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const table = await screen.findByRole("table", {
      name: "Candidate observations",
    });
    const scroll = screen.getByRole("region", {
      name: "Candidate observations · Scrollable exact observation table",
    });
    expect(scroll).toHaveAttribute("tabindex", "0");
    expect(scroll).toContainElement(table);
    expect(
      within(table).getByText("12.000000000000000001"),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    const translated = screen.getByRole("table", { name: "候选观察值" });
    expect(
      screen.getByRole("region", {
        name: "候选观察值 · 可滚动的精确观察值表",
      }),
    ).toContainElement(translated);
    expect(
      within(translated).getByText("125,000.000000000000000009"),
    ).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
  });
  it("names saved task controls by security, dates and time in both languages", async () => {
    render(<MarketUpdatesPanel />);
    expect(
      await screen.findByRole("button", {
        name: /^Open task: CN-A:SSE:600000 · 2026-01-05–2026-01-06 · 2026-09-22/,
      }),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByRole("button", {
        name: /^打开任务: CN-A:SSE:600000 · 2026-01-05–2026-01-06 · 2026\/09\/22/,
      }),
    ).toBeInTheDocument();
  });
  it("explains a denied capability read and recovers only after explicit refresh", async () => {
    const create = vi.spyOn(marketUpdateApi, "create");
    vi.mocked(marketUpdateApi.capabilities).mockRejectedValue(
      new ApiError(403, "denied"),
    );
    render(<MarketUpdatesPanel />);
    expect(
      await screen.findByText(/The service denied this request/),
    ).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByText(/服务拒绝了此请求/)).toBeInTheDocument();
    vi.mocked(marketUpdateApi.capabilities).mockResolvedValue(caps);
    await userEvent.click(screen.getByRole("button", { name: "刷新" }));
    expect(
      await screen.findByLabelText("证券标识（1–20 个）"),
    ).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
  });
  it("never acquires on open; preserves dates across language changes and waits for explicit consent", async () => {
    const create = vi.spyOn(marketUpdateApi, "create");
    render(<MarketUpdatesPanel />);
    await fill();
    expect(create).not.toHaveBeenCalled();
    expect(screen.getByRole("checkbox")).toHaveAccessibleName(
      /Data-use rights for this app remain unverified/,
    );
    await userEvent.click(screen.getByText("Provider source and terms"));
    expect(
      screen.getByText(/exchange-data rights for this app/),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByLabelText("开始日期")).toHaveValue("2026-01-05");
    expect(screen.getByLabelText("结束日期")).toHaveValue("2026-01-06");
    expect(screen.getByRole("checkbox")).toHaveAccessibleName(
      /本应用的数据使用权仍未核实/,
    );
    expect(screen.getByText(/不代表来源验收通过/)).toBeInTheDocument();
    expect(screen.getByText(/本应用使用交易所数据的权利/)).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
  });
  it("locks duplicate submit clicks and navigates only after the server returns its durable job", async () => {
    let resolve: ((value: UpdateJob) => void) | undefined;
    const create = vi.spyOn(marketUpdateApi, "create").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    render(<MarketUpdatesPanel />);
    await fill();
    await userEvent.dblClick(
      screen.getByRole("button", { name: "Request selected raw data" }),
    );
    expect(create).toHaveBeenCalledTimes(1);
    expect(
      screen.getByRole("button", { name: "Submitting request…" }),
    ).toBeDisabled();
    expect(location.search).toBe("");
    await act(async () => resolve?.(job));
    expect(location.search).toBe(`?updateJob=${job.job_id}`);
    expect(
      await screen.findByText(
        "Bounded raw requests completed. Candidate-only status is unchanged.",
      ),
    ).toBeInTheDocument();
  });
  it("reopens an uncertain submission with the same identity and does not submit automatically", async () => {
    const create = vi
      .spyOn(marketUpdateApi, "create")
      .mockRejectedValue(new ApiError(408, "timeout"));
    const first = render(<MarketUpdatesPanel />);
    await fill();
    await userEvent.click(
      screen.getByRole("button", { name: "Request selected raw data" }),
    );
    await screen.findByText(/Check service state and saved task history/);
    const key = create.mock.calls[0][1];
    first.unmount();
    render(<MarketUpdatesPanel />);
    await screen.findByLabelText("Security IDs (1–20)");
    expect(create).toHaveBeenCalledTimes(1);
    expect(screen.getByLabelText("Start date")).toHaveValue("2026-01-05");
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(
      screen.getByRole("button", { name: "Request selected raw data" }),
    );
    expect(create.mock.calls[1][1]).toBe(key);
    fireEvent.change(screen.getByLabelText("Security IDs (1–20)"), {
      target: { value: " CN-A:SSE:600000, " },
    });
    expect(JSON.parse(localStorage.getItem(UPDATE_DRAFT_KEY)!).requestKey).toBe(
      key,
    );
  });
  it("prevents acquisition with invalid scope or unavailable storage/source", async () => {
    const create = vi.spyOn(marketUpdateApi, "create");
    render(<MarketUpdatesPanel />);
    await fill();
    fireEvent.change(screen.getByLabelText("Security IDs (1–20)"), {
      target: { value: "CN-A:SSE:600000 CN-A:SSE:600000" },
    });
    await userEvent.click(screen.getByRole("checkbox"));
    await userEvent.click(
      screen.getByRole("button", { name: "Request selected raw data" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent(
      "distinct canonical IDs",
    );
    expect(create).not.toHaveBeenCalled();
    fireEvent.change(screen.getByLabelText("Security IDs (1–20)"), {
      target: { value: "CN-A:SSE:600000" },
    });
    await userEvent.click(screen.getByRole("checkbox"));
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("full", "QuotaExceededError");
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Request selected raw data" }),
    );
    expect(
      screen.getByText(
        /This request has not been submitted without a saved identity/,
      ),
    ).toBeInTheDocument();
    expect(create).not.toHaveBeenCalled();
  });
  it("reopens saved task URLs with exact observations, receipt hashes and honest unresolved dates", async () => {
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const table = await screen.findByRole("region", {
      name: "Candidate observations · Scrollable exact observation table",
    });
    expect(
      within(table).getByText("12.000000000000000001"),
    ).toBeInTheDocument();
    expect(
      within(table).getByText("125,000.000000000000000009"),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/not verified missing trading sessions/),
    ).toBeInTheDocument();
    await userEvent.click(
      screen.getByText("All unresolved dates for this security (1)"),
    );
    expect(
      screen.getByText("2026-01-06", { selector: ".updateGapDates" }),
    ).toBeInTheDocument();
    await userEvent.click(screen.getByText(/Rows in receipt: 1/));
    expect(
      screen.getByText(receipt.manifest_sha256, { selector: "dd" }),
    ).toBeInTheDocument();
  });
  it("cancels only by explicit command and never turns retained receipts into authority", async () => {
    const running = {
      ...job,
      status: "RUNNING" as const,
      phase: "FETCHING_RAW_CANDIDATES",
      completed_at: null,
      summary: null,
    };
    vi.mocked(marketUpdateApi.get).mockResolvedValue(running);
    const cancel = vi
      .spyOn(marketUpdateApi, "cancel")
      .mockResolvedValue({ ...running, cancel_requested: true });
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const button = await screen.findByRole("button", {
      name: "Request cancellation",
    });
    expect(cancel).not.toHaveBeenCalled();
    await userEvent.click(button);
    expect(cancel).toHaveBeenCalledExactlyOnceWith(job.job_id);
    expect(
      screen.getByText(/cannot be used for execution or forward acceptance/),
    ).toBeInTheDocument();
  });
  it("retry uses backend child semantics and source denial prevents further task requests", async () => {
    const failed = {
      ...job,
      status: "FAILED" as const,
      phase: "FAILED",
      error_code: "PROVIDER_TIMEOUT",
      summary: null,
    };
    vi.mocked(marketUpdateApi.get).mockResolvedValue(failed);
    const retry = vi.spyOn(marketUpdateApi, "retry").mockResolvedValue({
      ...job,
      job_id: "ab000000-0000-4000-8000-000000000002",
      retry_of: job.job_id,
    });
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    const view = render(<MarketUpdatesPanel />);
    await userEvent.click(
      await screen.findByRole("button", {
        name: "Retry this unsuccessful task",
      }),
    );
    expect(retry).toHaveBeenCalledExactlyOnceWith(job.job_id);
    expect(location.search).toContain("000000000002");
    view.unmount();
    vi.mocked(marketUpdateApi.get).mockResolvedValue({
      ...failed,
      error_code: "SOURCE_ACCESS_DENIED",
    });
    vi.mocked(marketUpdateApi.capabilities).mockResolvedValue({
      ...caps,
      available: false,
      reason_code: "SOURCE_ACCESS_DENIED",
    });
    render(<MarketUpdatesPanel />);
    expect(
      await screen.findByRole("button", {
        name: "Retry this unsuccessful task",
      }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Request selected raw data" }),
    ).toBeDisabled();
  });
  it("blocks acquisition and retry when original receipt persistence failed", async () => {
    const retry = vi.spyOn(marketUpdateApi, "retry");
    vi.mocked(marketUpdateApi.get).mockResolvedValue({
      ...job,
      status: "FAILED",
      phase: "FAILED",
      error_code: "RECEIPT_PERSISTENCE_BLOCKED",
      summary: null,
    });
    vi.mocked(marketUpdateApi.capabilities).mockResolvedValue({
      ...caps,
      available: false,
      reason_code: "RECEIPT_PERSISTENCE_BLOCKED",
    });
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    expect(
      await screen.findByRole("button", {
        name: "Retry this unsuccessful task",
      }),
    ).toBeDisabled();
    expect(
      screen.getByRole("button", { name: "Request selected raw data" }),
    ).toBeDisabled();
    expect(
      screen.getAllByText(/preserve the original reception evidence/).length,
    ).toBeGreaterThan(0);
    expect(retry).not.toHaveBeenCalled();
  });
  it("stops status polling on a read failure until manual refresh", async () => {
    vi.mocked(marketUpdateApi.get).mockRejectedValue(
      new ApiError(404, "missing", "MARKET_UPDATE_NOT_FOUND"),
    );
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    expect(
      await screen.findByText("This saved update task could not be found."),
    ).toBeInTheDocument();
    expect(marketUpdateApi.get).toHaveBeenCalledTimes(1);
    const detail = screen.getByRole("region", { name: `Task: ${job.job_id}` });
    await userEvent.click(
      within(detail).getByRole("button", { name: "Refresh" }),
    );
    await waitFor(() => expect(marketUpdateApi.get).toHaveBeenCalledTimes(2));
  });
  it("does not present an old completed task as current after a refresh failure", async () => {
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const detail = await screen.findByRole("region", {
      name: `Task: ${job.job_id}`,
    });
    expect(
      await within(detail).findByText(
        "Bounded raw requests completed. Candidate-only status is unchanged.",
      ),
    ).toBeInTheDocument();
    vi.mocked(marketUpdateApi.get).mockRejectedValueOnce(
      new ApiError(503, "service unavailable"),
    );
    await userEvent.click(
      within(detail).getAllByRole("button", { name: "Refresh" })[0],
    );
    expect(
      await within(detail).findByText(/Request could not be completed/),
    ).toBeInTheDocument();
    expect(
      within(detail).queryByText(
        "Bounded raw requests completed. Candidate-only status is unchanged.",
      ),
    ).not.toBeInTheDocument();
    await userEvent.click(
      within(detail).getByRole("button", { name: "Refresh" }),
    );
    expect(
      await within(detail).findByText(
        "Bounded raw requests completed. Candidate-only status is unchanged.",
      ),
    ).toBeInTheDocument();
  });
  it("announces loading instead of showing stale completion during manual refresh", async () => {
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const detail = await screen.findByRole("region", {
      name: `Task: ${job.job_id}`,
    });
    const completed =
      "Bounded raw requests completed. Candidate-only status is unchanged.";
    expect(await within(detail).findByText(completed)).toBeInTheDocument();
    let finish!: (result: UpdateJob) => void;
    vi.mocked(marketUpdateApi.get).mockImplementationOnce(
      () => new Promise((resolve) => (finish = resolve)),
    );
    await userEvent.click(
      within(detail).getAllByRole("button", { name: "Refresh" })[0],
    );
    expect(within(detail).queryByText(completed)).not.toBeInTheDocument();
    expect(within(detail).getByRole("status")).toHaveTextContent(
      "Loading saved state…",
    );
    await act(async () => finish(job));
    expect(await within(detail).findByText(completed)).toBeInTheDocument();
  });
});
