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
import { experimentApi } from "./api";
import {
  comparisonConditions,
  comparableDecimal,
  comparisonUrl,
  parseComparisonIds,
} from "./comparison";
import { ExperimentComparePage } from "./ExperimentComparePage";
import { ExperimentDetailPage } from "./ExperimentDetailPage";
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
  it.each(["en-US", "zh-CN"])(
    "compares actual result dates as well as requested dates (%s)",
    async (locale) => {
      await i18n.changeLanguage(locale);
      const saved = [
        { ...result, date_start: "2023-01-03", date_end: "2023-01-06" },
        { ...result, date_start: "2023-01-04", date_end: "2023-01-06" },
      ];
      const before = JSON.stringify(saved);
      vi.spyOn(experimentApi, "get").mockImplementation(async (id) => ({
        ...runs.find((run) => run.job_id === id)!,
        configuration: {
          ...job.configuration,
          start_date: "2023-01-01",
          end_date: "2023-01-07",
        },
      }));
      vi.spyOn(experimentApi, "result").mockImplementation(
        async (id) => saved[ids.indexOf(id)]!,
      );
      const comparison = render(<ExperimentComparePage />);
      const table = await screen.findByRole("table", {
        name:
          locale === "en-US"
            ? "Are these conditions the same?"
            : "这些条件是否一致？",
      });
      const period = within(table).getByRole("row", {
        name: locale === "en-US" ? /^Trading period/ : /^交易区间/,
      });
      expect(period).toHaveTextContent(
        locale === "en-US" ? "Different" : "不同",
      );
      expect(period).toHaveTextContent("2023-01-01 → 2023-01-07");
      expect(period).toHaveTextContent("2023-01-03 → 2023-01-06");
      expect(period).toHaveTextContent("2023-01-04 → 2023-01-06");
      expect(period).toHaveTextContent(
        locale === "en-US" ? "Actual result interval" : "实际结果区间",
      );
      expect(
        screen.getByText(
          locale === "en-US" ? /Some conditions differ/ : /部分条件不同/,
        ),
      ).toBeVisible();
      comparison.unmount();
      vi.spyOn(experimentApi, "equity").mockResolvedValue({
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      });
      render(<ExperimentDetailPage jobId={ids[0]!} />);
      const interval = await screen.findByText(
        locale === "en-US"
          ? "Actual result interval: 2023-01-03 → 2023-01-06 · Asia/Shanghai"
          : "实际结果区间: 2023-01-03 → 2023-01-06 · Asia/Shanghai",
      );
      expect(interval).toBeVisible();
      expect(
        screen.getByText(
          locale === "en-US"
            ? "Requested interval: 2023-01-01 → 2023-01-07 · Asia/Shanghai"
            : "请求区间: 2023-01-01 → 2023-01-07 · Asia/Shanghai",
        ),
      ).toBeVisible();
      expect(JSON.stringify(saved)).toBe(before);
    },
  );

  it.each(
    ["en-US", "zh-CN"].flatMap((locale) =>
      ["KNOWN_ECONOMIC_COVERAGE_GAP", "HISTORICAL_DATASET_QUALITY_UNKNOWN"].map(
        (quality) => ({ locale, quality }),
      ),
    ),
  )(
    "shows affected study quality before comparison money ($locale / $quality)",
    async ({ locale, quality }) => {
      await i18n.changeLanguage(locale);
      window.history.replaceState({}, "", comparisonUrl(ids.slice(0, 3)));
      const saved = {
        ...result,
        current_dataset_quality: quality as
          "KNOWN_ECONOMIC_COVERAGE_GAP" | "HISTORICAL_DATASET_QUALITY_UNKNOWN",
        current_source_integrity: "SOURCE_CONTRACT_INTEGRITY_FAILED" as const,
      };
      const before = JSON.stringify(saved);
      vi.spyOn(experimentApi, "get").mockImplementation(async (id) =>
        runs.find((run) => run.job_id === id)!,
      );
      vi.spyOn(experimentApi, "result").mockImplementation(async (id) =>
        id === ids[0] ? saved : result,
      );
      render(<ExperimentComparePage />);
      const table = await screen.findByRole("table", {
        name:
          locale === "en-US"
            ? "Saved full-period results"
            : "已保存的完整区间结果",
      });
      const note = screen.getByRole("note");
      expect(note).toHaveTextContent(
        locale === "en-US"
          ? "source references failed verification"
          : "来源引用未通过验证",
      );
      expect(note).toHaveTextContent("1. Study 1");
      expect(note).not.toHaveTextContent("2. Study 2");
      expect(note).not.toHaveTextContent("3. Study 3");
      expect(
        note.compareDocumentPosition(table) & Node.DOCUMENT_POSITION_FOLLOWING,
      ).toBeTruthy();
      expect(note).toHaveTextContent(
        quality === "KNOWN_ECONOMIC_COVERAGE_GAP"
          ? locale === "en-US"
            ? "Economic completeness is not validated"
            : "经济完整性尚未验证"
          : locale === "en-US"
            ? "unknown"
            : "未知",
      );
      await userEvent.click(
        screen.getByRole("checkbox", {
          name: locale === "en-US" ? "Show full precision" : "显示完整精度",
        }),
      );
      expect(within(table).getAllByText("12.000000000000000001")).toHaveLength(
        3,
      );
      expect(JSON.stringify(saved)).toBe(before);
    },
  );

  it.each([null, undefined])(
    "does not infer reviewed quality from a missing marker (%s)",
    async (quality) => {
      vi.spyOn(experimentApi, "get").mockImplementation(async (id) =>
        runs.find((run) => run.job_id === id)!,
      );
      vi.spyOn(experimentApi, "result").mockResolvedValue({
        ...result,
        current_dataset_quality: quality,
      });
      render(<ExperimentComparePage />);
      await screen.findByRole("table", { name: "Saved full-period results" });
      expect(screen.queryByRole("note")).not.toBeInTheDocument();
      expect(
        screen.queryByText(/financially validated/),
      ).not.toBeInTheDocument();
      expect(screen.getAllByRole("article")).toHaveLength(2);
    },
  );

  it.each(["en-US", "zh-CN"])(
    "keeps later quality advice scoped to its saved result and comparison card (%s)",
    async (locale) => {
      await i18n.changeLanguage(locale);
      const saved = {
        ...result,
        current_dataset_quality: "KNOWN_ECONOMIC_COVERAGE_GAP" as const,
        current_source_integrity: "SOURCE_CONTRACT_INTEGRITY_FAILED" as const,
      };
      const before = JSON.stringify(saved);
      vi.spyOn(experimentApi, "get").mockImplementation(async (id) =>
        runs.find((run) => run.job_id === id)!,
      );
      vi.spyOn(experimentApi, "result").mockImplementation(async (id) =>
        id === ids[0] ? saved : result,
      );
      vi.spyOn(experimentApi, "equity").mockResolvedValue({
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      });
      const text =
        locale === "en-US"
          ? /A later review found an unmodeled corporate-action gap/
          : /后续复核发现此冻结数据版本存在尚未建模的公司行动缺口/;
      const detail = render(<ExperimentDetailPage jobId={ids[0]!} />);
      const notices = await screen.findAllByText(text);
      expect(notices).toHaveLength(2); // limitations and shared saved plan
      expect(screen.getByRole("note")).toHaveTextContent(text);
      await userEvent.click(
        screen.getByRole("checkbox", {
          name: locale === "en-US" ? "Show full precision" : "显示完整精度",
        }),
      );
      expect(screen.getByText("12.000000000000000001")).toBeVisible();
      detail.unmount();
      render(<ExperimentComparePage />);
      expect(await screen.findAllByText(text)).toHaveLength(2);
      expect(screen.getByRole("note")).toHaveTextContent(text);
      const cards = screen.getAllByRole("article");
      const advice = within(cards[0]!).getByText(text);
      expect(cards[0]).toContainElement(advice);
      expect(cards[1]).not.toContainElement(advice);
      expect(within(cards[1]!).queryByText(text)).not.toBeInTheDocument();
      expect(JSON.stringify(saved)).toBe(before);
    },
  );
  it.each(["en-US", "zh-CN"])(
    "discloses the historical execution issue on a saved result in %s without revalidating it",
    async (locale) => {
      await i18n.changeLanguage(locale);
      const saved = {
        ...runs[0]!,
        mode: "historical_exploration" as const,
        dataset_id: "cn-a-research-20100101-20251231-v1",
        configuration: {
          ...job.configuration,
          dataset_id: "cn-a-research-20100101-20251231-v1",
        },
        created_at: "2030-01-01T00:00:00Z",
      };
      const get = vi.spyOn(experimentApi, "get").mockResolvedValue(saved);
      const summary = vi
        .spyOn(experimentApi, "result")
        .mockResolvedValue({ ...result, mode: "historical_exploration" });
      vi.spyOn(experimentApi, "equity").mockResolvedValue({
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      });
      render(<ExperimentDetailPage jobId={ids[0]!} />);
      const notice = await screen.findByText(
        locale === "en-US"
          ? /Earlier versions of this historical execution engine/
          : /旧版历史执行引擎可能错误拒绝本可成交的证券/,
      );
      expect(notice).toHaveTextContent(
        locale === "en-US"
          ? "does not revalidate old returns"
          : "不代表旧收益已重新验证",
      );
      await userEvent.click(
        screen.getByRole("checkbox", {
          name: locale === "en-US" ? "Show full precision" : "显示完整精度",
        }),
      );
      expect(screen.getByText("12.000000000000000001")).toBeInTheDocument();
      expect(
        screen.getByText(/100,012\.123456789012345678/),
      ).toBeInTheDocument();
      expect(get).toHaveBeenCalledTimes(1);
      expect(summary).toHaveBeenCalledTimes(1);
    },
  );

  it.each(["detail", "comparison"])(
    "keeps conflicting saved modes unverified in the %s view",
    async (view) => {
      vi.spyOn(experimentApi, "get").mockImplementation(async (id) => ({
        ...runs.find((run) => run.job_id === id)!,
        ...(id === ids[0]
          ? {
              mode: "historical_exploration" as const,
              dataset_id: "cn-a-research-20100101-20251231-v1",
              configuration: {
                ...job.configuration,
                dataset_id: "cn-a-research-20100101-20251231-v1",
              },
            }
          : {}),
      }));
      vi.spyOn(experimentApi, "result").mockImplementation(async (id) => ({
        ...result,
        job_id: id,
      }));
      vi.spyOn(experimentApi, "equity").mockResolvedValue({
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      });
      render(
        view === "detail" ? (
          <ExperimentDetailPage jobId={ids[0]!} />
        ) : (
          <ExperimentComparePage />
        ),
      );
      expect(
        await screen.findByText(
          /The saved execution source is not sufficiently verified/,
        ),
      ).toHaveTextContent("do not assume it is unaffected");
      expect(
        screen.queryByText(
          /Earlier versions of this historical execution engine/,
        ),
      ).toBeNull();
    },
  );

  it.each(["en-US", "zh-CN"])(
    "limits the %s comparison issue to the historical entry and preserves exact costs",
    async (locale) => {
      await i18n.changeLanguage(locale);
      const get = vi
        .spyOn(experimentApi, "get")
        .mockImplementation(async (id) => ({
          ...runs.find((run) => run.job_id === id)!,
          ...(id === ids[0]
            ? {
                mode: "historical_exploration" as const,
                dataset_id: "cn-a-research-20100101-20251231-v1",
                configuration: {
                  ...job.configuration,
                  dataset_id: "cn-a-research-20100101-20251231-v1",
                },
              }
            : {}),
        }));
      const summary = vi
        .spyOn(experimentApi, "result")
        .mockImplementation(async (id) => ({
          ...result,
          job_id: id,
          mode: id === ids[0] ? "historical_exploration" : "synthetic_demo",
        }));
      render(<ExperimentComparePage />);
      const notice = await screen.findByText(
        locale === "en-US"
          ? /Earlier versions of this historical execution engine/
          : /旧版历史执行引擎可能错误拒绝本可成交的证券/,
      );
      const cards = screen.getAllByRole("article");
      expect(cards[0]).toContainElement(notice);
      expect(cards[1]).not.toContainElement(notice);
      expect(
        within(cards[1]!).getByText(
          locale === "en-US"
            ? /These prices are synthetic/
            : /这里使用合成价格/,
        ),
      ).toBeInTheDocument();
      await userEvent.click(
        screen.getByRole("checkbox", {
          name: locale === "en-US" ? "Show full precision" : "显示完整精度",
        }),
      );
      expect(screen.getAllByText("12.000000000000000001")).toHaveLength(2);
      expect(get).toHaveBeenCalledTimes(2);
      expect(summary).toHaveBeenCalledTimes(2);
    },
  );

  it("starts a comparison from a reopened result with that result selected", async () => {
    window.history.replaceState({}, "", `/experiments/${ids[0]}`);
    vi.spyOn(experimentApi, "get").mockResolvedValue(runs[0]!);
    vi.spyOn(experimentApi, "result").mockResolvedValue(result);
    vi.spyOn(experimentApi, "equity").mockResolvedValue({
      items: [],
      total: 0,
      limit: 100,
      offset: 0,
    });
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    const detail = render(<ExperimentDetailPage jobId={ids[0]!} />);
    const link = await screen.findByRole("link", {
      name: "Select for comparison",
    });
    expect(
      screen.queryByText(
        /Earlier versions of this historical execution engine/,
      ),
    ).toBeNull();
    expect(link).toHaveAttribute("href", `/experiments?compare_from=${ids[0]}`);
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(
      screen.getByRole("link", { name: "选择用于比较" }),
    ).toBeInTheDocument();
    await act(async () => i18n.changeLanguage("en-US"));
    await userEvent.click(link);
    detail.unmount();
    expect(window.location.pathname + window.location.search).toBe(
      `/experiments?compare_from=${ids[0]}`,
    );
    render(<ExperimentsPage />);
    expect(await screen.findByText("Selected: 1 / 3")).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 1/ }),
    ).toBeChecked();
    await userEvent.click(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 2/ }),
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Compare selected experiments" }),
    );
    expect(window.location.pathname + window.location.search).toBe(
      comparisonUrl(ids.slice(0, 2)),
    );
  });

  it("does not preselect an unfinished or invalid comparison source", async () => {
    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    const get = vi.spyOn(experimentApi, "get").mockResolvedValue({
      ...runs[0]!,
      status: "RUNNING",
      result_available: false,
    });
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    const unfinished = render(<ExperimentsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "does not have a successful complete result yet",
    );
    expect(screen.getByText("Selected: 0 / 3")).toBeInTheDocument();
    expect(window.location.search).toBe("");
    unfinished.unmount();
    get.mockClear();
    window.history.replaceState({}, "", "/experiments?compare_from=invalid");
    render(<ExperimentsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "invalid identifiers",
    );
    expect(get).not.toHaveBeenCalled();
    expect(window.location.search).toBe("");
  });

  it("clears a missing saved source instead of retrying a terminal 404", async () => {
    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    vi.spyOn(experimentApi, "get").mockRejectedValue(
      new ApiError(404, "Missing"),
    );
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    render(<ExperimentsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent("not available");
    expect(window.location.search).toBe("");
    expect(screen.queryByRole("button", { name: "Retry loading" })).toBeNull();
    expect(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Study 2/,
      }),
    ).toBeEnabled();
  });

  it("keeps list selection unavailable until the result handoff resolves", async () => {
    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    let resolve!: (run: Experiment) => void;
    vi.spyOn(experimentApi, "get").mockImplementation(
      () =>
        new Promise<Experiment>((ready) => {
          resolve = ready;
        }),
    );
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    render(<ExperimentsPage />);
    const other = await screen.findByRole("checkbox", {
      name: /Select for comparison: Study 2/,
    });
    expect(other).toBeDisabled();
    expect(screen.getByText("Selected: 0 / 3")).toBeInTheDocument();
    await act(async () => resolve(runs[0]!));
    expect(await screen.findByText("Selected: 1 / 3")).toBeInTheDocument();
    expect(other).toBeEnabled();
    await userEvent.click(other);
    expect(screen.getByText("Selected: 2 / 3")).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Study 1/,
      }),
    ).toBeChecked();
  });

  it.each(["success", "failure"])(
    "abandons a pending source on same-path navigation without a late %s changing manual selection",
    async (outcome) => {
      window.history.replaceState(
        {},
        "",
        `/experiments?compare_from=${ids[0]}`,
      );
      let resolve!: (run: Experiment) => void;
      let reject!: (reason: Error) => void;
      const get = vi.spyOn(experimentApi, "get").mockReturnValue(
        new Promise((done, fail) => {
          resolve = done;
          reject = fail;
        }),
      );
      vi.spyOn(experimentApi, "list").mockResolvedValue({
        items: runs.slice(0, 2),
        total: 2,
        offset: 0,
        limit: 20,
      });
      render(<ExperimentsPage />);
      const other = await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 2/,
      });
      expect(other).toBeDisabled();
      const signal = get.mock.calls[0]![1]!;
      act(() => {
        navigate("/experiments");
      });
      await waitFor(() => expect(signal.aborted).toBe(true));
      expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
      expect(other).toBeEnabled();
      await userEvent.click(other);
      await act(async () => {
        if (outcome === "success") resolve(runs[0]!);
        else reject(new TypeError("offline"));
      });
      expect(other).toBeChecked();
      expect(screen.getByText("Selected: 1 / 3")).toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /Remove Study 1/ }),
      ).toBeNull();
    },
  );

  it("switches a pending source on the same path and preserves identity across locale changes", async () => {
    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    let resolveA!: (run: Experiment) => void;
    let resolveB!: (run: Experiment) => void;
    const get = vi
      .spyOn(experimentApi, "get")
      .mockReturnValueOnce(
        new Promise((done) => {
          resolveA = done;
        }),
      )
      .mockReturnValueOnce(
        new Promise((done) => {
          resolveB = done;
        }),
      )
      .mockResolvedValue(runs[1]!);
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    render(<ExperimentsPage />);
    await screen.findByRole("checkbox", {
      name: /Select for comparison: Study 2/,
    });
    act(() => {
      navigate(`/experiments?compare_from=${ids[1]}`);
    });
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
    expect(get.mock.calls[0]![1]!.aborted).toBe(true);
    expect(get.mock.calls[1]![0]).toBe(ids[1]);
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(get).toHaveBeenCalledTimes(2);
    act(() => {
      navigate(`/experiments?compare_from=${ids[1]}#selection`);
    });
    expect(get.mock.calls[1]![1]!.aborted).toBe(false);
    expect(
      screen.getByRole("checkbox", { name: /选择用于比较: Study 2/ }),
    ).toBeDisabled();
    await act(async () => resolveA(runs[0]!));
    expect(screen.queryByRole("button", { name: /移除 Study 1/ })).toBeNull();
    await act(async () => resolveB(runs[1]!));
    expect(
      screen.getByRole("checkbox", { name: /选择用于比较: Study 2/ }),
    ).toBeChecked();
    expect(window.location.search).toBe("");
    await act(async () => i18n.changeLanguage("en-US"));
    expect(screen.getByText("Selected: 1 / 3")).toBeInTheDocument();
    expect(get).toHaveBeenCalledTimes(2);
    act(() => {
      navigate(`/experiments?compare_from=${ids[1]}`);
    });
    await waitFor(() => expect(get).toHaveBeenCalledTimes(3));
    await waitFor(() => expect(window.location.search).toBe(""));
    expect(screen.getByText("Selected: 1 / 3")).toBeInTheDocument();
  });

  it.each(["pending", "failed"])(
    "reloads the final source after batched A→B→A navigation from a %s request",
    async (state) => {
      window.history.replaceState(
        {},
        "",
        `/experiments?compare_from=${ids[0]}`,
      );
      const get = vi
        .spyOn(experimentApi, "get")
        .mockImplementationOnce(() =>
          state === "failed"
            ? Promise.reject(new TypeError("offline"))
            : new Promise(() => {}),
        )
        .mockResolvedValueOnce(runs[0]!);
      vi.spyOn(experimentApi, "list").mockResolvedValue({
        items: runs.slice(0, 2),
        total: 2,
        offset: 0,
        limit: 20,
      });
      render(<ExperimentsPage />);
      await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 2/,
      });
      if (state === "failed") await screen.findByRole("alert");
      act(() => {
        navigate(`/experiments?compare_from=${ids[1]}`);
        navigate(`/experiments?compare_from=${ids[0]}`);
      });
      await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
      expect(get.mock.calls[1]![0]).toBe(ids[0]);
      expect(get.mock.calls[0]![1]!.aborted).toBe(true);
      await screen.findByText("Selected: 1 / 3");
      expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      expect(window.location.search).toBe("");
    },
  );

  it.each(["success", "not_ready"])(
    "ignores an obsolete source response before cleanup after a same-batch round trip (%s)",
    async (outcome) => {
      window.history.replaceState(
        {},
        "",
        `/experiments?compare_from=${ids[0]}`,
      );
      let resolveOld!: (run: Experiment) => void;
      const get = vi
        .spyOn(experimentApi, "get")
        .mockReturnValueOnce(
          new Promise((done) => {
            resolveOld = done;
          }),
        )
        .mockResolvedValueOnce(runs[0]!);
      vi.spyOn(experimentApi, "list").mockResolvedValue({
        items: runs.slice(0, 2),
        total: 2,
        offset: 0,
        limit: 20,
      });
      render(<ExperimentsPage />);
      await screen.findByRole("checkbox", {
        name: /Select for comparison: Study 2/,
      });
      await act(async () => {
        navigate(`/experiments?compare_from=${ids[1]}`);
        navigate(`/experiments?compare_from=${ids[0]}`);
        resolveOld({
          ...runs[0]!,
          name: "Obsolete source",
          ...(outcome === "not_ready"
            ? { status: "RUNNING", result_available: false }
            : {}),
        });
        await Promise.resolve();
      });
      await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
      expect(
        screen.getByRole("button", { name: /Remove Study 1/ }),
      ).toBeInTheDocument();
      expect(
        screen.queryByRole("button", { name: /Remove Obsolete source/ }),
      ).toBeNull();
      expect(screen.queryByRole("alert")).not.toBeInTheDocument();
      expect(screen.queryByText("Loading…")).not.toBeInTheDocument();
    },
  );

  it("restores manual selection on Forward between clean same-path history entries", async () => {
    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    const get = vi
      .spyOn(experimentApi, "get")
      .mockReturnValueOnce(new Promise(() => {}))
      .mockResolvedValueOnce(runs[0]!);
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    render(<ExperimentsPage />);
    await screen.findByRole("checkbox", {
      name: /Select for comparison: Study 2/,
    });
    act(() => {
      navigate("/experiments");
    });
    await userEvent.click(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 2/ }),
    );
    expect(window.history.state.experimentSelection[0].id).toBe(ids[1]);
    act(() => window.history.back());
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
    await waitFor(() => expect(window.location.search).toBe(""));
    expect(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 1/ }),
    ).toBeChecked();
    act(() => window.history.forward());
    await waitFor(() =>
      expect(window.history.state.experimentSelection[0].id).toBe(ids[1]),
    );
    await waitFor(() =>
      expect(
        screen.getByRole("checkbox", {
          name: /Select for comparison: Study 2/,
        }),
      ).toBeChecked(),
    );
    expect(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 1/ }),
    ).not.toBeChecked();
    expect(get).toHaveBeenCalledTimes(2);
  });

  it("reloads the source on Back/Forward without restarting the filtered list", async () => {
    window.history.replaceState(
      {
        experimentOffset: 20,
        experimentView: {
          q: "Study",
          status: "SUCCEEDED",
          mode: "",
          sort: "oldest",
          columns: { mode: true, period: true, created: true },
        },
      },
      "",
      `/experiments?compare_from=${ids[0]}`,
    );
    const pending: ((run: Experiment) => void)[] = [];
    const get = vi.spyOn(experimentApi, "get").mockImplementation(
      () =>
        new Promise((done) => {
          pending.push(done);
        }),
    );
    const list = vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 40,
      offset: 20,
      limit: 20,
    });
    render(<ExperimentsPage />);
    await screen.findByRole("checkbox", {
      name: /Select for comparison: Study 2/,
    });
    act(() => {
      navigate("/experiments");
    });
    act(() => window.history.back());
    await waitFor(() => expect(get).toHaveBeenCalledTimes(2));
    act(() => window.history.forward());
    await waitFor(() => expect(window.location.search).toBe(""));
    await waitFor(() => expect(get.mock.calls[1]![1]!.aborted).toBe(true));
    act(() => window.history.back());
    await waitFor(() => expect(get).toHaveBeenCalledTimes(3));
    await act(async () => {
      pending[0]!(runs[1]!);
      pending[1]!(runs[1]!);
      pending[2]!(runs[0]!);
    });
    expect(screen.getByText("Selected: 1 / 3")).toBeInTheDocument();
    expect(
      screen.getByRole("checkbox", { name: /Select for comparison: Study 1/ }),
    ).toBeChecked();
    expect(screen.getByRole("searchbox")).toHaveValue("Study");
    expect(list).toHaveBeenCalledTimes(1);
    expect(list).toHaveBeenCalledWith(
      expect.any(AbortSignal),
      20,
      20,
      "Study",
      {
        status: "SUCCEEDED",
        mode: undefined,
        sort: "oldest",
      },
    );
  });

  it("retains the source on transient failure, then retries or lets users choose manually", async () => {
    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    const get = vi
      .spyOn(experimentApi, "get")
      .mockRejectedValueOnce(new TypeError("offline"))
      .mockResolvedValueOnce(runs[0]!);
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: runs.slice(0, 2),
      total: 2,
      offset: 0,
      limit: 20,
    });
    const first = render(<ExperimentsPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not confirm a response",
    );
    expect(window.location.search).toBe(`?compare_from=${ids[0]}`);
    expect(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Study 2/,
      }),
    ).toBeDisabled();
    await userEvent.click(
      screen.getByRole("button", { name: "Retry loading" }),
    );
    expect(await screen.findByText("Selected: 1 / 3")).toBeInTheDocument();
    expect(get).toHaveBeenCalledTimes(2);
    expect(window.location.search).toBe("");
    expect(screen.getByText("Selected: 1 / 3")).toHaveFocus();
    first.unmount();

    window.history.replaceState({}, "", `/experiments?compare_from=${ids[0]}`);
    get.mockRejectedValue(new TypeError("offline"));
    render(<ExperimentsPage />);
    await screen.findByRole("alert");
    await userEvent.click(
      screen.getByRole("button", { name: "Choose studies manually" }),
    );
    expect(window.location.search).toBe("");
    expect(screen.getByText("Selected: 0 / 3")).toHaveFocus();
    expect(
      screen.getByRole("checkbox", {
        name: /Select for comparison: Study 2/,
      }),
    ).toBeEnabled();
  });

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
    expect(comparisonConditions(equivalent, result)).toEqual(
      comparisonConditions(job, result),
    );
    expect(Object.keys(comparisonConditions(job, result))).toEqual([
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
    expect(comparisonConditions(differing, result).cash).not.toBe(
      comparisonConditions(job, result).cash,
    );
    for (const key of ["date_start", "date_end"] as const) {
      expect(
        comparisonConditions(job, { ...result, [key]: "2023-01-04" }).period,
      ).not.toBe(comparisonConditions(job, result).period);
    }
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

  it("keeps same-named, same-second studies identifiable throughout comparison", async () => {
    const sameRuns = runs.slice(0, 2).map((run) => ({
      ...run,
      name: "Same study",
      created_at: "2026-09-22T10:00:00Z",
    }));
    vi.spyOn(experimentApi, "get").mockImplementation(async (id) =>
      sameRuns.find((run) => run.job_id === id)!,
    );
    vi.spyOn(experimentApi, "result").mockImplementation(async (id) => ({
      ...result,
      job_id: id,
    }));
    render(<ExperimentComparePage />);
    const labels = [1, 2].map(
      (number) => `${number}. Same study · 2026-09-22 10:00:00Z (UTC)`,
    );
    const tables = await screen.findAllByRole("table");
    for (const table of tables) {
      for (const [index, label] of labels.entries()) {
        expect(
          within(table).getByRole("link", { name: label }),
        ).toHaveAttribute("href", `/experiments/${ids[index]}`);
      }
    }
    const cards = screen.getAllByRole("article");
    for (const [index, label] of labels.entries()) {
      expect(
        within(cards[index]!).getByRole("heading", { name: label }),
      ).toBeInTheDocument();
      expect(
        within(cards[index]!).getByRole("link", {
          name: `Open experiment: ${label}`,
        }),
      ).toHaveAttribute("href", `/experiments/${ids[index]}`);
    }
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
    screen.getByRole("button", { name: /Remove Study 1/ }).focus();
    await userEvent.keyboard("{Enter}");
    expect(screen.getByText("Selected: 1 / 3")).toHaveFocus();
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
    expect(alert).toHaveTextContent(
      "The server response could not be confirmed",
    );
    expect(alert).not.toHaveTextContent("expand technical details");
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    await act(async () => i18n.changeLanguage("zh-CN"));
    expect(alert).toHaveTextContent("未能确认服务端响应");
    const heading = screen.getByRole("heading", { name: "实验比较" });
    const retry = screen.getByRole("button", { name: "重新加载" });
    retry.focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() => expect(attempts).toBe(2));
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.queryByRole("table")).not.toBeInTheDocument();
    expect(heading).toHaveFocus();
    await act(async () => resolve({ ...result, job_id: ids[2]! }));
    await screen.findByRole("heading", { name: "已保存的完整区间结果" });
    expect(heading).toHaveFocus();
    expect(screen.getAllByRole("table")).toHaveLength(2);
    expect(screen.getByRole("row", { name: /^累计收益/ })).toHaveTextContent(
      "+0.01%+0.01%",
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
      await screen.findByText(
        /These six conditions, including requested and actual result intervals, match/,
      ),
    ).toBeInTheDocument();
    for (const name of [
      "Saved full-period results",
      "Are these conditions the same?",
    ]) {
      const region = screen.getByRole("region", { name });
      expect(region).toHaveAttribute("tabindex", "0");
      expect(within(region).getByRole("table", { name })).toBeInTheDocument();
    }
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
    for (const name of ["已保存的完整区间结果", "这些条件是否一致？"]) {
      expect(
        within(screen.getByRole("region", { name })).getByRole("table", {
          name,
        }),
      ).toBeInTheDocument();
    }
    expect(screen.getByText("风险配置")).toBeInTheDocument();
    expect(screen.getByRole("row", { name: /^基准收益/ })).toHaveTextContent(
      "合成等权基准（演示）",
    );
  });
});
