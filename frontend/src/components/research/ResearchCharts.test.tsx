import { render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
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

test("chart data is lazy, paged and preserves independent dates and exact strings", async () => {
  const strategy = Array.from({ length: 101 }, (_, sequence) => ({
    sequence,
    trading_date: sequence === 100 ? "2024-04-01" : "2024-01-02",
    value: sequence === 100 ? "100.123456789012345678" : "1",
  }));
  render(
    <BenchmarkChart
      strategy={strategy}
      benchmark={[
        {
          sequence: 0,
          trading_date: "2024-04-02",
          value: "99.000000000000000001",
        },
      ]}
    />,
  );
  expect(
    screen.queryByRole("table", { name: "accessibility:benchmarkChart" }),
  ).toBeNull();
  await userEvent.click(screen.getByText("chartData"));
  const table = screen.getByRole("table", {
    name: "accessibility:benchmarkChart",
  });
  expect(within(table).getAllByRole("row")).toHaveLength(101);
  await userEvent.click(screen.getByRole("button", { name: "next" }));
  expect(within(table).getAllByRole("row")).toHaveLength(3);
  expect(within(table).getByText("100.123456789012345678")).toBeInTheDocument();
  expect(within(table).getByText("2024-04-01")).toBeInTheDocument();
  expect(within(table).getByText("99.000000000000000001")).toBeInTheDocument();
  expect(within(table).getByText("2024-04-02")).toBeInTheDocument();
});

test("drawdown exact point remains keyboard-accessible below visual bars", async () => {
  render(
    <DrawdownChart
      points={[
        { sequence: 0, trading_date: "2024-01-02", value: "-0.123456789" },
      ]}
    />,
  );
  await userEvent.click(screen.getByText("chartData"));
  const table = screen.getByRole("table", {
    name: "accessibility:drawdownChart",
  });
  expect(within(table).getByText("-0.123456789")).toBeInTheDocument();
  expect(within(table).getByText("2024-01-02")).toBeInTheDocument();
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
