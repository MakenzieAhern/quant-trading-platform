import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../components/Link";
import { Pagination } from "../components/Pagination";
import { useApiResource } from "../hooks/useApiResource";
import { experimentApi } from "./experiments/api";
import { marketApi, securityName } from "./markets/api";
import { useProductCopy } from "./copy";
import { Dialog } from "./Dialog";
import { ProductError } from "./ProductPages";

export function CommandPalette({ onClose }: { onClose: () => void }) {
  const copy = useProductCopy();
  const { i18n } = useTranslation();
  const searchInput = useRef<HTMLInputElement>(null);
  useEffect(() => searchInput.current?.focus(), []);
  const [query, setQuery] = useState("");
  const [search, setSearch] = useState({
    q: "",
    jobsOffset: 0,
    watchOffset: 0,
  });
  const [revision, setRevision] = useState(0);
  useEffect(() => {
    if (query.trim() === search.q) return;
    const timer = window.setTimeout(
      () => setSearch({ q: query.trim(), jobsOffset: 0, watchOffset: 0 }),
      250,
    );
    return () => window.clearTimeout(timer);
  }, [query, search.q]);
  const waiting = query.trim() !== search.q;
  const capabilities = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [revision],
  );
  const jobs = useApiResource(
    (signal) => experimentApi.list(signal, 20, search.jobsOffset, search.q),
    [search.q, search.jobsOffset, revision],
  );
  const watches = useApiResource(
    (signal) => marketApi.watchlist(search.watchOffset, signal, search.q),
    [search.q, search.watchOffset, revision],
  );
  const searchError = capabilities.error ?? jobs.error ?? watches.error;
  const commands = [
    { label: copy.home, href: "/" },
    { label: copy.markets, href: "/markets" },
    ...(window.location.pathname === "/research/new"
      ? []
      : [{ label: copy.start, href: "/research/new?new=1" }]),
    { label: copy.strategies, href: "/strategies" },
    { label: copy.research, href: "/experiments" },
    { label: copy.tasks, href: "/tasks" },
    { label: copy.archive, href: "/research/a-share" },
    { label: copy.accounts, href: "/paper" },
    { label: copy.data, href: "/data" },
    { label: copy.help, href: "/help" },
    { label: copy.settings, href: "/settings" },
    ...(capabilities.data?.strategies ?? []).map((item) => ({
      label: i18n.language.startsWith("zh") ? item.name_zh : item.name_en,
      href: `/strategies/${encodeURIComponent(item.strategy_id)}`,
    })),
  ].filter((item) =>
    item.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()),
  );
  return (
    <Dialog title={copy.search} onClose={onClose}>
      <label>
        <span className="srOnly">{copy.search}</span>
        <input
          ref={searchInput}
          type="search"
          maxLength={80}
          value={query}
          onChange={(event) => setQuery(event.target.value.slice(0, 80))}
          onKeyDown={(event) => {
            if (event.key === "Escape") {
              event.preventDefault();
              event.stopPropagation();
              onClose();
            }
          }}
          placeholder={copy.search}
        />
      </label>
      <p>{copy.searchScope}</p>
      {searchError && (
        <ProductError
          error={searchError}
          fallback={copy.searchFailed}
          retryLabel={copy.retry}
          retry={() => {
            searchInput.current?.focus();
            setRevision((value) => value + 1);
          }}
        />
      )}
      <nav className="commandResults" aria-label={copy.searchCommands}>
        {commands.map((item) => (
          <Link key={item.href} href={item.href} onClick={onClose}>
            {item.label}
            <span aria-hidden="true">↗</span>
          </Link>
        ))}
      </nav>
      <section aria-label={copy.searchStudies}>
        <h3>{copy.searchStudies}</h3>
        {waiting || jobs.loading ? (
          <p role="status">{copy.loading}</p>
        ) : (
          jobs.data && (
            <>
              <p>
                {copy.searchMatches}: {jobs.data.total}
              </p>
              {jobs.data.total === 0 && <p>{copy.searchNoStudies}</p>}
              <nav className="commandResults" aria-label={copy.searchStudies}>
                {jobs.data.items.map((item) => (
                  <Link
                    key={item.job_id}
                    href={`/experiments/${item.job_id}`}
                    onClick={onClose}
                  >
                    {item.name}
                    <small>{item.job_id}</small>
                  </Link>
                ))}
              </nav>
              {jobs.data.total > 20 && <p>{copy.searchMore}</p>}
            </>
          )
        )}
        <Pagination
          label={copy.searchStudies}
          offset={search.jobsOffset}
          limit={20}
          total={waiting ? null : (jobs.data?.total ?? null)}
          loading={waiting || jobs.loading}
          onChange={(offset) =>
            setSearch((value) => ({ ...value, jobsOffset: offset }))
          }
        />
      </section>
      <section aria-label={copy.searchWatchlist}>
        <h3>{copy.searchWatchlist}</h3>
        {waiting || watches.loading ? (
          <p role="status">{copy.loading}</p>
        ) : (
          watches.data && (
            <>
              <p>
                {copy.searchMatches}: {watches.data.total}
              </p>
              {watches.data.total === 0 && <p>{copy.searchNoWatchlist}</p>}
              <nav className="commandResults" aria-label={copy.searchWatchlist}>
                {watches.data.items.map((item) => (
                  <Link
                    key={`${item.dataset_id}:${item.security_id}`}
                    href={`/markets?${new URLSearchParams({ dataset: item.dataset_id, q: item.security_id })}#${new URLSearchParams({ dataset: item.dataset_id, security: item.security_id })}`}
                    onClick={onClose}
                  >
                    <span>
                      {securityName(item.security)} · {item.security_id}
                      {!item.security.name &&
                        item.security.source_observed_name && (
                          <small> · {copy.searchObservedName}</small>
                        )}
                    </span>
                    <small>
                      {item.dataset_id}
                      {!item.source_available
                        ? ` · ${copy.searchSourceUnavailable}`
                        : ""}
                    </small>
                  </Link>
                ))}
              </nav>
              {watches.data.total > 20 && <p>{copy.searchMore}</p>}
            </>
          )
        )}
        <Pagination
          label={copy.searchWatchlist}
          offset={search.watchOffset}
          limit={20}
          total={waiting ? null : (watches.data?.total ?? null)}
          loading={waiting || watches.loading}
          onChange={(offset) =>
            setSearch((value) => ({ ...value, watchOffset: offset }))
          }
        />
      </section>
    </Dialog>
  );
}
