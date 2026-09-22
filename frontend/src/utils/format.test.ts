import { describe, expect, it } from "vitest";
import { formatDecimal, formatPercent } from "./format";

describe("readable summary precision", () => {
  it("rounds only the display without floating point or losing exact source values", () => {
    const original = "12345678901234567890.995000000000000000001";
    expect(formatDecimal(original, 2)).toBe("12,345,678,901,234,567,891.00");
    expect(formatDecimal(original)).toBe(
      "12,345,678,901,234,567,890.995000000000000000001",
    );
    expect(formatDecimal("-0.004", 2)).toBe("-0.00");
    expect(formatDecimal("-1.005", 2)).toBe("-1.01");
    expect(formatDecimal("0.999", 0)).toBe("1");
    expect(formatPercent("0.004005450328446926932648008", 2)).toBe("0.40%");
    expect(formatPercent("-0.000384410635371702424409088", 2)).toBe("-0.04%");
    expect(formatPercent(null, 2)).toBe("N/A");
    expect(formatDecimal("invalid", 2)).toBe("invalid");
    expect(() => formatDecimal("1.2", -1)).toThrow(RangeError);
  });
});
