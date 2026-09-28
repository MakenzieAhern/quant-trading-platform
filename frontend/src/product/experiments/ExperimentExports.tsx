import { useEffect, useRef, useState } from "react";
import { ApiError } from "../../api/client";
import { experimentApi } from "./api";
import { useComparisonCopy } from "./comparisonCopy";
import { useExperimentCopy } from "./copy";
import type { DateRange, ExperimentCollection } from "./types";

export function ExperimentExports({
  jobId,
  range,
}: {
  jobId: string;
  range: DateRange;
}) {
  const c = useExperimentCopy();
  const u = useComparisonCopy();
  const [collection, setCollection] = useState<ExperimentCollection>("trades");
  const [status, setStatus] = useState<"idle" | "loading" | "done" | "error">(
    "idle",
  );
  const [missingHoldings, setMissingHoldings] = useState(false);
  const [prepared, setPrepared] = useState<{
    url: string;
    filename: string;
    range: DateRange;
  } | null>(null);
  const mounted = useRef(true);
  useEffect(() => {
    mounted.current = true;
    return () => {
      mounted.current = false;
    };
  }, []);
  useEffect(
    () => () => {
      if (prepared) URL.revokeObjectURL(prepared.url);
    },
    [prepared],
  );
  const pending = useRef(false);
  async function download(format: "json" | "csv") {
    if (pending.current) return;
    pending.current = true;
    setStatus("loading");
    setMissingHoldings(false);
    setPrepared(null);
    try {
      const blob = await experimentApi.export(jobId, format, collection, range);
      if (!mounted.current) return;
      const url = URL.createObjectURL(blob);
      const filename = `experiment-${jobId.replace(/[^a-zA-Z0-9-]/g, "")}-${format === "csv" ? collection : "report"}.${format}`;
      setPrepared({ url, filename, range: { ...range } });
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      // Keep a real user-activated fallback until another report replaces it or unmount.
      setStatus("done");
    } catch (error) {
      setMissingHoldings(
        error instanceof ApiError &&
          error.code === "HOLDINGS_NOT_RECORDED_FOR_THIS_RUN",
      );
      setStatus("error");
    } finally {
      pending.current = false;
    }
  }
  return (
    <section className="experimentPanel">
      <h2>{u.reports}</h2>
      <p className="experimentHelp">{u.exportHelp}</p>
      <p>
        {u.filterTitle}: {range.start_date ?? "…"} → {range.end_date ?? "…"}{" "}
        (Asia/Shanghai)
      </p>
      <div className="experimentActions">
        <button
          className="button secondary"
          aria-disabled={status === "loading"}
          onClick={() => void download("json")}
        >
          {u.exportJson}
        </button>
        <label>
          {u.collection}
          <select
            value={collection}
            disabled={status === "loading"}
            onChange={(event) =>
              setCollection(event.target.value as ExperimentCollection)
            }
          >
            <option value="trades">{c.trades}</option>
            <option value="equity">{c.equity}</option>
            <option value="holdings">{u.holdings}</option>
            <option value="decisions">{c.decisions}</option>
          </select>
        </label>
        <button
          className="button secondary"
          aria-disabled={status === "loading"}
          onClick={() => void download("csv")}
        >
          {u.exportCsv}
        </button>
      </div>
      {status === "loading" && <p role="status">{u.exporting}</p>}
      {status === "done" && <p role="status">{u.exported}</p>}
      {prepared && (
        <div>
          <a
            className="button secondary"
            href={prepared.url}
            download={prepared.filename}
          >
            {u.savePrepared}
          </a>
          <p className="experimentHelp">
            {prepared.filename} · {u.filterTitle}:{" "}
            {prepared.range.start_date ?? "…"} →{" "}
            {prepared.range.end_date ?? "…"} (Asia/Shanghai)
          </p>
        </div>
      )}
      {status === "error" && (
        <p role="alert">{missingHoldings ? u.notRecorded : u.downloadError}</p>
      )}
    </section>
  );
}
