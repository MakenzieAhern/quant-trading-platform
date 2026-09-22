import { ApiError } from "../../api/client";
import { i18n } from "../../i18n";
import { explainExperimentCode } from "./codes";
import type { ExperimentCopy } from "./copy";

export function experimentError(reason: unknown, c: ExperimentCopy) {
  if (!(reason instanceof ApiError)) return c.networkError;
  if (reason.code) return explainExperimentCode(reason.code, i18n.language);
  if (reason.status === 422 || reason.status === 400) return c.validationError;
  if (reason.status === 409) return c.conflictError;
  if (reason.status === 404) return c.notFoundError;
  return reason.status >= 500 ? c.serverError : c.networkError;
}
