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
import { UpdateRecords } from "./UpdateRecords";
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
  it("keeps active history visible until its terminal update and then stops polling", async () => {
    vi.useFakeTimers();
    const running: UpdateJob = { ...job, status: "RUNNING" };
    let complete!: (value: {
      items: UpdateJob[];
      total: number;
      limit: number;
      offset: number;
    }) => void;
    const list = vi
      .mocked(marketUpdateApi.list)
      .mockResolvedValueOnce({
        items: [running],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockImplementationOnce(
        () => new Promise((resolve) => (complete = resolve)),
      );
    render(<MarketUpdatesPanel />);
    await act(async () => {});
    const history = screen.getByRole("region", { name: "Update task history" });
    expect(within(history).getByRole("status")).toHaveTextContent("Running");
    await act(async () => vi.advanceTimersByTime(5000));
    expect(list).toHaveBeenCalledTimes(2);
    expect(within(history).getByRole("status")).toHaveTextContent("Running");
    await act(async () =>
      complete({ items: [job], total: 1, limit: 20, offset: 0 }),
    );
    expect(within(history).getByRole("status")).toHaveTextContent(
      "Requests completed",
    );
    await act(async () => vi.advanceTimersByTime(10000));
    expect(list).toHaveBeenCalledTimes(2);
  });
  it("hides an unconfirmed active status after a polling error until explicit refresh", async () => {
    vi.useFakeTimers();
    const running: UpdateJob = { ...job, status: "RUNNING" };
    const list = vi
      .mocked(marketUpdateApi.list)
      .mockResolvedValueOnce({
        items: [running],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockRejectedValueOnce(new ApiError(503, "unavailable"))
      .mockResolvedValueOnce({ items: [job], total: 1, limit: 20, offset: 0 });
    render(<MarketUpdatesPanel />);
    await act(async () => {});
    const history = screen.getByRole("region", { name: "Update task history" });
    expect(within(history).getByRole("status")).toHaveTextContent("Running");
    within(history)
      .getByRole("button", { name: /^Open task:/ })
      .focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(within(history).getByRole("alert")).toBeInTheDocument();
    expect(within(history).getByRole("alert")).toHaveFocus();
    expect(within(history).queryByText("Running")).not.toBeInTheDocument();
    await act(async () => vi.advanceTimersByTime(10000));
    expect(list).toHaveBeenCalledTimes(2);
    await act(async () =>
      fireEvent.click(screen.getByRole("button", { name: "Refresh" })),
    );
    expect(within(history).getByRole("status")).toHaveTextContent(
      "Requests completed",
    );
    expect(list).toHaveBeenCalledTimes(3);
  });
  it("moves focus to history heading when a successful poll replaces its focused task", async () => {
    vi.useFakeTimers();
    vi.mocked(marketUpdateApi.list)
      .mockResolvedValueOnce({
        items: [{ ...job, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [{ ...job, job_id: "aaaaaaaa-bbbb-4ccc-8ddd-000000000003" }],
        total: 2,
        limit: 20,
        offset: 0,
      });
    render(<MarketUpdatesPanel />);
    await act(async () => {});
    const history = screen.getByRole("region", { name: "Update task history" });
    const open = within(history).getByRole("button", { name: /^Open task:/ });
    open.focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(open).not.toBeInTheDocument();
    expect(
      within(history).getByRole("heading", { name: "Update task history" }),
    ).toHaveFocus();
  });
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
  it("keeps the focused observation pager mounted when progress refetches records", async () => {
    const rows = Array.from({ length: 51 }, (_, index) => ({
      ...observations.items[0],
      trading_date: new Date(Date.UTC(2026, 0, index + 1))
        .toISOString()
        .slice(0, 10),
    }));
    vi.mocked(marketUpdateApi.observations)
      .mockResolvedValueOnce({ ...observations, items: rows, total: 51 })
      .mockImplementationOnce(() => new Promise(() => {}));
    const running = {
      ...job,
      status: "RUNNING" as const,
      completed_requests: 0,
    };
    const { rerender } = render(<UpdateRecords job={running} revision={0} />);
    await screen.findByRole("table", { name: "Candidate observations" });
    const pager = screen.getAllByRole("group", { name: "Pagination" })[0];
    await userEvent.click(within(pager).getByRole("button", { name: "Next" }));
    expect(pager).toHaveFocus();
    rerender(
      <UpdateRecords
        job={{ ...running, completed_requests: 1 }}
        revision={0}
      />,
    );
    expect(pager).toBeInTheDocument();
    expect(pager).toHaveFocus();
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
  it("hands keyboard focus from history to the opened task", async () => {
    render(<MarketUpdatesPanel />);
    const open = await screen.findByRole("button", {
      name: /^Open task: CN-A:SSE:600000/,
    });
    open.focus();
    await userEvent.keyboard("{Enter}");
    expect(location.search).toBe(`?updateJob=${job.job_id}`);
    expect(
      screen.getByRole("region", { name: `Task: ${job.job_id}` }),
    ).toHaveFocus();
  });
  it("keeps the focused task before its reloading history list", async () => {
    const page = { items: [job], total: 1, limit: 20, offset: 0 };
    let finish!: (value: typeof page) => void;
    vi.mocked(marketUpdateApi.list)
      .mockResolvedValueOnce(page)
      .mockImplementationOnce(
        () => new Promise((resolve) => (finish = resolve)),
      );
    render(<MarketUpdatesPanel />);
    const open = await screen.findByRole("button", {
      name: /^Open task: CN-A:SSE:600000/,
    });
    open.focus();
    await userEvent.keyboard("{Enter}");
    const detail = screen.getByRole("region", {
      name: `Task: ${job.job_id}`,
    });
    const history = screen.getByRole("region", { name: "Update task history" });
    expect(detail).toHaveFocus();
    expect(
      detail.compareDocumentPosition(history) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
    await act(async () => finish(page));
    expect(detail).toHaveFocus();
    expect(
      detail.compareDocumentPosition(history) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
  it("does not steal focus when another control is chosen as history opens", async () => {
    render(<MarketUpdatesPanel />);
    const open = await screen.findByRole("button", {
      name: /^Open task: CN-A:SSE:600000/,
    });
    const refresh = screen.getByRole("button", { name: "Refresh" });
    open.focus();
    await act(async () => {
      fireEvent.click(open);
      refresh.focus();
    });
    expect(location.search).toBe(`?updateJob=${job.job_id}`);
    expect(refresh).toHaveFocus();
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
    const submit = screen.getByRole("button", {
      name: "Request selected raw data",
    });
    submit.focus();
    await userEvent.keyboard("{Enter}{Enter}");
    expect(create).toHaveBeenCalledTimes(1);
    expect(submit).toHaveFocus();
    expect(submit).toHaveAttribute("aria-disabled", "true");
    expect(screen.getByLabelText("Security IDs (1–20)")).toBeDisabled();
    await userEvent.click(submit);
    expect(create).toHaveBeenCalledTimes(1);
    expect(location.search).toBe("");
    await act(async () => resolve?.(job));
    expect(location.search).toBe(`?updateJob=${job.job_id}`);
    expect(
      screen.getByRole("region", { name: `Task: ${job.job_id}` }),
    ).toHaveFocus();
    expect(
      await screen.findByText(
        "Bounded raw requests completed. Candidate-only status is unchanged.",
      ),
    ).toBeInTheDocument();
  });
  it("keeps the submit focus and saved identity after an uncertain response", async () => {
    let reject!: (reason: unknown) => void;
    const create = vi
      .spyOn(marketUpdateApi, "create")
      .mockImplementation(() => new Promise((_, fail) => (reject = fail)));
    render(<MarketUpdatesPanel />);
    await fill();
    const submit = screen.getByRole("button", {
      name: "Request selected raw data",
    });
    submit.focus();
    await userEvent.keyboard("{Enter}");
    expect(submit).toHaveFocus();
    await act(async () => reject(new ApiError(503, "unavailable")));
    expect(submit).toHaveFocus();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Check service state and saved task history",
    );
    expect(JSON.parse(localStorage.getItem(UPDATE_DRAFT_KEY)!).requestKey).toBe(
      create.mock.calls[0][1],
    );
  });
  it("does not move focus from another control when a pending task completes", async () => {
    let resolve!: (value: UpdateJob) => void;
    vi.spyOn(marketUpdateApi, "create").mockImplementation(
      () => new Promise((done) => (resolve = done)),
    );
    render(<MarketUpdatesPanel />);
    await fill();
    screen.getByRole("button", { name: "Request selected raw data" }).focus();
    await userEvent.keyboard("{Enter}");
    const refresh = screen.getByRole("button", { name: "Refresh" });
    refresh.focus();
    await act(async () => resolve(job));
    expect(location.search).toBe(`?updateJob=${job.job_id}`);
    expect(refresh).toHaveFocus();
  });
  it("focuses an already open task after a same-identity retry succeeds", async () => {
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    vi.spyOn(marketUpdateApi, "create").mockResolvedValue(job);
    render(<MarketUpdatesPanel />);
    await fill();
    const task = screen.getByRole("region", { name: `Task: ${job.job_id}` });
    const submit = screen.getByRole("button", {
      name: "Request selected raw data",
    });
    submit.focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() => expect(task).toHaveFocus());
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
  it("keeps cancellation focused and moves to the terminal task status", async () => {
    const running: UpdateJob = {
      ...job,
      status: "RUNNING",
      phase: "FETCHING_RAW_CANDIDATES",
      completed_at: null,
      summary: null,
    };
    const cancelled: UpdateJob = {
      ...running,
      status: "CANCELLED",
      phase: "CANCELLED",
      cancel_requested: true,
    };
    let current = running;
    vi.mocked(marketUpdateApi.get).mockImplementation(async () => current);
    let finish!: (value: UpdateJob) => void;
    const cancel = vi
      .spyOn(marketUpdateApi, "cancel")
      .mockImplementation(() => new Promise((resolve) => (finish = resolve)));
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const button = await screen.findByRole("button", {
      name: "Request cancellation",
    });
    button.focus();
    await userEvent.keyboard("{Enter}{Enter}");
    expect(cancel).toHaveBeenCalledTimes(1);
    expect(button).toHaveFocus();
    expect(button).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(button);
    expect(cancel).toHaveBeenCalledTimes(1);
    current = cancelled;
    await act(async () => finish(cancelled));
    await waitFor(() =>
      expect(screen.getByRole("heading", { name: "Cancelled" })).toHaveFocus(),
    );
  });
  it("does not steal cancellation focus after moving to Refresh", async () => {
    const running: UpdateJob = { ...job, status: "RUNNING" };
    const cancelled: UpdateJob = {
      ...running,
      status: "CANCELLED",
      cancel_requested: true,
    };
    let current = running;
    vi.mocked(marketUpdateApi.get).mockImplementation(async () => current);
    let finish!: (value: UpdateJob) => void;
    vi.spyOn(marketUpdateApi, "cancel").mockImplementation(
      () => new Promise((resolve) => (finish = resolve)),
    );
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const button = await screen.findByRole("button", {
      name: "Request cancellation",
    });
    button.focus();
    await userEvent.keyboard("{Enter}");
    const refresh = within(
      screen.getByRole("region", { name: `Task: ${job.job_id}` }),
    ).getAllByRole("button", { name: "Refresh" })[0];
    refresh.focus();
    current = cancelled;
    await act(async () => finish(cancelled));
    await screen.findByRole("heading", { name: "Cancelled" });
    expect(refresh).toHaveFocus();
  });
  it("does not repeat cancellation once the server records the request", async () => {
    vi.mocked(marketUpdateApi.get).mockResolvedValue({
      ...job,
      status: "RUNNING",
      cancel_requested: true,
    });
    const cancel = vi.spyOn(marketUpdateApi, "cancel");
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const button = await screen.findByRole("button", {
      name: "Request cancellation",
    });
    expect(button).toHaveAttribute("aria-disabled", "true");
    button.focus();
    await userEvent.keyboard("{Enter}");
    await userEvent.click(button);
    expect(cancel).not.toHaveBeenCalled();
    expect(button).toHaveFocus();
  });
  it.each(["failure-first", "confirmation-first"] as const)(
    "reconciles an uncertain cancel response with saved task status: %s",
    async (order) => {
      const running: UpdateJob = {
        ...job,
        status: "RUNNING",
        phase: "FETCHING_RAW_CANDIDATES",
        summary: null,
      };
      const confirmed: UpdateJob =
        order === "failure-first"
          ? { ...running, cancel_requested: true }
          : { ...running, status: "CANCELLED", cancel_requested: true };
      let current = running;
      vi.mocked(marketUpdateApi.get).mockImplementation(async () => current);
      let fail!: (reason: unknown) => void;
      const cancel = vi
        .spyOn(marketUpdateApi, "cancel")
        .mockImplementation(() => new Promise((_, reject) => (fail = reject)));
      window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
      render(<MarketUpdatesPanel />);
      const detail = await screen.findByRole("region", {
        name: `Task: ${job.job_id}`,
      });
      await userEvent.click(
        within(detail).getByRole("button", { name: "Request cancellation" }),
      );
      expect(cancel).toHaveBeenCalledTimes(1);
      if (order === "failure-first") {
        await act(async () => fail(new ApiError(503, "unavailable")));
        expect(within(detail).getByRole("alert")).toHaveTextContent(
          "Request could not be completed",
        );
      }
      current = confirmed;
      await userEvent.click(
        within(detail).getAllByRole("button", { name: "Refresh" })[0],
      );
      if (order === "failure-first")
        await within(detail).findByText(
          "Cancellation requested; waiting for the server checkpoint.",
        );
      else await within(detail).findByRole("heading", { name: "Cancelled" });
      if (order === "confirmation-first")
        await act(async () => fail(new ApiError(503, "unavailable")));
      expect(within(detail).queryByRole("alert")).not.toBeInTheDocument();

      if (order === "confirmation-first") {
        vi.spyOn(marketUpdateApi, "retry").mockRejectedValue(
          new ApiError(503, "unavailable"),
        );
        await userEvent.click(
          within(detail).getByRole("button", {
            name: "Retry this unsuccessful task",
          }),
        );
        expect(within(detail).getByRole("alert")).toHaveTextContent(
          "Request could not be completed",
        );
      }
    },
  );
  it("keeps a denied cancel response visible despite a later cancellation", async () => {
    const running: UpdateJob = { ...job, status: "RUNNING" };
    let current = running;
    vi.mocked(marketUpdateApi.get).mockImplementation(async () => current);
    vi.spyOn(marketUpdateApi, "cancel").mockRejectedValue(
      new ApiError(403, "denied"),
    );
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const detail = await screen.findByRole("region", {
      name: `Task: ${job.job_id}`,
    });
    await userEvent.click(
      within(detail).getByRole("button", { name: "Request cancellation" }),
    );
    expect(within(detail).getByRole("alert")).toHaveTextContent(
      "The service denied this request",
    );
    current = { ...running, cancel_requested: true };
    await userEvent.click(
      within(detail).getAllByRole("button", { name: "Refresh" })[0],
    );
    await within(detail).findByText(
      "Cancellation requested; waiting for the server checkpoint.",
    );
    expect(within(detail).getByRole("alert")).toHaveTextContent(
      "The service denied this request",
    );
  });
  it.each([503, 403])(
    "keeps a denied cancel visible without duplicate alerts when the next read returns %i",
    async (readStatus) => {
      const running: UpdateJob = { ...job, status: "RUNNING" };
      vi.mocked(marketUpdateApi.get)
        .mockResolvedValueOnce(running)
        .mockRejectedValueOnce(new ApiError(readStatus, "unavailable"));
      vi.spyOn(marketUpdateApi, "cancel").mockRejectedValue(
        new ApiError(403, "denied"),
      );
      window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
      render(<MarketUpdatesPanel />);
      const detail = await screen.findByRole("region", {
        name: `Task: ${job.job_id}`,
      });
      await userEvent.click(
        within(detail).getByRole("button", { name: "Request cancellation" }),
      );
      expect(within(detail).getByRole("alert")).toHaveTextContent(
        "The service denied this request",
      );
      await userEvent.click(
        within(detail).getAllByRole("button", { name: "Refresh" })[0],
      );
      await waitFor(() => {
        const alerts = within(detail).getAllByRole("alert");
        expect(
          alerts.some((alert) =>
            alert.textContent?.includes("The service denied this request"),
          ),
        ).toBe(true);
        expect(alerts).toHaveLength(readStatus === 403 ? 1 : 2);
        if (readStatus === 503)
          expect(
            alerts.some((alert) =>
              alert.textContent?.includes("Request could not be completed"),
            ),
          ).toBe(true);
      });
    },
  );
  it("keeps an uncertain cancel warning when the next status read is denied", async () => {
    const running: UpdateJob = { ...job, status: "RUNNING" };
    vi.mocked(marketUpdateApi.get)
      .mockResolvedValueOnce(running)
      .mockRejectedValueOnce(new ApiError(403, "denied"));
    vi.spyOn(marketUpdateApi, "cancel").mockRejectedValue(
      new ApiError(503, "unavailable"),
    );
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const detail = await screen.findByRole("region", {
      name: `Task: ${job.job_id}`,
    });
    await userEvent.click(
      within(detail).getByRole("button", { name: "Request cancellation" }),
    );
    await userEvent.click(
      within(detail).getAllByRole("button", { name: "Refresh" })[0],
    );
    await waitFor(() => {
      const alerts = within(detail).getAllByRole("alert");
      expect(alerts).toHaveLength(2);
      expect(
        alerts.some((alert) =>
          alert.textContent?.includes("The service denied this request"),
        ),
      ).toBe(true);
      expect(
        alerts.some((alert) =>
          alert.textContent?.includes("Request could not be completed"),
        ),
      ).toBe(true);
    });
  });
  it("keeps retry focused during an uncertain response without repeating it", async () => {
    vi.mocked(marketUpdateApi.get).mockResolvedValue({
      ...job,
      status: "FAILED",
      phase: "FAILED",
      error_code: "PROVIDER_TIMEOUT",
      summary: null,
    });
    let fail!: (reason: unknown) => void;
    const retry = vi
      .spyOn(marketUpdateApi, "retry")
      .mockImplementation(() => new Promise((_, reject) => (fail = reject)));
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const button = await screen.findByRole("button", {
      name: "Retry this unsuccessful task",
    });
    button.focus();
    await userEvent.keyboard("{Enter}{Enter}");
    expect(retry).toHaveBeenCalledTimes(1);
    expect(button).toHaveFocus();
    expect(button).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(button);
    expect(retry).toHaveBeenCalledTimes(1);
    await act(async () => fail(new ApiError(503, "unavailable")));
    expect(button).toHaveFocus();
    expect(
      screen.getByText(/Request could not be completed/),
    ).toBeInTheDocument();
  });
  it("focuses the linked retry task after the original button disappears", async () => {
    const failed: UpdateJob = {
      ...job,
      status: "FAILED",
      phase: "FAILED",
      error_code: "PROVIDER_TIMEOUT",
      summary: null,
    };
    const linked: UpdateJob = {
      ...failed,
      job_id: "ab000000-0000-4000-8000-000000000002",
      status: "QUEUED",
      phase: "QUEUED",
      error_code: null,
      retry_of: job.job_id,
    };
    vi.mocked(marketUpdateApi.get).mockImplementation(async (id) =>
      id === linked.job_id ? linked : failed,
    );
    vi.spyOn(marketUpdateApi, "retry").mockResolvedValue(linked);
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const retry = await screen.findByRole("button", {
      name: "Retry this unsuccessful task",
    });
    retry.focus();
    await userEvent.keyboard("{Enter}");
    const linkedTask = await screen.findByRole("region", {
      name: `Task: ${linked.job_id}`,
    });
    await waitFor(() => expect(linkedTask).toHaveFocus());
  });
  it("does not steal focus from an outer control when a retry opens its child", async () => {
    const failed: UpdateJob = {
      ...job,
      status: "FAILED",
      phase: "FAILED",
      error_code: "PROVIDER_TIMEOUT",
      summary: null,
    };
    const linked: UpdateJob = {
      ...failed,
      job_id: "ab000000-0000-4000-8000-000000000002",
      status: "QUEUED",
      phase: "QUEUED",
      error_code: null,
      retry_of: job.job_id,
    };
    vi.mocked(marketUpdateApi.get).mockImplementation(async (id) =>
      id === linked.job_id ? linked : failed,
    );
    let finish!: (value: UpdateJob) => void;
    vi.spyOn(marketUpdateApi, "retry").mockImplementation(
      () => new Promise((resolve) => (finish = resolve)),
    );
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const retry = await screen.findByRole("button", {
      name: "Retry this unsuccessful task",
    });
    retry.focus();
    await userEvent.keyboard("{Enter}");
    const outerRefresh = screen.getAllByRole("button", { name: "Refresh" })[0];
    outerRefresh.focus();
    await act(async () => finish(linked));
    await screen.findByRole("region", { name: `Task: ${linked.job_id}` });
    expect(outerRefresh).toHaveFocus();
  });
  it("focuses the read error if a refresh removes the active cancel button", async () => {
    const running: UpdateJob = {
      ...job,
      status: "RUNNING",
      phase: "FETCHING_RAW_CANDIDATES",
      summary: null,
    };
    vi.mocked(marketUpdateApi.get)
      .mockResolvedValueOnce(running)
      .mockRejectedValue(new ApiError(503, "unavailable"));
    vi.spyOn(marketUpdateApi, "cancel").mockResolvedValue({
      ...running,
      cancel_requested: true,
    });
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    const cancel = await screen.findByRole("button", {
      name: "Request cancellation",
    });
    cancel.focus();
    await userEvent.keyboard("{Enter}");
    const detail = screen.getByRole("region", {
      name: `Task: ${job.job_id}`,
    });
    await waitFor(() =>
      expect(
        within(detail).getByText(/Request could not be completed/),
      ).toHaveFocus(),
    );
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
  it("lets an absent saved task return to requests when history is empty", async () => {
    vi.mocked(marketUpdateApi.get).mockRejectedValue(
      new ApiError(404, "missing", "MARKET_UPDATE_NOT_FOUND"),
    );
    vi.mocked(marketUpdateApi.list).mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    window.history.replaceState({}, "", `/data?updateJob=${job.job_id}`);
    render(<MarketUpdatesPanel />);
    expect(
      await screen.findByText(/Choose another task from history below/),
    ).toBeInTheDocument();
    expect(screen.getByText("No update tasks yet.")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Back to requests and task history" }),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByText(/请从下方历史选择其他任务/)).toBeInTheDocument();
    const historyLength = window.history.length;
    const recovery = screen.getByRole("button", { name: "返回请求与任务历史" });
    recovery.focus();
    await userEvent.keyboard("{Enter}");
    expect(location.search).toBe("");
    expect(window.history.length).toBe(historyLength);
    expect(
      screen.getByRole("heading", { name: "原始行情增量请求" }),
    ).toHaveFocus();
    expect(
      screen.getByText("打开任务后可查看回执、观察值及未解释日期。"),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "请求所选原始数据" }),
    ).toBeInTheDocument();
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
