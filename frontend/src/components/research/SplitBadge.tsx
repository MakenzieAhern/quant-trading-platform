import type { ResearchPeriod } from "../../types/research";

export function SplitBadge({ period }: { period: ResearchPeriod }) {
  return (
    <span className={`splitBadge split-${period.toLowerCase()}`}>
      {period === "PILOT_SMOKE"
        ? "PILOT_ENGINEERING_SMOKE_ONLY"
        : period.replaceAll("_", " ")}
    </span>
  );
}
