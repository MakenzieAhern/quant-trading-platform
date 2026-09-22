import { useTranslation } from "react-i18next";

import type { MonthlyReturn } from "../../types/research";
import { formatPercent } from "../../utils/format";

export function MonthlyReturnHeatmap({ values }: { values: MonthlyReturn[] }) {
  const { t } = useTranslation("accessibility");
  return (
    <div className="monthlyHeatmap" role="img" aria-label={t("monthlyHeatmap")}>
      {values.map((value) => {
        const numeric = value.value === null ? null : Number(value.value);
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
            title={`${value.month}: ${value.value ?? "N/A"}`}
          >
            <span>{value.month.slice(0, 7)}</span>
            <strong>{formatPercent(value.value)}</strong>
          </div>
        );
      })}
    </div>
  );
}
