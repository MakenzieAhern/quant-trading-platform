import { act, fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { HelpPage, ProductError } from "./ProductPages";

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
