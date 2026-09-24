import { useTranslation } from "react-i18next";

import { researchApi } from "../../api/research";
import { ErrorPanel, LoadingPanel } from "../../components/AsyncPanel";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import { formatUtc } from "../../utils/format";

export function ResearchDatasetPage({ datasetId }: { datasetId: string }) {
  const { t } = useTranslation(["research", "common", "validation"]);
  const dataset = useApiResource(
    (signal) => researchApi.dataset(datasetId, signal),
    [datasetId],
  );
  if (dataset.loading)
    return <LoadingPanel label={t("research:datasetDetail")} />;
  if (dataset.error) return <ErrorPanel message={dataset.error} />;
  if (!dataset.data) return null;
  return (
    <>
      <Link className="backLink" href="/research/a-share">
        {t("research:back")}
      </Link>
      <header className="detailHeader">
        <div>
          <p className="eyebrow">{t("research:datasetDetail")}</p>
          <h1>{dataset.data.dataset_id}</h1>
        </div>
      </header>
      <section className="runFacts" aria-label={t("research:lineage")}>
        <div>
          <span>{t("research:provider")}</span>
          <strong>
            {dataset.data.provider} / {dataset.data.provider_version}
          </strong>
        </div>
        <div>
          <span>{t("research:coverage")}</span>
          <strong>
            {dataset.data.coverage_start} — {dataset.data.coverage_end}
          </strong>
        </div>
        <div>
          <span>{t("research:securityCount")}</span>
          <strong>{dataset.data.security_count}</strong>
        </div>
        <div>
          <span>{t("research:ruleVersion")}</span>
          <strong>{dataset.data.rule_version}</strong>
        </div>
        <div>
          <span>{t("research:adjustmentMethod")}</span>
          <strong>{dataset.data.adjustment_method}</strong>
        </div>
        <div>
          <span>{t("research:retrieved")}</span>
          <strong>{formatUtc(dataset.data.retrieval_timestamp)}</strong>
        </div>
        <div>
          <span>{t("research:checksum")}</span>
          <strong className="mono">{dataset.data.canonical_sha256}</strong>
        </div>
        <div>
          <span>{t("common:status")}</span>
          <strong>
            {t(`research:readiness.${dataset.data.readiness_status}`, {
              defaultValue: t("research:readiness.unknown"),
            })}{" "}
            ·{" "}
            {dataset.data.frozen
              ? t("validation:frozen")
              : t("validation:notFrozen")}
          </strong>
        </div>
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:manifest")}</h2>
        </div>
        <pre className="manifestJson">
          {JSON.stringify(dataset.data.manifest, null, 2)}
        </pre>
      </section>
    </>
  );
}
