import { act, render, screen, within } from "@testing-library/react";
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
import { ExperimentsPage } from "./ExperimentsPage";
import { job, result } from "./fixtures.test-data";
import type { Experiment } from "./types";

const ids = [1, 2, 3, 4].map((n) => `aa000000-0000-4000-8000-00000000000${n}`);
const runs: Experiment[] = ids.map((id, index) => ({
  ...job,
  job_id: id,
  name: `Study ${index + 1}`,
  status: "SUCCEEDED",
  result_available: true,
}));
beforeEach(async () => {
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
        name: "Select for comparison: Study 1",
      }),
    );
    await userEvent.click(
      screen.getByRole("checkbox", { name: "Select for comparison: Study 2" }),
    );
    expect(compare).toBeEnabled();
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    await userEvent.click(
      await screen.findByRole("checkbox", {
        name: "Select for comparison: Study 3",
      }),
    );
    expect(
      screen.getByRole("checkbox", { name: "Select for comparison: Study 4" }),
    ).toBeDisabled();
    expect(
      screen.getByRole("checkbox", {
        name: "Select for comparison: Running study",
      }),
    ).toBeDisabled();
    await userEvent.click(compare);
    expect(window.location.pathname + window.location.search).toBe(
      comparisonUrl(ids.slice(0, 3)),
    );
  });

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
    expect(screen.getAllByText("Same", { exact: true })).toHaveLength(6);
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
  });
});
