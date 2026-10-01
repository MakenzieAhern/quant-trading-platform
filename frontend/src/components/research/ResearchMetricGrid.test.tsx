import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { i18n } from "../../i18n";
import type { ResearchMetric } from "../../types/research";
import { ResearchMetricGrid } from "./ResearchMetricGrid";

const metrics: ResearchMetric[] = [
  {
    period_kind: "OUT_OF_SAMPLE",
    metric_name: "average_gross_exposure",
    value: "0.2238308393216157076013704295",
  },
  {
    period_kind: "OUT_OF_SAMPLE",
    metric_name: "average_net_exposure",
    value: "0.2",
  },
  {
    period_kind: "OUT_OF_SAMPLE",
    metric_name: "average_holding_period",
    value: "82.5",
  },
  {
    period_kind: "OUT_OF_SAMPLE",
    metric_name: "closed_trade_sessions",
    value: "22",
  },
  { period_kind: "PILOT_SMOKE", metric_name: "number_of_trades", value: "88" },
];

afterEach(async () => {
  await i18n.changeLanguage("en-US");
});

test("saved research metrics explain names, units and splits in both languages", async () => {
  await i18n.changeLanguage("zh-CN");
  const view = render(<ResearchMetricGrid metrics={metrics} />);
  for (const label of [
    "平均总敞口",
    "平均净敞口",
    "平均持有期（交易日）",
    "卖出交易日记录数",
    "交易记录数",
  ])
    expect(screen.getByText(label)).toBeInTheDocument();
  expect(screen.getByText("22.38%")).toHaveAttribute(
    "title",
    "0.2238308393216157076013704295",
  );
  fireEvent.click(screen.getByRole("checkbox", { name: "显示完整精度" }));
  expect(
    screen.getByText("22.38308393216157076013704295%"),
  ).toBeInTheDocument();
  expect(screen.getAllByText("正式样本外")).toHaveLength(4);
  expect(screen.getByText("工程冒烟测试（非研究证据）")).toBeInTheDocument();

  await i18n.changeLanguage("en-US");
  view.rerender(<ResearchMetricGrid metrics={metrics} />);
  expect(
    screen.getByRole("checkbox", { name: "Show full precision" }),
  ).toBeChecked();
  for (const label of [
    "Average gross exposure",
    "Average net exposure",
    "Average holding period (trading sessions)",
    "Sell-session records",
    "Trade records",
  ])
    expect(screen.getByText(label)).toBeInTheDocument();
  expect(screen.getAllByText("Official out-of-sample")).toHaveLength(4);
  expect(
    screen.getByText("Engineering smoke test (not research evidence)"),
  ).toBeInTheDocument();
});
