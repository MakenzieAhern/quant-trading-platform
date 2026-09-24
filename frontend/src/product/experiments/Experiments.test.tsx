import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { ApiError } from "../../api/client";
import { i18n } from "../../i18n";
import { navigate } from "../../utils/navigation";
import { Link } from "../../components/Link";
import * as pageContext from "../dataContext";
import {
  experimentApi,
  parseCapabilities,
  parseExperiment,
  parseResult,
} from "./api";
import { CreateExperimentPage } from "./CreateExperimentPage";
import { ExperimentDetailPage } from "./ExperimentDetailPage";
import { ExperimentPlan } from "./ExperimentPlan";
import { EXPERIMENT_VIEW_KEY, ExperimentsPage } from "./ExperimentsPage";
import {
  EXPERIMENT_DRAFT_KEY,
  readExperimentDraft,
  saveExperimentDraft,
} from "./draft";
import {
  capabilities,
  configuration,
  job,
  plan,
  result,
} from "./fixtures.test-data";

beforeEach(async () => {
  window.localStorage.removeItem(EXPERIMENT_DRAFT_KEY);
  window.localStorage.removeItem(EXPERIMENT_VIEW_KEY);
  await i18n.changeLanguage("en-US");
  window.history.replaceState({}, "", "/research/new");
});

async function review() {
  await screen.findByText(
    "Ranks eligible shares and builds a long-only portfolio.",
  );
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  fireEvent.change(screen.getByLabelText("Starting capital (CNY)"), {
    target: { value: configuration.initial_cash },
  });
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  await userEvent.click(screen.getByRole("button", { name: "Continue" }));
  await userEvent.click(screen.getByRole("checkbox", { name: /I understand/ }));
}

describe("guided experiment", () => {
  it("does not steal direct-load focus but focuses each newly opened step", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    render(<CreateExperimentPage />);
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    const heading = document.querySelector<HTMLElement>(".experimentForm h2");
    expect(heading).not.toHaveFocus();
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(heading).toHaveFocus();
  });

  it("does not erase or navigate away from a newer draft when an abandoned create resolves", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    let resolve: ((value: typeof job) => void) | undefined;
    vi.spyOn(experimentApi, "create").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    const first = render(<CreateExperimentPage />);
    await review();
    await userEvent.click(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    first.unmount();
    const newer = {
      ...configuration,
      name: "Newer configuration",
      initial_cash: "432100.000000000000000009",
    };
    saveExperimentDraft(newer, 1, "newer-request-key");
    render(<CreateExperimentPage />);
    expect(await screen.findByLabelText("Experiment name")).toHaveValue(
      "Newer configuration",
    );
    await act(async () => resolve?.(job));
    expect(readExperimentDraft()).toMatchObject({
      form: newer,
      idempotencyKey: "newer-request-key",
    });
    expect(window.location.pathname).toBe("/research/new");
    expect(screen.getByLabelText("Starting capital (CNY)")).toHaveValue(
      newer.initial_cash,
    );
  });

  it("guards dirty sidebar and command navigation without losing the restored form", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(
      <>
        <Link href="/experiments">Sidebar research</Link>
        <CreateExperimentPage />
      </>,
    );
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    fireEvent.change(screen.getByLabelText("Starting capital (CNY)"), {
      target: { value: "123456.000000000000000001" },
    });
    await userEvent.click(
      screen.getByRole("link", { name: "Sidebar research" }),
    );
    expect(confirm).toHaveBeenCalledTimes(1);
    act(() => {
      expect(navigate("/settings")).toBe(false);
    });
    expect(confirm).toHaveBeenCalledTimes(2);
    expect(screen.getByLabelText("Starting capital (CNY)")).toHaveValue(
      "123456.000000000000000001",
    );
    expect(readExperimentDraft()?.form.initial_cash).toBe(
      "123456.000000000000000001",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save draft" }));
    act(() => {
      expect(navigate("/experiments")).toBe(true);
    });
    expect(confirm).toHaveBeenCalledTimes(2);
  });

  it("confirms explicit Save & exit only once", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<CreateExperimentPage />);
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save & exit" }));
    expect(confirm).toHaveBeenCalledTimes(1);
    expect(window.location.pathname).toBe("/");
    expect(readExperimentDraft()).not.toBeNull();
  });

  it("submits a real registry configuration with exact strings and locks duplicate clicks", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    let resolve: ((value: typeof job) => void) | undefined;
    const create = vi.spyOn(experimentApi, "create").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    render(<CreateExperimentPage />);
    await review();
    await userEvent.dblClick(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    expect(create).toHaveBeenCalledTimes(1);
    expect(create.mock.calls[0][0]).toMatchObject({
      initial_cash: configuration.initial_cash,
      costs: { commission_rate: "0.0003", minimum_commission: "5" },
      risk: { max_drawdown: "-0.2", max_position_weight: "0.1" },
    });
    expect(screen.getByRole("button", { name: "Submitting…" })).toBeDisabled();
    await act(async () => resolve?.(job));
    expect(window.location.pathname).toBe(`/experiments/${job.job_id}`);
    expect(readExperimentDraft()).toBeNull();
  });

  it("saves and restores the step, exact values and request identity without changing them on language switch", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    saveExperimentDraft(configuration, 2, "existing-request-key");
    const { unmount } = render(<CreateExperimentPage />);
    expect(
      await screen.findByText("Your saved draft has been restored."),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("Drawdown risk limit (negative fraction)"),
    ).toHaveValue("-0.2");
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByLabelText("佣金比例（小数）")).toHaveValue("0.0003");
    await userEvent.click(screen.getByRole("button", { name: "保存草稿" }));
    expect(readExperimentDraft()).toMatchObject({
      form: configuration,
      step: 2,
      idempotencyKey: "existing-request-key",
    });
    unmount();
    render(<CreateExperimentPage />);
    expect(await screen.findByLabelText("回撤风险阈值（负小数）")).toHaveValue(
      "-0.2",
    );
  });

  it("retains the idempotency key after an uncertain request and changes it only after editing", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const create = vi
      .spyOn(experimentApi, "create")
      .mockRejectedValue(new ApiError(503, "Unavailable"));
    render(<CreateExperimentPage />);
    await review();
    await userEvent.click(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    await screen.findByRole("alert");
    await userEvent.click(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    expect(create.mock.calls[1][1]).toBe(create.mock.calls[0][1]);
    await userEvent.click(screen.getByRole("button", { name: "Back" }));
    fireEvent.change(
      screen.getByLabelText("Minimum commission per trade (CNY)"),
      { target: { value: "6" } },
    );
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    await userEvent.click(
      screen.getByRole("checkbox", { name: /I understand/ }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    expect(create.mock.calls[2][1]).not.toBe(create.mock.calls[0][1]);
  });

  it("validates invalid risk inputs and preserves incomplete drafts for later correction", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    saveExperimentDraft(
      {
        ...configuration,
        costs: { ...configuration.costs, commission_rate: "" },
      },
      2,
      "draft",
    );
    render(<CreateExperimentPage />);
    expect(
      await screen.findByLabelText("Commission rate (decimal fraction)"),
    ).toHaveValue("");
    fireEvent.change(
      screen.getByLabelText("Commission rate (decimal fraction)"),
      { target: { value: "0.02" } },
    );
    await userEvent.click(screen.getByRole("button", { name: "Continue" }));
    expect(screen.getByRole("alert")).toHaveTextContent(
      "Check the highlighted step",
    );
    expect(
      screen.getByLabelText("Commission rate (decimal fraction)"),
    ).toHaveValue("0.02");
  });

  it("asks before exiting and does not discard the draft when exit is declined", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<CreateExperimentPage />);
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save & exit" }));
    expect(window.confirm).toHaveBeenCalledOnce();
    expect(window.location.pathname).toBe("/research/new");
    expect(readExperimentDraft()?.form.strategy_id).toBe(
      configuration.strategy_id,
    );
  });
});

describe("durable experiment detail", () => {
  it("offers a separate paper-account handoff only after a historical result succeeds", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      mode: "historical_exploration",
      result_available: true,
    });
    vi.spyOn(experimentApi, "result").mockResolvedValue({
      ...result,
      mode: "historical_exploration",
    });
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(
      await screen.findByRole("link", {
        name: "Review these settings in a separate historical paper account",
      }),
    ).toHaveAttribute("href", `/paper/new?from_experiment=${job.job_id}`);
    expect(
      screen.getByText(
        /does not copy results, create an account or submit an order/,
      ),
    ).toBeInTheDocument();
  });

  it("explains an eligible simulation check as acceptance, not a rejection, in both languages", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    vi.spyOn(experimentApi, "result").mockResolvedValue({
      ...result,
      execution: {
        ...result.execution,
        reason_counts: { ELIGIBLE_SIMULATION_ASSUMPTION: 5 },
      },
    });
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(
      await screen.findByText(
        "Passed conservative daily-bar simulation execution checks. This is a simulation assumption, not proof of a real market fill.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/additional execution constraint/),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("cell", { name: "5" })).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByText(
        "通过保守日线模拟执行检查。这属于模拟假设，不是真实市场成交的证明。",
      ),
    ).toBeInTheDocument();
  });

  it("labels the requested end separately from the observed completed result date", async () => {
    const context = vi
      .spyOn(pageContext, "usePageDataContext")
      .mockImplementation(() => undefined);
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    let resolve: ((value: typeof result) => void) | undefined;
    vi.spyOn(experimentApi, "result").mockImplementation(
      () =>
        new Promise((done) => {
          resolve = done;
        }),
    );
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await waitFor(() =>
      expect(context).toHaveBeenLastCalledWith(
        "synthetic_demo",
        job.configuration.end_date,
        "requested",
      ),
    );
    await waitFor(() => expect(resolve).toBeDefined());
    await act(async () => {
      if (!resolve) throw new Error("result request did not start");
      resolve({ ...result, date_end: "2031-06-27" });
    });
    await waitFor(() =>
      expect(context).toHaveBeenLastCalledWith(
        "synthetic_demo",
        "2031-06-27",
        "observed",
      ),
    );
  });

  it("reuses the persisted server retry identity after a lost response and a fresh mount", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "FAILED",
      phase: "FAILED",
    });
    const retry = vi
      .spyOn(experimentApi, "retry")
      .mockRejectedValueOnce(new ApiError(408, "Response lost"))
      .mockResolvedValue({
        ...job,
        job_id: "accepted-child",
        retry_of: job.job_id,
      });
    const first = render(<ExperimentDetailPage jobId={job.job_id} />);
    await userEvent.click(
      await screen.findByRole("button", {
        name: "Start or reopen linked retry",
      }),
    );
    await screen.findByText(/request timed out/);
    const acceptedKey = retry.mock.calls[0][1];
    first.unmount();
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await userEvent.click(
      await screen.findByRole("button", {
        name: "Start or reopen linked retry",
      }),
    );
    expect(retry.mock.calls[1][1]).toBe(acceptedKey);
    expect(acceptedKey).toBe(`experiment-retry-v1:${job.job_id}`);
    expect(window.location.pathname).toBe("/experiments/accepted-child");
  });

  it("polls the same durable job until terminal status and then stops", async () => {
    vi.useFakeTimers();
    const get = vi
      .spyOn(experimentApi, "get")
      .mockResolvedValueOnce({ ...job, status: "RUNNING", phase: "EXECUTING" })
      .mockResolvedValue({ ...job, status: "SUCCEEDED", phase: "COMPLETE" });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(get).toHaveBeenCalledTimes(1);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });
    expect(get).toHaveBeenCalledTimes(2);
    expect(screen.getByText("Complete")).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000);
    });
    expect(get).toHaveBeenCalledTimes(2);
  });

  it("refreshes active list entries without replacing the visible page by a spinner", async () => {
    vi.useFakeTimers();
    const list = vi
      .spyOn(experimentApi, "list")
      .mockResolvedValueOnce({ items: [job], total: 1, limit: 20, offset: 0 })
      .mockResolvedValue({
        items: [{ ...job, status: "SUCCEEDED" }],
        total: 1,
        limit: 20,
        offset: 0,
      });
    render(<ExperimentsPage />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    expect(screen.getByRole("cell", { name: "Queued" })).toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(5000);
    });
    expect(screen.getByRole("cell", { name: "Complete" })).toBeInTheDocument();
    expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(10000);
    });
    expect(list).toHaveBeenCalledTimes(2);
  });

  it("does not keep old studies visible after the list refresh fails", async () => {
    const list = vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [{ ...job, status: "SUCCEEDED" }],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<ExperimentsPage />);
    expect(
      await screen.findByRole("cell", { name: "Complete" }),
    ).toBeInTheDocument();
    list.mockRejectedValueOnce(new ApiError(503, "service unavailable"));
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "The server could not finish this request",
    );
    expect(
      screen.queryByRole("cell", { name: "Complete" }),
    ).not.toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: "Retry loading" }),
    );
    expect(
      await screen.findByRole("cell", { name: "Complete" }),
    ).toBeInTheDocument();
  });

  it("reopens a job, displays actual work counts, and requests server cancellation", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "RUNNING",
      phase: "EXECUTING",
      completed_sessions: 3,
      total_sessions: 20,
    });
    const cancel = vi
      .spyOn(experimentApi, "cancel")
      .mockResolvedValue({ ...job, status: "CANCELLED" });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(
      await screen.findByText("Completed trading sessions: 3 / 20"),
    ).toBeInTheDocument();
    expect(screen.getByRole("progressbar")).toHaveAttribute("value", "3");
    await userEvent.click(screen.getByRole("button", { name: "Cancel task" }));
    expect(cancel).toHaveBeenCalledWith(job.job_id);
  });

  it("does not invent a percentage when the server has no total", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue(job);
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(
      await screen.findByText(
        "The server has not reported a measurable total yet.",
      ),
    ).toBeInTheDocument();
    expect(screen.queryByRole("progressbar")).not.toBeInTheDocument();
  });

  it("explains denied result access and recovers after an explicit retry", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    vi.spyOn(experimentApi, "result")
      .mockRejectedValueOnce(new ApiError(403, "Forbidden", "FORBIDDEN"))
      .mockResolvedValue(result);
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Access was denied. Check your access before trying again.",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Retry loading" }),
    );
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
  });

  it("hides a stale completed study when refreshing its task status fails", async () => {
    const completed = {
      ...job,
      status: "SUCCEEDED" as const,
      result_available: true,
    };
    const get = vi.spyOn(experimentApi, "get").mockResolvedValue(completed);
    vi.spyOn(experimentApi, "result").mockResolvedValue(result);
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
    get.mockRejectedValueOnce(new ApiError(503, "service unavailable"));
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByRole("alert")).toBeInTheDocument();
    expect(screen.queryByText("What this run shows")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
  });

  it("shows exact results, retains null benchmark values, and loads only one bounded chart page", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      result_available: true,
    });
    vi.spyOn(experimentApi, "result").mockResolvedValue({
      ...result,
      benchmark_id: "SYNTHETIC_EQUAL_WEIGHT",
    });
    const equity = vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [
        {
          sequence: 0,
          trading_date: "2031-01-02",
          equity: result.metrics.final_equity!,
          benchmark: null,
          drawdown: "-0.0123",
        },
      ],
      total: 600,
      limit: 100,
      offset: 0,
    });
    const trades = vi
      .spyOn(experimentApi, "trades")
      .mockResolvedValue({ items: [], total: 0, limit: 20, offset: 0 });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await userEvent.click(
      await screen.findByRole("checkbox", { name: "Show full precision" }),
    );
    expect(
      await screen.findByText("12.000000000000000001"),
    ).toBeInTheDocument();
    expect(screen.getByText("Benchmark return").nextSibling).toHaveTextContent(
      "N/A",
    );
    expect(
      await screen.findByText(
        "These prices are synthetic and intentionally demonstrate the workflow. Returns cannot be used as investment evidence.",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/Synthetic equal-weight benchmark \(demo\)/),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/SYNTHETIC_EQUAL_WEIGHT/),
    ).not.toBeInTheDocument();
    await waitFor(() => expect(equity).toHaveBeenCalledTimes(1));
    expect(trades).not.toHaveBeenCalled();
    await userEvent.click(screen.getByText("Exact chart data"));
    expect(
      screen.getAllByText("100,012.123456789012345678").length,
    ).toBeGreaterThan(0);
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(equity.mock.calls.at(-1)?.[2]).toBe(100));
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByText(/合成等权基准（演示）/)).toBeInTheDocument();
  });

  it("retries a failed task through the backend and opens its linked attempt", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "INTERRUPTED",
      phase: "INTERRUPTED",
      error_code: "WORKER_RESTARTED_RETRY_AVAILABLE",
    });
    const retry = vi.spyOn(experimentApi, "retry").mockResolvedValue({
      ...job,
      job_id: "new-attempt",
      retry_of: job.job_id,
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await userEvent.click(
      await screen.findByRole("button", {
        name: "Start or reopen linked retry",
      }),
    );
    expect(retry).toHaveBeenCalledWith(job.job_id, expect.any(String));
    expect(window.location.pathname).toBe("/experiments/new-attempt");
  });

  it("offers a real first action on an empty list", async () => {
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    render(<ExperimentsPage />);
    expect(await screen.findByText(/No experiments yet/)).toBeInTheDocument();
    expect(
      screen.getAllByRole("link", { name: "New guided backtest" })[0],
    ).toHaveAttribute("href", "/research/new");
  });

  it("persists a server-wide filtered, sorted column view across remount", async () => {
    const list = vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [{ ...job, status: "SUCCEEDED", result_available: true }],
      total: 1,
      limit: 20,
      offset: 0,
    });
    const first = render(<ExperimentsPage />);
    await screen.findByRole("link", { name: job.name });
    await userEvent.type(
      screen.getByLabelText("Search saved studies"),
      "Precision",
    );
    await userEvent.selectOptions(screen.getByLabelText("Status"), "SUCCEEDED");
    await userEvent.selectOptions(
      screen.getByLabelText("Sort studies"),
      "name_asc",
    );
    await userEvent.click(screen.getByText("Columns"));
    await userEvent.click(
      screen.getByRole("checkbox", { name: "Created (UTC)" }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Save this view" }),
    );
    expect(screen.getByText("View saved on this device.")).toBeInTheDocument();
    first.unmount();
    render(<ExperimentsPage />);
    expect(screen.getByLabelText("Search saved studies")).toHaveValue(
      "Precision",
    );
    expect(screen.getByLabelText("Status")).toHaveValue("SUCCEEDED");
    expect(screen.getByLabelText("Sort studies")).toHaveValue("name_asc");
    expect(
      screen.queryByRole("columnheader", { name: "Created (UTC)" }),
    ).not.toBeInTheDocument();
    await waitFor(() =>
      expect(list).toHaveBeenLastCalledWith(
        expect.any(AbortSignal),
        20,
        0,
        "Precision",
        { status: "SUCCEEDED", mode: undefined, sort: "name_asc" },
      ),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Remove filter: Status" }),
    );
    expect(screen.getByLabelText("Status")).toHaveValue("");
    await userEvent.click(screen.getByRole("button", { name: "Reset view" }));
    expect(window.localStorage.getItem(EXPERIMENT_VIEW_KEY)).toBeNull();
  });

  it("restores an unsaved list filter after opening a result and going Back", async () => {
    window.history.replaceState({}, "", "/experiments");
    const list = vi
      .spyOn(experimentApi, "list")
      .mockImplementation(async (_signal, _limit, offset) => ({
        items: [job],
        total: 41,
        limit: 20,
        offset: offset ?? 0,
      }));
    const first = render(<ExperimentsPage />);
    await screen.findByRole("link", { name: job.name });
    await userEvent.type(screen.getByLabelText("Search saved studies"), "M1");
    await waitFor(() =>
      expect(window.history.state.experimentView.q).toBe("M1"),
    );
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(window.history.state.experimentOffset).toBe(20));
    await screen.findByRole("link", { name: job.name });
    expect(window.localStorage.getItem(EXPERIMENT_VIEW_KEY)).toBeNull();
    await userEvent.click(screen.getByRole("link", { name: job.name }));
    first.unmount();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/experiments"));
    render(<ExperimentsPage />);
    expect(screen.getByLabelText("Search saved studies")).toHaveValue("M1");
    await waitFor(() =>
      expect(list).toHaveBeenLastCalledWith(
        expect.any(AbortSignal),
        20,
        20,
        "M1",
        { status: undefined, mode: undefined, sort: "newest" },
      ),
    );
  });
});

describe("experiment contract", () => {
  it("renders an exact simulation-only plan in both languages without an execute control", async () => {
    render(<ExperimentPlan plan={plan} />);
    expect(screen.getByText("Simulated rebalance preview")).toBeInTheDocument();
    expect(screen.getByText(/Not today's trading advice/)).toBeInTheDocument();
    expect(screen.getByText("9.123456789123456789")).toBeInTheDocument();
    expect(screen.getByText("Approved for simulation")).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /execute|submit/i }),
    ).not.toBeInTheDocument();
    await i18n.changeLanguage("zh-CN");
    expect(screen.getByText("模拟调仓预览")).toBeInTheDocument();
    expect(screen.getByText(/不是今日交易建议/)).toBeInTheDocument();
  });
  it("rejects rounded or falsely submitted simulated plans", () => {
    expect(
      parseResult({ ...result, simulation_plan: plan }).simulation_plan,
    ).toEqual(plan);
    expect(() =>
      parseResult({
        ...result,
        simulation_plan: { ...plan, estimated_cash_required: 917.3 },
      }),
    ).toThrow();
    expect(() =>
      parseResult({
        ...result,
        simulation_plan: { ...plan, submitted_to_account: true },
      }),
    ).toThrow();
  });
  it("rejects rounded JSON financial numbers instead of coercing them", () => {
    expect(() =>
      parseExperiment({
        ...job,
        configuration: { ...configuration, initial_cash: 100000 },
      }),
    ).toThrow();
    expect(() =>
      parseResult({
        ...result,
        metrics: { ...result.metrics, transaction_costs: 12 },
      }),
    ).toThrow();
    expect(parseResult(result).metrics.transaction_costs).toBe(
      "12.000000000000000001",
    );
  });
  it("accepts an explicitly unavailable historical source with null provenance", () => {
    const data = {
      ...capabilities,
      datasets: [
        {
          ...capabilities.datasets[0],
          available: false,
          mode: "historical_exploration",
          sha256: null,
          as_of: null,
          reason_code: "DATASET_NOT_MOUNTED",
        },
      ],
    };
    expect(parseCapabilities(data).datasets[0].available).toBe(false);
  });
});
