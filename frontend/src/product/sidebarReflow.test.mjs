import { readFileSync } from "node:fs";
import { expect, it } from "vitest";

it("keeps vertical overflow enabled on the fixed sidebar", () => {
  const css = readFileSync("src/styles.css", "utf8");
  expect(css).toMatch(/\.sidebar\s*\{[^}]*overflow-y:\s*auto;/);
});
