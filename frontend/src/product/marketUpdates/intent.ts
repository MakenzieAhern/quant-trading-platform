import type { UpdateCapabilities, UpdateConfiguration } from "./types";
export const UPDATE_DRAFT_KEY = "quant.product.market-update-draft.v1";
export interface UpdateDraft {
  securityText: string;
  start_date: string;
  end_date: string;
  requestKey: string;
}
export function readUpdateDraft(): UpdateDraft | null {
  try {
    const item: unknown = JSON.parse(
      localStorage.getItem(UPDATE_DRAFT_KEY) ?? "null",
    );
    if (!item || typeof item !== "object") return null;
    const data = item as UpdateDraft;
    return [
      data.securityText,
      data.start_date,
      data.end_date,
      data.requestKey,
    ].every((value) => typeof value === "string")
      ? data
      : null;
  } catch {
    return null;
  }
}
export function saveUpdateDraft(draft: UpdateDraft) {
  localStorage.setItem(UPDATE_DRAFT_KEY, JSON.stringify(draft));
}
export function requestFromDraft(draft: UpdateDraft): UpdateConfiguration {
  return {
    security_ids: draft.securityText
      .split(/[\s,;，；]+/)
      .filter(Boolean)
      .sort(),
    start_date: draft.start_date,
    end_date: draft.end_date,
  };
}
export function earliestUpdateDate(caps: UpdateCapabilities): string | null {
  const archive = caps.archive.find(
    (item) => item.mode === "historical_exploration",
  );
  if (!archive) return null;
  const date = new Date(`${archive.coverage_end}T00:00:00Z`);
  if (!Number.isFinite(date.getTime())) return null;
  date.setUTCDate(date.getUTCDate() + 1);
  return date.toISOString().slice(0, 10);
}
export type InvalidUpdateField = "security_ids" | "start_date" | "end_date";
export function invalidUpdateRequestField(
  config: UpdateConfiguration,
  caps: UpdateCapabilities,
): InvalidUpdateField | null {
  const { security_ids: ids, start_date: start, end_date: end } = config;
  const validDate = (day: string) => {
    const date = new Date(`${day}T00:00:00Z`);
    return (
      /^\d{4}-\d{2}-\d{2}$/.test(day) &&
      Number.isFinite(date.getTime()) &&
      date.toISOString().slice(0, 10) === day
    );
  };
  const earliest = earliestUpdateDate(caps);
  if (
    ids.length < 1 ||
    ids.length > Math.min(20, caps.max_securities) ||
    new Set(ids).size !== ids.length ||
    !ids.every((id) => /^CN-A:(SSE|SZSE):[0-9]{6}$/.test(id))
  )
    return "security_ids";
  if (
    !validDate(start) ||
    earliest === null ||
    start < earliest ||
    start > caps.latest_publishable_date
  )
    return "start_date";
  if (!validDate(end) || end > caps.latest_publishable_date) return "end_date";
  const span =
    (Date.parse(`${end}T00:00:00Z`) - Date.parse(`${start}T00:00:00Z`)) /
    86400000;
  return span >= 0 && span < Math.min(366, caps.max_days) ? null : "end_date";
}
export function validUpdateRequest(
  config: UpdateConfiguration,
  caps: UpdateCapabilities,
): boolean {
  return invalidUpdateRequestField(config, caps) === null;
}
