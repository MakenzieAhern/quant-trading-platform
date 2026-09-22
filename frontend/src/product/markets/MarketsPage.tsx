import { useEffect, useRef, useState } from "react";
import { Pagination } from "../../components/Pagination";
import { useApiResource } from "../../hooks/useApiResource";
import { formatUtc } from "../../utils/format";
import { Dialog } from "../Dialog";
import { usePageDataContext } from "../dataContext";
import { marketApi, securityName } from "./api";
import { boardLabel, useMarketCopy } from "./copy";
import { MarketDetail } from "./MarketDetail";
import type { MarketDataset, MarketRange, Security } from "./types";
import "./markets.css";

export function MarketsPage() {
  const c = useMarketCopy();
  const [revision, setRevision] = useState(0);
  const datasets = useApiResource(
    (signal) => marketApi.datasets(signal),
    [revision],
  );
  return (
    <div className="marketWorkspace">
      <header>
        <h1>{c.title}</h1>
        <p>{c.intro}</p>
      </header>
      <p className="marketNotice">{c.cacheOnly}</p>
      {datasets.loading && <p role="status">{c.loading}</p>}
      {datasets.error && (
        <div role="alert">
          <p>{c.error}</p>
          <button
            className="button secondary"
            onClick={() => setRevision((n) => n + 1)}
          >
            {c.retry}
          </button>
        </div>
      )}
      {datasets.data && <MarketWorkspace datasets={datasets.data} />}
    </div>
  );
}

function MarketWorkspace({ datasets }: { datasets: MarketDataset[] }) {
  const c = useMarketCopy();
  const [datasetId, setDatasetId] = useState(
    () =>
      (
        datasets.find(
          (d) => d.available && d.mode === "historical_exploration",
        ) ??
        datasets.find((d) => d.available) ??
        datasets[0]
      )?.dataset_id ?? "",
  );
  const dataset = datasets.find((d) => d.dataset_id === datasetId);
  const [q, setQ] = useState(
    () =>
      new URLSearchParams(window.location.search).get("q")?.slice(0, 80) ?? "",
  );
  const [query, setQuery] = useState(q);
  const [exchange, setExchange] = useState("ALL");
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [watchOffset, setWatchOffset] = useState(0);
  const [watchRevision, setWatchRevision] = useState(0);
  const [selected, setSelected] = useState<{
    security: Security;
    dataset: MarketDataset;
  } | null>(null);
  const [ranges, setRanges] = useState<Record<string, MarketRange>>({});
  const [pending, setPending] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<"saved" | "removed" | "error" | null>(
    null,
  );
  const lock = useRef(false);
  const displayedSource = selected?.dataset ?? dataset;
  usePageDataContext(
    displayedSource?.mode ?? null,
    displayedSource?.as_of ?? null,
    "snapshot",
  );
  const results = useApiResource(
    (signal) =>
      dataset?.available
        ? marketApi.search(dataset.dataset_id, query, exchange, offset, signal)
        : Promise.resolve(null),
    [
      dataset?.dataset_id,
      dataset?.available,
      query,
      exchange,
      offset,
      revision,
    ],
  );
  const watchlist = useApiResource(
    (signal) => marketApi.watchlist(watchOffset, signal),
    [watchOffset, watchRevision],
  );
  useEffect(() => {
    const update = () => {
      const value =
        new URLSearchParams(window.location.search).get("q")?.slice(0, 80) ??
        "";
      setQ(value);
      setQuery(value);
      setOffset(0);
      setSelected(null);
    };
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  async function changeWatchlist(
    kind: "add" | "remove",
    source: string,
    id: string,
  ) {
    if (lock.current) return;
    lock.current = true;
    setPending(`${kind}:${source}:${id}`);
    setOutcome(null);
    try {
      if (kind === "add") {
        await marketApi.add(source, id);
        setWatchOffset(0);
      } else {
        await marketApi.remove(source, id);
        if (watchlist.data?.items.length === 1 && watchOffset > 0)
          setWatchOffset(Math.max(0, watchOffset - 20));
      }
      setOutcome(kind === "add" ? "saved" : "removed");
      setWatchRevision((n) => n + 1);
    } catch {
      setOutcome("error");
    } finally {
      lock.current = false;
      setPending(null);
    }
  }
  const mode = (d: MarketDataset) =>
    d.mode === "synthetic_demo" ? c.demo : c.historical;
  const inspect = (security: Security, d: MarketDataset) =>
    setSelected({ security, dataset: d });
  return (
    <>
      <section className="marketPanel">
        <label className="marketField">
          {c.dataset}
          <select
            value={datasetId}
            onChange={(event) => {
              setDatasetId(event.target.value);
              setOffset(0);
            }}
          >
            {datasets.map((d) => (
              <option key={d.dataset_id} value={d.dataset_id}>
                {mode(d)} · {d.dataset_id}
                {d.available ? "" : ` · ${c.unavailable}`}
              </option>
            ))}
          </select>
        </label>
        {dataset && (
          <>
            <p className="marketMode">{mode(dataset)}</p>
            <p>
              {dataset.mode === "synthetic_demo"
                ? c.demoWarning
                : c.historicalWarning}
            </p>
            <p>
              {c.coverage}: {dataset.coverage_start} → {dataset.coverage_end} ·
              Asia/Shanghai
            </p>
            <p>
              {c.asOf}: {dataset.as_of ?? c.notRecorded}
            </p>
          </>
        )}
        {(!dataset || !dataset.available) && (
          <div role="status">
            <p>
              {c.unavailable}. {c.sourceUnavailableHelp}
            </p>
            {dataset?.reason_code && <code>{dataset.reason_code}</code>}
          </div>
        )}
      </section>
      <section className="marketPanel" aria-label={c.search}>
        <h2>{c.search}</h2>
        <p className="marketHelp">{c.searchHelp}</p>
        <form
          className="marketControls"
          onSubmit={(event) => {
            event.preventDefault();
            setQuery(q.trim());
            setOffset(0);
          }}
        >
          <label className="marketField marketSearchField">
            {c.searchLabel}
            <input
              type="search"
              maxLength={80}
              value={q}
              onChange={(event) => setQ(event.target.value)}
            />
          </label>
          <label className="marketField">
            {c.exchange}
            <select
              value={exchange}
              onChange={(event) => {
                setExchange(event.target.value);
                setOffset(0);
              }}
            >
              <option value="ALL">{c.all}</option>
              <option value="SSE">{c.sse}</option>
              <option value="SZSE">{c.szse}</option>
            </select>
          </label>
          <button className="button" disabled={!dataset?.available}>
            {c.search}
          </button>
        </form>
        {dataset?.available && results.loading && (
          <p role="status">{c.loading}</p>
        )}
        {results.error && (
          <div role="alert">
            <p>{c.error}</p>
            <button
              className="button secondary"
              onClick={() => setRevision((n) => n + 1)}
            >
              {c.retry}
            </button>
          </div>
        )}
        {results.data && dataset && (
          <>
            <p className="marketHelp">
              {c.provider}: {results.data.metadata.provider} ·{" "}
              {results.data.metadata.provider_version} · {c.retrieved}:{" "}
              {results.data.metadata.retrieved_at_utc
                ? formatUtc(results.data.metadata.retrieved_at_utc)
                : c.notRecorded}
            </p>
            {results.data.items.length === 0 ? (
              <p>{c.empty}</p>
            ) : (
              <>
                <p className="marketHelp">{c.scroll}</p>
                <div
                  className="marketTableScroll"
                  tabIndex={0}
                  aria-label={c.search}
                >
                  <table>
                    <thead>
                      <tr>
                        <th scope="col">{c.security}</th>
                        <th scope="col">{c.name}</th>
                        <th scope="col">{c.exchange}</th>
                        <th scope="col">{c.board}</th>
                        <th scope="col">{c.watchlist}</th>
                      </tr>
                    </thead>
                    <tbody>
                      {results.data.items.map((item) => (
                        <tr key={item.security_id}>
                          <th scope="row">
                            <button
                              className="marketTextButton"
                              onClick={() => inspect(item, dataset)}
                              aria-label={`${c.inspect}: ${item.security_id}`}
                            >
                              {item.symbol}
                            </button>
                            <small>{item.security_id}</small>
                          </th>
                          <td>{securityName(item)}</td>
                          <td>{item.exchange === "SSE" ? c.sse : item.exchange === "SZSE" ? c.szse : item.exchange}</td>
                          <td>{boardLabel(item.board, c)}</td>
                          <td>
                            <button
                              className="button secondary"
                              disabled={pending !== null}
                              onClick={() =>
                                void changeWatchlist(
                                  "add",
                                  datasetId,
                                  item.security_id,
                                )
                              }
                            >
                              {pending ===
                              `add:${datasetId}:${item.security_id}`
                                ? c.saving
                                : c.save}
                            </button>
                          </td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              </>
            )}
            <Pagination
              offset={results.data.offset}
              limit={results.data.limit}
              total={results.data.total}
              onChange={setOffset}
            />
          </>
        )}
      </section>
      <section className="marketPanel" aria-label={c.watchlist}>
        <h2>{c.watchlist}</h2>
        <p className="marketHelp">{c.watchlistHelp}</p>
        {outcome && (
          <p role={outcome === "error" ? "alert" : "status"}>
            {outcome === "saved"
              ? c.saved
              : outcome === "removed"
                ? c.removed
                : c.saveError}
          </p>
        )}
        {watchlist.loading && <p role="status">{c.loading}</p>}
        {watchlist.error && (
          <div role="alert">
            <p>{c.error}</p>
            <button
              className="button secondary"
              onClick={() => setWatchRevision((n) => n + 1)}
            >
              {c.retry}
            </button>
          </div>
        )}
        {watchlist.data && (
          <>
            {watchlist.data.items.length === 0 && <p>{c.watchlistEmpty}</p>}
            <div className="marketWatchlist">
              {watchlist.data.items.map((item) => {
                const source = datasets.find(
                  (d) => d.dataset_id === item.dataset_id,
                );
                const canRead = item.source_available && source?.available;
                return (
                  <article
                    className="marketWatchItem"
                    key={`${item.dataset_id}:${item.security_id}`}
                  >
                    <div>
                      <h3>
                        {securityName(item.security)} · {item.security.symbol}
                      </h3>
                      <p className="marketHelp">
                        {source ? mode(source) : c.unavailable} ·{" "}
                        {item.dataset_id}
                      </p>
                      <p className="marketHelp">
                        {c.savedAt}: {formatUtc(item.added_at)}
                      </p>
                      {!canRead && <p>{c.archivedSource}</p>}
                    </div>
                    <div className="marketControls">
                      <button
                        className="button secondary"
                        disabled={!canRead}
                        onClick={() => source && inspect(item.security, source)}
                      >
                        {c.inspect}
                      </button>
                      <button
                        className="button secondary"
                        disabled={pending !== null}
                        onClick={() =>
                          void changeWatchlist(
                            "remove",
                            item.dataset_id,
                            item.security_id,
                          )
                        }
                      >
                        {pending ===
                        `remove:${item.dataset_id}:${item.security_id}`
                          ? c.removing
                          : c.remove}
                      </button>
                    </div>
                  </article>
                );
              })}
            </div>
            <Pagination
              offset={watchlist.data.offset}
              limit={watchlist.data.limit}
              total={watchlist.data.total}
              onChange={setWatchOffset}
            />
          </>
        )}
      </section>
      {selected && (
        <Dialog
          title={`${securityName(selected.security)} · ${selected.security.symbol}`}
          onClose={() => setSelected(null)}
        >
          <MarketDetail
            key={`${selected.dataset.dataset_id}:${selected.security.security_id}`}
            security={selected.security}
            dataset={selected.dataset}
            range={
              ranges[selected.dataset.dataset_id] ?? {
                start_date: selected.dataset.default_start,
                end_date: selected.dataset.default_end,
              }
            }
            onRangeChange={(range) =>
              setRanges((previous) => ({
                ...previous,
                [selected.dataset.dataset_id]: range,
              }))
            }
          />
        </Dialog>
      )}
    </>
  );
}
