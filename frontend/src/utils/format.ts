const DECIMAL_PATTERN = /^(-?)(\d+)(?:\.(\d+))?$/;

export function formatDecimal(value: string | null): string {
  if (value === null) return "N/A";
  const match = DECIMAL_PATTERN.exec(value);
  if (!match) return value;
  const [, sign, integer = "0", fraction = ""] = match;
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  return `${sign}${grouped}${fraction ? `.${fraction}` : ""}`;
}

export function formatPercent(value: string | null): string {
  if (value === null) return "N/A";
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
  return `${negative ? "-" : ""}${whole}${decimals ? `.${decimals}` : ""}%`;
}

export function formatUtc(value: string | null): string {
  if (value === null) return "N/A";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return `${date.toISOString().replace("T", " ").replace(".000Z", "Z")} (UTC)`;
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
