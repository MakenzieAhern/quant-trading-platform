import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { experimentApi } from "./api";
import { comparisonUrl } from "./comparison";
import { ExperimentComparePage } from "./ExperimentComparePage";
import { ExperimentDetailPage } from "./ExperimentDetailPage";
import { job, result } from "./fixtures.test-data";

describe("result direction across detail and comparison", () => {
  it.each(["en-US", "zh-CN"])(
    "preserves signed exact percentages and unknown values in %s",
    async (locale) => {
      await act(async () => i18n.changeLanguage(locale));
      const ids = [job.job_id, "aa000000-0000-4000-8000-000000000002"];
      const saved = {
        ...result,
        metrics: {
          ...result.metrics,
          cumulative_return: "0.010961967992773949350054841",
          benchmark_return: "0.01",
          excess_return: "0.0000000000000000000001",
        },
      };
      const original = JSON.stringify(saved);
      vi.spyOn(experimentApi, "get").mockImplementation(async (id) => ({
        ...job,
        job_id: id,
        status: "SUCCEEDED",
        result_available: true,
      }));
      vi.spyOn(experimentApi, "result").mockImplementation(async (id) => ({
        ...saved,
        job_id: id,
        ...(id === ids[1]
          ? {
              metrics: {
                ...saved.metrics,
                cumulative_return: "0",
                benchmark_return: null,
                excess_return: "-0.01",
              },
            }
          : {}),
      }));
      vi.spyOn(experimentApi, "equity").mockResolvedValue({
        items: [],
        total: 0,
        limit: 100,
        offset: 0,
      });
      window.history.replaceState({}, "", comparisonUrl(ids));
      const comparison = render(<ExperimentComparePage />);
      const isZh = locale.startsWith("zh");
      const table = await screen.findByRole("table", {
        name: isZh ? "已保存的完整区间结果" : "Saved full-period results",
      });
      const cells = (name: string) =>
        within(within(table).getByRole("rowheader", { name }).closest("tr")!)
          .getAllByRole("cell")
          .map((cell) => cell.textContent);
      expect(cells(isZh ? "累计收益" : "Total return")).toEqual([
        "+1.10%",
        "0%",
      ]);
      expect(cells(isZh ? "相对基准收益" : "Return above benchmark")).toEqual([
        "+0.00%",
        "-1%",
      ]);
      expect(cells(isZh ? "基准收益" : "Benchmark return")[1]).toMatch(
        isZh ? /^暂无/ : /^N\/A/,
      );
      await userEvent.click(
        screen.getByRole("checkbox", {
          name: isZh ? "显示完整精度" : "Show full precision",
        }),
      );
      expect(cells(isZh ? "累计收益" : "Total return")[0]).toBe(
        "+1.0961967992773949350054841%",
      );
      expect(cells(isZh ? "相对基准收益" : "Return above benchmark")[0]).toBe(
        "+0.00000000000000000001%",
      );
      comparison.unmount();
      render(<ExperimentDetailPage jobId={ids[0]!} />);
      expect(await screen.findByText("+1.10%")).toBeVisible();
      await userEvent.click(
        screen.getByRole("checkbox", {
          name: isZh ? "显示完整精度" : "Show full precision",
        }),
      );
      expect(screen.getByText("+1.0961967992773949350054841%")).toBeVisible();
      expect(JSON.stringify(saved)).toBe(original);
    },
  );
});
