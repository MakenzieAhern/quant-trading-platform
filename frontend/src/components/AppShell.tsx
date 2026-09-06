import { useEffect, useState, type ReactNode } from "react";

import { describeConnection, getHealth } from "../api/health";
import type { HealthResponse } from "../types/health";
import { Link } from "./Link";

export function AppShell({ children }: { children: ReactNode }) {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState(false);

  useEffect(() => {
    const controller = new AbortController();
    void getHealth(controller.signal)
      .then(setHealth)
      .catch((reason: unknown) => {
        if (reason instanceof Error && reason.name !== "AbortError")
          setError(true);
      });
    return () => controller.abort();
  }, []);

  return (
    <div className="appShell">
      <header className="topbar">
        <Link
          className="brand"
          href="/backtests"
          aria-label="Quant Platform backtests"
        >
          <span className="brandMark">Q</span>
          <span>QUANT / PLATFORM</span>
        </Link>
        <nav aria-label="Primary navigation">
          <Link href="/backtests">Backtests</Link>
          <Link href="/paper">Paper trading</Link>
          <Link className="primaryLink" href="/backtests/new">
            New backtest
          </Link>
        </nav>
        <span className={`status ${error ? "statusError" : ""}`}>
          <i aria-hidden="true" />{" "}
          {error ? "API unavailable" : describeConnection(health)}
        </span>
      </header>
      <main className="workspace">{children}</main>
      <footer>
        <strong>RESEARCH / BACKTEST / PAPER</strong>
        <span>
          Simulated execution only. No live broker connectivity or real-money
          orders.
        </span>
      </footer>
    </div>
  );
}
