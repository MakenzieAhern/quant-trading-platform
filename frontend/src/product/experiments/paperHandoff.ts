import type { Experiment } from "./types";

export function canUsePaperHandoff(job: Experiment | null): job is Experiment {
  return Boolean(
    job?.status === "SUCCEEDED" &&
    job.result_available &&
    job.mode === "historical_exploration" &&
    job.dataset_id === "cn-a-research-20100101-20251231-v1" &&
    job.configuration.dataset_id === job.dataset_id &&
    job.configuration.strategy_id ===
      "cn_a_cross_sectional_momentum_low_vol_v1",
  );
}
