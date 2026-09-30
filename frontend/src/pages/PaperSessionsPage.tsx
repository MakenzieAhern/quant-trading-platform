import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { paperApi } from "../api/paper";
import { EmptyState, ErrorPanel, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { PaperSafetyBanner } from "../components/PaperSafetyBanner";
import { StatusBadge } from "../components/StatusBadge";
import { useApiResource } from "../hooks/useApiResource";
import { formatUtc, shortId } from "../utils/format";

const LIMIT = 20;

export function PaperSessionsPage() {
  const { t } = useTranslation(["paper", "common", "research"]);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const heading = useRef<HTMLHeadingElement>(null);
  const focusedList = useRef(false);
  const sessions = useApiResource(
    (signal) => paperApi.list(LIMIT, offset, signal),
    [offset, revision],
    {
      intervalMs: 5000,
      while: (page) =>
        page.items.some(
          (item) =>
            item.status === "STARTING" ||
            item.status === "RUNNING" ||
            item.status === "PAUSING" ||
            item.status === "STOPPING",
        ),
    },
  );
  useEffect(() => {
    if (
      (sessions.data || sessions.error) &&
      focusedList.current &&
      document.activeElement === document.body
    ) {
      heading.current?.focus();
      focusedList.current = false;
    }
  }, [sessions.data, sessions.error]);
  return (
    <>
      <PaperSafetyBanner />
      <header className="pageHeader">
        <div>
          <p className="eyebrow">{t("paper:eyebrow")}</p>
          <h1>{t("paper:title")}</h1>
          <p>{t("paper:description")}</p>
        </div>
        <Link className="button buttonPrimary" href="/paper/new">
          {t("paper:create")}
        </Link>
      </header>
      <section className="panel" aria-labelledby="paper-sessions-title">
        <div className="panelHeader">
          <h2 ref={heading} id="paper-sessions-title" tabIndex={-1}>
            {t("paper:persisted")}
          </h2>
          <button
            className="button secondary"
            type="button"
            onClick={() => setRevision((value) => value + 1)}
          >
            {t("paper:refresh")}
          </button>
        </div>
        {sessions.loading && <LoadingPanel label={t("paper:loading")} />}
        {sessions.error && <ErrorPanel message={sessions.error} />}
        {sessions.data?.items.length === 0 && (
          <EmptyState>{t("paper:empty")}</EmptyState>
        )}
        {sessions.data && sessions.data.items.length > 0 && (
          <div
            className="tableScroll"
            role="region"
            tabIndex={0}
            aria-label={t("research:scrollTable")}
            onFocusCapture={() => (focusedList.current = true)}
            onBlurCapture={() => (focusedList.current = false)}
          >
            <table>
              <thead>
                <tr>
                  <th scope="col">{t("paper:sessionColumn")}</th>
                  <th scope="col">{t("common:strategy")}</th>
                  <th scope="col">{t("research:provider")}</th>
                  <th scope="col">{t("common:status")}</th>
                  <th scope="col">{t("common:created")}</th>
                </tr>
              </thead>
              <tbody>
                {sessions.data.items.map((item) => (
                  <tr key={item.session_id}>
                    <td>
                      <Link
                        className="monoLink"
                        href={`/paper/${item.session_id}`}
                        aria-label={`${t("paper:openSession")}: ${t(`paper:strategies.${item.strategy_type}`)} · ${t(`paper:providers.${item.provider_type}`)} · ${t(`common:statuses.${item.status}`)} · ${formatUtc(item.created_at)} · ${shortId(item.session_id)}`}
                      >
                        {t("paper:openSession")}
                      </Link>
                    </td>
                    <td>{t(`paper:strategies.${item.strategy_type}`)}</td>
                    <td>{t(`paper:providers.${item.provider_type}`)}</td>
                    <td>
                      <span
                        role="status"
                        aria-label={`${t(`paper:strategies.${item.strategy_type}`)}: ${t(`common:statuses.${item.status}`)} · ${formatUtc(item.created_at)} · ${shortId(item.session_id)}`}
                      >
                        <StatusBadge status={item.status} />
                      </span>
                    </td>
                    <td>{formatUtc(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          offset={offset}
          limit={LIMIT}
          total={sessions.data?.total ?? null}
          loading={sessions.loading}
          onChange={setOffset}
        />
      </section>
    </>
  );
}
