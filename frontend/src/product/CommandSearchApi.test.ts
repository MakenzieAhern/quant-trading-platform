import { expect, it, vi } from "vitest";
import { experimentApi } from "./experiments/api";
import { job } from "./experiments/fixtures.test-data";
import { marketApi } from "./markets/api";
import { watched } from "./markets/fixtures.test-data";

it("passes literal Unicode/wildcard search text to server pagination without local filtering", async () => {
  const fetch = vi
    .spyOn(globalThis, "fetch")
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ items: [job], total: 42, limit: 20, offset: 20 }),
      ),
    )
    .mockResolvedValueOnce(
      new Response(
        JSON.stringify({ items: [watched], total: 33, limit: 20, offset: 40 }),
      ),
    );
  const query = "研究%_ /";
  const studies = await experimentApi.list(undefined, 20, 20, query);
  const watches = await marketApi.watchlist(40, undefined, query);
  expect(
    new URL(String(fetch.mock.calls[0][0]), "http://local").searchParams.get(
      "q",
    ),
  ).toBe(query);
  expect(String(fetch.mock.calls[0][0])).toContain(
    "/api/experiments?limit=20&offset=20&",
  );
  expect(
    new URL(String(fetch.mock.calls[1][0]), "http://local").searchParams.get(
      "q",
    ),
  ).toBe(query);
  expect(String(fetch.mock.calls[1][0])).toContain(
    "/api/markets/watchlist?limit=20&offset=40&",
  );
  expect(studies.items[0]).toEqual(job);
  expect(watches.items[0]).toEqual(watched);
  expect(studies.total).toBe(42);
  expect(watches.total).toBe(33);
});
