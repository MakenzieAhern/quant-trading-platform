import { useTranslation } from "react-i18next";

import { researchApi } from "../../api/research";
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
} from "../../components/AsyncPanel";
import { Link } from "../../components/Link";
import { SplitBadge } from "../../components/research/SplitBadge";
import { useApiResource } from "../../hooks/useApiResource";
import { formatUtc, shortId } from "../../utils/format";

export function ResearchHomePage() {
  const { t } = useTranslation(["research", "common", "validation"]);
  const datasets = useApiResource((signal) => researchApi.datasets(signal), []);
  const runs = useApiResource((signal) => researchApi.runs(signal), []);
  return (
    <>
      <header className="pageHeader researchHero">
        <div>
          <p className="eyebrow">{t("research:eyebrow")}</p>
          <h1>{t("research:landingTitle")}</h1>
          <p>{t("research:landingDescription")}</p>
        </div>
        <Link
          className="button buttonPrimary"
          href="/research/a-share/strategies"
        >
          {t("research:openStrategy")}
        </Link>
      </header>
      <div className="oosGuard" role="note">
        {t("research:evidenceSummary")}
      </div>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:datasets")}</h2>
        </div>
        {datasets.loading && <LoadingPanel label={t("research:datasets")} />}
        {datasets.error && <ErrorPanel message={datasets.error} />}
        {datasets.data?.items.length === 0 && (
          <EmptyState>{t("research:noDatasets")}</EmptyState>
        )}
        {datasets.data && datasets.data.items.length > 0 && (
          <div className="tableScroll">
            <table>
              <thead>
                <tr>
                  <th>{t("common:dataset")}</th>
                  <th>{t("research:provider")}</th>
                  <th>{t("research:coverage")}</th>
                  <th>{t("research:checksum")}</th>
                  <th>{t("common:status")}</th>
                </tr>
              </thead>
              <tbody>
                {datasets.data.items.map((dataset) => (
                  <tr key={dataset.dataset_id}>
                    <td>
                      <Link
                        className="monoLink"
                        href={`/research/a-share/datasets/${encodeURIComponent(dataset.dataset_id)}`}
                      >
                        {dataset.dataset_id}
                      </Link>
                    </td>
                    <td>
                      {dataset.provider} / {dataset.provider_version}
                    </td>
                    <td>
                      {dataset.coverage_start} — {dataset.coverage_end}
                    </td>
                    <td className="mono" title={dataset.canonical_sha256}>
                      {shortId(dataset.canonical_sha256)}
                    </td>
                    <td>
                      {dataset.readiness_status} ·{" "}
                      {dataset.frozen
                        ? t("validation:frozen")
                        : t("validation:notFrozen")}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:runs")}</h2>
        </div>
        {runs.loading && <LoadingPanel label={t("research:runs")} />}
        {runs.error && <ErrorPanel message={runs.error} />}
        {runs.data?.items.length === 0 && (
          <EmptyState>{t("research:noRuns")}</EmptyState>
        )}
        {runs.data && runs.data.items.length > 0 && (
          <div className="tableScroll">
            <table>
              <thead>
                <tr>
                  <th>{t("common:run")}</th>
                  <th>{t("common:strategy")}</th>
                  <th>{t("research:period")}</th>
                  <th>{t("common:status")}</th>
                  <th>{t("common:created")}</th>
                </tr>
              </thead>
              <tbody>
                {runs.data.items.map((run) => (
                  <tr key={run.run_id}>
                    <td>
                      <Link
                        className="monoLink"
                        href={`/research/a-share/runs/${run.run_id}`}
                      >
                        {shortId(run.run_id)}
                      </Link>
                    </td>
                    <td>{run.strategy_id}</td>
                    <td>
                      <SplitBadge period={run.period_kind} />
                    </td>
                    <td>{run.status}</td>
                    <td>{formatUtc(run.created_at)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </>
  );
}
