import { ApiError } from "../../api/client";
import { i18n } from "../../i18n";
import { explainExperimentCode } from "./codes";
import type { ExperimentCopy } from "./copy";
import type { DatasetCapability } from "./types";

export function datasetExecutionCode(
  dataset: DatasetCapability,
): string | null {
  if (!dataset.available) return dataset.reason_code || "DATASET_NOT_MOUNTED";
  // Explicit adverse findings outrank an omitted or contradictory legacy flag.
  return (
    dataset.current_source_integrity ||
    dataset.execution_reason_code ||
    (dataset.execution_available === false
      ? "DATASET_EXECUTION_NOT_ACCEPTED"
      : null)
  );
}

export function executionAdmissionCode(reason: unknown): string | null {
  if (!(reason instanceof ApiError) || reason.status !== 422) return null;
  const code = reason.code ?? reason.message;
  return [
    "SOURCE_CONTRACT_INTEGRITY_FAILED",
    "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED",
    "DATASET_CHANGED_SINCE_SUBMISSION",
  ].includes(code)
    ? code
    : null;
}

export function experimentError(reason: unknown, c: ExperimentCopy) {
  if (!(reason instanceof ApiError)) return c.networkError;
  if (reason.status === 401 || reason.status === 403)
    return i18n.t("common:loadErrors.permission");
  if (reason.status === 408) return i18n.t("common:loadErrors.timeout");
  const fallback =
    reason.status === 422 || reason.status === 400
      ? c.validationError
      : reason.status === 409
        ? c.conflictError
        : reason.status === 404
          ? c.notFoundError
          : reason.status >= 500
            ? c.serverError
            : c.networkError;
  return reason.code
    ? explainExperimentCode(reason.code, i18n.language, fallback)
    : fallback;
}
