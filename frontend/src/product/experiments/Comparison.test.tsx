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
import { experimentApi } from "./api";
import {
  comparisonConditions,
  comparableDecimal,
  comparisonUrl,
  parseComparisonIds,
} from "./comparison";
import { ExperimentComparePage } from "./ExperimentComparePage";
import { EXPERIMENT_VIEW_KEY, ExperimentsPage } from "./ExperimentsPage";
import { job, result } from "./fixtures.test-data";
import type { Experiment, Page } from "./types";

const ids = [1, 2, 3, 4].map((n) => `aa000000-0000-4000-8000-00000000000${n}`);
const runs: Experiment[] = ids.map((id, index) => ({
  ...job,
  job_id: id,
  name: `Study ${index + 1}`,
  status: "SUCCEEDED",
  result_available: true,
}));
beforeEach(async () => {
  window.localStorage.removeItem(EXPERIMENT_VIEW_KEY);
  await i18n.changeLanguage("en-US");
  window.history.replaceState({}, "", comparisonUrl(ids.slice(0, 2)));
});

describe("experiment comparison", () => {
  it("compares decimals without floating point and checks exactly six conditions", () => {
    expect(comparableDecimal("-000.000")).toBe("0");
    expect(comparableDecimal("00100.000000000000000010")).toBe(
      "100.00000000000000001",
    );
    const equivalent = {
      ...job,
      configuration: {
        ...job.configuration,
        costs: { commission_rate: "0.0003000", minimum_commission: "5.0" },
      },
    };
    expect(comparisonConditions(equivalent)).toEqual(comparisonConditions(job));
    expect(Object.keys(comparisonConditions(job))).toEqual([
      "data",
      "period",
      "costs",
      "cash",
      "risk",
      "strategy",
    ]);
    const differing = {
      ...job,
      configuration: {
        ...job.configuration,
        initial_cash: "100000.000000000000000002",
      },
    };
    expect(comparisonConditions(differing).cash).not.toBe(
      comparisonConditions(job).cash,
    );
  });

  it("rejects missing, duplicate and unbounded identifiers before requesting a job", () => {
    expect(parseComparisonIds(`?ids=${ids.join(",")}`)).toBeNull();
    expect(parseComparisonIds(`?ids=${ids[0]},${ids[0]}`)).toBeNull();
    expect(parseComparisonIds(`?ids=${ids[0]},missing`)).toBeNull();
    window.history.replaceState({}, "", "/experiments/compare?ids=unknown");
    const get = vi.spyOn(experimentApi, "get");
    render(<ExperimentComparePage />);
    expect(screen.getByRole("alert")).toHaveTextContent("invalid identifiers");
    expect(get).not.toHaveBeenCalled();
  });

  it("selects 2–3 successful experiments, retains selection between list pages and opens a durable URL", async () => {
    vi.spyOn(experimentApi, "list").mockImplementation(
      async (_signal, _limit, offset) => ({
        items: offset
          ? [
              runs[2],
              runs[3],
              { ...job, name: "Running study", job_id: "running" },
            ]
          : runs.slice(0, 2),
        total: 5,
        offset: offset ?? 0,
        limit: 2,
      }),
    );
    render(<ExperimentsPage />);
    const compare = screen.getByRole("button", {
      name: "Compare selected experiments",
    });
    expect(compare).toBeDisabled();
    await userEvent.click(
      await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 1 · Complete ·/,
      }),
    );
    await userEvent.click(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Study 2 · Complete ·/,
      }),
    );
    expect(compare).toBeEnabled();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await userEvent.click(
      await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 3 · Complete ·/,
      }),
    );
    expect(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Study 4 · Complete ·/,
      }),
    ).toBeDisabled();
    expect(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Running study · Queued ·/,
      }),
    ).toBeDisabled();
    await userEvent.click(compare);
    expect(window.location.pathname + window.location.search).toBe(
      comparisonUrl(ids.slice(0, 3)),
    );
  });

  it("distinguishes same-named studies in selection and removal controls", async () => {
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [
        { ...runs[0], name: "Same study", created_at: "2026-09-22T10:00:00Z" },
        { ...runs[1], name: "Same study", created_at: "2026-09-22T10:01:00Z" },
      ],
      total: 2,
      offset: 0,
      limit: 20,
    });
    render(<ExperimentsPage />);
    const boxes = await screen.findAllByRole("checkbox", {
      name: /Select for comparison: Same study · Complete ·/,
    });
    expect(boxes).toHaveLength(2);
    expect(boxes[0]).not.toHaveAttribute(
      "aria-label",
      boxes[1]?.getAttribute("aria-label"),
    );
    const studyLinks = screen.getAllByRole("link", {
      name: /^Same study · Complete ·/,
    });
    expect(studyLinks).toHaveLength(2);
    expect(studyLinks[0]).not.toHaveAttribute(
      "aria-label",
      studyLinks[1]?.getAttribute("aria-label"),
    );
    expect(
      screen.getAllByRole("link", { name: /^Open experiment: Same study ·/ }),
    ).toHaveLength(2);
    await userEvent.click(boxes[0]!);
    await userEvent.click(boxes[1]!);
    const remove = screen.getAllByRole("button", { name: /Remove Same study/ });
    expect(remove).toHaveLength(2);
    expect(remove[0]).not.toHaveAttribute(
      "aria-label",
      remove[1]?.getAttribute("aria-label"),
    );
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(
      screen.getAllByRole("button", { name: /移除 Same study/ }),
    ).toHaveLength(2);
  });

  it("restores comparison selection after result Back and list remount, without saving it in the view", async () => {
    window.history.replaceState({}, "", "/experiments");
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    const first = render(<ExperimentsPage />);
    await userEvent.click(
      await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 1/,
      }),
    );
    await userEvent.click(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 2/ }),
    );
    expect(screen.getByText("Selected: 2 / 3")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("link", { name: /^Open experiment: Study 1/ }),
    );
    first.unmount();
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/experiments"));
    const restored = render(<ExperimentsPage />);
    expect(screen.getByText("Selected: 2 / 3")).toBeInTheDocument();
    expect(
      await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 1/,
      }),
    ).toBeChecked();
    expect(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 2/ }),
    ).toBeChecked();
    await userEvent.click(
      screen.getByRole("button", { name: "Save this view" }),
    );
    expect(
      JSON.parse(window.localStorage.getItem(EXPERIMENT_VIEW_KEY)!),
    ).not.toHaveProperty("selected");
    restored.unmount();
    render(<ExperimentsPage />);
    expect(screen.getByText("Selected: 2 / 3")).toBeInTheDocument();
    await userEvent.click(
      screen.getByRole("button", { name: /Remove Study 1/ }),
    );
    expect(screen.getByText("Selected: 1 / 3")).toBeInTheDocument();
  });

  it("restores scroll only after rows load, then records user scrolling without replaying it on rerender", async () => {
    window.history.replaceState({ experimentScrollY: 693 }, "", "/experiments");
    vi.stubGlobal("scrollY", 55);
    let resolve!: (page: Page<Experiment>) => void;
    vi.spyOn(experimentApi, "list").mockReturnValue(
      new Promise((done) => {
        resolve = done;
      }),
    );
    render(<ExperimentsPage />);
    fireEvent.scroll(window);
    expect(window.history.state.experimentScrollY).toBe(693);
    expect(window.scrollTo).not.toHaveBeenCalled();
    await act(async () =>
      resolve({ items: runs, total: 4, offset: 0, limit: 20 }),
    );
    expect(window.scrollTo).toHaveBeenCalledExactlyOnceWith({
      top: 693,
      left: 0,
      behavior: "instant",
    });
    vi.stubGlobal("scrollY", 725);
    fireEvent.scroll(window);
    expect(window.history.state.experimentScrollY).toBe(725);
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(window.scrollTo).toHaveBeenCalledTimes(1);
    window.history.pushState({}, "", `/experiments/${ids[0]}`);
    fireEvent.scroll(window);
    expect(window.history.state).not.toHaveProperty("experimentScrollY");
  });

  it("does not restore the old list position after filters change while loading", async () => {
    window.history.replaceState({ experimentScrollY: 693 }, "", "/experiments");
    let resolve!: (page: Page<Experiment>) => void;
    vi.spyOn(experimentApi, "list")
      .mockReturnValueOnce(new Promise(() => {}))
      .mockReturnValueOnce(
        new Promise((done) => {
          resolve = done;
        }),
      );
    render(<ExperimentsPage />);
    fireEvent.change(screen.getByRole("searchbox"), {
      target: { value: "Study" },
    });
    await act(async () =>
      resolve({ items: runs, total: 4, offset: 0, limit: 20 }),
    );
    expect(window.scrollTo).not.toHaveBeenCalled();
    expect(window.history.state.experimentScrollY).toBeNull();
  });

  it.each([null, -1, "693", NaN, Infinity])(
    "ignores invalid list scroll metadata: %j",
    async (position) => {
      window.history.replaceState(
        { experimentScrollY: position },
        "",
        "/experiments",
      );
      vi.spyOn(experimentApi, "list").mockResolvedValue({
        items: runs,
        total: 4,
        offset: 0,
        limit: 20,
      });
      render(<ExperimentsPage />);
      await screen.findByRole("link", { name: /^Open experiment: Study 1/ });
      expect(window.scrollTo).not.toHaveBeenCalled();
    },
  );

  it.each([
    null,
    [null],
    [{ id: ids[0], name: "Study", createdAt: "not-a-date" }],
    [1, 2].map(() => ({
      id: ids[0],
      name: "Study",
      createdAt: job.created_at,
    })),
    ids.map((id) => ({ id, name: "Study", createdAt: job.created_at })),
  ])(
    "ignores malformed, duplicate or oversized history selection: %j",
    async (selection) => {
      window.history.replaceState(
        { experimentSelection: selection },
        "",
        "/experiments",
      );
      vi.spyOn(experimentApi, "list").mockResolvedValue({
        items: runs.slice(0, 2),
        total: 2,
        offset: 0,
        limit: 20,
      });
      render(<ExperimentsPage />);
      expect(screen.getByText("Selected: 0 / 3")).toBeInTheDocument();
      expect(
        screen.getByRole("button", { name: "Compare selected experiments" }),
      ).toBeDisabled();
      expect(
        await screen.findByRole("checkbox", {
          name: /Select for comparison: Study 1/,
        }),
      ).not.toBeChecked();
    },
  );

  it("keeps unknown and unfinished requested studies visible instead of making a partial comparison", async () => {
    vi.spyOn(experimentApi, "get").mockImplementation(async (id) => {
      if (id === ids[0]) throw new ApiError(404, "Unknown");
      return { ...runs[1], status: "RUNNING", result_available: false };
    });
    const summary = vi.spyOn(experimentApi, "result");
    render(<ExperimentComparePage />);
    const error = await screen.findByRole("alert");
    expect(error).toHaveTextContent("Comparison is incomplete");
    expect(error).toHaveTextContent(ids[0]);
    expect(error).toHaveTextContent("Study 2");
    expect(error).toHaveTextContent(
      "does not have a successful complete result",
    );
    expect(summary).not.toHaveBeenCalled();
    expect(
      screen.queryByText("Saved full-period results"),
    ).not.toBeInTheDocument();
  });

  it("retains known study names on result failure and retries without stale or partial metrics", async () => {
    vi.spyOn(experimentApi, "get").mockImplementation(async (id) =>
      runs.find((run) => run.job_id === id)!,
    );
    let reject!: (reason: Error) => void;
    let resolve!: (value: typeof result) => void;
    let attempts = 0;
    const summary = vi
      .spyOn(experimentApi, "result")
      .mockImplementation((id) =>
        id !== ids[2]
          ? Promise.resolve({ ...result, job_id: id })
          : new Promise((done, fail) => {
              attempts += 1;
              if (attempts === 1) reject = fail;
              else resolve = done;
            }),
      );
    render(<ExperimentComparePage />);
    await screen.findByRole("heading", { name: "Saved full-period results" });
    act(() => {
      window.history.pushState({}, "", comparisonUrl([ids[0], ids[2]]));
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    await waitFor(() =>
      expect(summary).toHaveBeenCalledWith(ids[2], expect.any(AbortSignal)),
    );
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    await act(async () =>
      reject(new ApiError(503, "Unavailable", "UNREGISTERED_RESULT_ERROR")),
    );
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent("Study 1");
    expect(alert).toHaveTextContent("Study 3");
    expect(alert).toHaveTextContent("The server could not finish this request");
    expect(alert).not.toHaveTextContent("expand technical details");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(alert).toHaveTextContent("服务端未完成请求");
    await userEvent.click(screen.getByRole("button", { name: "重新加载" }));
    await waitFor(() => expect(attempts).toBe(2));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    await act(async () => resolve({ ...result, job_id: ids[2]! }));
    await screen.findByRole("heading", { name: "已保存的完整区间结果" });
    expect(screen.getAllByRole("table")).toHaveLength(2);
    expect(screen.getByRole("row", { name: /^累计收益/ })).toHaveTextContent(
      "0.01%0.01%",
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByText("Study 2")).not.toBeInTheDocument();
  });

  it("shows exact metrics/nulls and six conditions, reacts to query-only navigation and language changes", async () => {
    vi.spyOn(experimentApi, "get").mockImplementation(async (id) => {
      const found = runs.find((r) => r.job_id === id)!;
      return id === ids[2]
        ? {
            ...found,
            configuration: {
              ...found.configuration,
              risk: {
                ...found.configuration.risk,
                max_position_weight: "0.05",
              },
            },
          }
        : found;
    });
    vi.spyOn(experimentApi, "result").mockImplementation(async (id) => ({
      ...result,
      job_id: id,
      benchmark_id: "SYNTHETIC_EQUAL_WEIGHT",
    }));
    render(<ExperimentComparePage />);
    expect(
      await screen.findByText(/These six configuration conditions match/),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        /Implementation fingerprints, execution-model versions and effective statutory cost schedules are not verified here/,
      ),
    ).toBeInTheDocument();
    expect(screen.getAllByText("12.00")).toHaveLength(2);
    await userEvent.click(
      screen.getByRole("checkbox", { name: "Show full precision" }),
    );
    expect(screen.getAllByText("12.000000000000000001")).toHaveLength(2);
    const benchmark = screen.getByRole("row", { name: /Benchmark return/ });
    expect(
      within(benchmark)
        .getAllByRole("cell")
        .every((cell) => cell.textContent?.includes("N/A")),
    ).toBe(true);
    expect(benchmark).toHaveTextContent(
      "Synthetic equal-weight benchmark (demo)",
    );
    expect(benchmark).not.toHaveTextContent("SYNTHETIC_EQUAL_WEIGHT");
    expect(screen.getAllByText("Same", { exact: true })).toHaveLength(6);
    const costs = screen.getByRole("row", { name: /Cost configuration/ });
    expect(within(costs).getAllByRole("cell")[0]).toHaveTextContent("0.0003");
    expect(within(costs).getAllByRole("cell")[0]).not.toHaveTextContent(
      "0.03%",
    );
    const risk = screen.getByRole("row", { name: /Risk configuration/ });
    expect(within(risk).getAllByRole("cell")[0]).toHaveTextContent("-0.2");
    act(() => {
      window.history.pushState({}, "", comparisonUrl([ids[0], ids[2]]));
      window.dispatchEvent(new PopStateEvent("popstate"));
    });
    expect(
      await screen.findByText(/Some conditions differ/),
    ).toBeInTheDocument();
    expect(screen.getAllByText("Different", { exact: true })).toHaveLength(1);
    expect(screen.getByLabelText("Shareable comparison URL")).toHaveValue(
      window.location.href,
    );
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(
      screen.getByRole("heading", { name: "实验比较" }),
    ).toBeInTheDocument();
    expect(screen.getByText("风险配置")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /^基准收益/ })).toHaveTextContent(
      "合成等权基准（演示）",
    );
  });
});
