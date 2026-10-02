import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

it("retains source guards for narrow headers and exact monthly values", () => {
  const css = readFileSync("src/styles.css", "utf8");
  expect(css).toMatch(
    /\.pageHeader > div,\s*\.detailHeader > div\s*\{[^}]*max-width:\s*100%;/,
  );
  expect(css).toMatch(/\.monthlyHeatmap > div\s*\{[^}]*min-width:\s*0;/);
  expect(css).toMatch(
    /\.monthlyHeatmap > div\s*\{[^}]*overflow-wrap:\s*anywhere;/,
  );
});
