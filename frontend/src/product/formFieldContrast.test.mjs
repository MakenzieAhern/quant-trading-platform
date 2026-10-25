import { readFileSync } from "node:fs";
import { URL } from "node:url";
import { expect, it } from "vitest";

const css = (path) => readFileSync(new URL(path, import.meta.url), "utf8");

it("keeps product form boundaries on the accessible field token", () => {
  expect(css("./markets/markets.css")).toMatch(
    /\.marketField input,\s*\.marketField select\s*\{[^}]*border: 1px solid var\(--field-border\)/,
  );
  expect(css("./marketUpdates/updates.css")).toMatch(
    /\.marketUpdates input:not\(\[type="checkbox"\]\),\s*\.marketUpdates textarea,\s*\.marketUpdates select\s*\{[^}]*border: 1px solid var\(--field-border\)/,
  );
  expect(css("./configs/configs.css")).toMatch(
    /\.configurationVersionSave input\s*\{[^}]*border: 1px solid var\(--field-border\)/,
  );
});
