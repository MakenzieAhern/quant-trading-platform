import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { experimentApi } from "./experiments/api";
import {
  capabilities,
  configuration,
  job,
} from "./experiments/fixtures.test-data";
import { EXPERIMENT_DRAFT_KEY } from "./experiments/draft";
import {
  DataCenterPage,
  HelpPage,
  ModeGuide,
  ProductError,
  ProductStrategiesPage,
  WorkbenchPage,
} from "./ProductPages";

afterEach(() => vi.restoreAllMocks());

it.each(["en-US", "zh-CN"])(
  "offers read-only next steps for blocked historical data (%s)",
  async (locale) => {
    await act(() => i18n.changeLanguage(locale));
    const historical = {
      ...capabilities.datasets[0]!,
      dataset_id: "historical id & revision=1",
      mode: "historical_exploration" as const,
      current_source_integrity: "SOURCE_CONTRACT_INTEGRITY_FAILED" as const,
      execution_available: false,
    };
    const data = { ...capabilities, datasets: [historical] };
    const before = JSON.stringify(data);
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(data);
    render(<DataCenterPage />);
    const cached = await screen.findByRole("link", {
      name:
        locale === "en-US"
          ? "Browse this cached dataset"
          : "查看此数据集的缓存",
    });
    expect(cached).toHaveAttribute(
      "href",
      `/markets?dataset=${encodeURIComponent(historical.dataset_id)}`,
    );
    expect(
      screen.getByRole("link", {
        name: locale === "en-US" ? "View saved research" : "查看已保存研究",
      }),
    ).toHaveAttribute("href", "/experiments");
    expect(
      screen.getByRole("link", {
        name:
          locale === "en-US" ? "Why is execution blocked?" : "为什么不能运行？",
      }),
    ).toHaveAttribute("href", "/help#help-data-blocked");
    expect(JSON.stringify(data)).toBe(before);
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it("does not offer an unreadable dataset as cached or show recovery for an admitted one", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  vi.spyOn(experimentApi, "capabilities").mockResolvedValue({
    ...capabilities,
    datasets: [
      {
        ...capabilities.datasets[0]!,
        mode: "historical_exploration",
        available: false,
      },
    ],
  });
  const view = render(<DataCenterPage />);
  await screen.findByRole("link", { name: "Why is execution blocked?" });
  expect(
    screen.queryByRole("link", { name: "Browse this cached dataset" }),
  ).not.toBeInTheDocument();
  view.unmount();
  vi.mocked(experimentApi.capabilities).mockResolvedValue(capabilities);
  render(<DataCenterPage />);
  await screen.findByText("Cached data available");
  expect(
    screen.queryByRole("link", { name: "Why is execution blocked?" }),
  ).not.toBeInTheDocument();
});

it.each([
  ["QUEUED", "Queued", "排队中"],
  ["RUNNING", "Running", "运行中"],
  ["SUCCEEDED", "Complete", "已完成"],
  ["FAILED", "Failed", "失败"],
  ["CANCELLED", "Cancelled", "已取消"],
  ["INTERRUPTED", "Interrupted", "已中断"],
] as const)(
  "shows the server's %s status on recent research without changing its mode or record",
  async (status, english, chinese) => {
    await act(() => i18n.changeLanguage("en-US"));
    const item = { ...job, status };
    const before = JSON.stringify(item);
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    const list = vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [item],
      limit: 4,
      offset: 0,
      total: 1,
    });
    render(<WorkbenchPage />);
    const link = await screen.findByRole("link", {
      name: new RegExp(job.name),
    });
    expect(link).toHaveTextContent(english);
    expect(link).toHaveTextContent("Synthetic demonstration");
    expect(link).toHaveAttribute("href", `/experiments/${job.job_id}`);
    await act(() => i18n.changeLanguage("zh-CN"));
    expect(link).toHaveTextContent(chinese);
    expect(link).toHaveTextContent("合成演示");
    expect(JSON.stringify(item)).toBe(before);
    expect(list).toHaveBeenCalledOnce();
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it.each([
  [
    "en-US",
    "local-app",
    "Can I use the local app while GitHub CI/CD is unavailable?",
  ],
  ["zh-CN", "local-app", "GitHub CI/CD 暂停时，本地平台还能用吗？"],
  ["en-US", "data-blocked", "Why can I view data but not run a new study?"],
  ["zh-CN", "data-blocked", "为什么能查看数据，却不能运行新的研究？"],
  ["en-US", "backtest", "What is a backtest?"],
  ["en-US", "drawdown", "What is maximum drawdown?"],
  ["en-US", "win", "Is a high win rate the same as a good return?"],
  ["en-US", "benchmark", "Why compare with a benchmark?"],
  ["zh-CN", "backtest", "什么是回测？"],
  ["zh-CN", "drawdown", "什么是最大回撤？"],
  ["zh-CN", "win", "胜率高，收益就好吗？"],
  ["zh-CN", "benchmark", "为什么要看基准？"],
])(
  "opens and focuses the %s %s answer on a direct help link",
  async (locale, topic, question) => {
    await act(() => i18n.changeLanguage(locale));
    const originalUrl = location.href;
    window.history.replaceState({}, "", `/help#help-${topic}`);
    const view = render(<HelpPage />);
    try {
      const summary = screen.getByText(question);
      expect(summary.closest("details")).toHaveAttribute("open");
      await waitFor(() => expect(summary).toHaveFocus());
      expect(document.querySelectorAll("details[open]")).toHaveLength(1);
    } finally {
      view.unmount();
      window.history.replaceState({}, "", originalUrl);
      await act(() => i18n.changeLanguage("en-US"));
    }
  },
);

it.each(["en-US", "zh-CN"])(
  "explains local-app recovery without claiming fresh data or remote CI (%s)",
  async (locale) => {
    await act(() => i18n.changeLanguage(locale));
    render(<HelpPage />);
    const answer = document.getElementById("help-local-app");
    expect(answer).not.toBeNull();
    expect(answer).toHaveTextContent("http://localhost:5173/");
    expect(answer).toHaveTextContent("Docker Desktop");
    expect(answer).toHaveTextContent(
      locale === "en-US"
        ? "Service online does not mean prices are current"
        : "服务在线不代表行情最新",
    );
    expect(answer).toHaveTextContent(
      locale === "en-US"
        ? "Local checks do not replace remote CI or release approval"
        : "本地检查不能替代远端 CI 或发布审批",
    );
    expect(answer).toHaveTextContent(
      locale === "en-US"
        ? "do not reset Docker or delete data"
        : "不要重置 Docker 或删除数据",
    );
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it("handles help-topic traversal without closing other manually opened answers", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  const originalUrl = location.href;
  window.history.replaceState({}, "", "/help");
  const view = render(<HelpPage />);
  try {
    fireEvent.click(screen.getByText("What is a backtest?"));
    const drawdown = screen.getByText("What is maximum drawdown?");
    const scroll = vi.fn();
    drawdown.closest("details")!.scrollIntoView = scroll;
    window.history.pushState({}, "", "/help#help-drawdown");
    fireEvent(window, new PopStateEvent("popstate"));
    expect(drawdown.closest("details")).toHaveAttribute("open");
    await waitFor(() => expect(drawdown).toHaveFocus());
    expect(scroll).toHaveBeenCalledOnce();
    expect(
      screen.getByText("What is a backtest?").closest("details"),
    ).toHaveAttribute("open");
    window.history.pushState({}, "", "/help#help-benchmark");
    fireEvent(window, new HashChangeEvent("hashchange"));
    await waitFor(() =>
      expect(screen.getByText("Why compare with a benchmark?")).toHaveFocus(),
    );
    window.history.pushState({}, "", "/help#not-a-topic");
    fireEvent(window, new PopStateEvent("popstate"));
    expect(screen.getByText("Why compare with a benchmark?")).toHaveFocus();
  } finally {
    view.unmount();
    window.history.replaceState({}, "", originalUrl);
  }
});

it("preserves a manually collapsed linked answer and language-control focus", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  const originalUrl = location.href;
  window.history.replaceState({}, "", "/help#help-drawdown");
  const view = render(
    <>
      <button>Language</button>
      <HelpPage />
    </>,
  );
  try {
    await waitFor(() =>
      expect(screen.getByText("What is maximum drawdown?")).toHaveFocus(),
    );
    fireEvent.click(screen.getByText("What is maximum drawdown?"));
    const language = screen.getByRole("button", { name: "Language" });
    language.focus();
    await act(() => i18n.changeLanguage("zh-CN"));
    expect(
      screen.getByText("什么是最大回撤？").closest("details"),
    ).not.toHaveAttribute("open");
    expect(language).toHaveFocus();
  } finally {
    view.unmount();
    window.history.replaceState({}, "", originalUrl);
    await act(() => i18n.changeLanguage("en-US"));
  }
});

it.each(["en-US", "zh-CN"])(
  "distinguishes readable historical data from economic validation (%s)",
  async (locale) => {
    await act(() => i18n.changeLanguage(locale));
    const historical = {
      ...capabilities.datasets[0]!,
      dataset_id: "cn-a-research-20100101-20251231-v1",
      mode: "historical_exploration" as const,
      current_dataset_quality: "KNOWN_ECONOMIC_COVERAGE_GAP" as const,
      current_source_integrity: "SOURCE_CONTRACT_INTEGRITY_FAILED" as const,
      execution_available: false,
      execution_reason_code: "SOURCE_CONTRACT_INTEGRITY_FAILED",
    };
    const data = {
      ...capabilities,
      datasets: [historical, capabilities.datasets[0]!],
    };
    const before = JSON.stringify(data);
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockResolvedValue(data);
    render(<DataCenterPage />);
    const notice = await screen.findByRole("note");
    expect(notice).toHaveTextContent(
      locale === "en-US"
        ? "Economic completeness is not validated"
        : "经济完整性尚未验证",
    );
    expect(historical.available).toBe(true);
    expect(
      screen.getByText(
        locale === "en-US"
          ? "View only · new execution blocked"
          : "仅可查看 · 禁止新执行",
      ),
    ).toBeInTheDocument();
    expect(notice).toHaveTextContent(
      locale === "en-US"
        ? "source references failed verification"
        : "来源引用未通过验证",
    );
    expect(screen.getAllByRole("note")).toHaveLength(1);
    expect(JSON.stringify(data)).toBe(before);
    expect(read).toHaveBeenCalledOnce();
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it.each(["en-US", "zh-CN"])(
  "explains inspection-only admission without requiring an old-version finding (%s)",
  async (locale) => {
    await act(() => i18n.changeLanguage(locale));
    const inspection = {
      ...capabilities.datasets[0]!,
      dataset_id: "inspection-only-candidate-v2",
      mode: "historical_exploration" as const,
      execution_available: false,
      execution_reason_code: "DATASET_EXECUTION_NOT_ACCEPTED",
    };
    const data = {
      ...capabilities,
      datasets: [inspection, capabilities.datasets[0]!],
    };
    const before = JSON.stringify(data);
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockResolvedValue(data);
    render(<DataCenterPage />);
    expect(
      await screen.findByText(
        locale === "en-US"
          ? /registered for inspection only/
          : /此数据版本仅注册用于查看/,
      ),
    ).toBeInTheDocument();
    expect(
      screen.getByText(
        locale === "en-US" ? "Cached data available" : "可查看缓存",
      ),
    ).toBeInTheDocument();
    expect(
      screen.queryByText(/source references failed|来源引用未通过/),
    ).toBeNull();
    expect(read).toHaveBeenCalledOnce();
    expect(JSON.stringify(data)).toBe(before);
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it.each([
  ["en-US", "New-market forward simulation", "Not available yet."],
  ["zh-CN", "新行情前向模拟", "尚未开放。"],
])(
  "states current forward availability in the shared mode guide (%s)",
  async (locale, title, unavailable) => {
    await act(() => i18n.changeLanguage(locale));
    render(<ModeGuide />);
    expect(
      screen.getByRole("heading", { name: title }).closest("section"),
    ).toHaveTextContent(unavailable);
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it("describes guided research without claiming it starts a simulated account", async () => {
  vi.spyOn(experimentApi, "capabilities").mockRejectedValue(
    new Error("offline"),
  );
  vi.spyOn(experimentApi, "list").mockRejectedValue(new Error("offline"));
  await act(() => i18n.changeLanguage("en-US"));
  render(<WorkbenchPage />);
  expect(
    screen.getByText(/Choose a strategy, set your assumptions/),
  ).toHaveTextContent("in a guided backtest");
  expect(
    screen.queryByText(/using a simulated account/),
  ).not.toBeInTheDocument();
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(screen.getByText(/选一个策略，设定你的假设/)).toHaveTextContent(
    "通过模拟研究",
  );
  await act(() => i18n.changeLanguage("en-US"));
});

it("separates starting a new backtest from continuing the saved draft", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
  vi.spyOn(experimentApi, "list").mockResolvedValue({
    items: [],
    limit: 4,
    offset: 0,
    total: 0,
  });
  window.localStorage.setItem(
    EXPERIMENT_DRAFT_KEY,
    JSON.stringify({
      version: 1,
      form: configuration,
      step: 2,
      idempotencyKey: "saved-intent",
      savedAt: "2026-09-30T00:00:00Z",
    }),
  );
  try {
    render(<WorkbenchPage />);
    expect(
      screen.getByRole("link", { name: "Continue your draft" }),
    ).toHaveAttribute("href", "/research/new");
    expect(
      screen.getByRole("link", { name: "Start guided backtest" }),
    ).toHaveAttribute("href", "/research/new?new=1");
  } finally {
    window.localStorage.removeItem(EXPERIMENT_DRAFT_KEY);
  }
});

it("keeps a section-level Retry near its persistent heading", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  render(
    <main>
      <h1>Research</h1>
      <section>
        <h2>Equity chart</h2>
        <ProductError error={new Error("offline")} retry={() => {}} />
      </section>
    </main>,
  );
  screen.getByRole("button", { name: "Try again" }).focus();
  await userEvent.keyboard("{Enter}");
  expect(screen.getByRole("heading", { name: "Equity chart" })).toHaveFocus();
});

it("closes the optional guide when browser storage rejects writes", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  // jsdom has no native dialog methods; browser behavior is checked separately.
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
  vi.spyOn(experimentApi, "capabilities").mockRejectedValue(
    new Error("offline"),
  );
  vi.spyOn(experimentApi, "list").mockRejectedValue(new Error("offline"));
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Denied", "SecurityError");
  });
  render(<WorkbenchPage />);
  fireEvent.click(
    screen.getByRole("button", { name: "How this workspace works" }),
  );
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Got it, continue exploring" }),
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

it("keeps an open help answer expanded when its translated label changes", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  render(<HelpPage />);
  fireEvent.click(screen.getByText("What is a backtest?"));
  expect(
    screen.getByText("What is a backtest?").closest("details"),
  ).toHaveAttribute("open");
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(screen.getByText("什么是回测？").closest("details")).toHaveAttribute(
    "open",
  );
  await act(() => i18n.changeLanguage("en-US"));
});

it.each([
  ["en-US", new Error("invalid contract")],
  ["en-US", new ApiError(502, "invalid JSON")],
  ["en-US", new ApiError(503, "unavailable")],
  ["zh-CN", new Error("invalid contract")],
  ["zh-CN", new ApiError(502, "invalid JSON")],
  ["zh-CN", new ApiError(503, "unavailable")],
])(
  "does not promise saved-record availability on an unverified read (%s, %s)",
  async (locale, error) => {
    await act(() => i18n.changeLanguage(locale));
    const retry = vi.fn();
    render(<ProductError error={error} retry={retry} />);
    const alert = screen.getByRole("alert");
    expect(alert).toHaveTextContent(
      locale === "en-US"
        ? "cannot verify that saved records are available"
        : "尚不能核验已保存记录是否可用",
    );
    expect(alert).toHaveTextContent(locale === "en-US" ? "Help" : "帮助");
    expect(alert).not.toHaveTextContent(
      locale === "en-US" ? "Your saved work is preserved" : "不会因此丢失",
    );
    fireEvent.click(
      screen.getByRole("button", {
        name: locale === "en-US" ? "Try again" : "重新尝试",
      }),
    );
    expect(retry).toHaveBeenCalledOnce();
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it.each(["en-US", "zh-CN"])(
  "preserves the exact local draft without claiming server records survived a failed read (%s)",
  async (locale) => {
    await act(() => i18n.changeLanguage(locale));
    const original = localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    const draft = JSON.stringify({
      version: 1,
      form: { ...configuration, initial_cash: "123456.789000000000001" },
      step: 2,
      idempotencyKey: "read-failure-intent",
      savedAt: "2026-10-07T00:00:00Z",
    });
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockRejectedValue(new ApiError(503, "unavailable"));
    const list = vi
      .spyOn(experimentApi, "list")
      .mockRejectedValue(new ApiError(503, "unavailable"));
    const create = vi.spyOn(experimentApi, "create");
    localStorage.setItem(EXPERIMENT_DRAFT_KEY, draft);
    const view = render(<WorkbenchPage />);
    try {
      const alerts = await screen.findAllByRole("alert");
      expect(alerts).toHaveLength(2);
      for (const alert of alerts)
        expect(alert).toHaveTextContent(
          locale === "en-US"
            ? "cannot verify that saved records are available"
            : "尚不能核验已保存记录是否可用",
        );
      expect(
        screen.getByRole("link", {
          name: locale === "en-US" ? "Continue your draft" : "继续上次的草稿",
        }),
      ).toHaveAttribute("href", "/research/new");
      expect(localStorage.getItem(EXPERIMENT_DRAFT_KEY)).toBe(draft);
      expect(read).toHaveBeenCalledOnce();
      expect(list).toHaveBeenCalledOnce();
      expect(create).not.toHaveBeenCalled();
    } finally {
      view.unmount();
      if (original === null) localStorage.removeItem(EXPERIMENT_DRAFT_KEY);
      else localStorage.setItem(EXPERIMENT_DRAFT_KEY, original);
      await act(() => i18n.changeLanguage("en-US"));
    }
  },
);

it("distinguishes permission, timeout and offline failures while keeping retry", async () => {
  await i18n.changeLanguage("en-US");
  const retry = vi.fn();
  const view = render(
    <ProductError error={new ApiError(403, "denied")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("Access was denied");
  view.rerender(
    <ProductError error={new ApiError(408, "timeout")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("request timed out");
  view.rerender(
    <ProductError error={new TypeError("offline")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("service is unavailable");
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(retry).toHaveBeenCalledOnce();
});

it("does not promise historical or demo availability while data-center service is offline", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  vi.spyOn(experimentApi, "capabilities").mockRejectedValue(
    new TypeError("offline"),
  );
  render(<DataCenterPage />);
  await screen.findByRole("button", { name: "Try again" });
  expect(screen.getByText(/Raw candidate updates/)).not.toHaveTextContent(
    "remain available",
  );
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(screen.getByText(/原始候选更新/)).not.toHaveTextContent("仍可使用");
  await act(() => i18n.changeLanguage("en-US"));
});

it("returns an unknown strategy deep link to the registered catalog", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
  render(<ProductStrategiesPage strategyId="does-not-exist" />);
  const missing = await screen.findByRole("alert");
  expect(missing).toHaveTextContent("This strategy is not registered");
  expect(screen.getByRole("heading", { level: 1 })).not.toHaveTextContent(
    "Momentum & lower volatility",
  );
  expect(screen.getByRole("link", { name: "Strategies" })).toHaveAttribute(
    "href",
    "/strategies",
  );
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(missing).toHaveTextContent("该策略未注册");
  expect(screen.getByRole("link", { name: "策略" })).toHaveAttribute(
    "href",
    "/strategies",
  );
  await act(() => i18n.changeLanguage("en-US"));
});

it.each(["success", "error"])(
  "keeps keyboard focus in the Workbench after a capabilities Retry returns %s",
  async (outcome) => {
    await act(() => i18n.changeLanguage("en-US"));
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockRejectedValueOnce(new ApiError(503, "unavailable"));
    if (outcome === "success") read.mockResolvedValue(capabilities);
    else read.mockRejectedValue(new ApiError(403, "denied"));
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [],
      limit: 4,
      offset: 0,
      total: 0,
    });
    render(<WorkbenchPage />);
    const retry = await screen.findByRole("button", { name: "Try again" });
    retry.focus();
    expect(retry).toHaveFocus();
    fireEvent.click(retry);
    await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
    if (outcome === "success")
      await waitFor(() =>
        expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
      );
    else await screen.findByText(/Access was denied/);
    expect(
      screen.getByRole("heading", { name: "Your research data" }),
    ).toHaveFocus();
  },
);

it.each([
  ["Strategies", <ProductStrategiesPage />],
  ["Data Center", <DataCenterPage />],
])(
  "keeps keyboard focus after a %s data Retry replaces its error",
  async (_name, page) => {
    await act(() => i18n.changeLanguage("en-US"));
    let completeRetry: ((value: typeof capabilities) => void) | undefined;
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockRejectedValueOnce(new ApiError(503, "unavailable"))
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            completeRetry = resolve;
          }),
      );
    render(<main>{page}</main>);
    const retry = await screen.findByRole("button", { name: "Try again" });
    retry.focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveFocus();
    await act(async () => completeRetry?.(capabilities));
    expect(heading).toHaveFocus();
  },
);
