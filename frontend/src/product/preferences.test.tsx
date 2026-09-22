import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";
import { SettingsPage } from "./ProductPages";
import { PREFERENCES_KEY } from "./preferences";
import { i18n } from "../i18n";
import { LOCALE_STORAGE_KEY, resolveInitialLocale } from "../i18n/locale";
import { writePresentationSetting } from "../utils/presentationStorage";

afterEach(async () => {
  vi.restoreAllMocks();
  act(() => {
    writePresentationSetting(PREFERENCES_KEY, "{}");
    writePresentationSetting(LOCALE_STORAGE_KEY, "en-US");
  });
  await act(() => i18n.changeLanguage("en-US"));
});

describe("safe presentation preferences", () => {
  it("applies settings and locale for the tab without claiming persistence after quota failure", async () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
      throw new DOMException("Full", "QuotaExceededError");
    });
    render(<SettingsPage />);
    fireEvent.change(screen.getByLabelText("Theme"), {
      target: { value: "dark" },
    });
    expect(screen.getByLabelText("Theme")).toHaveValue("dark");
    expect(screen.getByRole("status")).toHaveTextContent("only to this tab");
    fireEvent.click(screen.getByRole("button", { name: "中文" }));
    expect(await screen.findByLabelText("主题")).toHaveValue("dark");
    expect(document.documentElement.lang).toBe("zh-CN");
    expect(screen.getByRole("status")).toHaveTextContent("当前标签页");
    vi.restoreAllMocks();
    fireEvent.click(screen.getByRole("button", { name: "EN" }));
    fireEvent.change(screen.getByLabelText("Theme"), {
      target: { value: "light" },
    });
    expect(screen.getByRole("status")).toHaveTextContent("Changes are saved");
    expect(JSON.parse(localStorage.getItem(PREFERENCES_KEY)!)).toMatchObject({
      theme: "light",
    });
  });

  it("does not crash initial locale resolution when storage access is denied", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => {
      throw new DOMException("Denied", "SecurityError");
    });
    expect(() => resolveInitialLocale()).not.toThrow();
  });

  it("declares the actual language after restoring a saved locale", async () => {
    writePresentationSetting(LOCALE_STORAGE_KEY, "zh-CN");
    await i18n.changeLanguage(resolveInitialLocale());
    expect(i18n.language).toBe("zh-CN");
    expect(document.documentElement.lang).toBe("zh-CN");
  });
});
