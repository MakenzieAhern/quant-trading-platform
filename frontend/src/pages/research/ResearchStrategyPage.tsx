import { useTranslation } from "react-i18next";

import { researchApi } from "../../api/research";
import { ErrorPanel, LoadingPanel } from "../../components/AsyncPanel";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";

export function ResearchStrategyPage({ strategyId }: { strategyId: string }) {
  const { t, i18n } = useTranslation("research");
  const strategy = useApiResource(
    (signal) => researchApi.strategy(strategyId, signal),
    [strategyId],
  );
  if (strategy.loading) return <LoadingPanel label={t("strategies")} />;
  if (strategy.error) return <ErrorPanel message={strategy.error} />;
  if (!strategy.data) return null;
  return (
    <>
      <Link className="backLink" href="/research/a-share">
        {t("back")}
      </Link>
      <header className="detailHeader">
        <div>
          <p className="eyebrow">{strategy.data.strategy_id}</p>
          <h1>
            {i18n.language === "zh-CN"
              ? strategy.data.name_zh
              : strategy.data.name_en}
          </h1>
          <p>{t("noGuarantee")}</p>
        </div>
      </header>
      <section className="panel methodologyPanel">
        <div className="panelHeader">
          <h2>{t("methodology")}</h2>
        </div>
        <div className="methodologyGrid">
          <div>
            <span>{t("factors")}</span>
            <ul>
              {strategy.data.factor_formulas.map((formula) => (
                <li className="mono" key={formula}>
                  {formula}
                </li>
              ))}
            </ul>
          </div>
          <div>
            <span>{t("rebalance")}</span>
            <strong>{t("equalWeight")}</strong>
          </div>
          <div>
            <span>Configuration SHA-256</span>
            <strong className="mono">{strategy.data.configuration_hash}</strong>
          </div>
        </div>
      </section>
    </>
  );
}
