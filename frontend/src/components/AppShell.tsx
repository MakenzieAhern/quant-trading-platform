import { useEffect, useState, type ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { getHealth } from "../api/health";
import type { HealthResponse } from "../types/health";
import { Link } from "./Link";
import { LanguageSelector } from "./LanguageSelector";

export function AppShell({ children }: { children: ReactNode }) {
  const { t } = useTranslation(["navigation", "common"]);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void getHealth(controller.signal)
      .then(setHealth)
      .catch((reason: unknown) => {
        if (reason instanceof Error && reason.name !== "AbortError")
          setError(true);
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="appShell">
      <a className="skipLink" href="#main-content">
        {t("navigation:skip")}
      </a>
      <header className="topbar">
        <Link
          className="brand"
          href="/backtests"
          aria-label={t("navigation:brand")}
        >
          <span className="brandMark">Q</span>
          <span>QUANT / PLATFORM</span>
        </Link>
        <nav aria-label={t("navigation:primary")}>
          <Link href="/backtests">{t("navigation:backtests")}</Link>
          <Link href="/paper">{t("navigation:paper")}</Link>
          <Link href="/research/a-share">{t("navigation:research")}</Link>
          <Link className="primaryLink" href="/backtests/new">
            {t("navigation:newBacktest")}
          </Link>
        </nav>
        <div className="topbarTools">
          <LanguageSelector />
          <span className={`status ${error ? "statusError" : ""}`}>
            <i aria-hidden="true" />{" "}
            {error
              ? t("navigation:apiUnavailable")
              : health
                ? `${health.environment} · ${health.broker_mode}`
                : t("common:connecting")}
          </span>
        </div>
      </header>
      <main id="main-content" tabIndex={-1} className="workspace">
        {children}
      </main>
      <footer>
        <strong>{t("navigation:footerMode")}</strong>
        <span>{t("navigation:footerSafety")}</span>
      </footer>
    </div>
  );
}
