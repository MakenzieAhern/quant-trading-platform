import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, test, vi } from "vitest";

import { researchApi } from "../../api/research";
import type { ResearchPoint, ResearchRun } from "../../types/research";
import { ResearchRunPage } from "./ResearchRunPage";

vi.mock("../../api/research", () => ({
  researchApi: {
    run: vi.fn(),
    metrics: vi.fn(),
    points: vi.fn(),
    monthlyReturns: vi.fn(),
    rollingMetrics: vi.fn(),
    holdings: vi.fn(),
    rebalances: vi.fn(),
    trades: vi.fn(),
  },
}));
vi.mock("react-i18next", () => ({
  useTranslation: () => ({
    t: (key: string, values?: { start?: string; end?: string }) =>
      values?.start ? `${key}:${values.start}–${values.end}` : key,
  }),
}));

const empty = { items: [], limit: 200, offset: 0, total: 0 };
const savedRun = {
  run_id: "saved",
  strategy_id: "saved-strategy",
  period_kind: "VALIDATION",
  dataset_id: "saved-dataset",
  provider: "audited",
  provider_version: "1",
  dataset_checksum: "abc",
  market_rule_version: "1",
  benchmark_id: "CSI300",
  created_at: "2024-01-01T00:00:00Z",
  git_commit: "abc",
  strategy_config_hash: "abc",
  diagnostics: {},
} as ResearchRun;

function pointPage(offset: number, count: number) {
  const items: ResearchPoint[] = Array.from({ length: count }, (_, index) => ({
    sequence: offset + index,
    trading_date: offset === 0 ? "2024-01-02" : "2024-04-01",
    value: "100.000000000000000001",
  }));
  return { items, limit: 200, offset, total: 201 };
}

beforeEach(() => {
  vi.clearAllMocks();
  vi.mocked(researchApi.run).mockResolvedValue(savedRun);
  vi.mocked(researchApi.metrics).mockResolvedValue(empty);
  vi.mocked(researchApi.monthlyReturns).mockResolvedValue(empty);
  vi.mocked(researchApi.rollingMetrics).mockResolvedValue(empty);
  vi.mocked(researchApi.holdings).mockResolvedValue(empty);
  vi.mocked(researchApi.rebalances).mockResolvedValue(empty);
  vi.mocked(researchApi.trades).mockResolvedValue(empty);
  vi.mocked(researchApi.points).mockImplementation(async (_id, _kind, offset) =>
    pointPage(offset ?? 0, offset === 0 ? 200 : 1),
  );
});

test("one curve page advances all three series without changing stored metrics", async () => {
  render(<ResearchRunPage runId="saved" />);
  await screen.findByText("research:displayedDateRange:2024-01-02–2024-01-02");
  const equitySection = (
    await screen.findByRole("heading", {
      name: "research:equity / research:benchmarkCurve",
    })
  ).closest("section")!;
  await userEvent.click(
    within(equitySection).getByRole("button", { name: "next" }),
  );
  await screen.findByText("research:displayedDateRange:2024-04-01–2024-04-01");
  expect(researchApi.points).toHaveBeenCalledTimes(6);
  for (const kind of ["equity", "benchmark", "drawdown"])
    expect(researchApi.points).toHaveBeenCalledWith(
      "saved",
      kind,
      200,
      expect.any(AbortSignal),
    );
  expect(researchApi.metrics).toHaveBeenCalledTimes(1);
});

test("failed curve request is not reported as empty data", async () => {
  vi.mocked(researchApi.points).mockImplementation(
    async (_id, kind, offset) => {
      if (kind === "benchmark") throw new TypeError("offline");
      return pointPage(offset ?? 0, 200);
    },
  );
  render(<ResearchRunPage runId="saved" />);
  const equitySection = (
    await screen.findByRole("heading", {
      name: "research:equity / research:benchmarkCurve",
    })
  ).closest("section")!;
  await within(equitySection).findByRole("alert");
  expect(within(equitySection).queryByText("common:noData")).toBeNull();
  expect(
    within(equitySection).getByText("loadErrors.offline"),
  ).toBeInTheDocument();
});
