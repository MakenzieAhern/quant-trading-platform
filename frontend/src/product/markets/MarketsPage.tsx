import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Pagination } from "../../components/Pagination";
import { Link } from "../../components/Link";
import { useApiResource } from "../../hooks/useApiResource";
import { formatUtc } from "../../utils/format";
import { navigate, replaceUrl } from "../../utils/navigation";
import { Dialog } from "../Dialog";
import { ProductError } from "../ProductPages";
import { usePageDataContext } from "../dataContext";
import { explainExperimentCode } from "../experiments/codes";
import { marketApi, securityName } from "./api";
import { boardLabel, useMarketCopy } from "./copy";
import { MarketDetail } from "./MarketDetail";
import type { MarketDataset, MarketRange, Security } from "./types";
import "./markets.css";

function detailFromHash(hash: string) {
  const params = new URLSearchParams(hash.slice(1));
  const datasetId = params.get("dataset");
  const securityId = params.get("security");
  return datasetId && securityId ? { datasetId, securityId } : null;
}

function exchangeFromUrl() {
  const value = new URLSearchParams(window.location.search).get("exchange");
  return value === "SSE" || value === "SZSE" ? value : "ALL";
}

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
      <p className="marketNotice">
        {c.cacheOnly} <Link href="/data">{c.updatesLink}</Link>
      </p>
      {datasets.loading && <p role="status">{c.loading}</p>}
      {datasets.error && (
        <ProductError
          error={datasets.error}
          fallback={c.error}
          retryLabel={c.retry}
          retry={() => setRevision((n) => n + 1)}
        />
      )}
      {datasets.data && <MarketWorkspace datasets={datasets.data} />}
    </div>
  );
}

function MarketWorkspace({ datasets }: { datasets: MarketDataset[] }) {
  const c = useMarketCopy();
  const { i18n } = useTranslation();
  const defaultDatasetId =
    (
      datasets.find(
        (d) => d.available && d.mode === "historical_exploration",
      ) ??
      datasets.find((d) => d.available) ??
      datasets[0]
    )?.dataset_id ?? "";
  const [datasetId, setDatasetId] = useState(
    () =>
      new URLSearchParams(window.location.search).get("dataset") ??
      defaultDatasetId,
  );
  const dataset = datasets.find((d) => d.dataset_id === datasetId);
  const [q, setQ] = useState(
    () =>
      new URLSearchParams(window.location.search).get("q")?.slice(0, 80) ?? "",
  );
  const [query, setQuery] = useState(q);
  const draftPending = q.trim() !== query;
  const [exchange, setExchange] = useState(exchangeFromUrl);
  const [offset, setOffset] = useState(0);
  const [revision, setRevision] = useState(0);
  const [watchOffset, setWatchOffset] = useState(0);
  const [watchRevision, setWatchRevision] = useState(0);
  const [detailHash, setDetailHash] = useState(window.location.hash);
  const [selected, setSelected] = useState<{
    security: Security;
    dataset: MarketDataset;
  } | null>(null);
  const [detailError, setDetailError] = useState<Error | null>(null);
  const [detailRevision, setDetailRevision] = useState(0);
  const [ranges, setRanges] = useState<Record<string, MarketRange>>({});
  const [pending, setPending] = useState<string | null>(null);
  const [outcome, setOutcome] = useState<"saved" | "removed" | "error" | null>(
    null,
  );
  const lock = useRef(false);
  const watchlistSection = useRef<HTMLElement>(null);
  const lastSearch = useRef(window.location.search);
  const persistFilters = (source: string, term: string, venue: string) => {
    const params = new URLSearchParams(window.location.search);
    params.set("dataset", source);
    if (term) params.set("q", term);
    else params.delete("q");
    if (venue !== "ALL") params.set("exchange", venue);
    else params.delete("exchange");
    replaceUrl(`${window.location.pathname}?${params}${window.location.hash}`);
    lastSearch.current = window.location.search;
  };
  const detail = detailFromHash(detailHash);
  const detailDatasetId = detail?.datasetId ?? "";
  const detailSecurityId = detail?.securityId ?? "";
  const detailSource = datasets.find((d) => d.dataset_id === detailDatasetId);
  const canResolveDetail =
    !!detailSource?.available &&
    /^CN-A:(SSE|SZSE):\d{6}$/.test(detailSecurityId);
  const activeSelection =
    detail &&
    selected?.dataset.dataset_id === detail.datasetId &&
    selected.security.security_id === detail.securityId
      ? selected
      : null;
  const displayedSource = activeSelection?.dataset ?? dataset;
  usePageDataContext(
    displayedSource?.mode ?? null,
    displayedSource?.as_of ?? null,
    "snapshot",
  );
  const results = useApiResource(
    (signal) =>
      dataset?.available && !draftPending
        ? marketApi.search(dataset.dataset_id, query, exchange, offset, signal)
        : Promise.resolve(null),
    [
      dataset?.dataset_id,
      dataset?.available,
      draftPending,
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
      if (window.location.search !== lastSearch.current) {
        lastSearch.current = window.location.search;
        const params = new URLSearchParams(window.location.search);
        const value = params.get("q")?.slice(0, 80) ?? "";
        setQ(value);
        setQuery(value);
        setDatasetId(params.get("dataset") ?? defaultDatasetId);
        setExchange(exchangeFromUrl());
        setOffset(0);
      }
      setDetailError(null);
      setDetailHash(window.location.hash);
    };
    window.addEventListener("popstate", update);
    window.addEventListener("hashchange", update);
    return () => {
      window.removeEventListener("popstate", update);
      window.removeEventListener("hashchange", update);
    };
  }, [defaultDatasetId]);
  useEffect(() => {
    if (!canResolveDetail || activeSelection || !detailSource) return;
    const controller = new AbortController();
    let active = true;
    void marketApi
      .search(detailDatasetId, detailSecurityId, "ALL", 0, controller.signal)
      .then((page) => {
        if (!active) return;
        const security = page.items.find(
          (item) => item.security_id === detailSecurityId,
        );
        if (security) setSelected({ security, dataset: detailSource });
        else setDetailError(new Error("Security not found"));
      })
      .catch((reason: unknown) => {
        if (active)
          setDetailError(
            reason instanceof Error ? reason : new Error("Detail read failed"),
          );
      });
    return () => {
      active = false;
      controller.abort();
    };
  }, [
    activeSelection,
    canResolveDetail,
    detailDatasetId,
    detailSecurityId,
    detailSource,
    detailRevision,
  ]);
  async function changeWatchlist(
    kind: "add" | "remove",
    source: string,
    id: string,
    trigger?: HTMLButtonElement,
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
        if (document.activeElement === trigger)
          watchlistSection.current?.focus();
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
  const inspect = (security: Security, d: MarketDataset) => {
    const hash = `#${new URLSearchParams({ dataset: d.dataset_id, security: security.security_id })}`;
    navigate(`${window.location.pathname}${window.location.search}${hash}`);
    window.history.replaceState(
      { ...window.history.state, productMarketDetail: true },
      "",
      window.location.href,
    );
    setSelected({ security, dataset: d });
    setDetailHash(hash);
  };
  const closeDetail = () => {
    if (window.history.state?.productMarketDetail) window.history.back();
    else {
      replaceUrl(window.location.pathname + window.location.search);
      setDetailHash("");
    }
  };
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
              persistFilters(event.target.value, query, exchange);
            }}
          >
            {!dataset && (
              <option value={datasetId} disabled>
                {c.unavailable} · {datasetId}
              </option>
            )}
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
            {dataset?.reason_code && (
              <>
                <p>
                  {explainExperimentCode(dataset.reason_code, i18n.language)}
                </p>
                <details className="technicalDetails">
                  <summary>{c.lineage}</summary>
                  <code>{dataset.reason_code}</code>
                </details>
              </>
            )}
          </div>
        )}
        {dataset?.available && dataset.execution_available === false && (
          <p role="status">
            {explainExperimentCode(
              dataset.execution_reason_code ?? "DATASET_EXECUTION_NOT_ACCEPTED",
              i18n.language,
            )}
          </p>
        )}
      </section>
      <section className="marketPanel" aria-label={c.search}>
        <h2>{c.search}</h2>
        <p className="marketHelp">{c.searchHelp}</p>
        <form
          className="marketControls"
          onSubmit={(event) => {
            event.preventDefault();
            const term = q.trim();
            setQuery(term);
            setOffset(0);
            persistFilters(datasetId, term, exchange);
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
                persistFilters(datasetId, query, event.target.value);
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
        {dataset?.available && draftPending && (
          <p role="status">{c.pendingSearch}</p>
        )}
        {dataset?.available && !draftPending && results.loading && (
          <p role="status">{c.loading}</p>
        )}
        {!draftPending && results.error && (
          <ProductError
            error={results.error}
            fallback={c.error}
            retryLabel={c.retry}
            retry={() => setRevision((n) => n + 1)}
          />
        )}
        {!draftPending && results.data && dataset && (
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
                  role="region"
                  aria-label={`${c.search} · ${c.scroll}`}
                >
                  <table aria-label={c.search}>
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
                          <td>
                            {item.exchange === "SSE"
                              ? c.sse
                              : item.exchange === "SZSE"
                                ? c.szse
                                : item.exchange}
                          </td>
                          <td>{boardLabel(item.board, c)}</td>
                          <td>
                            <button
                              className="button secondary"
                              aria-disabled={pending !== null}
                              aria-label={`${pending === `add:${datasetId}:${item.security_id}` ? c.saving : c.save}: ${item.security_id}`}
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
          </>
        )}
        {!draftPending && (
          <Pagination
            label={c.search}
            offset={offset}
            limit={results.data?.limit ?? 20}
            total={results.data?.total ?? null}
            loading={results.loading && !!dataset?.available}
            onChange={setOffset}
          />
        )}
      </section>
      <section
        className="marketPanel"
        aria-label={c.watchlist}
        ref={watchlistSection}
        tabIndex={-1}
      >
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
          <ProductError
            error={watchlist.error}
            fallback={c.error}
            retryLabel={c.retry}
            retry={() => setWatchRevision((n) => n + 1)}
          />
        )}
        {watchlist.data && (
          <>
            {watchlist.data.items.length === 0 && <p>{c.watchlistEmpty}</p>}
            <div className="marketWatchlist">
              {watchlist.data.items.map((item) => {
                const source = datasets.find(
                  (d) => d.dataset_id === item.dataset_id,
                );
                const canRead =
                  item.source_available &&
                  source?.available &&
                  item.dataset_sha256 === source.sha256;
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
                        aria-label={`${c.inspect}: ${item.security_id} · ${item.dataset_id}`}
                        onClick={() => source && inspect(item.security, source)}
                      >
                        {c.inspect}
                      </button>
                      <button
                        className="button secondary"
                        aria-disabled={pending !== null}
                        aria-label={`${pending === `remove:${item.dataset_id}:${item.security_id}` ? c.removing : c.remove}: ${item.security_id} · ${item.dataset_id}`}
                        onClick={(event) =>
                          void changeWatchlist(
                            "remove",
                            item.dataset_id,
                            item.security_id,
                            event.currentTarget,
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
          </>
        )}
        <Pagination
          label={c.watchlist}
          offset={watchOffset}
          limit={watchlist.data?.limit ?? 20}
          total={watchlist.data?.total ?? null}
          loading={watchlist.loading}
          onChange={setWatchOffset}
        />
      </section>
      {detail && !activeSelection && (
        <div>
          {detailError ? (
            <ProductError
              error={detailError}
              fallback={c.detailUnavailable}
              retryLabel={c.retry}
              retry={() => {
                setDetailError(null);
                setDetailRevision((n) => n + 1);
              }}
            />
          ) : (
            <p role={!canResolveDetail ? "alert" : "status"}>
              {!canResolveDetail ? c.detailUnavailable : c.loading}
            </p>
          )}
          {(detailError || !canResolveDetail) && (
            <button className="button secondary" onClick={closeDetail}>
              {c.closeDetail}
            </button>
          )}
        </div>
      )}
      {activeSelection && (
        <Dialog
          title={`${securityName(activeSelection.security)} · ${activeSelection.security.symbol}`}
          onClose={closeDetail}
        >
          <MarketDetail
            key={`${activeSelection.dataset.dataset_id}:${activeSelection.security.security_id}`}
            security={activeSelection.security}
            dataset={activeSelection.dataset}
            range={
              ranges[activeSelection.dataset.dataset_id] ?? {
                start_date: activeSelection.dataset.default_start,
                end_date: activeSelection.dataset.default_end,
              }
            }
            onRangeChange={(range) =>
              setRanges((previous) => ({
                ...previous,
                [activeSelection.dataset.dataset_id]: range,
              }))
            }
          />
        </Dialog>
      )}
    </>
  );
}
