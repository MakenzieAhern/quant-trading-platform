import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Pagination } from "./Pagination";

describe("Pagination", () => {
  it.each([
    [0, 0, "0–0 of 0", true],
    [1, 0, "1–1 of 1", true],
    [20, 0, "1–20 of 20", true],
    [21, 0, "1–20 of 21", false],
    [21, 20, "21–21 of 21", true],
  ] as const)(
    "renders the %i-item boundary",
    (total, offset, label, nextDisabled) => {
      render(
        <Pagination
          offset={offset}
          limit={20}
          total={total}
          onChange={() => undefined}
        />,
      );
      expect(screen.getByText(label)).toBeInTheDocument();
      expect(screen.getByRole("button", { name: "Next" })).toHaveProperty(
        "disabled",
        nextDisabled,
      );
    },
  );

  it("moves by exactly one page in each direction", async () => {
    const onChange = vi.fn();
    render(
      <Pagination offset={20} limit={20} total={41} onChange={onChange} />,
    );
    await userEvent.click(screen.getByRole("button", { name: "Previous" }));
    await userEvent.click(screen.getByRole("button", { name: "Next" }));
    expect(onChange.mock.calls).toEqual([[0], [40]]);
  });
});
