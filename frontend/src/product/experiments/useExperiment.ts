import { useEffect, useState } from "react";
import { experimentApi } from "./api";
import type { Experiment } from "./types";

export const isActiveExperiment = (job: Experiment) =>
  job.status === "QUEUED" || job.status === "RUNNING";

export function useExperiment(jobId: string) {
  const [revision, setRevision] = useState(0);
  const [state, setState] = useState<{
    jobId: string;
    data: Experiment | null;
    error: unknown;
  }>({ jobId, data: null, error: null });
  if (state.jobId !== jobId) setState({ jobId, data: null, error: null });
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timer: number | undefined;
    async function load() {
      try {
        const data = await experimentApi.get(jobId, controller.signal);
        if (!active) return;
        setState({ jobId, data, error: null });
        if (isActiveExperiment(data))
          timer = window.setTimeout(() => void load(), 2500);
      } catch (error) {
        if (active) setState((previous) => ({ ...previous, error }));
      }
    }
    void load();
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timer);
    };
  }, [jobId, revision]);
  return {
    data: state.jobId === jobId ? state.data : null,
    error: state.error,
    refresh: () => setRevision((value) => value + 1),
  };
}
