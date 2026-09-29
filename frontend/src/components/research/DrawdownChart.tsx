import { useTranslation } from "react-i18next";

import type { ResearchPoint } from "../../types/research";
import { ResearchPointTable } from "./ResearchPointTable";

export function DrawdownChart({ points }: { points: ResearchPoint[] }) {
  const { t } = useTranslation(["accessibility", "research"]);
  const values = points.map((point) => Number(point.value));
  const finite = values.every(Number.isFinite);
  const minimum = finite ? Math.min(0, ...values) : -1;
  return (
    <figure
      className="researchChart"
      aria-label={t("accessibility:drawdownChart")}
    >
      <div className="drawdownBars" aria-hidden="true">
        {finite &&
          points.map((point, index) => (
            <span
              key={`${point.trading_date}-${index}`}
              title={`${point.trading_date}: ${point.value}`}
              style={{
                height: `${minimum === 0 ? 2 : Math.max(2, (Number(point.value) / minimum) * 100)}%`,
              }}
            />
          ))}
      </div>
      {!finite && <p>{t("research:chartUnavailable")}</p>}
      <ResearchPointTable
        label={t("accessibility:drawdownChart")}
        series={[{ label: t("research:drawdown"), points }]}
      />
    </figure>
  );
}
