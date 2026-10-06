import { act, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { i18n } from "../../i18n";
import { PAPER_ID } from "../../test/paperFixtures";
import { parseSimulationPlan } from "./api";
import { ExperimentPlan } from "./ExperimentPlan";
import { plan } from "./fixtures.test-data";
import type { PaperAccountPlan } from "./types";

describe("saved plan account date", () => {
  it.each([true, false])(
    "reveals a directly linked plan after it mounts, without rescrolling updates (account %s)",
    (account) => {
      const scroll = vi.fn();
      const previous = HTMLElement.prototype.scrollIntoView;
      HTMLElement.prototype.scrollIntoView = scroll;
      try {
        window.history.replaceState({}, "", "/paper/test#simulation-plan");
        const view = render(<div>Loading</div>);
        expect(scroll).not.toHaveBeenCalled();
        view.rerender(<ExperimentPlan plan={plan} account={account} />);
        expect(scroll).toHaveBeenCalledExactlyOnceWith({ block: "start" });
        expect(scroll.mock.contexts[0]).toBe(
          document.getElementById("simulation-plan"),
        );
        view.rerender(
          <ExperimentPlan
            plan={plan}
            account={account}
            quality="KNOWN_ECONOMIC_COVERAGE_GAP"
          />,
        );
        expect(scroll).toHaveBeenCalledOnce();
        expect(screen.getByText("90,123.000000000000000001")).toBeVisible();
      } finally {
        if (previous) HTMLElement.prototype.scrollIntoView = previous;
        else Reflect.deleteProperty(HTMLElement.prototype, "scrollIntoView");
      }
    },
  );

  it.each(["", "#other"])(
    "does not scroll an unrequested plan fragment (%s)",
    (fragment) => {
      const scroll = vi.fn();
      const previous = HTMLElement.prototype.scrollIntoView;
      HTMLElement.prototype.scrollIntoView = scroll;
      try {
        window.history.replaceState({}, "", `/experiments/test${fragment}`);
        const view = render(<ExperimentPlan plan={plan} />);
        expect(scroll).not.toHaveBeenCalled();
        view.rerender(
          <ExperimentPlan plan={plan} quality="KNOWN_ECONOMIC_COVERAGE_GAP" />,
        );
        expect(scroll).not.toHaveBeenCalled();
      } finally {
        if (previous) HTMLElement.prototype.scrollIntoView = previous;
        else Reflect.deleteProperty(HTMLElement.prototype, "scrollIntoView");
      }
    },
  );

  it.each(["en-US", "zh-CN"])(
    "shows later data-quality advice without changing a saved plan (%s)",
    async (locale) => {
      await act(async () => i18n.changeLanguage(locale));
      const before = JSON.stringify(plan);
      const view = render(
        <ExperimentPlan plan={plan} quality="KNOWN_ECONOMIC_COVERAGE_GAP" />,
      );
      expect(screen.getByRole("note")).toHaveTextContent(
        locale === "en-US"
          ? "Economic completeness is not validated"
          : "经济完整性尚未验证",
      );
      expect(screen.getByText("90,123.000000000000000001")).toBeVisible();
      view.rerender(
        <ExperimentPlan
          plan={plan}
          quality="HISTORICAL_DATASET_QUALITY_UNKNOWN"
        />,
      );
      expect(screen.getByRole("note")).toHaveTextContent(
        locale === "en-US"
          ? "Economic completeness is unknown"
          : "经济完整性未知",
      );
      expect(JSON.stringify(plan)).toBe(before);
      await act(async () => i18n.changeLanguage("en-US"));
    },
  );
  it.each([undefined, null, "2031-04-13"])(
    "warns when the account date is %s without rewriting the record",
    async (snapshotDate) => {
      const saved = { ...plan, account_snapshot_trading_date: snapshotDate };
      const original = JSON.stringify(saved);
      render(<ExperimentPlan plan={saved} />);
      expect(screen.getByRole("alert")).toHaveTextContent(
        "unverified historical record",
      );
      expect(screen.getByText("90,123.000000000000000001")).toBeVisible();
      expect(screen.getByText("9.123456789123456789")).toBeVisible();
      try {
        await act(async () => i18n.changeLanguage("zh-CN"));
        expect(screen.getByRole("alert")).toHaveTextContent(
          "未经日期核验的历史记录",
        );
        expect(screen.getByText("90,123.000000000000000001")).toBeVisible();
        expect(JSON.stringify(saved)).toBe(original);
      } finally {
        await act(async () => i18n.changeLanguage("en-US"));
      }
    },
  );

  it("warns for an original V1 account plan even if its status says preview", () => {
    const saved: PaperAccountPlan = {
      ...plan,
      mode: "historical_exploration",
      account_mode: "HISTORICAL_PAPER_REPLAY",
      submitted_to_account: true,
      paper_session_id: PAPER_ID,
      plan_version: "PAPER_ACCOUNT_PLAN_V1",
    };
    render(<ExperimentPlan plan={saved} account />);
    expect(screen.getByRole("alert")).toHaveTextContent(
      "unverified historical record",
    );
    expect(screen.getByText("Recorded account cash (CNY)")).toBeVisible();
    expect(
      screen.queryByText("Cash at plan time (CNY)"),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /execute|submit/i }),
    ).not.toBeInTheDocument();
  });

  it("uses the plan's own recorded date, not another latest account date", () => {
    render(
      <ExperimentPlan
        plan={{
          ...plan,
          account_snapshot_trading_date: plan.as_of_trading_date,
        }}
      />,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(
      screen.getByText("Account snapshot trading date (Asia/Shanghai)"),
    ).toBeVisible();
    expect(screen.getAllByText(plan.as_of_trading_date)).toHaveLength(2);
  });

  it("does not imply a usable account when the backend has none", () => {
    render(
      <ExperimentPlan
        plan={{
          ...plan,
          status: "ACCOUNT_SNAPSHOT_UNAVAILABLE",
          account: null,
          candidates: [],
          estimated_cash_required: null,
        }}
      />,
    );
    expect(screen.queryByRole("alert")).not.toBeInTheDocument();
    expect(screen.getByRole("status")).toHaveTextContent(
      "No account snapshot is available",
    );
    expect(
      screen.queryByText("90,123.000000000000000001"),
    ).not.toBeInTheDocument();
  });

  it.each([42, [plan.as_of_trading_date]])(
    "rejects an invalid date field %s",
    (value) => {
      expect(() =>
        parseSimulationPlan({ ...plan, account_snapshot_trading_date: value }),
      ).toThrow();
    },
  );
});
