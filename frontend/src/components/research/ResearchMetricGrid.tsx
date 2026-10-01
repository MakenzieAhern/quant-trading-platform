import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { ResearchMetric } from "../../types/research";
import { formatDecimal, formatPercent } from "../../utils/format";

const PERCENT_METRICS = new Set([
  "cumulative_return",
  "cagr",
  "annualized_volatility",
  "maximum_drawdown",
  "win_rate",
  "turnover",
  "benchmark_return",
  "excess_return",
  "tracking_error",
  "average_gross_exposure",
  "average_net_exposure",
]);

export function ResearchMetricGrid({ metrics }: { metrics: ResearchMetric[] }) {
  const { t } = useTranslation(["metrics", "research"]);
  const [fullPrecision, setFullPrecision] = useState(false);
  const places = fullPrecision ? undefined : 2;
  return (
    <>
      <label className="metricPrecision">
        <input
          type="checkbox"
          checked={fullPrecision}
          onChange={(event) => setFullPrecision(event.target.checked)}
        />
        {t("research:fullPrecision")}
      </label>
      <div className="metricsGrid">
        {metrics.map((metric) => (
          <div
            className="metric"
            key={`${metric.period_kind}-${metric.metric_name}`}
          >
            <span>
              {t(metric.metric_name, {
                defaultValue: metric.metric_name.replaceAll("_", " "),
              })}
            </span>
            <strong title={metric.value ?? undefined}>
              {PERCENT_METRICS.has(metric.metric_name)
                ? formatPercent(metric.value, places)
                : formatDecimal(metric.value, places)}
            </strong>
            <small title={metric.period_kind}>
              {t(`research:periods.${metric.period_kind}`)}
            </small>
          </div>
        ))}
      </div>
    </>
  );
}
