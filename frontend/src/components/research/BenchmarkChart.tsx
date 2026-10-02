import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { NullableResearchPoint } from "../../types/research";
import { ResearchPointTable } from "./ResearchPointTable";

interface ChartPoint {
  x: number;
  y: number;
}

function coordinates(
  points: NullableResearchPoint[],
  width: number,
  height: number,
  scaleValues: number[],
  dates: Map<string, number>,
): (ChartPoint | null)[] {
  const values = points.map((point) =>
    point.value === null ? null : Number(point.value),
  );
  if (
    !scaleValues.length ||
    scaleValues.some((value) => !Number.isFinite(value))
  )
    return [];
  const minimum = Math.min(...scaleValues);
  const maximum = Math.max(...scaleValues);
  const range = maximum - minimum || 1;
  return values.map((value, index) => {
    const dateIndex = dates.get(points[index].trading_date);
    return value === null || dateIndex === undefined
      ? null
      : {
          x:
            dates.size === 1
              ? width / 2
              : (dateIndex / (dates.size - 1)) * width,
          y: height - ((value - minimum) / range) * height,
        };
  });
}

function traces(points: (ChartPoint | null)[], className: string) {
  const segments: ChartPoint[][] = [[]];
  for (const point of points) {
    if (point === null) {
      if (segments[segments.length - 1].length) segments.push([]);
    } else {
      segments[segments.length - 1].push(point);
    }
  }
  return segments
    .filter((segment) => segment.length)
    .map((segment, index) =>
      segment.length === 1 ? (
        <circle
          key={index}
          className={className}
          cx={segment[0].x}
          cy={segment[0].y}
          r={3}
        />
      ) : (
        <polyline
          key={index}
          className={className}
          points={segment.map((point) => `${point.x},${point.y}`).join(" ")}
        />
      ),
    );
}

export function BenchmarkChart({
  strategy,
  benchmark,
  strategyLabel,
  benchmarkLabel,
  ariaLabel,
  showBenchmark = true,
  selectedDate,
  onSelectDate,
}: {
  strategy: NullableResearchPoint[];
  benchmark: NullableResearchPoint[];
  strategyLabel?: string;
  benchmarkLabel?: string;
  ariaLabel?: string;
  showBenchmark?: boolean;
  selectedDate?: string;
  onSelectDate?: (date: string) => void;
}) {
  const { t } = useTranslation(["accessibility", "research", "common"]);
  const [localDate, setLocalDate] = useState("");
  const selectDate = onSelectDate ?? setLocalDate;
  const chartLabel = ariaLabel ?? t("accessibility:benchmarkChart");
  const firstLabel = strategyLabel ?? t("research:strategySeries");
  const secondLabel = benchmarkLabel ?? t("research:benchmark");
  const width = 900;
  const height = 260;
  const scaleValues = [
    ...strategy,
    ...(showBenchmark ? benchmark : []),
  ].flatMap((point) => (point.value === null ? [] : [Number(point.value)]));
  const dates = new Map(
    [...new Set([...strategy, ...benchmark].map((point) => point.trading_date))]
      .sort()
      .map((date, index) => [date, index]),
  );
  const strategyCoordinates = coordinates(
    strategy,
    width,
    height,
    scaleValues,
    dates,
  );
  const benchmarkCoordinates = coordinates(
    benchmark,
    width,
    height,
    scaleValues,
    dates,
  );
  const dateOptions = [...dates.keys()];
  const candidateDate = selectedDate ?? localDate;
  const activeDate = dates.has(candidateDate)
    ? candidateDate
    : (dateOptions.at(-1) ?? "");
  const pointValue = (points: NullableResearchPoint[]) =>
    points.find((point) => point.trading_date === activeDate)?.value ??
    t("common:unavailable");
  const hitPoints = (
    points: NullableResearchPoint[],
    positions: (ChartPoint | null)[],
    label: string,
  ) =>
    positions.map((position, index) =>
      position === null ? null : (
        <circle
          key={`${label}-${points[index].sequence}`}
          className="researchChartPoint"
          cx={position.x}
          cy={position.y}
          r={6}
          fill="transparent"
          onMouseEnter={() => selectDate(points[index].trading_date)}
          onClick={() => selectDate(points[index].trading_date)}
        >
          <title>{`${label} — ${points[index].trading_date}: ${points[index].value}`}</title>
        </circle>
      ),
    );
  return (
    <figure className="researchChart" aria-label={chartLabel}>
      {dateOptions.length > 0 && (
        <label className="researchChartDate">
          {t("research:columns.date")}
          <select
            aria-label={`${chartLabel} — ${t("research:columns.date")}`}
            value={activeDate}
            onChange={(event) => selectDate(event.target.value)}
          >
            {dateOptions.map((date) => (
              <option key={date} value={date}>
                {date}
              </option>
            ))}
          </select>
        </label>
      )}
      <svg viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
        {traces(strategyCoordinates, "strategyLine")}
        {showBenchmark && traces(benchmarkCoordinates, "benchmarkLine")}
        {hitPoints(strategy, strategyCoordinates, firstLabel)}
        {showBenchmark &&
          hitPoints(benchmark, benchmarkCoordinates, secondLabel)}
      </svg>
      <figcaption>
        <span className="strategyLegend">{firstLabel}</span>
        {showBenchmark && (
          <span className="benchmarkLegend">{secondLabel}</span>
        )}
      </figcaption>
      {activeDate && (
        <p className="researchChartReadout" role="status" aria-atomic="true">
          <strong>{activeDate}</strong> · {firstLabel}: {pointValue(strategy)}
          {showBenchmark && ` · ${secondLabel}: ${pointValue(benchmark)}`}
        </p>
      )}
      {(!scaleValues.length ||
        scaleValues.some((value) => !Number.isFinite(value))) && (
        <p>{t("research:chartUnavailable")}</p>
      )}
      <ResearchPointTable
        label={chartLabel}
        series={[
          { label: firstLabel, points: strategy },
          { label: secondLabel, points: benchmark },
        ]}
      />
    </figure>
  );
}
