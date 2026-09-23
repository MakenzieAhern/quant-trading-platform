import { fireEvent, render, screen } from "@testing-library/react";
import { expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { ProductError } from "./ProductPages";

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
