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
  const { container } = render(
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
    container.querySelector("circle.benchmarkLine")?.getAttribute("cx"),
  ).toBe("900");
  expect(
    container
      .querySelector("polyline.strategyLine")
      ?.getAttribute("points")
      ?.split(" ")
      .at(-1)
      ?.startsWith("450,"),
  ).toBe(true);
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

test("equity table keeps same-date strategy and benchmark rows together across pages", async () => {
  const dates = Array.from({ length: 200 }, (_, index) =>
    new Date(Date.UTC(2023, 0, index + 1)).toISOString().slice(0, 10),
  );
  render(
    <BenchmarkChart
      strategy={dates.map((trading_date, sequence) => ({
        sequence,
        trading_date,
        value: `S${sequence}`,
      }))}
      benchmark={dates.map((trading_date, sequence) => ({
        sequence,
        trading_date,
        value: `B${sequence}`,
      }))}
    />,
  );
  await userEvent.click(screen.getByText("chartData"));
  const table = screen.getByRole("table", {
    name: "accessibility:benchmarkChart",
  });
  expect(within(table).getAllByText("research:strategySeries")).toHaveLength(
    50,
  );
  expect(within(table).getAllByText("research:benchmark")).toHaveLength(50);
  expect(within(table).getByText("S49")).toBeInTheDocument();
  expect(within(table).getByText("B49")).toBeInTheDocument();
  expect(within(table).queryByText("S50")).toBeNull();
  await userEvent.click(screen.getByRole("button", { name: "next" }));
  expect(within(table).getByText("S50")).toBeInTheDocument();
  expect(within(table).getByText("B50")).toBeInTheDocument();
});

test("a missing rolling value stays visible and breaks only its own chart line", async () => {
  const dates = ["2024-01-02", "2024-01-03", "2024-01-04"];
  const { container } = render(
    <BenchmarkChart
      strategy={dates.map((trading_date, sequence) => ({
        sequence,
        trading_date,
        value: sequence === 1 ? null : `${sequence + 1}`,
      }))}
      benchmark={dates.map((trading_date, sequence) => ({
        sequence,
        trading_date,
        value: `-${sequence + 1}`,
      }))}
    />,
  );
  expect(container.querySelectorAll("polyline.strategyLine")).toHaveLength(0);
  expect(container.querySelectorAll("circle.strategyLine")).toHaveLength(2);
  expect(container.querySelectorAll("polyline.benchmarkLine")).toHaveLength(1);
  await userEvent.click(screen.getByText("chartData"));
  const table = screen.getByRole("table", {
    name: "accessibility:benchmarkChart",
  });
  const unavailable = within(table).getByText("common:unavailable");
  expect(
    within(unavailable.closest("tr")!).getByText("2024-01-03"),
  ).toBeInTheDocument();
  expect(within(table).getByText("-2")).toBeInTheDocument();
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

test("exact chart values work with hover, point clicks and keyboard date selection without inventing missing values", async () => {
  const strategy = [
    {
      sequence: 0,
      trading_date: "2024-01-02",
      value: "100.123456789012345678",
    },
    { sequence: 1, trading_date: "2024-01-03", value: null },
    { sequence: 2, trading_date: "2024-01-04", value: "102.00" },
  ];
  const benchmark = [
    { sequence: 0, trading_date: "2024-01-02", value: "99.000000000000000001" },
    { sequence: 1, trading_date: "2024-01-03", value: "0" },
    { sequence: 2, trading_date: "2024-01-05", value: "103.00" },
  ];
  const view = render(
    <BenchmarkChart strategy={strategy} benchmark={benchmark} />,
  );
  const picker = screen.getByRole("combobox", {
    name: "accessibility:benchmarkChart — research:columns.date",
  });
  const readout = screen.getByRole("status");
  expect(picker).toHaveValue("2024-01-05");
  expect(readout).toHaveTextContent(
    "research:strategySeries: common:unavailable",
  );
  expect(readout).toHaveTextContent("research:benchmark: 103.00");
  expect(
    view.container.querySelectorAll("circle.researchChartPoint"),
  ).toHaveLength(5);
  const exactTitle = screen.getByText(
    "research:strategySeries — 2024-01-02: 100.123456789012345678",
    { selector: "title" },
  );
  await userEvent.hover(exactTitle.parentElement!);
  expect(picker).toHaveValue("2024-01-02");
  expect(readout).toHaveTextContent("100.123456789012345678");
  expect(readout).toHaveTextContent("99.000000000000000001");
  await userEvent.selectOptions(picker, "2024-01-03");
  expect(readout).toHaveTextContent(
    "research:strategySeries: common:unavailable",
  );
  expect(readout).toHaveTextContent("research:benchmark: 0");
  await userEvent.click(exactTitle.parentElement!);
  expect(picker).toHaveValue("2024-01-02");
  view.rerender(
    <BenchmarkChart
      strategy={strategy}
      benchmark={benchmark}
      showBenchmark={false}
    />,
  );
  expect(picker).toHaveValue("2024-01-02");
  expect(readout).not.toHaveTextContent("research:benchmark");
  expect(
    view.container.querySelectorAll("circle.researchChartPoint"),
  ).toHaveLength(2);
  expect(view.container.querySelectorAll("svg title")).toHaveLength(2);
  await userEvent.click(screen.getByText("chartData"));
  const table = screen.getByRole("table", {
    name: "accessibility:benchmarkChart",
  });
  expect(within(table).getByText("99.000000000000000001")).toBeInTheDocument();
  expect(within(table).getByText("common:unavailable")).toBeInTheDocument();
  view.rerender(
    <BenchmarkChart
      strategy={[{ sequence: 3, trading_date: "2024-01-08", value: "104.00" }]}
      benchmark={[]}
    />,
  );
  expect(picker).toHaveValue("2024-01-08");
  expect(readout).not.toHaveTextContent("2024-01-02");
  expect(readout).toHaveTextContent("104.00");
});
