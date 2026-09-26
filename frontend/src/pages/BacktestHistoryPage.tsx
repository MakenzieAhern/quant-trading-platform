import { backtestsApi } from "../api/backtests";
import { ErrorPanel, EmptyState, LoadingPanel } from "../components/AsyncPanel";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { StatusBadge } from "../components/StatusBadge";
import { useApiResource } from "../hooks/useApiResource";
import { formatUtc, shortId } from "../utils/format";
import { useState } from "react";
import { useTranslation } from "react-i18next";

const LIMIT = 20;

export function BacktestHistoryPage() {
  const { t } = useTranslation(["backtests", "research"]);
  const [offset, setOffset] = useState(0);
  const runs = useApiResource(
    (signal) => backtestsApi.list(LIMIT, offset, signal),
    [offset],
  );

  return (
    <>
      <header className="pageHeader">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("title")}</h1>
          <p>{t("description")}</p>
        </div>
        <Link className="button buttonPrimary" href="/backtests/new">
          {t("create")}
        </Link>
      </header>
      <section className="panel" aria-labelledby="history-title">
        <div className="panelHeader">
          <div>
            <p className="kicker">{t("history")}</p>
            <h2 id="history-title">{t("persisted")}</h2>
          </div>
        </div>
        {runs.loading && <LoadingPanel label={t("loading")} />}
        {runs.error && <ErrorPanel message={runs.error} />}
        {runs.data && runs.data.items.length === 0 && (
          <EmptyState>{t("empty")}</EmptyState>
        )}
        {runs.data && runs.data.items.length > 0 && (
          <div
            className="tableScroll"
            role="region"
            tabIndex={0}
            aria-label={t("research:scrollTable")}
          >
            <table>
              <thead>
                <tr>
                  <th scope="col">{t("columns.run")}</th>
                  <th scope="col">{t("columns.strategy")}</th>
                  <th scope="col">{t("columns.dataset")}</th>
                  <th scope="col">{t("columns.status")}</th>
                  <th scope="col">{t("columns.created")}</th>
                  <th scope="col">{t("columns.started")}</th>
                  <th scope="col">{t("columns.completed")}</th>
                </tr>
              </thead>
              <tbody>
                {runs.data.items.map((run) => (
                  <tr key={run.run_id}>
                    <td>
                      <Link
                        className="monoLink"
                        href={`/backtests/${run.run_id}`}
                        title={run.run_id}
                      >
                        {shortId(run.run_id)}
                      </Link>
                    </td>
                    <td>{run.strategy_type.replaceAll("_", " ")}</td>
                    <td>{run.dataset_id}</td>
                    <td>
                      <StatusBadge status={run.status} />
                    </td>
                    <td>{formatUtc(run.created_at)}</td>
                    <td>{formatUtc(run.started_at)}</td>
                    <td>{formatUtc(run.completed_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
        <Pagination
          offset={offset}
          limit={LIMIT}
          total={runs.data?.total ?? null}
          loading={runs.loading}
          onChange={setOffset}
        />
      </section>
    </>
  );
}
