import { useTranslation } from "react-i18next";

import type { ResearchPeriod } from "../../types/research";

export function SplitBadge({ period }: { period: ResearchPeriod }) {
  const { t } = useTranslation("research");
  return (
    <span className={`splitBadge split-${period.toLowerCase()}`} title={period}>
      {t(`periods.${period}`)}
    </span>
  );
}
