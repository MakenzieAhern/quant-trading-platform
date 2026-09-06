import type { BacktestStatus } from "../types/backtests";
import type { PaperSessionStatus } from "../types/paper";

export function StatusBadge({
  status,
}: {
  status: BacktestStatus | PaperSessionStatus;
}) {
  return (
    <span className={`statusBadge status-${status.toLowerCase()}`}>
      {status}
    </span>
  );
}
