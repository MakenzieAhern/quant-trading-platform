import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";
import { ApiError } from "../api/client";
import { Link } from "../components/Link";
import { LanguageSelector } from "../components/LanguageSelector";
import { useApiResource } from "../hooks/useApiResource";
import { navigate } from "../utils/navigation";
import { experimentApi } from "./experiments/api";
import { readExperimentDraft } from "./experiments/draft";
import { explainExperimentCode } from "./experiments/codes";
import { useProductCopy } from "./copy";
import { Dialog } from "./Dialog";
import { usePreferences } from "./preferences";
import { MarketUpdatesPanel } from "./marketUpdates";

export function ProductError({
  error,
  retry,
}: {
  error: unknown;
  retry: () => void;
}) {
  const c = useProductCopy();
  const { t } = useTranslation("common");
  const reason =
    error instanceof ApiError
      ? error.status === 401 || error.status === 403
        ? "permission"
        : error.status === 408
          ? "timeout"
          : null
      : error instanceof TypeError
        ? "offline"
        : null;
  return (
    <div className="productError" role="alert">
      <p>{reason ? t(`loadErrors.${reason}`) : c.loadingError}</p>
      <button className="button secondary" onClick={retry}>
        {c.retry}
      </button>
    </div>
  );
}
export function ModeGuide() {
  const c = useProductCopy();
  return (
    <div className="modeGrid">
      {[
        [c.historical, c.historicalHelp],
        [c.replay, c.replayHelp],
        [c.demo, c.demoHelp],
        [c.forward, c.forwardHelp],
      ].map(([title, body]) => (
        <section key={title}>
          <h3>{title}</h3>
          <p>{body}</p>
        </section>
      ))}
    </div>
  );
}
export function WorkbenchPage() {
  const c = useProductCopy();
  const { i18n } = useTranslation();
  const [retry, setRetry] = useState(0);
  const data = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [retry],
  );
  const jobs = useApiResource(
    (signal) => experimentApi.list(signal, 4, 0),
    [retry],
  );
  const draft = readExperimentDraft();
  const [guide, setGuide] = useState(false);
  const historicalSource = data.data?.datasets.find(
    (item) => item.mode === "historical_exploration",
  );
  const history = historicalSource?.available ? historicalSource : undefined;
  return (
    <div className="productPage">
      <header className="workbenchHeading">
        <div>
          <p className="eyebrow">{c.welcome}</p>
          <h1>{c.home}</h1>
        </div>
        <span className="quietTag">{c.local}</span>
      </header>
      {draft && (
        <div className="draftBanner">
          <div>
            <strong>{draft.form.name || c.continueDraft}</strong>
            <span>{c.draftHint}</span>
          </div>
          <Link className="button secondary" href="/research/new">
            {c.continueDraft}
            <span aria-hidden="true">→</span>
          </Link>
        </div>
      )}
      <div className="welcomeGrid">
        <section className="welcomeCard">
          <span className="sectionIndex">01 / {c.strategies}</span>
          <h2>{c.lead}</h2>
          <p className="welcomeDescription">{c.intro}</p>
          <div className="welcomeActions">
            <Link className="button" href="/research/new">
              {c.start}
              <span aria-hidden="true">→</span>
            </Link>
            <Link className="textLink" href="/experiments">
              {c.existing}
            </Link>
          </div>
          <button className="textButton" onClick={() => setGuide(true)}>
            {c.guide} <span aria-hidden="true">↗</span>
          </button>
        </section>
        <aside className="dataOverview">
          <h2>{c.environment}</h2>
          {data.loading ? (
            <p role="status">{c.loading}</p>
          ) : data.error ? (
            <ProductError
              error={data.error}
              retry={() => setRetry(retry + 1)}
            />
          ) : (
            <>
              <span className="quietTag">
                {history ? c.historical : c.demo}
              </span>
              <p className="dataDateLabel">
                {history ? c.dataDate : c.dataUnavailable}
              </p>
              {history ? (
                <strong className="dataDate">
                  {history.as_of ?? c.notRecorded}
                </strong>
              ) : (
                <p>{c.dataUnavailableHint}</p>
              )}
              <p className="smallText">{history ? c.staleHint : c.demoHelp}</p>
              {!history && historicalSource?.reason_code && (
                <p className="inlineNotice">
                  {explainExperimentCode(
                    historicalSource.reason_code,
                    i18n.language,
                  )}
                </p>
              )}
              <Link className="textLink" href="/data">
                {c.dataInspect}
                <span aria-hidden="true">→</span>
              </Link>
            </>
          )}
        </aside>
      </div>
      <section className="stepsOverview" aria-label={c.guide}>
        {[
          [c.step1, c.step1Hint],
          [c.step2, c.step2Hint],
          [c.step3, c.step3Hint],
        ].map(([title, body], index) => (
          <article key={title}>
            <span className="stepNumber">0{index + 1}</span>
            <div>
              <h3>{title}</h3>
              <p>{body}</p>
            </div>
          </article>
        ))}
      </section>
      <section className="panel">
        <div className="panelHeader">
          <h2>{c.recent}</h2>
          <Link className="textLink" href="/experiments">
            {c.viewAll} →
          </Link>
        </div>
        {jobs.loading ? (
          <p className="panelState" role="status">
            {c.loading}
          </p>
        ) : jobs.error ? (
          <ProductError error={jobs.error} retry={() => setRetry(retry + 1)} />
        ) : jobs.data?.items.length ? (
          <div className="recentStudies">
            {jobs.data.items.map((job) => (
              <Link key={job.job_id} href={`/experiments/${job.job_id}`}>
                <div>
                  <strong>{job.name}</strong>
                  <span>
                    {job.configuration.start_date} —{" "}
                    {job.configuration.end_date}
                  </span>
                </div>
                <span className="quietTag">
                  {job.mode === "synthetic_demo" ? c.demo : c.historical}
                </span>
                <span aria-hidden="true">→</span>
              </Link>
            ))}
          </div>
        ) : (
          <div className="productEmpty">
            <span className="emptyGlyph" aria-hidden="true">
              ▤
            </span>
            <h3>{c.noRecent}</h3>
            <p>{c.noRecentHint}</p>
          </div>
        )}
      </section>
      <div className="archiveFootnote">
        <span>{c.noGuarantee}</span>
        <Link href="/research/a-share">{c.archive} ↗</Link>
      </div>
      {guide && (
        <Dialog
          title={c.guideTitle}
          onClose={() => {
            setGuide(false);
          }}
        >
          <ModeGuide />
          <button
            className="button"
            onClick={() => {
              setGuide(false);
              localStorage.setItem("quant.product.guide-seen", "1");
            }}
          >
            {c.skip}
          </button>
        </Dialog>
      )}
    </div>
  );
}
function StrategyContent() {
  const c = useProductCopy();
  return (
    <div className="strategyExplanation">
      {[
        [c.rules, c.rulesBody],
        [c.rebalance, c.rebalanceBody],
        [c.risks, c.risksBody],
        [c.parameters, c.parametersBody],
        [c.requirements, c.requirementsBody],
        [c.evidence, c.evidenceBody],
      ].map(([title, body]) => (
        <section key={title}>
          <h3>{title}</h3>
          <p>{body}</p>
        </section>
      ))}
    </div>
  );
}
function strategyDrawerFromUrl() {
  return new URLSearchParams(window.location.hash.slice(1)).get("strategy");
}
export function ProductStrategiesPage({ strategyId }: { strategyId?: string }) {
  const c = useProductCopy();
  const { i18n } = useTranslation();
  const [retry, setRetry] = useState(0);
  const catalog = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [retry],
  );
  const [selected, setSelected] = useState<string | null>(
    strategyDrawerFromUrl,
  );
  useEffect(() => {
    const sync = () => setSelected(strategyDrawerFromUrl());
    window.addEventListener("hashchange", sync);
    window.addEventListener("popstate", sync);
    return () => {
      window.removeEventListener("hashchange", sync);
      window.removeEventListener("popstate", sync);
    };
  }, []);
  const openDrawer = (id: string) => {
    navigate(
      `${window.location.pathname}${window.location.search}#${new URLSearchParams({ strategy: id })}`,
    );
    window.history.replaceState(
      { ...window.history.state, productStrategyDrawer: true },
      "",
      window.location.href,
    );
    setSelected(id);
  };
  const closeDrawer = () => {
    if (window.history.state?.productStrategyDrawer) window.history.back();
    else {
      window.history.replaceState(
        window.history.state,
        "",
        window.location.pathname + window.location.search,
      );
      setSelected(null);
    }
  };
  const strategy = catalog.data?.strategies.find(
    (item) => item.strategy_id === (strategyId ?? selected),
  );
  const name = strategy
    ? i18n.language.startsWith("zh")
      ? strategy.name_zh
      : strategy.name_en
    : c.strategyName;
  return (
    <div className="productPage">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">{c.strategies}</p>
          <h1>{strategyId ? name : c.strategyTitle}</h1>
          <p>{c.strategyIntro}</p>
        </div>
        {strategyId && strategy && (
          <Link className="button" href="/research/new">
            {c.configure} →
          </Link>
        )}
      </header>
      {catalog.loading && <p role="status">{c.loading}</p>}
      {catalog.error && (
        <ProductError error={catalog.error} retry={() => setRetry(retry + 1)} />
      )}
      {strategyId ? (
        strategy ? (
          <>
            <p className="quietTag">
              {c.registered} · v{strategy.version}
            </p>
            <StrategyContent />
            <details className="technicalDetails">
              <summary>{c.details}</summary>
              <p className="mono">{strategy.strategy_id}</p>
              <Link
                href={`/research/a-share/strategies/${strategy.strategy_id}`}
              >
                {c.fullMethod} ↗
              </Link>
            </details>
          </>
        ) : (
          !catalog.loading && !catalog.error && <p>{c.noStrategies}</p>
        )
      ) : (
        <div className="productStrategyCards">
          {catalog.data?.strategies.map((item) => (
            <article
              className="panel productStrategyCard"
              key={item.strategy_id}
            >
              <div className="strategySymbol" aria-hidden="true">
                ↗
              </div>
              <span className="quietTag">A-SHARE · v{item.version}</span>
              <h2>
                {i18n.language.startsWith("zh") ? item.name_zh : item.name_en}
              </h2>
              <p>{c.strategySummary}</p>
              <p className="smallText">{c.noGuarantee}</p>
              <button
                className="button secondary"
                onClick={() => openDrawer(item.strategy_id)}
              >
                {c.inspectStrategy} →
              </button>
            </article>
          ))}
        </div>
      )}
      {selected && strategy && (
        <Dialog title={name} drawer onClose={closeDrawer}>
          <p>{c.strategySummary}</p>
          <StrategyContent />
          <div className="drawerActions">
            <Link
              className="button"
              href="/research/new"
              onClick={() => setSelected(null)}
            >
              {c.configure}
            </Link>
            <Link
              className="textLink"
              href={`/strategies/${strategy.strategy_id}`}
              onClick={() => setSelected(null)}
            >
              {c.open} ↗
            </Link>
          </div>
        </Dialog>
      )}
    </div>
  );
}
export function DataCenterPage() {
  const c = useProductCopy();
  const { i18n } = useTranslation();
  const [retry, setRetry] = useState(0);
  const data = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [retry],
  );
  return (
    <div className="productPage">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">{c.mode}</p>
          <h1>{c.data}</h1>
          <p>{c.dataHint}</p>
        </div>
      </header>
      {data.loading && <p role="status">{c.loading}</p>}
      {data.error && (
        <ProductError error={data.error} retry={() => setRetry(retry + 1)} />
      )}
      {data.data?.datasets.map((item) => (
        <section className="panel dataSourceCard" key={item.dataset_id}>
          <div className="panelHeader">
            <h2>{item.mode === "synthetic_demo" ? c.demo : c.historical}</h2>
            <span className="quietTag">
              {item.available ? c.available : c.unavailable}
            </span>
          </div>
          <div className="dataFacts">
            <div>
              <span>{c.coverage}</span>
              <strong>
                {item.coverage_start ?? c.notRecorded} —{" "}
                {item.coverage_end ?? c.notRecorded}
              </strong>
            </div>
            <div>
              <span>{c.securities}</span>
              <strong>{item.security_count.toLocaleString()}</strong>
            </div>
            <div>
              <span>{c.dataDate}</span>
              <strong>{item.as_of ?? c.notRecorded}</strong>
            </div>
          </div>
          {!item.available && item.reason_code && (
            <p role="status" className="inlineNotice">
              {explainExperimentCode(item.reason_code, i18n.language)}
            </p>
          )}
          <p className="dataCardNote">
            {item.mode === "synthetic_demo" ? c.demoHelp : c.staleHint}
          </p>
          <details className="technicalDetails">
            <summary>{c.details}</summary>
            <dl>
              <dt>{c.dataset}</dt>
              <dd>{item.dataset_id}</dd>
              <dt>SHA-256</dt>
              <dd>{item.sha256 ?? c.notRecorded}</dd>
              <dt>{c.mode}</dt>
              <dd>{item.mode}</dd>
            </dl>
            {item.mode === "historical_exploration" && (
              <Link href={`/research/a-share/datasets/${item.dataset_id}`}>
                {c.archive} ↗
              </Link>
            )}
          </details>
        </section>
      ))}
      <MarketUpdatesPanel />
      <p className="inlineNotice">{c.futureUnavailable}</p>
      <p className="smallText">{c.dateZone}</p>
    </div>
  );
}
export function HelpPage() {
  const c = useProductCopy();
  return (
    <div className="productPage readingPage">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">{c.help}</p>
          <h1>{c.helpTitle}</h1>
        </div>
      </header>
      <section className="panel helpModes">
        <h2>{c.guideTitle}</h2>
        <ModeGuide />
      </section>
      {[
        [c.backtestQuestion, c.backtestAnswer],
        [c.drawdownQuestion, c.drawdownAnswer],
        [c.winQuestion, c.winAnswer],
        [c.benchmarkQuestion, c.benchmarkAnswer],
      ].map(([q, a]) => (
        <details className="helpQuestion" key={q}>
          <summary>{q}</summary>
          <p>{a}</p>
        </details>
      ))}
      <Link className="button" href="/research/new">
        {c.start} →
      </Link>
    </div>
  );
}
export function SettingsPage() {
  const c = useProductCopy();
  const { preferences, update, unsaved } = usePreferences();
  return (
    <div className="productPage readingPage">
      <header className="pageHeader">
        <div>
          <p className="eyebrow">{c.settings}</p>
          <h1>{c.settingsTitle}</h1>
          <p>{c.settingsHint}</p>
        </div>
      </header>
      <section className="panel settingsPanel">
        <label>
          {c.theme}
          <select
            value={preferences.theme}
            onChange={(e) =>
              update({ theme: e.target.value as typeof preferences.theme })
            }
          >
            <option value="system">{c.system}</option>
            <option value="light">{c.light}</option>
            <option value="dark">{c.dark}</option>
          </select>
        </label>
        <div className="settingsLanguage">
          <span>{c.language}</span>
          <LanguageSelector />
        </div>
        <label>
          {c.motion}
          <select
            value={preferences.motion}
            onChange={(e) =>
              update({ motion: e.target.value as typeof preferences.motion })
            }
          >
            <option value="system">{c.motionSystem}</option>
            <option value="off">{c.motionOff}</option>
          </select>
        </label>
        <label>
          {c.colors}
          <select
            value={preferences.marketColors}
            onChange={(e) =>
              update({
                marketColors: e.target.value as typeof preferences.marketColors,
              })
            }
          >
            <option value="red-up">{c.redUp}</option>
            <option value="green-up">{c.greenUp}</option>
          </select>
          <span className="marketColorPreview">
            <span className="marketUp">+ {c.up}</span>
            <span className="marketDown">− {c.down}</span>
          </span>
        </label>
        <label>
          {c.priceView}
          <select
            value={preferences.priceView}
            onChange={(e) =>
              update({
                priceView: e.target.value as typeof preferences.priceView,
              })
            }
          >
            <option value="raw">{c.raw}</option>
            <option value="adjusted">{c.adjusted}</option>
          </select>
        </label>
        <p className="smallText" role="status">
          {unsaved ? c.unsaved : c.saved}
        </p>
      </section>
    </div>
  );
}
