import { useTranslation } from "react-i18next";

import { researchApi } from "../../api/research";
import { ErrorPanel, LoadingPanel } from "../../components/AsyncPanel";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";

export function ResearchStrategiesPage() {
  const { t, i18n } = useTranslation("research");
  const strategies = useApiResource(
    (signal) => researchApi.strategies(signal),
    [],
  );
  return (
    <>
      <header className="pageHeader compactHeader">
        <div>
          <p className="eyebrow">{t("eyebrow")}</p>
          <h1>{t("strategies")}</h1>
        </div>
      </header>
      {strategies.loading && <LoadingPanel label={t("strategies")} />}
      {strategies.error && <ErrorPanel message={strategies.error} />}
      <div className="strategyCards">
        {strategies.data?.map((strategy) => (
          <article className="panel strategyCard" key={strategy.strategy_id}>
            <p className="kicker">{strategy.strategy_id}</p>
            <h2>
              {i18n.language === "zh-CN" ? strategy.name_zh : strategy.name_en}
            </h2>
            <p>{t("noGuarantee")}</p>
            <Link
              className="button"
              href={`/research/a-share/strategies/${strategy.strategy_id}`}
            >
              {t("openStrategy")}
            </Link>
          </article>
        ))}
      </div>
    </>
  );
}
