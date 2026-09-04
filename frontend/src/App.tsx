import { useEffect, useState } from "react";

import { describeConnection, getHealth } from "./api/health";
import type { HealthResponse } from "./types/health";

const futureModules = ["Market data", "Strategies", "Backtests", "Risk", "Paper trading"];

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    void getHealth(controller.signal)
      .then(setHealth)
      .catch((reason: unknown) => {
        if (reason instanceof Error && reason.name !== "AbortError") setError(reason.message);
      });
    return () => controller.abort();
  }, []);

  return (
    <main className="shell">
      <header className="topbar">
        <div className="brand"><span className="brandMark">Q</span> QUANT / PLATFORM</div>
        <span className={`status ${error ? "statusError" : ""}`}>
          <i /> {error ?? describeConnection(health)}
        </span>
      </header>

      <section className="hero">
        <p className="eyebrow">PHASE 01 / FOUNDATION</p>
        <h1>Research first.<br /><em>Execute safely.</em></h1>
        <p className="lede">
          A deterministic, event-driven workspace for US-equity research, realistic backtesting,
          and clearly isolated paper execution.
        </p>
      </section>

      <section className="grid" aria-label="Platform modules">
        {futureModules.map((module, index) => (
          <article className="module" key={module}>
            <span>0{index + 1}</span>
            <h2>{module}</h2>
            <p>{index === 0 ? "Foundation online" : "Planned in roadmap"}</p>
          </article>
        ))}
      </section>

      <footer>
        <strong>PAPER ONLY</strong>
        <span>Real-money trading is disabled by configuration.</span>
      </footer>
    </main>
  );
}
