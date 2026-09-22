import type { ExperimentConfiguration } from "./types";

export const EXPERIMENT_DRAFT_KEY = "quant.product.experiment-draft.v1";
export interface ExperimentDraft {
  version: 1;
  form: ExperimentConfiguration;
  step: number;
  idempotencyKey: string;
  savedAt: string;
}
export function readExperimentDraft(): ExperimentDraft | null {
  try {
    const raw = window.localStorage.getItem(EXPERIMENT_DRAFT_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as ExperimentDraft;
    if (
      value.version !== 1 ||
      !Number.isInteger(value.step) ||
      value.step < 0 ||
      value.step > 3 ||
      typeof value.idempotencyKey !== "string" ||
      typeof value.savedAt !== "string"
    )
      return null;
    // Drafts can contain unfinished values. Validate shape, not run eligibility.
    const form = value.form;
    if (
      !form ||
      [
        form.name,
        form.dataset_id,
        form.strategy_id,
        form.start_date,
        form.end_date,
        form.initial_cash,
        form.universe,
        form.costs?.commission_rate,
        form.costs?.minimum_commission,
        form.risk?.max_drawdown,
        form.risk?.max_position_weight,
      ].some((field) => typeof field !== "string") ||
      !Number.isSafeInteger(form.strategy?.rebalance_sessions) ||
      !Number.isSafeInteger(form.strategy?.maximum_holdings)
    )
      return null;
    return value;
  } catch {
    return null;
  }
}
export function saveExperimentDraft(
  form: ExperimentConfiguration,
  step: number,
  idempotencyKey: string,
) {
  window.localStorage.setItem(
    EXPERIMENT_DRAFT_KEY,
    JSON.stringify({
      version: 1,
      form,
      step,
      idempotencyKey,
      savedAt: new Date().toISOString(),
    } satisfies ExperimentDraft),
  );
}
