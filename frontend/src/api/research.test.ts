import { afterEach, expect, test, vi } from "vitest";
import { researchApi } from "./research";

afterEach(() => vi.unstubAllGlobals());

test("research curves include every page and preserve exact decimal strings", async () => {
  const rows = Array.from({ length: 382 }, (_, sequence) => ({
    sequence,
    trading_date: "2024-01-02",
    value: "1000000.000000000000000001",
  }));
  const fetcher = vi.fn(async (url: string) => {
    const offset = Number(
      new URL(url, "http://localhost").searchParams.get("offset"),
    );
    return new Response(
      JSON.stringify({
        items: rows.slice(offset, offset + 200),
        limit: 200,
        offset,
        total: rows.length,
      }),
      { status: 200 },
    );
  });
  vi.stubGlobal("fetch", fetcher);
  const result = await researchApi.points("smoke", "equity");
  expect(result.items).toEqual(rows);
  expect(fetcher).toHaveBeenCalledTimes(2);
});

test("truncated curve pages fail visibly instead of silently accepting partial results", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            items: [],
            limit: 200,
            offset: 0,
            total: 382,
          }),
          { status: 200 },
        ),
    ),
  );
  await expect(researchApi.points("smoke", "equity")).rejects.toThrow();
});
