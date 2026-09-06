import type { BacktestStatus } from "../types/backtests";

export function StatusBadge({ status }: { status: BacktestStatus }) {
  return (
    <span className={`statusBadge status-${status.toLowerCase()}`}>
      {status}
    </span>
  );
}
