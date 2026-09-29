import { useTranslation } from "react-i18next";

import type { MonthlyReturn } from "../../types/research";
import { formatPercent } from "../../utils/format";

export function MonthlyReturnHeatmap({ values }: { values: MonthlyReturn[] }) {
  const { t } = useTranslation("accessibility");
  return (
    <section className="monthlyHeatmap" aria-label={t("monthlyHeatmap")}>
      {values.map((value) => {
        const numeric = value.value === null ? null : Number(value.value);
        const display = formatPercent(value.value);
        const className =
          numeric === null || !Number.isFinite(numeric)
            ? "neutral"
            : numeric >= 0
              ? "positive"
              : "negative";
        return (
          <div
            key={value.month}
            className={className}
            title={`${value.month}: ${display}`}
          >
            <span>{value.month.slice(0, 7)}</span>
            <strong>{display}</strong>
          </div>
        );
      })}
    </section>
  );
}
