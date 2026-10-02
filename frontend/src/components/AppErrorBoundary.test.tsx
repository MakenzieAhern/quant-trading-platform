import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { i18n } from "../i18n";
import { AppErrorBoundary } from "./AppErrorBoundary";

function BrokenPage(): never {
  throw new Error("render failed");
}

describe("application render failure", () => {
  afterEach(() => vi.restoreAllMocks());

  it.each([
    ["en-US", "This page stopped displaying", "Check saved tasks"],
    ["zh-CN", "本页显示已中断", "核对已保存任务"],
  ])("offers safe recovery in %s", async (locale, heading, tasks) => {
    await i18n.changeLanguage(locale);
    window.history.replaceState({}, "", "/experiments/example");
    vi.spyOn(console, "error").mockImplementation(() => {});
    render(
      <AppErrorBoundary>
        <BrokenPage />
      </AppErrorBoundary>,
    );

    expect(screen.getByRole("alert")).toContainElement(
      screen.getByRole("heading", { name: heading }),
    );
    expect(screen.getByRole("link", { name: tasks })).toHaveAttribute(
      "target",
      "_blank",
    );
    expect(screen.getByRole("link", { name: tasks })).toHaveAttribute(
      "href",
      "/tasks",
    );
    expect(screen.getByRole("link", { name: /accounts|账户/ })).toHaveAttribute(
      "href",
      "/paper",
    );
    expect(
      screen.getByRole("link", { name: /Reload page|重新加载本页/ }),
    ).toHaveAttribute("href", window.location.href);
  });
});
