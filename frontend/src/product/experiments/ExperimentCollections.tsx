import { useId, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pagination } from "../../components/Pagination";
import { useApiResource } from "../../hooks/useApiResource";
import { formatDecimal, formatPercent, formatUtc } from "../../utils/format";
import { experimentApi, tradingDate } from "./api";
import { useExperimentCopy } from "./copy";
import { explainExperimentCode } from "./codes";
import { useComparisonCopy } from "./comparisonCopy";
import { ExperimentExports } from "./ExperimentExports";
import { ExperimentHoldings } from "./ExperimentHoldings";
import type { DateRange, ExperimentEquity } from "./types";

export function ExperimentCollections({ jobId }: { jobId: string }) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [range, setRange] = useState<DateRange>({});
  const [invalid, setInvalid] = useState(false);
  const [focused, setFocused] = useState("");
  const filter = focused ? { start_date: focused, end_date: focused } : range;
  return (
    <>
      <section className="experimentPanel">
        <h2>{u.filterTitle}</h2>
        <p className="experimentHelp">{u.rangeHelp}</p>
        <form
          className="experimentActions"
          onSubmit={(event) => {
            event.preventDefault();
            if (start && end && start > end) {
              setInvalid(true);
              return;
            }
            setInvalid(false);
            setFocused("");
            setRange({
              ...(start ? { start_date: start } : {}),
              ...(end ? { end_date: end } : {}),
            });
          }}
        >
          <label>
            {c.start}
            <input
              type="date"
              value={start}
              onInput={(event) => setStart(event.currentTarget.value)}
            />
          </label>
          <label>
            {c.end}
            <input
              type="date"
              value={end}
              onInput={(event) => setEnd(event.currentTarget.value)}
            />
          </label>
          <button className="button secondary" type="submit">
            {u.apply}
          </button>
          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setStart("");
              setEnd("");
              setRange({});
              setFocused("");
              setInvalid(false);
            }}
          >
            {u.reset}
          </button>
        </form>
        {invalid && <p role="alert">{u.invalidRange}</p>}
        {focused && (
          <div className="experimentActions">
            <p role="status">
              {u.focusedDate}: <strong>{focused}</strong> · Asia/Shanghai
            </p>
            <button className="button secondary" onClick={() => setFocused("")}>
              {u.clearFocus}
            </button>
          </div>
        )}
      </section>
      <FilteredCollections
        key={`${jobId}-${filter.start_date}-${filter.end_date}`}
        jobId={jobId}
        range={filter}
        focused={focused}
        onFocusDate={setFocused}
      />
      <ExperimentExports jobId={jobId} range={filter} />
    </>
  );
}

function FilteredCollections({
  jobId,
  range,
  focused,
  onFocusDate,
}: {
  jobId: string;
  range: DateRange;
  focused: string;
  onFocusDate: (date: string) => void;
}) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [showTrades, setShowTrades] = useState(Boolean(focused));
  const [showDecisions, setShowDecisions] = useState(false);
  const [showHoldings, setShowHoldings] = useState(Boolean(focused));
  const equity = useApiResource(
    (signal) => experimentApi.equity(jobId, signal, offset, range),
    [jobId, offset, range.start_date, range.end_date, revision],
  );
  return (
    <>
      <section className="experimentPanel">
        <h2>{c.chart}</h2>
        <p className="experimentHelp">{c.shownPage}</p>
        {equity.loading && <p role="status">{c.loading}</p>}
        {equity.error && (
          <div role="alert">
            <p>{c.networkError}</p>
            <button
              className="button secondary"
              onClick={() => setRevision((value) => value + 1)}
            >
              {c.retryLoad}
            </button>
          </div>
        )}
        {equity.data && (
          <>
            <EquityDisplay
              key={`${jobId}-${offset}`}
              points={equity.data.items}
              onFocusDate={onFocusDate}
            />
            <Pagination
              offset={equity.data.offset}
              limit={equity.data.limit}
              total={equity.data.total}
              onChange={setOffset}
            />
          </>
        )}
      </section>
      <details
        className="experimentPanel"
        open={showTrades}
        onToggle={(event) => setShowTrades(event.currentTarget.open)}
      >
        <summary>{c.trades}</summary>
        {showTrades && (
          <TradeCollection
            jobId={jobId}
            range={range}
            onFocusDate={onFocusDate}
          />
        )}
      </details>
      <details
        className="experimentPanel"
        open={showHoldings}
        onToggle={(event) => setShowHoldings(event.currentTarget.open)}
      >
        <summary>{u.holdings}</summary>
        {showHoldings && <ExperimentHoldings jobId={jobId} range={range} />}
      </details>
      <details
        className="experimentPanel"
        onToggle={(event) => setShowDecisions(event.currentTarget.open)}
      >
        <summary>{c.decisions}</summary>
        {showDecisions && <DecisionCollection jobId={jobId} range={range} />}
      </details>
    </>
  );
}

function EquityDisplay({
  points,
  onFocusDate,
}: {
  points: ExperimentEquity[];
  onFocusDate: (date: string) => void;
}) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const id = useId();
  const [showBenchmark, setShowBenchmark] = useState(true);
  const [selected, setSelected] = useState(points.at(-1)?.trading_date ?? "");
  if (!points.length) return <p>{u.filteredEmpty}</p>;
  const point = points.find((item) => item.trading_date === selected);
  // Only SVG positions use Number. Financial labels and tables retain server strings.
  const values = points.flatMap((item) => [
    Number(item.equity),
    ...(showBenchmark && item.benchmark !== null
      ? [Number(item.benchmark)]
      : []),
  ]);
  const finite = values.every(Number.isFinite);
  const low = finite ? Math.min(...values) : 0;
  const high = finite ? Math.max(...values) : 1;
  const range = high - low || 1;
  const x = (index: number) =>
    24 + (index / Math.max(1, points.length - 1)) * 852;
  const y = (value: string) => 210 - ((Number(value) - low) / range) * 180;
  const equityLine = finite
    ? points.map((item, index) => `${x(index)},${y(item.equity)}`).join(" ")
    : "";
  const benchmarkLine =
    finite && points.every((item) => item.benchmark !== null)
      ? points
          .map((item, index) => `${x(index)},${y(item.benchmark!)}`)
          .join(" ")
      : "";
  const drawdowns = points.map((item) =>
    item.drawdown === null ? null : Number(item.drawdown),
  );
  const drawdownFinite = drawdowns.every(
    (value) => value !== null && Number.isFinite(value),
  );
  const lowestDrawdown = drawdownFinite
    ? Math.min(-0.01, ...(drawdowns as number[]))
    : -1;
  const drawdownLine = drawdownFinite
    ? drawdowns
        .map(
          (value, index) =>
            `${x(index)},${260 + (value! / lowestDrawdown) * 70}`,
        )
        .join(" ")
    : "";
  const selectedIndex = points.findIndex(
    (item) => item.trading_date === selected,
  );
  return (
    <>
      <div className="experimentChartControls">
        <label className="experimentCheck">
          <input
            type="checkbox"
            checked={showBenchmark}
            onChange={(event) => setShowBenchmark(event.target.checked)}
          />
          {c.showBenchmark}
        </label>
        <label>
          {c.selectDate}
          <select
            value={selected}
            onChange={(event) => setSelected(event.target.value)}
          >
            {points.map((item) => (
              <option key={item.sequence} value={item.trading_date}>
                {item.trading_date}
              </option>
            ))}
          </select>
        </label>
        <button
          className="button secondary"
          disabled={!selected}
          onClick={() => onFocusDate(selected)}
        >
          {u.inspectActivity}
        </button>
      </div>
      <figure className="experimentChart">
        <svg
          viewBox="0 0 900 350"
          role="img"
          aria-labelledby={`${id}-title ${id}-description`}
        >
          <title id={`${id}-title`}>{c.chart}</title>
          <desc id={`${id}-description`}>
            {c.shownPage} {c.table}
          </desc>
          <line
            x1="24"
            x2="876"
            y1="210"
            y2="210"
            className="experimentChartAxis"
          />
          <line
            x1="24"
            x2="876"
            y1="260"
            y2="260"
            className="experimentChartAxis"
          />
          {finite ? (
            <>
              <polyline className="experimentEquityLine" points={equityLine} />
              {showBenchmark && benchmarkLine && (
                <polyline
                  className="experimentBenchmarkLine"
                  points={benchmarkLine}
                />
              )}
              {drawdownLine && (
                <polyline
                  className="experimentDrawdownLine"
                  points={drawdownLine}
                />
              )}
              {selectedIndex >= 0 && (
                <line
                  x1={x(selectedIndex)}
                  x2={x(selectedIndex)}
                  y1="24"
                  y2="335"
                  className="experimentSelectedLine"
                />
              )}
              {points.map((item, index) => (
                <circle
                  key={item.sequence}
                  cx={x(index)}
                  cy={y(item.equity)}
                  r="4"
                  className={`experimentChartPoint${item.trading_date === selected ? " isSelected" : ""}`}
                  onMouseEnter={() => setSelected(item.trading_date)}
                >
                  <title>
                    {item.trading_date}: {formatDecimal(item.equity)}
                  </title>
                </circle>
              ))}
            </>
          ) : (
            <text x="450" y="140" textAnchor="middle">
              {c.geometryUnavailable}
            </text>
          )}
        </svg>
        <figcaption>
          <span className="experimentEquityLegend">{c.equity}</span>
          {showBenchmark && (
            <span className="experimentBenchmarkLegend">
              {c.chartBenchmark}
            </span>
          )}
          <span className="experimentDrawdownLegend">{c.drawdownSeries}</span>
        </figcaption>
      </figure>
      {point && (
        <p className="experimentChartReadout">
          {c.selectedDate}: <strong>{point.trading_date}</strong> · {c.equity}:{" "}
          <strong>{formatDecimal(point.equity)}</strong>
          {showBenchmark && (
            <>
              {" "}
              · {c.chartBenchmark}: {formatDecimal(point.benchmark)}
            </>
          )}{" "}
          · {c.drawdownSeries}: {formatPercent(point.drawdown)}
        </p>
      )}
      <details>
        <summary>{c.table}</summary>
        <p className="experimentHelp">{c.tableScroll}</p>
        <div
          className="experimentTableScroll"
          tabIndex={0}
          aria-label={c.tableScroll}
        >
          <table>
            <thead>
              <tr>
                <th scope="col">{c.date}</th>
                <th scope="col">{c.equity}</th>
                <th scope="col">{c.chartBenchmark}</th>
                <th scope="col">{c.drawdownSeries}</th>
              </tr>
            </thead>
            <tbody>
              {points.map((item) => (
                <tr
                  key={item.sequence}
                  className={item.trading_date === selected ? "isSelected" : ""}
                >
                  <th scope="row">
                    <button
                      type="button"
                      className="experimentDateButton"
                      aria-pressed={item.trading_date === selected}
                      onClick={() => setSelected(item.trading_date)}
                    >
                      {item.trading_date}
                    </button>
                  </th>
                  <td>{formatDecimal(item.equity)}</td>
                  <td>{formatDecimal(item.benchmark)}</td>
                  <td>{formatPercent(item.drawdown)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </>
  );
}

function TradeCollection({
  jobId,
  range,
  onFocusDate,
}: {
  jobId: string;
  range: DateRange;
  onFocusDate: (date: string) => void;
}) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const data = useApiResource(
    (signal) => experimentApi.trades(jobId, signal, offset, range),
    [jobId, offset, range.start_date, range.end_date, revision],
  );
  if (data.loading) return <p role="status">{c.loading}</p>;
  if (data.error)
    return (
      <div role="alert">
        <p>{c.networkError}</p>
        <button
          className="button secondary"
          onClick={() => setRevision((value) => value + 1)}
        >
          {c.retryLoad}
        </button>
      </div>
    );
  if (!data.data) return null;
  return (
    <>
      <p className="experimentHelp">{c.tableScroll}</p>
      {data.data.items.length === 0 ? (
        <p>{u.filteredEmpty}</p>
      ) : (
        <div
          className="experimentTableScroll"
          tabIndex={0}
          aria-label={c.tableScroll}
        >
          <table>
            <thead>
              <tr>
                {[
                  c.time,
                  c.security,
                  c.side,
                  c.quantity,
                  c.price,
                  c.tradeCost,
                ].map((label) => (
                  <th scope="col" key={label}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.data.items.map((item) => (
                <tr key={item.sequence}>
                  <td>
                    {formatUtc(item.timestamp)}
                    {tradingDate(item) && (
                      <>
                        <br />
                        <button
                          className="experimentDateButton"
                          onClick={() => onFocusDate(tradingDate(item)!)}
                        >
                          {u.viewTradeDate}: {tradingDate(item)}
                        </button>
                      </>
                    )}
                  </td>
                  <td>{item.security_id}</td>
                  <td>
                    {item.side === "BUY"
                      ? c.buy
                      : item.side === "SELL"
                        ? c.sell
                        : item.side}
                  </td>
                  <td>{formatDecimal(item.quantity)}</td>
                  <td>{formatDecimal(item.price)}</td>
                  <td>{formatDecimal(item.transaction_cost)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination
        offset={data.data.offset}
        limit={data.data.limit}
        total={data.data.total}
        onChange={setOffset}
      />
    </>
  );
}

function DecisionCollection({
  jobId,
  range,
}: {
  jobId: string;
  range: DateRange;
}) {
  const c = useExperimentCopy();
  const { i18n } = useTranslation();
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const data = useApiResource(
    (signal) => experimentApi.decisions(jobId, signal, offset, range),
    [jobId, offset, range.start_date, range.end_date, revision],
  );
  if (data.loading) return <p role="status">{c.loading}</p>;
  if (data.error)
    return (
      <div role="alert">
        <p>{c.networkError}</p>
        <button
          className="button secondary"
          onClick={() => setRevision((value) => value + 1)}
        >
          {c.retryLoad}
        </button>
      </div>
    );
  if (!data.data) return null;
  return (
    <>
      <p className="experimentHelp">{c.tableScroll}</p>
      {data.data.items.length === 0 ? (
        <p>{c.emptyCollection}</p>
      ) : (
        <div
          className="experimentTableScroll"
          tabIndex={0}
          aria-label={c.tableScroll}
        >
          <table>
            <thead>
              <tr>
                {[c.time, c.security, c.decision, c.reason].map((label) => (
                  <th scope="col" key={label}>
                    {label}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.data.items.map((item) => (
                <tr key={item.sequence}>
                  <td>{formatUtc(item.timestamp)}</td>
                  <td>{item.security_id}</td>
                  <td>{item.approved ? c.allowed : c.rejected}</td>
                  <td>
                    {explainExperimentCode(item.reason_code, i18n.language)}
                    <details>
                      <summary>{c.technical}</summary>
                      <code>{item.reason_code}</code>
                      <p>{item.message}</p>
                    </details>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination
        offset={data.data.offset}
        limit={data.data.limit}
        total={data.data.total}
        onChange={setOffset}
      />
    </>
  );
}
