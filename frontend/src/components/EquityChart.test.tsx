import { render, screen } from "@testing-library/react";
import { describe, expect, it } from "vitest";

import { EquityChart } from "./EquityChart";

const timestamp = "2024-11-03T05:30:00Z";

describe("EquityChart", () => {
  it("renders an empty series safely", () => {
    const { container } = render(<EquityChart points={[]} />);
    expect(container).toBeEmptyDOMElement();
  });

  it("preserves exact text for a single point and repeated timestamp", () => {
    const equity = "999999999999999999.123456789012345678";
    render(
      <EquityChart
        points={[
          { timestamp, equity, cash: equity, market_value: "0" },
          { timestamp, equity, cash: equity, market_value: "0" },
        ]}
      />,
    );
    expect(screen.getAllByText(equity)).toHaveLength(2);
    expect(
      document.querySelector("polyline")?.getAttribute("points"),
    ).not.toMatch(/NaN|Infinity/);
  });

  it("degrades geometry safely while retaining extreme authoritative values", () => {
    const extreme = `1${"0".repeat(400)}`;
    render(
      <EquityChart
        points={[
          { timestamp, equity: extreme, cash: extreme, market_value: "0" },
        ]}
      />,
    );
    expect(screen.getByText(/Chart geometry unavailable/)).toBeInTheDocument();
    expect(screen.getByText(extreme)).toBeInTheDocument();
    expect(document.querySelector("polyline")).not.toBeInTheDocument();
  });
});
