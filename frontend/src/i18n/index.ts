import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { enUS } from "./resources/en-US";
import { zhCN } from "./resources/zh-CN";
import { LOCALE_STORAGE_KEY, resolveInitialLocale } from "./locale";

const initialLocale = resolveInitialLocale();
document.documentElement.lang = initialLocale;
i18n.on("languageChanged", (locale) => {
  document.documentElement.lang = locale;
});
window.addEventListener("storage", (event) => {
  if (event.key !== LOCALE_STORAGE_KEY && event.key !== null) return;
  const locale = resolveInitialLocale();
  if (locale !== i18n.language) void i18n.changeLanguage(locale);
});

void i18n.use(initReactI18next).init({
  resources: {
    "en-US": enUS,
    "zh-CN": zhCN,
  },
  lng: initialLocale,
  fallbackLng: "en-US",
  supportedLngs: ["en-US", "zh-CN"],
  ns: [
    "common",
    "navigation",
    "backtests",
    "paper",
    "research",
    "metrics",
    "validation",
    "errors",
    "accessibility",
  ],
  defaultNS: "common",
  interpolation: { escapeValue: true },
  returnNull: false,
});

export { i18n };
