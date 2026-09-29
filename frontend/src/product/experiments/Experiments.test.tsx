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

function enableNativeDialog() {
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
}

describe("guided experiment", () => {
  it.each([
    [new ApiError(403, "denied"), "Access was denied", "访问被拒绝"],
    [new ApiError(408, "timeout"), "request timed out", "请求超时"],
    [new TypeError("offline"), "service is unavailable", "服务暂时无法连接"],
  ] as const)(
    "explains a capability-load failure before any submission: %s",
    async (failure, english, chinese) => {
      vi.spyOn(experimentApi, "capabilities")
        .mockRejectedValueOnce(failure)
        .mockResolvedValue(capabilities);
      const create = vi.spyOn(experimentApi, "create");
      render(<CreateExperimentPage />);
      expect(await screen.findByRole("alert")).toHaveTextContent(english);
      expect(screen.getByRole("alert")).not.toHaveTextContent("request key");
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(chinese);
      expect(create).not.toHaveBeenCalled();
      await userEvent.click(screen.getByRole("button", { name: "重新尝试" }));
      expect(
        (await screen.findAllByText(capabilities.strategies[0].name_zh)).length,
      ).toBeGreaterThan(0);
      expect(create).not.toHaveBeenCalled();
    },
  );

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

  it("confirms explicit Save & exit in an accessible dialog and restores the draft", async () => {
    enableNativeDialog();
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<CreateExperimentPage />);
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save & exit" }));
    const dialog = screen.getByRole("dialog", { name: "Save & exit" });
    expect(dialog).toHaveTextContent(
      "Your latest draft is saved on this device.",
    );
    await userEvent.click(
      within(dialog).getByRole("button", { name: "Save & exit" }),
    );
    expect(confirm).not.toHaveBeenCalled();
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
    expect(screen.getByRole("button", { name: "Submitting…" })).toHaveAttribute(
      "aria-disabled",
      "true",
    );
    await act(async () => resolve?.(job));
    expect(window.location.pathname).toBe(`/experiments/${job.job_id}`);
    expect(readExperimentDraft()).toBeNull();
  });

  it("does not submit when the request identity cannot be saved, then permits a safe retry", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const create = vi.spyOn(experimentApi, "create").mockResolvedValue(job);
    const write = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("storage unavailable");
      });
    try {
      render(<CreateExperimentPage />);
      await review();
      expect(readExperimentDraft()).toBeNull();
      await userEvent.click(
        screen.getByRole("button", { name: "Run this configuration" }),
      );
      expect(create).not.toHaveBeenCalled();
      expect(screen.getByRole("alert")).toHaveTextContent(
        "This browser could not save your draft",
      );
      expect(
        screen.getByRole("button", { name: "Run this configuration" }),
      ).toBeEnabled();
      expect(window.location.pathname).toBe("/research/new");
    } finally {
      write.mockRestore();
    }
    await userEvent.click(
      screen.getByRole("button", { name: "Run this configuration" }),
    );
    await waitFor(() => expect(create).toHaveBeenCalledTimes(1));
    expect(window.location.pathname).toBe(`/experiments/${job.job_id}`);
  });

  it("keeps the run action focused while pending, then focuses the failed-request alert", async () => {
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    let rejectCreate: ((reason: Error) => void) | undefined;
    const create = vi
      .spyOn(experimentApi, "create")
      .mockImplementationOnce(
        () =>
          new Promise<typeof job>((_, reject) => {
            rejectCreate = reject;
          }),
      )
      .mockRejectedValue(new ApiError(503, "Unavailable"));
    render(<CreateExperimentPage />);
    await review();
    const submit = screen.getByRole("button", {
      name: "Run this configuration",
    });
    await userEvent.click(submit);
    expect(create).toHaveBeenCalledTimes(1);
    expect(submit).toHaveFocus();
    expect(submit).not.toBeDisabled();
    expect(submit).toHaveAttribute("aria-disabled", "true");
    await userEvent.click(submit);
    expect(create).toHaveBeenCalledTimes(1);
    await act(async () => rejectCreate?.(new ApiError(503, "Unavailable")));
    const alert = await screen.findByRole("alert");
    expect(alert).toBeVisible();
    expect(alert).toHaveFocus();
    expect(submit).toHaveAttribute("aria-disabled", "false");
    await userEvent.click(submit);
    await waitFor(() => expect(create).toHaveBeenCalledTimes(2));
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

  it.each([503, 408, "network"] as const)(
    "retains request identity after uncertain response %s, locale switch and remount until editing",
    async (status) => {
      vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
      const create = vi
        .spyOn(experimentApi, "create")
        .mockRejectedValue(
          typeof status === "number"
            ? new ApiError(status, "Unavailable")
            : new TypeError("Failed to fetch"),
        );
      const { unmount } = render(<CreateExperimentPage />);
      await review();
      await userEvent.click(
        screen.getByRole("button", { name: "Run this configuration" }),
      );
      expect(await screen.findByRole("alert")).toHaveTextContent(
        status === 503
          ? "The server response could not be confirmed."
          : status === 408
            ? "The request timed out."
            : "Could not confirm a response from the service.",
      );
      expect(screen.getByRole("alert")).toHaveTextContent(
        "Retrying without editing keeps the same request ID",
      );
      expect(
        screen.getByRole("link", { name: "Check task center" }),
      ).toHaveAttribute("href", "/tasks");
      const acceptedKey = create.mock.calls[0][1];
      const acceptedForm = create.mock.calls[0][0];
      await act(async () => i18n.changeLanguage("zh-CN"));
      expect(screen.getByRole("alert")).toHaveTextContent(
        status === 503
          ? "未能确认服务端响应"
          : status === 408
            ? "请求超时"
            : "未能确认服务响应",
      );
      expect(screen.getByRole("alert")).toHaveTextContent(
        "不修改配置重试会保留同一请求编号",
      );
      expect(create).toHaveBeenCalledTimes(1);
      expect(readExperimentDraft()).toMatchObject({
        form: acceptedForm,
        step: 3,
        idempotencyKey: acceptedKey,
      });
      await act(async () => i18n.changeLanguage("en-US"));
      unmount();
      render(<CreateExperimentPage />);
      await screen.findByText("Your saved draft has been restored.");
      expect(create).toHaveBeenCalledTimes(1);
      expect(
        screen.getByRole("button", { name: "Run this configuration" }),
      ).toBeDisabled();
      expect(
        screen.getByRole("button", { name: "Run this configuration" }),
      ).toHaveAttribute("aria-disabled", "true");
      await userEvent.click(
        screen.getByRole("checkbox", { name: /I understand/ }),
      );
      await userEvent.click(
        screen.getByRole("button", { name: "Run this configuration" }),
      );
      expect(create.mock.calls[1][1]).toBe(create.mock.calls[0][1]);
      expect(create.mock.calls[1][0]).toEqual(acceptedForm);
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
    },
  );

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

  it("keeps the saved draft and wizard open when explicit exit is declined", async () => {
    enableNativeDialog();
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<CreateExperimentPage />);
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Save & exit" }));
    const dialog = screen.getByRole("dialog", { name: "Save & exit" });
    await userEvent.click(within(dialog).getByRole("button", { name: "Back" }));
    expect(screen.queryByRole("dialog", { name: "Save & exit" })).toBeNull();
    expect(confirm).not.toHaveBeenCalled();
    expect(window.location.pathname).toBe("/research/new");
    expect(readExperimentDraft()?.form.strategy_id).toBe(
      configuration.strategy_id,
    );
  });

  it("does not open the exit dialog when the draft cannot be saved", async () => {
    enableNativeDialog();
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    render(<CreateExperimentPage />);
    await screen.findByText(
      "Ranks eligible shares and builds a long-only portfolio.",
    );
    const write = vi
      .spyOn(Storage.prototype, "setItem")
      .mockImplementation(() => {
        throw new Error("storage unavailable");
      });
    try {
      await userEvent.click(
        screen.getByRole("button", { name: "Save & exit" }),
      );
      expect(screen.queryByRole("dialog", { name: "Save & exit" })).toBeNull();
      expect(window.location.pathname).toBe("/research/new");
      expect(screen.getByRole("alert")).toHaveTextContent(
        "This browser could not save your draft",
      );
    } finally {
      write.mockRestore();
    }
  });
});

describe("durable experiment detail", () => {
  it("offers a separate paper-account handoff only after a historical result succeeds", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "SUCCEEDED",
      mode: "historical_exploration",
      dataset_id: "cn-a-research-20100101-20251231-v1",
      configuration: {
        ...job.configuration,
        dataset_id: "cn-a-research-20100101-20251231-v1",
      },
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

  it("does not advertise paper setup for an unsupported historical dataset", async () => {
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
    await screen.findByText("What this run shows");
    expect(
      screen.queryByRole("link", {
        name: "Review these settings in a separate historical paper account",
      }),
    ).not.toBeInTheDocument();
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
    expect(
      screen.getByLabelText(
        "Technical details: ELIGIBLE_SIMULATION_ASSUMPTION",
      ),
    ).toBeInTheDocument();
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByText(
        "通过保守日线模拟执行检查。这属于模拟假设，不是真实市场成交的证明。",
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByLabelText("技术详情: ELIGIBLE_SIMULATION_ASSUMPTION"),
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

  it.each([
    ["removed row", true],
    ["focus moved elsewhere", false],
  ] as const)("recovers focus after an active-list poll fails: %s", async (_, onRow) => {
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce({ items: [job], total: 1, limit: 20, offset: 0 })
      .mockRejectedValueOnce(new ApiError(503, "service unavailable"));
    render(<ExperimentsPage />);
    await act(async () => vi.advanceTimersByTimeAsync(0));
    const rowLink = screen.getByRole("link", { name: /^Open experiment:/ });
    const refresh = screen.getByRole("button", { name: "Refresh" });
    rowLink.focus();
    if (!onRow) refresh.focus();
    await act(async () => vi.advanceTimersByTimeAsync(5000));
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("The server response could not be confirmed");
    expect(rowLink).not.toBeInTheDocument();
    expect(onRow ? alert : refresh).toHaveFocus();
  });

  it("returns focus to the list heading when a polled row disappears but the table remains", async () => {
    vi.useFakeTimers();
    const remaining = { ...job, job_id: "22222222-2222-4222-8222-222222222222", name: "Remaining study" };
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce({ items: [job, remaining], total: 2, limit: 20, offset: 0 })
      .mockResolvedValueOnce({ items: [remaining], total: 1, limit: 20, offset: 0 });
    render(<ExperimentsPage />);
    await act(async () => vi.advanceTimersByTimeAsync(0));
    const rowLink = screen.getAllByRole("link", { name: /^Open experiment:/ })[0];
    rowLink.focus();
    await act(async () => vi.advanceTimersByTimeAsync(5000));
    expect(rowLink).not.toBeInTheDocument();
    expect(screen.getByRole("link", { name: /^Open experiment: Remaining study/ })).toBeInTheDocument();
    expect(screen.getByRole("heading", { level: 1, name: "Your experiments" })).toHaveFocus();
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
      "The server response could not be confirmed",
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
    expect(screen.getByRole("heading", { level: 1, name: "Your experiments" })).toHaveFocus();
  });

  it("does not steal focus moved away while a failed-list retry is pending", async () => {
    const saved = { items: [{ ...job, status: "SUCCEEDED" as const }], total: 1, limit: 20, offset: 0 };
    let finishRetry: (() => void) | undefined;
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce(saved)
      .mockRejectedValueOnce(new ApiError(503, "service unavailable"))
      .mockImplementationOnce(() => new Promise((resolve) => {
        finishRetry = () => resolve(saved);
      }));
    render(<ExperimentsPage />);
    await screen.findByRole("cell", { name: "Complete" });
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await screen.findByRole("alert");
    await userEvent.click(screen.getByRole("button", { name: "Retry loading" }));
    const refresh = screen.getByRole("button", { name: "Refresh" });
    refresh.focus();
    await act(async () => finishRetry?.());
    expect(screen.getByRole("cell", { name: "Complete" })).toBeInTheDocument();
    expect(refresh).toHaveFocus();
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

  it("keeps cancellation focused and moves to its stable final status", async () => {
    const running = { ...job, status: "RUNNING" as const, phase: "EXECUTING" };
    const cancelled = { ...running, status: "CANCELLED" as const };
    let current: typeof job = running;
    vi.spyOn(experimentApi, "get").mockImplementation(async () => current);
    let finish!: (value: typeof cancelled) => void;
    const cancel = vi
      .spyOn(experimentApi, "cancel")
      .mockImplementation(() => new Promise((resolve) => (finish = resolve)));
    render(<ExperimentDetailPage jobId={job.job_id} />);
    const button = await screen.findByRole("button", { name: "Cancel task" });
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
      expect(
        screen.getByText("Cancelled", { selector: ".experimentStatus" }),
      ).toHaveFocus(),
    );
  });

  it("focuses the read error when polling removes the focused cancel button", async () => {
    vi.useFakeTimers();
    const running = { ...job, status: "RUNNING" as const, phase: "EXECUTING" };
    vi.spyOn(experimentApi, "get")
      .mockResolvedValueOnce(running)
      .mockRejectedValueOnce(new ApiError(503, "service unavailable"));
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await act(async () => {
      await vi.advanceTimersByTimeAsync(0);
    });
    screen.getByRole("button", { name: "Cancel task" }).focus();
    await act(async () => {
      await vi.advanceTimersByTimeAsync(2500);
    });
    expect(screen.getByRole("alert")).toHaveFocus();
  });

  it("does not steal focus when the user leaves cancellation before completion", async () => {
    const running = { ...job, status: "RUNNING" as const };
    const cancelled = { ...running, status: "CANCELLED" as const };
    let current: typeof job = running;
    vi.spyOn(experimentApi, "get").mockImplementation(async () => current);
    let finish!: (value: typeof cancelled) => void;
    vi.spyOn(experimentApi, "cancel").mockImplementation(
      () => new Promise((resolve) => (finish = resolve)),
    );
    render(<ExperimentDetailPage jobId={job.job_id} />);
    const button = await screen.findByRole("button", { name: "Cancel task" });
    button.focus();
    await userEvent.keyboard("{Enter}");
    const refresh = screen.getByRole("button", { name: "Refresh" });
    refresh.focus();
    current = cancelled;
    await act(async () => finish(cancelled));
    await screen.findByText("Cancelled", { selector: ".experimentStatus" });
    expect(refresh).toHaveFocus();
  });

  it("does not repeat a cancellation already acknowledged by the server", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "RUNNING",
      cancel_requested: true,
    });
    const cancel = vi.spyOn(experimentApi, "cancel");
    render(<ExperimentDetailPage jobId={job.job_id} />);
    const button = await screen.findByRole("button", { name: "Cancel task" });
    expect(button).toHaveAttribute("aria-disabled", "true");
    button.focus();
    await userEvent.keyboard("{Enter}");
    await userEvent.click(button);
    expect(cancel).not.toHaveBeenCalled();
    expect(button).toHaveFocus();
  });

  it.each(["failure-first", "confirmation-first"] as const)(
    "reconciles a lost cancel response with the confirmed task state: %s",
    async (order) => {
      const running = {
        ...job,
        status: "RUNNING" as const,
        phase: "EXECUTING" as const,
      };
      const confirmed =
        order === "failure-first"
          ? { ...running, cancel_requested: true }
          : { ...running, status: "CANCELLED" as const };
      let current: typeof job = running;
      vi.spyOn(experimentApi, "get").mockImplementation(async () => current);
      let fail!: (reason: unknown) => void;
      const cancel = vi
        .spyOn(experimentApi, "cancel")
        .mockImplementation(() => new Promise((_, reject) => (fail = reject)));
      render(<ExperimentDetailPage jobId={job.job_id} />);
      await userEvent.click(
        await screen.findByRole("button", { name: "Cancel task" }),
      );
      expect(cancel).toHaveBeenCalledTimes(1);

      if (order === "failure-first") {
        await act(async () => fail(new ApiError(503, "unavailable")));
        expect(screen.getByRole("alert")).toHaveTextContent(
          "The server response could not be confirmed",
        );
      }
      current = confirmed;
      await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
      if (order === "failure-first")
        await screen.findByText(
          "Cancellation requested. The server will stop safely at its next checkpoint.",
        );
      else
        await screen.findByText("Cancelled", {
          selector: ".experimentStatus",
        });
      if (order === "confirmation-first")
        await act(async () => fail(new ApiError(503, "unavailable")));
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();

      if (order === "confirmation-first") {
        vi.spyOn(experimentApi, "retry").mockRejectedValue(
          new ApiError(503, "unavailable"),
        );
        await userEvent.click(
          screen.getByRole("button", { name: "Start or reopen linked retry" }),
        );
        expect(screen.getByRole("alert")).toHaveTextContent(
          "The server response could not be confirmed",
        );
      }
    },
  );

  it("keeps denied cancellation visible when a different actor later requests cancellation", async () => {
    const running = { ...job, status: "RUNNING" as const };
    let current: typeof job = running;
    vi.spyOn(experimentApi, "get").mockImplementation(async () => current);
    vi.spyOn(experimentApi, "cancel").mockRejectedValue(
      new ApiError(403, "denied"),
    );
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await userEvent.click(
      await screen.findByRole("button", { name: "Cancel task" }),
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Access was denied");
    current = { ...running, cancel_requested: true };
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    await screen.findByText(
      "Cancellation requested. The server will stop safely at its next checkpoint.",
    );
    expect(screen.getByRole("alert")).toHaveTextContent("Access was denied");
  });

  it("keeps retry focused through an uncertain response without a duplicate", async () => {
    vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...job,
      status: "INTERRUPTED",
      phase: "INTERRUPTED",
    });
    let fail!: (reason: unknown) => void;
    const retry = vi
      .spyOn(experimentApi, "retry")
      .mockImplementation(() => new Promise((_, reject) => (fail = reject)));
    render(<ExperimentDetailPage jobId={job.job_id} />);
    const button = await screen.findByRole("button", {
      name: "Start or reopen linked retry",
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
    expect(screen.getByRole("alert")).toHaveTextContent(
      "The server response could not be confirmed",
    );
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
    let completeRetry: ((value: typeof result) => void) | undefined;
    vi.spyOn(experimentApi, "result")
      .mockRejectedValueOnce(new ApiError(403, "Forbidden", "FORBIDDEN"))
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            completeRetry = resolve;
          }),
      );
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
    screen.getByRole("button", { name: "Retry loading" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(
      screen.getByRole("heading", { level: 1, name: job.name }),
    ).toHaveFocus();
    await act(async () => completeRetry?.(result));
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: job.name }),
    ).toHaveFocus();
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
    expect(screen.getByRole("alert")).toHaveFocus();
    expect(screen.queryByText("What this run shows")).not.toBeInTheDocument();
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
  });

  it("hides saved results and retains focus while a manual status refresh waits", async () => {
    const context = vi
      .spyOn(pageContext, "usePageDataContext")
      .mockImplementation(() => undefined);
    const completed = {
      ...job,
      status: "SUCCEEDED" as const,
      result_available: true,
    };
    let resolveRefresh: ((value: typeof completed) => void) | undefined;
    const get = vi
      .spyOn(experimentApi, "get")
      .mockResolvedValueOnce(completed)
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            resolveRefresh = resolve;
          }),
      );
    vi.spyOn(experimentApi, "result").mockResolvedValue({
      ...result,
      date_end: "2031-06-27",
    });
    render(<ExperimentDetailPage jobId={job.job_id} />);
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
    await waitFor(() =>
      expect(context).toHaveBeenLastCalledWith(
        "synthetic_demo",
        "2031-06-27",
        "observed",
      ),
    );
    screen.getByRole("button", { name: "Refresh" }).focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
    expect(screen.queryByText("What this run shows")).not.toBeInTheDocument();
    const loading = screen.getByText("Loading…");
    expect(loading).toHaveAttribute("role", "status");
    expect(loading).toHaveFocus();
    expect(context).toHaveBeenLastCalledWith(null, null, "requested");
    await act(async () => resolveRefresh?.(completed));
    expect(await screen.findByText("What this run shows")).toBeInTheDocument();
    expect(document.querySelector(".experimentStatus")).toHaveFocus();
  });

  it("ignores an older poll response after a manual refresh starts", async () => {
    vi.useFakeTimers();
    const running = { ...job, status: "RUNNING" as const };
    const completed = { ...job, status: "SUCCEEDED" as const };
    let resolvePoll!: (value: typeof running) => void;
    let resolveRefresh!: (value: typeof completed) => void;
    const get = vi
      .spyOn(experimentApi, "get")
      .mockResolvedValueOnce(running)
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolvePoll = resolve)),
      )
      .mockImplementationOnce(
        () => new Promise((resolve) => (resolveRefresh = resolve)),
      );
    render(<ExperimentDetailPage jobId={job.job_id} />);
    await act(async () => vi.advanceTimersByTimeAsync(0));
    await act(async () => vi.advanceTimersByTimeAsync(2500));
    expect(get).toHaveBeenCalledTimes(2);
    fireEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(get).toHaveBeenCalledTimes(3);
    await act(async () => resolvePoll(running));
    expect(screen.getByText("Loading…")).toBeInTheDocument();
    expect(
      screen.queryByText("Running", { selector: ".experimentStatus" }),
    ).not.toBeInTheDocument();
    await act(async () => resolveRefresh(completed));
    expect(
      screen.getByText("Complete", { selector: ".experimentStatus" }),
    ).toBeInTheDocument();
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
    await screen.findByRole("link", { name: new RegExp(`^${job.name} ·`) });
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
    screen.getByRole("button", { name: "Remove filter: Status" }).focus();
    await userEvent.keyboard("{Enter}");
    expect(screen.getByLabelText("Status")).toHaveValue("");
    expect(
      screen.getByRole("region", { name: "Study view settings" }),
    ).toHaveFocus();
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
    await screen.findByRole("link", { name: new RegExp(`^${job.name} ·`) });
    await userEvent.type(screen.getByLabelText("Search saved studies"), "M1");
    await waitFor(() =>
      expect(window.history.state.experimentView.q).toBe("M1"),
    );
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await waitFor(() => expect(window.history.state.experimentOffset).toBe(20));
    await screen.findByRole("link", { name: new RegExp(`^${job.name} ·`) });
    expect(window.localStorage.getItem(EXPERIMENT_VIEW_KEY)).toBeNull();
    await userEvent.click(
      screen.getByRole("link", { name: new RegExp(`^${job.name} ·`) }),
    );
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
  it("keeps unknown saved plan reasons distinct from an actual strategy exit", async () => {
    const unknown = "UNRECOGNIZED_TEST_REASON";
    const candidate = plan.candidates[0];
    const saved = {
      ...plan,
      candidates: [
        candidate,
        {
          ...candidate,
          security_id: "CN-A:SSE:600001",
          trigger_reason: "EXITED_STRATEGY_TARGET",
          side: "SELL",
          target_weight: "0",
          held_quantity: "100",
          target_quantity: "0",
        },
        {
          ...candidate,
          security_id: "CN-A:SSE:600002",
          trigger_reason: unknown,
        },
      ],
    };
    render(
      <ExperimentPlan
        plan={
          parseResult({ ...result, simulation_plan: saved }).simulation_plan ??
          null
        }
      />,
    );
    expect(
      screen.getByText("Top-ranked eligible momentum/low-volatility share"),
    ).toBeVisible();
    expect(screen.getByText("No longer in the strategy target")).toBeVisible();
    expect(
      screen.getByText(`Unrecognized recorded reason (${unknown})`),
    ).toBeVisible();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(screen.getByText("不再属于策略目标持仓")).toBeVisible();
    expect(screen.getByText(`未识别的已记录原因 (${unknown})`)).toBeVisible();
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
