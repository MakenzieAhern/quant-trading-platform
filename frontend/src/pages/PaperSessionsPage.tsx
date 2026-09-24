import { useState } from "react";
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
  const sessions = useApiResource(
    (signal) => paperApi.list(LIMIT, offset, signal),
    [offset],
  );
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
          <h2 id="paper-sessions-title">{t("paper:persisted")}</h2>
        </div>
        {sessions.loading && <LoadingPanel label={t("paper:loading")} />}
        {sessions.error && <ErrorPanel message={sessions.error} />}
        {sessions.data?.items.length === 0 && (
          <EmptyState>{t("paper:empty")}</EmptyState>
        )}
        {sessions.data && sessions.data.items.length > 0 && (
          <div className="tableScroll">
            <table>
              <thead>
                <tr>
                  <th scope="col">{t("common:run")}</th>
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
                        title={item.session_id}
                      >
                        {shortId(item.session_id)}
                      </Link>
                    </td>
                    <td>{t(`paper:strategies.${item.strategy_type}`)}</td>
                    <td>{t(`paper:providers.${item.provider_type}`)}</td>
                    <td>
                      <StatusBadge status={item.status} />
                    </td>
                    <td>{formatUtc(item.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        {sessions.data && (
          <Pagination
            offset={offset}
            limit={LIMIT}
            total={sessions.data.total}
            onChange={setOffset}
          />
        )}
      </section>
    </>
  );
}
