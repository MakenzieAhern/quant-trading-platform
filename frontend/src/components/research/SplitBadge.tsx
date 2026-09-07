import type { ResearchPeriod } from "../../types/research";

export function SplitBadge({ period }: { period: ResearchPeriod }) {
  return (
    <span className={`splitBadge split-${period.toLowerCase()}`}>
      {period.replaceAll("_", " ")}
    </span>
  );
}
