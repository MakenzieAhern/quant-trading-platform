import { useTranslation } from "react-i18next";

import { persistLocale, type SupportedLocale } from "../i18n/locale";

export function LanguageSelector() {
  const { i18n, t } = useTranslation("accessibility");
  const change = (locale: SupportedLocale) => {
    persistLocale(locale);
    void i18n.changeLanguage(locale);
    document.documentElement.lang = locale;
  };
  return (
    <div className="languageSelector" role="group" aria-label={t("language")}>
      <button
        type="button"
        onClick={() => change("zh-CN")}
        aria-pressed={i18n.language === "zh-CN"}
      >
        中文
      </button>
      <span aria-hidden="true">|</span>
      <button
        type="button"
        onClick={() => change("en-US")}
        aria-pressed={i18n.language === "en-US"}
      >
        EN
      </button>
    </div>
  );
}
