import { act, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { LanguageSelector } from "../components/LanguageSelector";
import { HelpPage } from "../product/ProductPages";
import { i18n } from ".";
import { LOCALE_STORAGE_KEY, normalizeLocale, persistLocale } from "./locale";
import { enUS } from "./resources/en-US";
import { zhCN } from "./resources/zh-CN";

function leafKeys(value: object, prefix = ""): string[] {
  return Object.entries(value).flatMap(([key, child]) => {
    const path = prefix ? `${prefix}.${key}` : key;
    return typeof child === "object" && child !== null
      ? leafKeys(child, path)
      : [path];
  });
}

describe("application internationalization", () => {
  afterEach(async () => {
    localStorage.clear();
    await i18n.changeLanguage("en-US");
  });

  it("keeps complete resource parity between English and Chinese", () => {
    expect(leafKeys(enUS)).toEqual(leafKeys(zhCN));
  });

  it("normalizes supported browser languages and rejects unknown values", () => {
    expect(normalizeLocale("zh-Hans-CN")).toBe("zh-CN");
    expect(normalizeLocale("en-AU")).toBe("en-US");
    expect(normalizeLocale("fr-FR")).toBeNull();
  });

  it("persists only the validated locale identifier", () => {
    persistLocale("zh-CN");
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("zh-CN");
  });

  it("switches the one component tree between both languages", async () => {
    render(<LanguageSelector />);
    fireEvent.click(screen.getByRole("button", { name: "中文" }));
    expect(localStorage.getItem(LOCALE_STORAGE_KEY)).toBe("zh-CN");
    expect(document.documentElement.lang).toBe("zh-CN");
    expect(i18n.language).toBe("zh-CN");
  });

  it("updates an open tab when another tab changes the saved language", async () => {
    await i18n.changeLanguage("en-US");
    render(
      <>
        <LanguageSelector />
        <HelpPage />
      </>,
    );
    expect(screen.getByText("What is a backtest?")).toBeInTheDocument();

    localStorage.setItem(LOCALE_STORAGE_KEY, "zh-CN");
    await act(async () => {
      window.dispatchEvent(
        new StorageEvent("storage", {
          key: LOCALE_STORAGE_KEY,
          newValue: "zh-CN",
          storageArea: localStorage,
        }),
      );
    });

    expect(screen.getByText("什么是回测？")).toBeInTheDocument();
    expect(document.documentElement.lang).toBe("zh-CN");
    expect(screen.getByRole("button", { name: "中文" })).toHaveAttribute(
      "aria-pressed",
      "true",
    );
  });
});
