import { useTranslation } from "react-i18next";

import type { BacktestStatus } from "../types/backtests";
import type { PaperSessionStatus } from "../types/paper";

export function StatusBadge({
  status,
}: {
  status: BacktestStatus | PaperSessionStatus;
}) {
  const { t } = useTranslation("common");
  return (
    <span className={`statusBadge status-${status.toLowerCase()}`}>
      {t(`statuses.${status}`)}
    </span>
  );
}
