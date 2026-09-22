import { i18n } from "../i18n";

const DECIMAL_PATTERN = /^(-?)(\d+)(?:\.(\d+))?$/;

export function formatDecimal(value: string | null): string {
  if (value === null) return i18n.t("common:unavailable");
  const match = DECIMAL_PATTERN.exec(value);
  if (!match) return value;
  const [, sign, integer = "0", fraction = ""] = match;
  const locale = i18n.resolvedLanguage ?? "en-US";
  // BigInt has no negative zero: retain the sign for exact fractional losses.
  const signedInteger =
    sign === "-" && BigInt(integer) === 0n ? -0 : BigInt(`${sign}${integer}`);
  const grouped = new Intl.NumberFormat(locale, {
    maximumFractionDigits: 0,
  }).format(signedInteger);
  const decimalSeparator =
    new Intl.NumberFormat(locale)
      .formatToParts(1.1)
      .find((part) => part.type === "decimal")?.value ?? ".";
  return `${grouped}${fraction ? `${decimalSeparator}${fraction}` : ""}`;
}

export function formatPercent(value: string | null): string {
  if (value === null) return i18n.t("common:unavailable");
  const match = DECIMAL_PATTERN.exec(value);
  if (!match) return value;
  const negative = match[1] === "-";
  const integer = match[2] ?? "0";
  const fraction = match[3] ?? "";
  const decimalPosition = integer.length + 2;
  const shifted = `${integer}${fraction}`.padEnd(decimalPosition, "0");
  const whole =
    shifted.slice(0, decimalPosition).replace(/^0+(?=\d)/, "") || "0";
  const decimals = shifted.slice(decimalPosition).replace(/0+$/, "");
  const shiftedValue = `${negative ? "-" : ""}${whole}${decimals ? `.${decimals}` : ""}`;
  const percentSign =
    new Intl.NumberFormat(i18n.resolvedLanguage ?? "en-US", {
      style: "percent",
    })
      .formatToParts(0)
      .find((part) => part.type === "percentSign")?.value ?? "%";
  return `${formatDecimal(shiftedValue)}${percentSign}`;
}

export function formatUtc(value: string | null): string {
  if (value === null) return i18n.t("common:unavailable");
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  const locale = i18n.resolvedLanguage ?? "en-US";
  const formatter = new Intl.DateTimeFormat(locale, {
    timeZone: "UTC",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  if (locale === "en-US") {
    const parts = Object.fromEntries(
      formatter
        .formatToParts(date)
        .filter((part) => part.type !== "literal")
        .map((part) => [part.type, part.value]),
    );
    return `${parts.year}-${parts.month}-${parts.day} ${parts.hour}:${parts.minute}:${parts.second}Z (UTC)`;
  }
  return `${formatter.format(date)} (UTC)`;
}

export function shortId(value: string): string {
  return value.length > 12 ? `${value.slice(0, 8)}…${value.slice(-4)}` : value;
}

export function isPositiveDecimal(value: string): boolean {
  const match = DECIMAL_PATTERN.exec(value.trim());
  if (!match || match[1] === "-") return false;
  return /[1-9]/.test(`${match[2] ?? ""}${match[3] ?? ""}`);
}

export function parsePositiveInteger(value: string): number | null {
  if (!/^[1-9]\d*$/.test(value)) return null;
  const parsed = Number(value);
  return Number.isSafeInteger(parsed) ? parsed : null;
}

export function comparePositiveDecimals(
  left: string,
  right: string,
): number | null {
  const leftMatch = DECIMAL_PATTERN.exec(left);
  const rightMatch = DECIMAL_PATTERN.exec(right);
  if (
    !leftMatch ||
    !rightMatch ||
    leftMatch[1] === "-" ||
    rightMatch[1] === "-"
  )
    return null;
  const leftInteger = (leftMatch[2] ?? "0").replace(/^0+(?=\d)/, "");
  const rightInteger = (rightMatch[2] ?? "0").replace(/^0+(?=\d)/, "");
  if (leftInteger.length !== rightInteger.length)
    return leftInteger.length < rightInteger.length ? -1 : 1;
  if (leftInteger !== rightInteger) return leftInteger < rightInteger ? -1 : 1;
  const width = Math.max(leftMatch[3]?.length ?? 0, rightMatch[3]?.length ?? 0);
  const leftFraction = (leftMatch[3] ?? "").padEnd(width, "0");
  const rightFraction = (rightMatch[3] ?? "").padEnd(width, "0");
  return leftFraction === rightFraction
    ? 0
    : leftFraction < rightFraction
      ? -1
      : 1;
}
