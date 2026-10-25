import type { TFunction } from "i18next";

export function localizeRiskMessage(message: string, t: TFunction<"paper">) {
  const reserved = /^reserved quantity for (.+) must be finite$/.exec(message);
  if (reserved)
    return t("detail.riskMessages.reservedQuantityFinite", {
      symbol: reserved[1],
    });
  const mark = /^a positive observed mark is required for (.+)$/.exec(message);
  if (mark)
    return t("detail.riskMessages.positiveMarkRequired", { symbol: mark[1] });
  return t(`detail.riskMessages.${message}`, { defaultValue: message });
}
