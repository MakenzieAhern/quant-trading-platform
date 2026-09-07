export type SupportedLocale = "en-US" | "zh-CN";

export const LOCALE_STORAGE_KEY = "quant-platform-locale";

export function normalizeLocale(
  value: string | null | undefined,
): SupportedLocale | null {
  if (!value) return null;
  const normalized = value.replace("_", "-").toLowerCase();
  if (
    normalized === "zh" ||
    normalized.startsWith("zh-cn") ||
    normalized.startsWith("zh-hans")
  )
    return "zh-CN";
  if (normalized === "en" || normalized.startsWith("en-")) return "en-US";
  return null;
}

export function resolveInitialLocale(): SupportedLocale {
  const stored = normalizeLocale(
    window.localStorage.getItem(LOCALE_STORAGE_KEY),
  );
  return stored ?? normalizeLocale(window.navigator.language) ?? "en-US";
}

export function persistLocale(locale: SupportedLocale): void {
  window.localStorage.setItem(LOCALE_STORAGE_KEY, locale);
}
