import { render } from "@testing-library/react";
import { expect, test, vi } from "vitest";
import { BenchmarkChart } from "./BenchmarkChart";
import { DrawdownChart } from "./DrawdownChart";

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
