import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";

import { Pagination } from "./Pagination";
import { i18n } from "../i18n";
import { useState } from "react";

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

  it("never autofocuses or steals focus when pending data settles or locale changes", async () => {
    const onChange = vi.fn();
    const view = render(
      <>
        <input aria-label="Other task" />
        <Pagination offset={0} limit={20} total={41} onChange={onChange} />
      </>,
    );
    const pager = screen.getByRole("group", { name: "Pagination" });
    expect(pager).not.toHaveFocus();
    await userEvent.click(within(pager).getByRole("button", { name: "Next" }));
    expect(pager).toHaveFocus();
    view.rerender(
      <>
        <input aria-label="Other task" />
        <Pagination
          offset={20}
          limit={20}
          total={null}
          loading
          onChange={onChange}
        />
      </>,
    );
    expect(pager).toHaveAttribute("aria-busy", "true");
    expect(within(pager).getByRole("button", { name: "Next" })).toBeDisabled();
    expect(screen.queryByText("1–20 of 41")).not.toBeInTheDocument();
    screen.getByLabelText("Other task").focus();
    view.rerender(
      <>
        <input aria-label="Other task" />
        <Pagination offset={20} limit={20} total={41} onChange={onChange} />
      </>,
    );
    await act(async () => {
      await i18n.changeLanguage("zh-CN");
    });
    expect(screen.getByLabelText("Other task")).toHaveFocus();
    expect(pager).toHaveAccessibleName("分页");
    await act(async () => {
      await i18n.changeLanguage("en-US");
    });
    view.unmount();
    expect(pager).not.toBeInTheDocument();
    expect(onChange).toHaveBeenCalledExactlyOnceWith(20);
  });

  it("keeps unknown totals disabled without preventing an independent pager", async () => {
    const first = vi.fn();
    const second = vi.fn();
    render(
      <>
        <Pagination offset={20} limit={20} total={null} onChange={first} />
        <Pagination offset={20} limit={20} total={21} onChange={second} />
      </>,
    );
    const [unavailable, available] = screen.getAllByRole("group", {
      name: "Pagination",
    });
    for (const button of within(unavailable).getAllByRole("button")) {
      expect(button).toBeDisabled();
      await userEvent.click(button);
    }
    await userEvent.click(
      within(available).getByRole("button", { name: "Previous" }),
    );
    expect(available).toHaveFocus();
    expect(first).not.toHaveBeenCalled();
    expect(second).toHaveBeenCalledExactlyOnceWith(0);
  });

  it("preserves a stateful client pager at both boundaries and tabs to the available direction", async () => {
    function ClientPage() {
      const [offset, setOffset] = useState(0);
      return (
        <Pagination
          offset={offset}
          limit={20}
          total={21}
          onChange={setOffset}
        />
      );
    }
    render(<ClientPage />);
    const pager = screen.getByRole("group", { name: "Pagination" });
    await userEvent.click(within(pager).getByRole("button", { name: "Next" }));
    expect(pager).toHaveFocus();
    expect(pager).toHaveTextContent("21–21 of 21");
    expect(within(pager).getByRole("button", { name: "Next" })).toBeDisabled();
    await userEvent.tab();
    expect(
      within(pager).getByRole("button", { name: "Previous" }),
    ).toHaveFocus();
    await userEvent.keyboard("{Enter}");
    expect(pager).toHaveFocus();
    expect(
      within(pager).getByRole("button", { name: "Previous" }),
    ).toBeDisabled();
    await userEvent.tab();
    expect(within(pager).getByRole("button", { name: "Next" })).toHaveFocus();
  });
});
