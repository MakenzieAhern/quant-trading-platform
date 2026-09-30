import { useEffect, useId, useRef, useState } from "react";
import { Pagination } from "../../components/Pagination";
import { useApiResource } from "../../hooks/useApiResource";
import { formatDecimal, formatUtc } from "../../utils/format";
import { ProductError } from "../ProductPages";
import { usePreferences } from "../preferences";
import { closingPrice, marketApi, validRange } from "./api";
import { observationLabel, useMarketCopy } from "./copy";
import type {
  MarketBar,
  MarketBars,
  MarketDataset,
  MarketRange,
  Security,
} from "./types";

export function MarketDetail({
  security,
  dataset,
  range,
  onRangeChange,
}: {
  security: Security;
  dataset: MarketDataset;
  range: MarketRange;
  onRangeChange: (range: MarketRange) => void;
}) {
  const c = useMarketCopy();
  const { preferences } = usePreferences();
  const [view, setView] = useState(preferences.priceView);
  const [applied, setApplied] = useState(range);
  const [invalid, setInvalid] = useState(!validRange(range, dataset));
  const [revision, setRevision] = useState(0);
  const firstDate = useRef<HTMLInputElement>(null);
  const invalidRangeId = useId();
  useEffect(() => {
    if (invalid) queueMicrotask(() => firstDate.current?.focus());
  }, [invalid]);
  function changeRange(nextRange: MarketRange) {
    onRangeChange(nextRange);
    if (validRange(nextRange, dataset)) setInvalid(false);
  }
  const data = useApiResource(
    (signal) =>
      validRange(applied, dataset)
        ? marketApi.bars(
            dataset.dataset_id,
            security.security_id,
            applied,
            signal,
          )
        : Promise.resolve(null),
    [
      dataset.dataset_id,
      security.security_id,
      applied.start_date,
      applied.end_date,
      revision,
    ],
  );
  return (
    <div className="marketDetail">
      <span className="marketMode">
        {dataset.mode === "synthetic_demo" ? c.demo : c.historical}
      </span>
      <p className="marketNotice">
        {dataset.mode === "synthetic_demo"
          ? c.demoWarning
          : c.historicalWarning}
      </p>
      <p className="marketHelp">{c.searchHelp}</p>
      <form
        className="marketControls"
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          if (!validRange(range, dataset)) {
            setInvalid(true);
            if (invalid) firstDate.current?.focus();
            return;
          }
          setInvalid(false);
          setApplied({ ...range });
        }}
      >
        <fieldset>
          <legend>{c.dates}</legend>
          <p className="marketHelp">{c.rangeHelp}</p>
          <div className="marketControls">
            <label className="marketField">
              {c.first}
              <input
                type="date"
                ref={firstDate}
                required
                min={dataset.coverage_start}
                max={dataset.coverage_end}
                value={range.start_date}
                aria-invalid={invalid || undefined}
                aria-describedby={invalid ? invalidRangeId : undefined}
                onInput={(event) =>
                  changeRange({
                    ...range,
                    start_date: event.currentTarget.value,
                  })
                }
              />
            </label>
            <label className="marketField">
              {c.last}
              <input
                type="date"
                required
                min={dataset.coverage_start}
                max={dataset.coverage_end}
                value={range.end_date}
                aria-invalid={invalid || undefined}
                aria-describedby={invalid ? invalidRangeId : undefined}
                onInput={(event) =>
                  changeRange({
                    ...range,
                    end_date: event.currentTarget.value,
                  })
                }
              />
            </label>
            <button className="button" type="submit">
              {c.apply}
            </button>
          </div>
        </fieldset>
      </form>
      {invalid && (
        <p id={invalidRangeId} role="alert">
          {c.invalidRange}
        </p>
      )}
      <label className="marketField">
        {c.priceView}
        <select
          value={view}
          onChange={(event) =>
            setView(event.target.value as "raw" | "adjusted")
          }
        >
          <option value="raw">{c.raw}</option>
          <option value="adjusted">{c.adjusted}</option>
        </select>
      </label>
      <p className="marketHelp">
        {view === "raw" ? c.rawHelp : c.adjustmentHelp}
      </p>
      {data.loading && <p role="status">{c.loading}</p>}
      {data.error && (
        <ProductError
          error={data.error}
          fallback={c.error}
          retryLabel={c.retry}
          retry={() => setRevision((n) => n + 1)}
        />
      )}
      {data.data && (
        <MarketObservation
          key={`${applied.start_date}:${applied.end_date}`}
          data={data.data}
          view={view}
        />
      )}
    </div>
  );
}

function MarketObservation({
  data,
  view,
}: {
  data: MarketBars;
  view: "raw" | "adjusted";
}) {
  const c = useMarketCopy();
  const { metadata: m, security, items } = data;
  return (
    <>
      <section className="marketPanel">
        <h3>{c.diagnostics}</h3>
        <dl className="marketFacts">
          <div>
            <dt>{c.dates}</dt>
            <dd>
              {m.requested_start} → {m.requested_end} · Asia/Shanghai
            </dd>
          </div>
          <div>
            <dt>{c.asOf}</dt>
            <dd>{m.as_of ?? c.notRecorded}</dd>
          </div>
          <div>
            <dt>{c.retrieved}</dt>
            <dd>
              {m.retrieved_at_utc
                ? formatUtc(m.retrieved_at_utc)
                : c.notRecorded}
            </dd>
          </div>
        </dl>
        <dl className="marketFacts">
          {Object.entries(m.status_counts ?? {}).map(([status, count]) => (
            <div key={status}>
              <dt>{observationLabel(status, c)}</dt>
              <dd>{count}</dd>
            </div>
          ))}
          <div>
            <dt>{c.adjustedMissing}</dt>
            <dd>{m.adjustment_missing_observations ?? c.notRecorded}</dd>
          </div>
        </dl>
        <p className="marketHelp">{c.gapHelp}</p>
        <p className="marketHelp">{c.featureHelp}</p>
        <p className="marketHelp">{c.suspensionHelp}</p>
      </section>
      {items.length ? (
        <PriceChart items={items} view={view} />
      ) : (
        <p role="status">{c.noBars}</p>
      )}
      <details className="marketPanel">
        <summary>{c.provenance}</summary>
        <dl className="marketFacts">
          <div>
            <dt>{c.provider}</dt>
            <dd>
              {m.provider} · {m.provider_version}
            </dd>
          </div>
          <div>
            <dt>{c.rules}</dt>
            <dd>{m.market_rule_version}</dd>
          </div>
          <div>
            <dt>{c.checksum}</dt>
            <dd>
              <code>{m.sha256 ?? c.notRecorded}</code>
            </dd>
          </div>
          <div>
            <dt>{c.listed}</dt>
            <dd>
              {security.listed_from} → {security.listed_to ?? c.openEnded}
            </dd>
          </div>
          <div>
            <dt>{c.sourceName}</dt>
            <dd>{security.name_temporal_authority ?? c.notRecorded}</dd>
          </div>
          <div>
            <dt>{c.sourceUrl}</dt>
            <dd>{security.source_url ?? c.notRecorded}</dd>
          </div>
        </dl>
        <h4>{c.lineage}</h4>
        <ul>
          {m.source_lineage.map((line, i) => (
            <li key={`${i}:${line}`}>
              <code>{line}</code>
            </li>
          ))}
        </ul>
        <h4>{c.limitations}</h4>
        <ul>
          {m.limitations.map((line, i) => (
            <li key={`${i}:${line}`}>
              <code>{line}</code>
            </li>
          ))}
        </ul>
        <h4>{c.partitions}</h4>
        <ul>
          {m.partitions?.map((partition) => (
            <li key={partition.path}>
              <code>
                {partition.path}: {partition.sha256}
              </code>
            </li>
          ))}
        </ul>
      </details>
    </>
  );
}

function PriceChart({
  items,
  view,
}: {
  items: MarketBar[];
  view: "raw" | "adjusted";
}) {
  const c = useMarketCopy();
  const id = useId();
  const [selected, setSelected] = useState(items.at(-1)!.trading_date);
  const [offset, setOffset] = useState(0);
  const selectedBar = items.find((item) => item.trading_date === selected);
  const values = items.map((item) => closingPrice(item, view));
  const points = values
    .filter((value): value is string => value !== null)
    .map(Number);
  const finite = points.length > 0 && points.every(Number.isFinite);
  const low = finite ? Math.min(...points) : 0;
  const high = finite ? Math.max(...points) : 1;
  const range = high - low || 1;
  // Number is used solely for approximate SVG geometry, never labels or data.
  const x = (index: number) =>
    24 + (index / Math.max(1, items.length - 1)) * 552;
  const y = (value: string) => 184 - ((Number(value) - low) / range) * 156;
  const line = finite
    ? values
        .map((value, index) =>
          value === null
            ? ""
            : `${index > 0 && values[index - 1] !== null ? "L" : "M"}${x(index)},${y(value)}`,
        )
        .join(" ")
    : "";
  function choose(date: string) {
    setSelected(date);
    const index = items.findIndex((item) => item.trading_date === date);
    if (index >= 0) setOffset(Math.floor(index / 50) * 50);
  }
  return (
    <section className="marketPanel">
      <h3>
        {c.chart} · {view === "raw" ? c.raw : c.adjusted}
      </h3>
      <p className="marketHelp">{c.chartHelp}</p>
      <label className="marketField">
        {c.pickDate}
        <select
          value={selected}
          onChange={(event) => choose(event.target.value)}
        >
          {items.map((item) => (
            <option key={item.trading_date} value={item.trading_date}>
              {item.trading_date} · {observationLabel(item.status, c)}
            </option>
          ))}
        </select>
      </label>
      <figure className="marketChart">
        <svg
          viewBox="0 0 600 215"
          role="img"
          aria-labelledby={`${id}-title ${id}-description`}
        >
          <title id={`${id}-title`}>{c.chart}</title>
          <desc id={`${id}-description`}>{c.chartHelp}</desc>
          <line x1="24" x2="576" y1="184" y2="184" className="marketAxis" />
          {finite ? (
            <>
              <path d={line} className="marketPriceLine" />
              {items.map(
                (item, index) =>
                  values[index] !== null && (
                    <circle
                      key={item.trading_date}
                      cx={x(index)}
                      cy={y(values[index]!)}
                      r={item.status === "FEATURE_ONLY" ? 4 : 3}
                      className={`marketPricePoint${item.trading_date === selected ? " isSelected" : ""}${item.status === "FEATURE_ONLY" ? " isFeature" : ""}`}
                      onMouseEnter={() => choose(item.trading_date)}
                    >
                      <title>
                        {item.trading_date}: {formatDecimal(values[index])} ·{" "}
                        {observationLabel(item.status, c)}
                      </title>
                    </circle>
                  ),
              )}
            </>
          ) : (
            <text x="300" y="105" textAnchor="middle">
              {c.geometryUnavailable}
            </text>
          )}
        </svg>
        <figcaption>
          {view === "raw" ? c.raw : c.adjusted} · {c.close} · CNY{" "}
          <span>{c.feature}</span>
        </figcaption>
      </figure>
      {selectedBar && (
        <div className="marketReadout">
          <span role="status">
            <strong>{selectedBar.trading_date}</strong> ·{" "}
            {observationLabel(selectedBar.status, c)}
          </span>
          <dl className="marketFacts">
            {[
              [c.open, selectedBar[view].open],
              [c.high, selectedBar[view].high],
              [c.low, selectedBar[view].low],
              [c.close, selectedBar[view].close],
              [c.volume, selectedBar.raw.volume],
              [c.amount, selectedBar.raw.amount],
              [c.factor, selectedBar.adjustment_factor],
            ].map(([label, value]) => (
              <div key={label}>
                <dt>{label}</dt>
                <dd>{formatDecimal(value)}</dd>
              </div>
            ))}
          </dl>
          <p>
            {c.factorDate}:{" "}
            {selectedBar.adjustment_effective_date ?? c.notRecorded} · {c.risk}:{" "}
            {selectedBar.risk_status === "NORMAL"
              ? c.normal
              : (selectedBar.risk_status ?? c.unknown)}{" "}
            · {c.blocked}:{" "}
            {selectedBar.execution_open_blocked === null
              ? c.unknown
              : selectedBar.execution_open_blocked
                ? c.yes
                : c.no}
          </p>
          <details>
            <summary>{c.lineage}</summary>
            <p>
              <code>{selectedBar.source_lineage ?? c.notRecorded}</code>
            </p>
            <p>
              <code>{selectedBar.adjustment_lineage ?? c.notRecorded}</code>
            </p>
          </details>
          {selectedBar.suspension_evidence &&
            selectedBar.suspension_evidence.length > 0 && (
              <details>
                <summary>{c.suspensionEvidence}</summary>
                <pre>
                  {JSON.stringify(selectedBar.suspension_evidence, null, 2)}
                </pre>
              </details>
            )}
        </div>
      )}
      <details>
        <summary>{c.exact}</summary>
        <p className="marketHelp">
          {c.units} {c.scroll}
        </p>
        <div
          className="marketTableScroll"
          tabIndex={0}
          role="region"
          aria-label={c.exact}
        >
          <table aria-label={c.exact}>
            <thead>
              <tr>
                {[
                  c.date,
                  c.status,
                  c.open,
                  c.high,
                  c.low,
                  c.close,
                  c.volume,
                  c.amount,
                  c.factor,
                  c.blocked,
                ].map((label) => (
                  <th scope="col" key={label}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {items.slice(offset, offset + 50).map((item) => (
                <tr
                  key={item.trading_date}
                  className={item.trading_date === selected ? "isSelected" : ""}
                >
                  <th scope="row">
                    <button
                      className="marketTextButton"
                      aria-pressed={item.trading_date === selected}
                      onClick={() => choose(item.trading_date)}
                    >
                      {item.trading_date}
                    </button>
                  </th>
                  <td>{observationLabel(item.status, c)}</td>
                  {[
                    item[view].open,
                    item[view].high,
                    item[view].low,
                    item[view].close,
                    item.raw.volume,
                    item.raw.amount,
                    item.adjustment_factor,
                  ].map((value, index) => (
                    <td key={index}>{formatDecimal(value)}</td>
                  ))}
                  <td>
                    {item.execution_open_blocked === null
                      ? c.unknown
                      : item.execution_open_blocked
                        ? c.yes
                        : c.no}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
        <Pagination
          offset={offset}
          limit={50}
          total={items.length}
          onChange={setOffset}
        />
      </details>
    </section>
  );
}
