import { afterEach, expect, test, vi } from "vitest";
import { researchApi } from "./research";

afterEach(() => vi.unstubAllGlobals());

test("research curves fetch only the requested page and preserve exact decimal strings", async () => {
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
  const first = await researchApi.points("smoke", "equity", 0);
  expect(first.items).toEqual(rows.slice(0, 200));
  expect(first.total).toBe(382);
  expect(fetcher).toHaveBeenCalledTimes(1);
  const second = await researchApi.points("smoke", "equity", 200);
  expect(second.items).toEqual(rows.slice(200));
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

test("research curves reject a page with an unexpected offset or sequence", async () => {
  vi.stubGlobal(
    "fetch",
    vi.fn(
      async () =>
        new Response(
          JSON.stringify({
            items: [{ sequence: "0", trading_date: "2024-01-02", value: "1" }],
            limit: 200,
            offset: 0,
            total: 1,
          }),
          { status: 200 },
        ),
    ),
  );
  await expect(researchApi.points("smoke", "equity", 200)).rejects.toThrow();
  await expect(researchApi.points("smoke", "equity", 0)).rejects.toThrow();
});

test("every dated research collection serializes the same bounded display range", async () => {
  const fetcher = vi.fn(
    async () =>
      new Response(
        JSON.stringify({
          items: [],
          limit: 200,
          offset: 200,
          total: 0,
        }),
        { status: 200 },
      ),
  );
  vi.stubGlobal("fetch", fetcher);
  const signal = new AbortController().signal;
  const range = { start_date: "2024-01-02", end_date: "2024-04-01" };
  for (const kind of ["equity", "benchmark", "drawdown"] as const)
    await researchApi.points("saved/id", kind, 200, signal, range);
  for (const method of [
    researchApi.holdings,
    researchApi.trades,
    researchApi.rebalances,
    researchApi.rollingMetrics,
  ])
    await method("saved/id", 200, signal, range);
  expect(fetcher).toHaveBeenCalledTimes(7);
  for (const [url, options] of fetcher.mock.calls as unknown as [
    string,
    RequestInit,
  ][]) {
    const parsed = new URL(url, "http://localhost");
    expect(parsed.pathname).toContain("/saved%2Fid/");
    expect(Object.fromEntries(parsed.searchParams)).toEqual({
      limit: "200",
      offset: "200",
      ...range,
    });
    expect(options.signal).toBeInstanceOf(AbortSignal);
  }
});
