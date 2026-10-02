import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { ResearchPoint } from "../../types/research";
import { ResearchPointTable } from "./ResearchPointTable";

export function DrawdownChart({
  points,
  selectedDate,
  onSelectDate,
}: {
  points: ResearchPoint[];
  selectedDate?: string;
  onSelectDate?: (date: string) => void;
}) {
  const { t } = useTranslation(["accessibility", "research", "common"]);
  const [localDate, setLocalDate] = useState("");
  const selectDate = onSelectDate ?? setLocalDate;
  const dates = [...new Set(points.map((point) => point.trading_date))];
  const candidateDate = selectedDate ?? localDate;
  const activeDate = dates.includes(candidateDate)
    ? candidateDate
    : (dates.at(-1) ?? "");
  const values = points.map((point) => Number(point.value));
  const finite = values.every(Number.isFinite);
  const minimum = finite ? Math.min(0, ...values) : -1;
  return (
    <figure
      className="researchChart"
      aria-label={t("accessibility:drawdownChart")}
    >
      {dates.length > 0 && (
        <label className="researchChartDate">
          {t("research:columns.date")}
          <select
            aria-label={`${t("accessibility:drawdownChart")} — ${t("research:columns.date")}`}
            value={activeDate}
            onChange={(event) => selectDate(event.target.value)}
          >
            {dates.map((date) => (
              <option key={date} value={date}>
                {date}
              </option>
            ))}
          </select>
        </label>
      )}
      <div className="drawdownBars" aria-hidden="true">
        {finite &&
          points.map((point, index) => (
            <span
              key={`${point.trading_date}-${index}`}
              title={`${point.trading_date}: ${point.value}`}
              onMouseEnter={() => selectDate(point.trading_date)}
              onClick={() => selectDate(point.trading_date)}
              style={{
                height: `${minimum === 0 ? 2 : Math.max(2, (Number(point.value) / minimum) * 100)}%`,
              }}
            />
          ))}
      </div>
      {activeDate && (
        <p className="researchChartReadout" role="status" aria-atomic="true">
          <strong>{activeDate}</strong> · {t("research:drawdown")}:{" "}
          {points.find((point) => point.trading_date === activeDate)?.value ??
            t("common:unavailable")}
        </p>
      )}
      {!finite && <p>{t("research:chartUnavailable")}</p>}
      <ResearchPointTable
        label={t("accessibility:drawdownChart")}
        series={[{ label: t("research:drawdown"), points }]}
      />
    </figure>
  );
}
