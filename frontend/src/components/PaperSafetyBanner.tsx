export function PaperSafetyBanner() {
  return (
    <aside
      className="paperBanner"
      role="note"
      aria-label="Paper trading safety notice"
    >
      <strong>PAPER TRADING — SIMULATED EXECUTION ONLY</strong>
      <span>
        No live broker connectivity, brokerage credentials, or real-money
        orders.
      </span>
    </aside>
  );
}
