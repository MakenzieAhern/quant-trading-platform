import { useState } from "react";
import { Pagination } from "../../components/Pagination";
import { useApiResource } from "../../hooks/useApiResource";
import { formatDecimal, formatPercent, formatUtc } from "../../utils/format";
import { experimentApi } from "./api";
import { useComparisonCopy } from "./comparisonCopy";
import { useExperimentCopy } from "./copy";
import type { DateRange } from "./types";

export function ExperimentHoldings({
  jobId,
  range,
}: {
  jobId: string;
  range: DateRange;
}) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const data = useApiResource(
    (signal) => experimentApi.holdings(jobId, signal, offset, range),
    [jobId, offset, range.start_date, range.end_date, revision],
  );
  const available = data.data?.availability === "AVAILABLE";
  const pager = (
    <Pagination
      key="pagination"
      offset={offset}
      limit={data.data?.limit ?? 1}
      total={available ? data.data!.total : null}
      loading={data.loading}
      onChange={setOffset}
    />
  );
  if (data.loading)
    return (
      <>
        <p role="status">{c.loading}</p>
        {pager}
      </>
    );
  if (data.error)
    return (
      <>
        <div role="alert">
          <p>{c.networkError}</p>
          <button
            className="button secondary"
            onClick={() => setRevision((value) => value + 1)}
          >
            {c.retryLoad}
          </button>
        </div>
        {pager}
      </>
    );
  if (!data.data) return <>{pager}</>;
  if (data.data.availability === "NOT_RECORDED")
    return (
      <>
        <p role="status">{u.notRecorded}</p>
        {pager}
      </>
    );
  if (data.data.availability === "NOT_READY")
    return (
      <>
        <p role="status">{u.notReadyRecords}</p>
        {pager}
      </>
    );
  return (
    <>
      {data.data.items.length === 0 && <p>{u.filteredEmpty}</p>}
      {data.data.items.map((item) => (
        <article key={item.sequence}>
          <h3>{item.trading_date} · Asia/Shanghai</h3>
          <p className="experimentHelp">{formatUtc(item.timestamp)}</p>
          <dl className="experimentSummaryGrid">
            {[
              [u.cash, item.cash],
              [c.equity, item.equity],
              [u.accountValue, item.market_value],
              [u.totalPnl, item.total_pnl ?? null],
              [u.realized, item.realized_pnl],
              [u.corporateRealized, item.corporate_action_realized_pnl ?? null],
              [u.unrealized, item.unrealized_pnl],
              [u.commissionTotal, item.cumulative_commission],
              [u.pendingActions, item.pending_corporate_action_value],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{formatDecimal(value)}</dd>
              </div>
            ))}
          </dl>
          <p className="experimentHelp">{u.pendingIncluded}</p>
          {item.positions.length === 0 ? (
            <p>{u.allCash}</p>
          ) : (
            <div
              className="experimentTableScroll"
              role="region"
              tabIndex={0}
              aria-label={u.holdings}
            >
              <table aria-label={u.holdings}>
                <thead>
                  <tr>
                    {[
                      c.security,
                      c.quantity,
                      u.averagePrice,
                      u.marketPrice,
                      u.marketValue,
                      u.weight,
                    ].map((label) => (
                      <th key={label} scope="col">
                        {label}
                      </th>
                    ))}
                  </tr>
                </thead>
                <tbody>
                  {item.positions.map((position) => (
                    <tr key={position.security_id}>
                      <th scope="row">{position.security_id}</th>
                      <td>{formatDecimal(position.quantity)}</td>
                      <td>{formatDecimal(position.average_price)}</td>
                      <td>{formatDecimal(position.market_price)}</td>
                      <td>{formatDecimal(position.market_value)}</td>
                      <td>{formatPercent(position.weight)}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </article>
      ))}
      {pager}
    </>
  );
}
