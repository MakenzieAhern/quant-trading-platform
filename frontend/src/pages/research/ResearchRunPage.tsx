import { useId, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiContractError } from "../../api/contracts";
import { researchApi } from "../../api/research";
import {
  EmptyState,
  ErrorPanel,
  LoadingPanel,
} from "../../components/AsyncPanel";
import { Link } from "../../components/Link";
import { Pagination } from "../../components/Pagination";
import { BenchmarkChart } from "../../components/research/BenchmarkChart";
import { DrawdownChart } from "../../components/research/DrawdownChart";
import { MonthlyReturnHeatmap } from "../../components/research/MonthlyReturnHeatmap";
import { ResearchMetricGrid } from "../../components/research/ResearchMetricGrid";
import { SplitBadge } from "../../components/research/SplitBadge";
import { useApiResource } from "../../hooks/useApiResource";
import { useComparisonCopy } from "../../product/experiments/comparisonCopy";
import { useExperimentCopy } from "../../product/experiments/copy";
import type { DateRange } from "../../product/experiments/types";
import {
  formatDecimal,
  formatPercent,
  formatUtc,
  shortId,
} from "../../utils/format";

const FORMAL_KNOWN_LIMITATIONS =
  "Daily-bar simulation; Validation did not establish robust alpha; no guarantee of future returns.";

export function ResearchRunPage({ runId }: { runId: string }) {
  const { t } = useTranslation([
    "research",
    "common",
    "metrics",
    "accessibility",
    "paper",
  ]);
  const [curveOffset, setCurveOffset] = useState(0);
  const [showBenchmark, setShowBenchmark] = useState(true);
  const [rollingOffset, setRollingOffset] = useState(0);
  const [holdingsOffset, setHoldingsOffset] = useState(0);
  const [rebalancesOffset, setRebalancesOffset] = useState(0);
  const [tradesOffset, setTradesOffset] = useState(0);
  const u = useComparisonCopy();
  const c = useExperimentCopy();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [range, setRange] = useState<DateRange>({});
  const [invalid, setInvalid] = useState(false);
  const [selectedDate, setSelectedDate] = useState("");
  const [activityDate, setActivityDate] = useState("");
  const firstDate = useRef<HTMLInputElement>(null);
  const filterAnchor = useRef<HTMLElement>(null);
  const activityAnchor = useRef<HTMLElement>(null);
  const invalidRangeId = useId();
  const activityRange = activityDate
    ? { start_date: activityDate, end_date: activityDate }
    : range;
  const resetRecordOffsets = () => {
    setHoldingsOffset(0);
    setRebalancesOffset(0);
    setTradesOffset(0);
  };
  const applyRange = (nextRange: DateRange) => {
    setRange(nextRange);
    setInvalid(false);
    setSelectedDate("");
    setActivityDate("");
    setCurveOffset(0);
    setRollingOffset(0);
    resetRecordOffsets();
  };
  const run = useApiResource(
    (signal) => researchApi.run(runId, signal),
    [runId],
  );
  const metrics = useApiResource(
    (signal) => researchApi.metrics(runId, signal),
    [runId],
  );
  const curves = useApiResource(
    async (signal) => {
      const [equity, benchmark, drawdown] = await Promise.all([
        researchApi.points(runId, "equity", curveOffset, signal, range),
        researchApi.points(runId, "benchmark", curveOffset, signal, range),
        researchApi.points(runId, "drawdown", curveOffset, signal, range),
      ]);
      if (
        equity.total !== benchmark.total ||
        equity.total !== drawdown.total ||
        equity.items.some(
          (point, index) =>
            point.sequence !== benchmark.items[index]?.sequence ||
            point.sequence !== drawdown.items[index]?.sequence ||
            point.trading_date !== benchmark.items[index]?.trading_date ||
            point.trading_date !== drawdown.items[index]?.trading_date,
        )
      )
        throw new ApiContractError();
      return { equity, benchmark, drawdown };
    },
    [runId, curveOffset, range.start_date, range.end_date],
  );
  const monthly = useApiResource(
    (signal) => researchApi.monthlyReturns(runId, signal),
    [runId],
  );
  const rolling = useApiResource(
    (signal) => researchApi.rollingMetrics(runId, rollingOffset, signal, range),
    [runId, rollingOffset, range.start_date, range.end_date],
  );
  const holdings = useApiResource(
    (signal) =>
      researchApi.holdings(runId, holdingsOffset, signal, activityRange),
    [runId, holdingsOffset, activityRange.start_date, activityRange.end_date],
  );
  const rebalances = useApiResource(
    (signal) =>
      researchApi.rebalances(runId, rebalancesOffset, signal, activityRange),
    [runId, rebalancesOffset, activityRange.start_date, activityRange.end_date],
  );
  const trades = useApiResource(
    (signal) => researchApi.trades(runId, tradesOffset, signal, activityRange),
    [runId, tradesOffset, activityRange.start_date, activityRange.end_date],
  );
  if (run.loading) return <LoadingPanel label={t("research:runDetail")} />;
  if (run.error) return <ErrorPanel message={run.error} />;
  if (!run.data) return null;
  const knownLimitations = run.data.diagnostics.known_limitations;
  const curveDates =
    curves.data?.equity.items.map((point) => point.trading_date) ?? [];
  const activeDate = curveDates.includes(selectedDate)
    ? selectedDate
    : (curveDates.at(-1) ?? "");
  const filtered = Boolean(range.start_date || range.end_date);
  const rollingByDate = new Map<string, Record<string, string | null>>();
  for (const item of rolling.data?.items ?? []) {
    const values = rollingByDate.get(item.trading_date) ?? {};
    values[item.metric_name] = item.value;
    rollingByDate.set(item.trading_date, values);
  }
  const rollingDates = [...rollingByDate];
  const rollingPoints = (metricName: "sharpe" | "drawdown") =>
    rollingDates.map(([trading_date, values], sequence) => ({
      sequence,
      trading_date,
      value: values[metricName] ?? null,
    }));
  const rollingSharpe = rollingPoints("sharpe");
  const rollingDrawdown = rollingPoints("drawdown");
  return (
    <>
      <Link className="backLink" href="/research/a-share">
        {t("research:back")}
      </Link>
      <header className="detailHeader">
        <div>
          <p className="eyebrow">
            {t("research:runDetail")} / {shortId(runId)}
          </p>
          <h1>{run.data.strategy_id}</h1>
          <p className="runId">{runId}</p>
        </div>
        <SplitBadge period={run.data.period_kind} />
      </header>
      {run.data.period_kind !== "PILOT_SMOKE" && (
        <div className="oosGuard" role="note">
          {run.data.period_kind === "OUT_OF_SAMPLE"
            ? t("research:oosResultCaution")
            : t("research:preOosEvidence")}
        </div>
      )}
      {Boolean(run.data.diagnostics.dataset_acceptance_warning) && (
        <div className="oosGuard" role="alert">
          {String(run.data.diagnostics.dataset_acceptance_warning)}
        </div>
      )}
      {run.data.period_kind === "PILOT_SMOKE" && (
        <div className="oosGuard" role="note">
          {t("research:pilotSmokeWarning")}
        </div>
      )}
      <section className="runFacts" aria-label={t("research:lineage")}>
        <div>
          <span>{t("common:dataset")}</span>
          <strong>
            <Link
              className="monoLink"
              href={`/research/a-share/datasets/${encodeURIComponent(run.data.dataset_id)}`}
            >
              {run.data.dataset_id}
            </Link>
          </strong>
        </div>
        <div>
          <span>{t("research:provider")}</span>
          <strong>
            {run.data.provider} / {run.data.provider_version}
          </strong>
        </div>
        <div>
          <span>{t("research:checksum")}</span>
          <strong className="mono" title={run.data.dataset_checksum}>
            {shortId(run.data.dataset_checksum)}
          </strong>
        </div>
        <div>
          <span>{t("research:ruleVersion")}</span>
          <strong>{run.data.market_rule_version}</strong>
        </div>
        <div>
          <span>{t("research:benchmark")}</span>
          <strong>{run.data.benchmark_id}</strong>
        </div>
        <div>
          <span>{t("common:created")}</span>
          <strong>{formatUtc(run.data.created_at)}</strong>
        </div>
        <div>
          <span>{t("research:gitCommit")}</span>
          <strong className="mono" title={run.data.git_commit}>
            {shortId(run.data.git_commit)}
          </strong>
        </div>
        <div>
          <span>{t("research:strategyConfig")}</span>
          <strong className="mono" title={run.data.strategy_config_hash}>
            {shortId(run.data.strategy_config_hash)}
          </strong>
        </div>
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:methodology")}</h2>
        </div>
        {metrics.loading && <LoadingPanel label={t("research:methodology")} />}
        {metrics.error && <ErrorPanel message={metrics.error} />}
        {metrics.data && <ResearchMetricGrid metrics={metrics.data.items} />}
        <p>{u.comparisonMetrics}</p>
      </section>
      <section
        className="panel experimentPanel"
        ref={filterAnchor}
        tabIndex={-1}
        aria-label={u.filterTitle}
      >
        <h2>{u.filterTitle}</h2>
        <p>{u.rangeHelp} · Asia/Shanghai</p>
        <form
          className="experimentActions"
          onSubmit={(event) => {
            event.preventDefault();
            if (start && end && start > end) {
              setInvalid(true);
              firstDate.current?.focus();
              return;
            }
            applyRange({
              ...(start ? { start_date: start } : {}),
              ...(end ? { end_date: end } : {}),
            });
          }}
        >
          <label>
            {c.start}
            <input
              type="date"
              ref={firstDate}
              value={start}
              aria-invalid={invalid || undefined}
              aria-describedby={invalid ? invalidRangeId : undefined}
              onInput={(event) => {
                setStart(event.currentTarget.value);
                if (
                  !event.currentTarget.value ||
                  !end ||
                  event.currentTarget.value <= end
                )
                  setInvalid(false);
              }}
            />
          </label>
          <label>
            {c.end}
            <input
              type="date"
              value={end}
              aria-invalid={invalid || undefined}
              aria-describedby={invalid ? invalidRangeId : undefined}
              onInput={(event) => {
                setEnd(event.currentTarget.value);
                if (
                  !start ||
                  !event.currentTarget.value ||
                  start <= event.currentTarget.value
                )
                  setInvalid(false);
              }}
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
              applyRange({});
            }}
          >
            {u.reset}
          </button>
        </form>
        {invalid && (
          <p id={invalidRangeId} role="alert">
            {u.invalidRange}
          </p>
        )}
        <p role="status">
          {filtered
            ? `${range.start_date ?? u.noStartLimit} — ${range.end_date ?? u.noEndLimit}`
            : u.fullSavedInterval}
        </p>
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>
            {t("research:equity")} / {t("research:benchmarkCurve")}
          </h2>
          <label className="metricPrecision">
            <input
              type="checkbox"
              checked={showBenchmark}
              onChange={(event) => setShowBenchmark(event.target.checked)}
            />
            {t("research:showBenchmark")}
          </label>
        </div>
        {curves.loading ? (
          <LoadingPanel label={t("research:equity")} />
        ) : curves.error ? (
          <ErrorPanel message={curves.error} />
        ) : !curves.data?.equity.items.length ? (
          <EmptyState>
            {filtered ? u.filteredEmpty : t("common:noData")}
          </EmptyState>
        ) : (
          <>
            <BenchmarkChart
              key={curveOffset}
              strategy={curves.data.equity.items}
              benchmark={curves.data.benchmark.items}
              showBenchmark={showBenchmark}
              selectedDate={activeDate}
              onSelectDate={setSelectedDate}
            />
            <p className="researchChartRange">
              {t("research:displayedDateRange", {
                start: curves.data.equity.items[0].trading_date,
                end: curves.data.equity.items.at(-1)?.trading_date,
              })}
            </p>
            <button
              className="button secondary"
              type="button"
              onClick={() => {
                setActivityDate(activeDate);
                resetRecordOffsets();
                activityAnchor.current?.focus();
              }}
            >
              {u.inspectActivity}
            </button>
          </>
        )}
        <Pagination
          offset={curveOffset}
          limit={200}
          total={curves.data?.equity.total ?? null}
          loading={curves.loading}
          label={`${t("research:equity")} / ${t("research:benchmarkCurve")}`}
          onChange={setCurveOffset}
        />
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:drawdown")}</h2>
        </div>
        {curves.loading ? (
          <LoadingPanel label={t("research:drawdown")} />
        ) : curves.error ? (
          <ErrorPanel message={curves.error} />
        ) : curves.data?.drawdown.items.length ? (
          <DrawdownChart
            key={curveOffset}
            points={curves.data.drawdown.items}
            selectedDate={activeDate}
            onSelectDate={setSelectedDate}
          />
        ) : (
          <EmptyState>
            {filtered ? u.filteredEmpty : t("common:noData")}
          </EmptyState>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:monthlyReturns")}</h2>
        </div>
        <p>{u.comparisonMetrics}</p>
        {monthly.loading ? (
          <LoadingPanel label={t("research:monthlyReturns")} />
        ) : monthly.error ? (
          <ErrorPanel message={monthly.error} />
        ) : monthly.data?.items.length ? (
          <MonthlyReturnHeatmap values={monthly.data.items} />
        ) : (
          <EmptyState>{t("common:noData")}</EmptyState>
        )}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{t("research:rollingMetrics")}</h2>
        </div>
        {rolling.loading ? (
          <LoadingPanel label={t("research:rollingMetrics")} />
        ) : rolling.error ? (
          <ErrorPanel message={rolling.error} />
        ) : rollingSharpe.length || rollingDrawdown.length ? (
          <>
            <BenchmarkChart
              key={rollingOffset}
              strategy={rollingSharpe}
              benchmark={rollingDrawdown}
              strategyLabel={t("metrics:sharpe_ratio")}
              benchmarkLabel={t("research:rollingDrawdown")}
              ariaLabel={t("accessibility:rollingChart")}
            />
            <p className="researchChartRange">
              {t("research:displayedDateRange", {
                start: rollingSharpe[0]?.trading_date,
                end: rollingSharpe.at(-1)?.trading_date,
              })}
            </p>
          </>
        ) : (
          <EmptyState>{t("common:noData")}</EmptyState>
        )}
        <Pagination
          offset={rollingOffset}
          limit={200}
          total={rolling.data?.total ?? null}
          loading={rolling.loading}
          label={t("research:rollingMetrics")}
          onChange={setRollingOffset}
        />
      </section>
      <section
        className="panel experimentPanel"
        ref={activityAnchor}
        tabIndex={-1}
        aria-label={u.focusedDate}
      >
        <h2>{u.focusedDate}</h2>
        <p role="status">
          {activityDate
            ? `${activityDate} · Asia/Shanghai`
            : filtered
              ? `${range.start_date ?? u.noStartLimit} — ${range.end_date ?? u.noEndLimit} · Asia/Shanghai`
              : u.fullSavedInterval}
        </p>
        {activityDate && (
          <button
            className="button secondary"
            type="button"
            onClick={() => {
              setActivityDate("");
              resetRecordOffsets();
              filterAnchor.current?.focus();
            }}
          >
            {u.clearFocus}
          </button>
        )}
      </section>
      <ResearchTable
        title={t("research:holdings")}
        emptyMessage={activityDate || filtered ? u.filteredEmpty : undefined}
        loading={holdings.loading}
        error={holdings.error}
        offset={holdingsOffset}
        total={holdings.data?.total ?? null}
        onChange={setHoldingsOffset}
        headings={[
          t("research:columns.date"),
          t("research:columns.security"),
          t("research:columns.quantity"),
          t("research:columns.weight"),
          t("research:columns.marketValue"),
        ]}
        rows={
          holdings.data?.items.map((item) => [
            item.trading_date,
            item.security_id,
            formatDecimal(item.quantity),
            formatPercent(item.weight),
            formatDecimal(item.market_value),
          ]) ?? []
        }
      />
      <ResearchTable
        title={t("research:rebalances")}
        emptyMessage={activityDate || filtered ? u.filteredEmpty : undefined}
        loading={rebalances.loading}
        error={rebalances.error}
        offset={rebalancesOffset}
        total={rebalances.data?.total ?? null}
        onChange={setRebalancesOffset}
        headings={[
          t("research:columns.date"),
          t("research:columns.turnover"),
          t("research:columns.transactionCost"),
        ]}
        rows={
          rebalances.data?.items.map((item) => [
            item.trading_date,
            formatPercent(item.turnover),
            formatDecimal(item.transaction_cost),
          ]) ?? []
        }
      />
      <ResearchTable
        title={t("research:trades")}
        emptyMessage={activityDate || filtered ? u.filteredEmpty : undefined}
        loading={trades.loading}
        error={trades.error}
        offset={tradesOffset}
        total={trades.data?.total ?? null}
        onChange={setTradesOffset}
        headings={[
          t("research:columns.utcTime"),
          t("research:columns.security"),
          t("research:columns.side"),
          t("research:columns.quantity"),
          t("research:columns.price"),
          t("research:columns.cost"),
        ]}
        rows={
          trades.data?.items.map((item) => [
            formatUtc(item.timestamp),
            item.security_id,
            t(`paper:detail.directions.${item.side}`, {
              defaultValue: item.side,
            }),
            formatDecimal(item.quantity),
            formatDecimal(item.price),
            formatDecimal(item.transaction_cost),
          ]) ?? []
        }
      />
      <section className="researchNotes">
        <article>
          <h2>{t("research:knownLimitations")}</h2>
          <p>
            {knownLimitations === FORMAL_KNOWN_LIMITATIONS
              ? t("research:formalKnownLimitations")
              : knownLimitations
                ? String(knownLimitations)
                : t("common:noData")}
          </p>
        </article>
        <article>
          <h2>{t("research:reproducibility")}</h2>
          <p>{t("research:reproduceCommand")}</p>
          <code>
            python backend/scripts/reproduce_research.py --run-id {runId}
          </code>
        </article>
      </section>
    </>
  );
}

function ResearchTable({
  title,
  headings,
  rows,
  loading,
  error,
  offset,
  total,
  onChange,
  emptyMessage,
}: {
  title: string;
  headings: string[];
  rows: string[][];
  loading: boolean;
  error: Error | null;
  offset: number;
  total: number | null;
  onChange: (offset: number) => void;
  emptyMessage?: string;
}) {
  const { t } = useTranslation("common");
  return (
    <section className="panel">
      <div className="panelHeader">
        <h2>{title}</h2>
      </div>
      {loading ? (
        <LoadingPanel label={title} />
      ) : error ? (
        <ErrorPanel message={error} />
      ) : rows.length === 0 ? (
        <EmptyState>{emptyMessage ?? t("noData")}</EmptyState>
      ) : (
        <div
          className="tableScroll"
          tabIndex={0}
          aria-label={`${title} — ${t("research:scrollTable")}`}
        >
          <table aria-label={title}>
            <thead>
              <tr>
                {headings.map((heading) => (
                  <th scope="col" key={heading}>
                    {heading}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((row, index) => (
                <tr key={index}>
                  {row.map((value, column) => (
                    <td key={`${column}-${value}`}>{value}</td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <Pagination
        offset={offset}
        limit={200}
        total={total}
        loading={loading}
        label={title}
        onChange={onChange}
      />
    </section>
  );
}
