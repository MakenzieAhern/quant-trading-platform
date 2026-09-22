import { useMemo, useSyncExternalStore } from "react";
export const PREFERENCES_KEY = "quant.product.preferences.v1";
export interface Preferences {
  theme: "system" | "light" | "dark";
  motion: "system" | "off";
  marketColors: "red-up" | "green-up";
  priceView: "raw" | "adjusted";
}
const defaults: Preferences = {
  theme: "system",
  motion: "system",
  marketColors: "red-up",
  priceView: "raw",
};
function snapshot() {
  try {
    return localStorage.getItem(PREFERENCES_KEY);
  } catch {
    return null;
  }
}
function subscribe(listener: () => void) {
  window.addEventListener("storage", listener);
  window.addEventListener("product-preferences", listener);
  return () => {
    window.removeEventListener("storage", listener);
    window.removeEventListener("product-preferences", listener);
  };
}
export function parsePreferences(raw: string | null): Preferences {
  try {
    const value: unknown = JSON.parse(raw ?? "null");
    if (!value || typeof value !== "object") return defaults;
    const saved = value as Record<string, unknown>;
    return {
      theme:
        saved.theme === "light" || saved.theme === "dark"
          ? saved.theme
          : "system",
      motion: saved.motion === "off" ? "off" : "system",
      marketColors: saved.marketColors === "green-up" ? "green-up" : "red-up",
      priceView: saved.priceView === "adjusted" ? "adjusted" : "raw",
    };
  } catch {
    return defaults;
  }
}
export function usePreferences() {
  const raw = useSyncExternalStore(subscribe, snapshot, () => null);
  const preferences = useMemo(() => parsePreferences(raw), [raw]);
  const update = (change: Partial<Preferences>) => {
    localStorage.setItem(
      PREFERENCES_KEY,
      JSON.stringify({ ...preferences, ...change }),
    );
    window.dispatchEvent(new Event("product-preferences"));
  };
  return { preferences, update };
}
