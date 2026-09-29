import { useTranslation } from "react-i18next";

import type { ResearchPoint } from "../../types/research";
import { ResearchPointTable } from "./ResearchPointTable";

interface ChartPoint {
  x: number;
  y: number;
}

function coordinates(
  points: ResearchPoint[],
  width: number,
  height: number,
  scaleValues: number[],
): ChartPoint[] {
  const values = points.map((point) => Number(point.value));
  if (scaleValues.some((value) => !Number.isFinite(value))) return [];
  const minimum = Math.min(...scaleValues);
  const maximum = Math.max(...scaleValues);
  const range = maximum - minimum || 1;
  return values.map((value, index) => ({
    x: points.length === 1 ? width / 2 : (index / (points.length - 1)) * width,
    y: height - ((value - minimum) / range) * height,
  }));
}

function polyline(points: ChartPoint[]): string {
  return points.map((point) => `${point.x},${point.y}`).join(" ");
}

export function BenchmarkChart({
  strategy,
  benchmark,
  strategyLabel,
  benchmarkLabel,
  ariaLabel,
}: {
  strategy: ResearchPoint[];
  benchmark: ResearchPoint[];
  strategyLabel?: string;
  benchmarkLabel?: string;
  ariaLabel?: string;
}) {
  const { t } = useTranslation(["accessibility", "research"]);
  const chartLabel = ariaLabel ?? t("accessibility:benchmarkChart");
  const firstLabel = strategyLabel ?? t("research:strategySeries");
  const secondLabel = benchmarkLabel ?? t("research:benchmark");
  const width = 900;
  const height = 260;
  const scaleValues = [...strategy, ...benchmark].map((point) =>
    Number(point.value),
  );
  const strategyCoordinates = coordinates(strategy, width, height, scaleValues);
  const benchmarkCoordinates = coordinates(
    benchmark,
    width,
    height,
    scaleValues,
  );
  return (
    <figure className="researchChart" aria-label={chartLabel}>
      <svg viewBox={`0 0 ${width} ${height}`} aria-hidden="true">
        <polyline
          className="strategyLine"
          points={polyline(strategyCoordinates)}
        />
        <polyline
          className="benchmarkLine"
          points={polyline(benchmarkCoordinates)}
        />
      </svg>
      <figcaption>
        <span className="strategyLegend">{firstLabel}</span>
        <span className="benchmarkLegend">{secondLabel}</span>
      </figcaption>
      {scaleValues.some((value) => !Number.isFinite(value)) && (
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
