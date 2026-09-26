import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { experimentApi } from "./experiments/api";
import {
  HelpPage,
  ModeGuide,
  ProductError,
  WorkbenchPage,
} from "./ProductPages";

afterEach(() => vi.restoreAllMocks());

it.each([
  ["en-US", "New-market forward simulation", "Not available yet."],
  ["zh-CN", "新行情前向模拟", "尚未开放。"],
])(
  "states current forward availability in the shared mode guide (%s)",
  async (locale, title, unavailable) => {
    await act(() => i18n.changeLanguage(locale));
    render(<ModeGuide />);
    expect(
      screen.getByRole("heading", { name: title }).closest("section"),
    ).toHaveTextContent(unavailable);
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it("closes the optional guide when browser storage rejects writes", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  // jsdom has no native dialog methods; browser behavior is checked separately.
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.setAttribute("open", "");
      },
    },
    close: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.removeAttribute("open");
      },
    },
  });
  vi.spyOn(experimentApi, "capabilities").mockRejectedValue(
    new Error("offline"),
  );
  vi.spyOn(experimentApi, "list").mockRejectedValue(new Error("offline"));
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Denied", "SecurityError");
  });
  render(<WorkbenchPage />);
  fireEvent.click(
    screen.getByRole("button", { name: "How this workspace works" }),
  );
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Got it, continue exploring" }),
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

it("keeps an open help answer expanded when its translated label changes", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  render(<HelpPage />);
  fireEvent.click(screen.getByText("What is a backtest?"));
  expect(
    screen.getByText("What is a backtest?").closest("details"),
  ).toHaveAttribute("open");
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(screen.getByText("什么是回测？").closest("details")).toHaveAttribute(
    "open",
  );
  await act(() => i18n.changeLanguage("en-US"));
});

it("distinguishes permission, timeout and offline failures while keeping retry", async () => {
  await i18n.changeLanguage("en-US");
  const retry = vi.fn();
  const view = render(
    <ProductError error={new ApiError(403, "denied")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("Access was denied");
  view.rerender(
    <ProductError error={new ApiError(408, "timeout")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("request timed out");
  view.rerender(
    <ProductError error={new TypeError("offline")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("service is unavailable");
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(retry).toHaveBeenCalledOnce();
});
