const DECIMAL_PATTERN = /^(-?)(\d+)(?:\.(\d+))?$/;

export function formatDecimal(
  value: string | null,
  maximumFractionDigits = 6,
): string {
  if (value === null) return "N/A";
  const match = DECIMAL_PATTERN.exec(value);
  if (!match) return value;
  const [, sign, integer = "0", fraction = ""] = match;
  const grouped = integer.replace(/\B(?=(\d{3})+(?!\d))/g, ",");
  const visibleFraction = fraction
    .slice(0, maximumFractionDigits)
    .replace(/0+$/, "");
  return `${sign}${grouped}${visibleFraction ? `.${visibleFraction}` : ""}`;
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
  const decimals = shifted
    .slice(decimalPosition)
    .slice(0, 6)
    .replace(/0+$/, "");
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
