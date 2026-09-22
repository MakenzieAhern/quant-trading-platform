import i18n from "i18next";
import { initReactI18next } from "react-i18next";

import { enUS } from "./resources/en-US";
import { zhCN } from "./resources/zh-CN";
import { resolveInitialLocale } from "./locale";

void i18n.use(initReactI18next).init({
  resources: {
    "en-US": enUS,
    "zh-CN": zhCN,
  },
  lng: resolveInitialLocale(),
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
