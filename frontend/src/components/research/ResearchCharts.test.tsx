import { render, screen, within } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { BenchmarkChart } from "./BenchmarkChart";
import { DrawdownChart } from "./DrawdownChart";
import { MonthlyReturnHeatmap } from "./MonthlyReturnHeatmap";

vi.mock("react-i18next", () => ({
  useTranslation: () => ({ t: (key: string) => key }),
}));

test("benchmark and strategy use a common equity scale", () => {
  const point = (value: string, sequence: number) => ({
    value,
    sequence,
    trading_date: "2024-01-02",
  });
  const { container } = render(
    <BenchmarkChart
      strategy={[point("100", 0), point("100", 1)]}
      benchmark={[point("100", 0), point("90", 1)]}
    />,
  );
  const lines = container.querySelectorAll("polyline");
  expect(lines[0].getAttribute("points")?.split(" ")[0]).toEqual(
    lines[1].getAttribute("points")?.split(" ")[0],
  );
});

test("zero drawdown renders finite minimum-height bars", () => {
  const { container } = render(
    <DrawdownChart
      points={[{ sequence: 0, trading_date: "2024-01-02", value: "0" }]}
    />,
  );
  expect(container.querySelector("span")?.style.height).toBe("2%");
});

test("monthly returns remain readable as individual values", () => {
  render(
    <MonthlyReturnHeatmap
      values={[
        { month: "2024-01-01", value: "0.01" },
        { month: "2024-02-01", value: null },
      ]}
    />,
  );
  const region = screen.getByRole("region", { name: "monthlyHeatmap" });
  expect(within(region).getByText("2024-01")).toBeInTheDocument();
  expect(within(region).getByText("1%")).toBeInTheDocument();
  expect(within(region).getByTitle("2024-01-01: 1%")).toBeInTheDocument();
  expect(within(region).getByText("2024-02")).toBeInTheDocument();
});
