import { useTranslation } from "react-i18next";

import type { ResearchPoint } from "../../types/research";

export function DrawdownChart({ points }: { points: ResearchPoint[] }) {
  const { t } = useTranslation("accessibility");
  const values = points.map((point) => Number(point.value));
  const finite = values.every(Number.isFinite);
  const minimum = finite ? Math.min(0, ...values) : -1;
  return (
    <figure className="drawdownBars" aria-label={t("drawdownChart")}>
      {finite &&
        points.map((point, index) => (
          <span
            key={`${point.trading_date}-${index}`}
            title={`${point.trading_date}: ${point.value}`}
            style={{
              height: `${Math.max(2, (Number(point.value) / minimum) * 100)}%`,
            }}
          />
        ))}
    </figure>
  );
}
