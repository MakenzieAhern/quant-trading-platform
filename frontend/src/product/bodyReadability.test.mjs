import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

it("keeps mode, help and actionable error paragraphs at the inherited body size", () => {
  const css = readFileSync("src/styles.css", "utf8");
  expect(css).toMatch(/:root\s*\{[^}]*font-size:\s*15px;/);
  for (const selector of ["productError", "modeGrid", "helpQuestion"]) {
    const rules = css.matchAll(
      new RegExp(`\\.${selector} p\\s*\\{([^}]+)\\}`, "g"),
    );
    for (const rule of rules) expect(rule[1]).not.toMatch(/font-size:/);
  }
  expect(css).toMatch(/\.productError p\s*\{[^}]*color:\s*var\(--danger\);/);
});
