import { useState } from "react";
import { Pagination } from "../../components/Pagination";
import { useApiResource } from "../../hooks/useApiResource";
import { formatDecimal, formatUtc } from "../../utils/format";
import { marketUpdateApi } from "./api";
import { useUpdateCopy } from "./copy";
import type { UpdateJob } from "./types";

export function UpdateRecords({
  job,
  revision,
}: {
  job: UpdateJob;
  revision: number;
}) {
  const c = useUpdateCopy();
  const [security, setSecurity] = useState(job.configuration.security_ids[0]);
  const [receiptOffset, setReceiptOffset] = useState(0);
  const [observationOffset, setObservationOffset] = useState(0);
  const [reload, setReload] = useState(0);
  const receipts = useApiResource(
    (signal) => marketUpdateApi.receipts(job.job_id, receiptOffset, signal),
    [
      job.job_id,
      receiptOffset,
      job.completed_requests,
      job.status,
      revision,
      reload,
    ],
  );
  const observations = useApiResource(
    (signal) =>
      marketUpdateApi.observations(
        security,
        {
          start_date: job.configuration.start_date,
          end_date: job.configuration.end_date,
        },
        signal,
      ),
    [
      security,
      job.configuration.start_date,
      job.configuration.end_date,
      job.completed_requests,
      job.status,
      revision,
      reload,
    ],
  );
  const gaps = job.summary?.unresolved_dates?.[security];
  return (
    <div className="updateRecords">
      <h4>{c.observations}</h4>
      <p>{c.cacheView}</p>
      <label>
        {c.selectSecurity}
        <select
          value={security}
          onChange={(event) => {
            setSecurity(event.target.value);
            setObservationOffset(0);
          }}
        >
          {job.configuration.security_ids.map((id) => (
            <option key={id}>{id}</option>
          ))}
        </select>
      </label>
      <button
        type="button"
        className="button secondary"
        onClick={() => setReload((value) => value + 1)}
      >
        {c.refresh}
      </button>
      <p>{c.gapHelp}</p>
      {gaps && (
        <details>
          <summary>
            {c.viewAllGaps} ({gaps.length})
          </summary>
          <p className="updateGapDates">{gaps.join(", ") || "—"}</p>
        </details>
      )}
      {observations.loading && <p role="status">{c.loading}</p>}
      {observations.error && <p role="alert">{c.loadFailed}</p>}
      {observations.data && (
        <>
          {!observations.data.items.length && <p>{c.noObservations}</p>}
          <div
            className="updateTableScroll"
            tabIndex={0}
            role="region"
            aria-label={c.scroll}
          >
            <table>
              <thead>
                <tr>
                  {[
                    c.date,
                    c.status,
                    c.openPrice,
                    c.high,
                    c.low,
                    c.close,
                    c.volume,
                    c.amount,
                    c.vendorST,
                    c.receiptId,
                  ].map((label) => (
                    <th scope="col" key={label}>
                      {label}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {observations.data.items
                  .slice(observationOffset, observationOffset + 50)
                  .map((row) => (
                    <tr key={`${row.security_id}:${row.trading_date}`}>
                      <th scope="row">{row.trading_date}</th>
                      <td>
                        {row.status === "VENDOR_SUSPENDED"
                          ? c.vendorSuspend
                          : c.raw}
                      </td>
                      {(
                        [
                          "open",
                          "high",
                          "low",
                          "close",
                          "volume",
                          "amount",
                        ] as const
                      ).map((key) => (
                        <td key={key}>{formatDecimal(row.raw[key])}</td>
                      ))}
                      <td>{row.provider_is_st === "1" ? c.yes : c.no}</td>
                      <td>
                        <code>{row.receipt_id}</code>
                      </td>
                    </tr>
                  ))}
              </tbody>
            </table>
          </div>
          <Pagination
            offset={observationOffset}
            limit={50}
            total={observations.data.total}
            onChange={setObservationOffset}
          />
        </>
      )}
      <h4>{c.receipts}</h4>
      {receipts.loading && <p role="status">{c.loading}</p>}
      {receipts.error && <p role="alert">{c.loadFailed}</p>}
      {receipts.data && (
        <>
          {!receipts.data.items.length && <p>{c.noReceipts}</p>}
          {receipts.data.items.map((row) => (
            <details key={row.receipt_id}>
              <summary>
                {row.security_id} · {formatUtc(row.received_at_utc)} ·{" "}
                {c.rowCount}: {row.row_count}
              </summary>
              <dl>
                <dt>{c.receiptId}</dt>
                <dd>{row.receipt_id}</dd>
                <dt>{c.provider}</dt>
                <dd>{row.provider}</dd>
                <dt>{c.parser}</dt>
                <dd>{row.parser_version}</dd>
                <dt>{c.requested}</dt>
                <dd>{formatUtc(row.requested_at_utc)}</dd>
                <dt>{c.received}</dt>
                <dd>{formatUtc(row.received_at_utc)}</dd>
                <dt>{c.sha}</dt>
                <dd>{row.manifest_sha256}</dd>
                <dt>{c.rawSha}</dt>
                <dd>{row.raw_response_sha256}</dd>
              </dl>
              <p>{c.termsHelp}</p>
              <pre>{JSON.stringify(row, null, 2)}</pre>
            </details>
          ))}
          <Pagination
            offset={receiptOffset}
            limit={20}
            total={receipts.data.total}
            onChange={setReceiptOffset}
          />
        </>
      )}
    </div>
  );
}
