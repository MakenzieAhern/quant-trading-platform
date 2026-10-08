import { describe, expect, it, vi } from "vitest";
import { API_BASE_URL } from "../../api/config";
import { jsonResponse } from "../../test/fixtures";
import { marketApi, parseBars, validRange } from "./api";
import {
  bars,
  dataset,
  metadata,
  security,
  watched,
} from "./fixtures.test-data";

describe("market HTTP boundary", () => {
  it.each(["PASS", true, 0, {}, [], "__proto__"])(
    "rejects unrecognized current quality %j in catalog, search and bars",
    async (quality) => {
      vi.spyOn(globalThis, "fetch")
        .mockResolvedValueOnce(
          jsonResponse([{ ...dataset, current_dataset_quality: quality }]),
        )
        .mockResolvedValueOnce(
          jsonResponse({
            items: [],
            total: 0,
            limit: 20,
            offset: 0,
            metadata: { ...metadata, current_dataset_quality: quality },
          }),
        )
        .mockResolvedValueOnce(
          jsonResponse({
            ...bars,
            metadata: { ...metadata, current_dataset_quality: quality },
          }),
        );
      await expect(marketApi.datasets()).rejects.toThrow();
      await expect(
        marketApi.search(dataset.dataset_id, "", "ALL"),
      ).rejects.toThrow();
      await expect(
        marketApi.bars(dataset.dataset_id, security.security_id, {
          start_date: "2024-02-27",
          end_date: "2024-02-29",
        }),
      ).rejects.toThrow();
    },
  );
  it.each([
    "KNOWN_ECONOMIC_COVERAGE_GAP",
    "HISTORICAL_DATASET_QUALITY_UNKNOWN",
    null,
    undefined,
  ])(
    "preserves current quality %j without changing market bytes or prices",
    async (quality) => {
      vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
        jsonResponse([{ ...dataset, current_dataset_quality: quality }]),
      );
      expect((await marketApi.datasets())[0].current_dataset_quality).toBe(
        quality,
      );
      const input = {
        ...bars,
        metadata: { ...metadata, current_dataset_quality: quality },
      };
      const before = JSON.stringify(input);
      expect(parseBars(input).metadata.current_dataset_quality).toBe(quality);
      expect(JSON.stringify(input)).toBe(before);
      expect(parseBars(input).items[0].raw.close).toBe("10.123456789012345678");
    },
  );
  it("uses /api routes, encoded identities, explicit dates and bounded pages", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse([dataset]))
      .mockResolvedValueOnce(
        jsonResponse({
          items: [security],
          total: 1,
          limit: 20,
          offset: 20,
          metadata,
        }),
      )
      .mockResolvedValueOnce(jsonResponse(bars))
      .mockResolvedValueOnce(
        jsonResponse({ items: [watched], total: 1, limit: 20, offset: 0 }),
      );
    await expect(marketApi.datasets()).resolves.toEqual([dataset]);
    await marketApi.search(dataset.dataset_id, "浦发 & bank", "SSE", 20);
    await marketApi.bars(dataset.dataset_id, security.security_id, {
      start_date: "2024-02-27",
      end_date: "2024-02-29",
    });
    await marketApi.watchlist();
    const root = `${API_BASE_URL}/api/markets`;
    expect(fetch.mock.calls.map(([url]) => String(url).split("?")[0])).toEqual([
      `${root}/datasets`,
      `${root}/securities`,
      `${root}/securities/CN-A%3ASSE%3A600000/bars`,
      `${root}/watchlist`,
    ]);
    expect(
      Object.fromEntries(new URL(String(fetch.mock.calls[1][0])).searchParams),
    ).toEqual({
      dataset_id: dataset.dataset_id,
      q: "浦发 & bank",
      exchange: "SSE",
      limit: "20",
      offset: "20",
    });
    expect(
      Object.fromEntries(new URL(String(fetch.mock.calls[2][0])).searchParams),
    ).toEqual({
      dataset_id: dataset.dataset_id,
      start_date: "2024-02-27",
      end_date: "2024-02-29",
    });
  });
  it("PUTs dataset identity and accepts DELETE 204 without requiring JSON", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(watched))
      .mockResolvedValueOnce(new Response(null, { status: 204 }))
      .mockResolvedValueOnce(
        jsonResponse({ code: "DATASET_INTEGRITY_FAILED" }, 422),
      );
    await expect(
      marketApi.add(dataset.dataset_id, security.security_id),
    ).resolves.toEqual(watched);
    expect(fetch.mock.calls[0][1]?.method).toBe("PUT");
    expect(JSON.parse(String(fetch.mock.calls[0][1]?.body))).toEqual({
      dataset_id: dataset.dataset_id,
    });
    await expect(
      marketApi.remove(dataset.dataset_id, security.security_id),
    ).resolves.toBeUndefined();
    expect(fetch.mock.calls[1][1]?.method).toBe("DELETE");
    expect(
      new URL(String(fetch.mock.calls[1][0])).searchParams.get("dataset_id"),
    ).toBe(dataset.dataset_id);
    await expect(
      marketApi.remove(dataset.dataset_id, security.security_id),
    ).rejects.toMatchObject({ code: "DATASET_INTEGRITY_FAILED", status: 422 });
  });
  it("rejects financial JSON numbers and keeps unavailable feature prices null", () => {
    expect(parseBars(bars).items[0].raw.close).toBe("10.123456789012345678");
    expect(parseBars(bars).items[2].adjusted.close).toBeNull();
    expect(() =>
      parseBars({
        ...bars,
        total: 1,
        items: [
          { ...bars.items[0], raw: { ...bars.items[0].raw, volume: 100000 } },
        ],
      }),
    ).toThrow();
    expect(() =>
      parseBars({
        ...bars,
        total: 1,
        items: [{ ...bars.items[0], adjustment_factor: 2 }],
      }),
    ).toThrow();
    expect(() =>
      parseBars({ ...bars, metadata: { ...metadata, is_live: true } }),
    ).toThrow();
    expect(() =>
      parseBars({ ...bars, total: 367, items: Array(367).fill(bars.items[0]) }),
    ).toThrow();
  });
  it("accepts an inclusive leap-year 366-day window but rejects 367 days and out-of-coverage dates", () => {
    expect(
      validRange({ start_date: "2024-02-31", end_date: "2024-03-03" }, dataset),
    ).toBe(false);
    expect(
      validRange({ start_date: "2024-01-01", end_date: "2024-12-31" }, dataset),
    ).toBe(true);
    expect(
      validRange({ start_date: "2024-01-01", end_date: "2025-01-01" }, dataset),
    ).toBe(false);
    expect(
      validRange({ start_date: "2024-02-29", end_date: "2024-02-28" }, dataset),
    ).toBe(false);
    expect(
      validRange({ start_date: "2026-01-01", end_date: "2026-01-02" }, dataset),
    ).toBe(false);
  });
  it("retains unknown suspension boundary flags and original evidence rather than coercing them to false", () => {
    const evidence = [
      {
        suspended_at: "2024/2/28 13:00",
        resumed_or_ended_at: "2024-02-29",
        boundary_semantics: "UNKNOWN",
        day_open_blocked: null,
        source_sha256_json: '["source-hash"]',
      },
    ];
    const input = {
      ...bars,
      total: 1,
      items: [
        {
          ...bars.items[1],
          status: "SUSPENSION_BOUNDARY_UNCERTAIN",
          execution_open_blocked: null,
          suspension_evidence: evidence,
        },
      ],
    };
    expect(parseBars(input).items[0]).toMatchObject({
      status: "SUSPENSION_BOUNDARY_UNCERTAIN",
      execution_open_blocked: null,
      suspension_evidence: evidence,
    });
  });
});
