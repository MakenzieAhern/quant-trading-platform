import { describe, expect, it, vi } from "vitest";
import { API_BASE_URL } from "../../api/config";
import { ApiContractError } from "../../api/contracts";
import { jsonResponse } from "../../test/fixtures";
import {
  experimentApi,
  parseCapabilities,
  parseCurrentDatasetQuality,
  parseCurrentSourceIntegrity,
  parseExperiment,
  parseResult,
} from "./api";
import { capabilities, configuration, job, result } from "./fixtures.test-data";

describe("experiment HTTP boundary", () => {
  it("validates independent source findings without approving missing or unknown versions", () => {
    for (const value of [
      "SOURCE_CONTRACT_INTEGRITY_FAILED",
      "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED",
      null,
      undefined,
    ]) {
      const saved = { ...result, current_source_integrity: value };
      expect(parseResult(saved)).toEqual(saved);
      expect(parseCurrentSourceIntegrity(value)).toBe(value ?? null);
    }
    for (const value of [
      "PASS",
      "",
      true,
      [],
      {},
      "KNOWN_ECONOMIC_COVERAGE_GAP",
    ]) {
      expect(() => parseCurrentSourceIntegrity(value)).toThrow(
        ApiContractError,
      );
      expect(() =>
        parseResult({ ...result, current_source_integrity: value }),
      ).toThrow(ApiContractError);
      expect(() =>
        parseCapabilities({
          ...capabilities,
          datasets: capabilities.datasets.map((item) => ({
            ...item,
            current_source_integrity: value,
          })),
        }),
      ).toThrow(ApiContractError);
    }
  });
  it("validates observed failure identity without inventing legacy context", () => {
    const error_context = {
      trading_date: "2024-01-04",
      security_ids: ["CN-A:SSE:600000"],
      security_count: 1,
    };
    const failed = {
      ...job,
      status: "FAILED",
      error_code: "UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT",
      error_context,
    };
    expect(parseExperiment(job)).toEqual(job);
    expect(
      parseExperiment({ ...failed, error_context: null }).error_context,
    ).toBeNull();
    expect(parseExperiment(failed).error_context).toEqual(error_context);
    for (const change of [
      { trading_date: "2024-02-30" },
      { trading_date: "2024-01-04T00:00:00Z" },
      { security_ids: [] },
      { security_ids: ["private/path"] },
      {
        security_ids: ["CN-A:SSE:600000", "CN-A:SSE:600000"],
        security_count: 2,
      },
      {
        security_ids: ["CN-A:SZSE:000001", "CN-A:SSE:600000"],
        security_count: 2,
      },
      { security_count: true },
      { security_count: 0 },
      { security_count: 2 },
      { traceback: "private" },
      {
        security_ids: Array.from(
          { length: 101 },
          (_, n) => `CN-A:SSE:${String(n).padStart(6, "0")}`,
        ),
        security_count: 101,
      },
    ])
      expect(() =>
        parseExperiment({
          ...failed,
          error_context: { ...error_context, ...change },
        }),
      ).toThrow(ApiContractError);
    for (const change of [
      { status: "SUCCEEDED" },
      { error_code: "EXPERIMENT_EXECUTION_FAILED" },
      { result_available: true },
    ])
      expect(() => parseExperiment({ ...failed, ...change })).toThrow(
        ApiContractError,
      );
    const prefix = Array.from(
      { length: 100 },
      (_, n) => `CN-A:SSE:${String(n).padStart(6, "0")}`,
    );
    expect(
      parseExperiment({
        ...failed,
        error_context: {
          ...error_context,
          security_ids: prefix,
          security_count: 101,
        },
      }).error_context?.security_count,
    ).toBe(101);
  });
  it("preserves read-time quality, accepts legacy omission and rejects unknown quality claims", () => {
    const saved = {
      ...result,
      current_dataset_quality: "KNOWN_ECONOMIC_COVERAGE_GAP",
    };
    const before = JSON.stringify(saved);
    expect(parseResult(saved).current_dataset_quality).toBe(
      "KNOWN_ECONOMIC_COVERAGE_GAP",
    );
    expect(parseResult(result)).toEqual(result);
    expect(JSON.stringify(saved)).toBe(before);
    for (const value of [
      "PASS",
      ["KNOWN_ECONOMIC_COVERAGE_GAP"],
      { status: "KNOWN_ECONOMIC_COVERAGE_GAP" },
      1,
    ]) {
      expect(() => parseCurrentDatasetQuality(value)).toThrow(ApiContractError);
      expect(() =>
        parseResult({ ...result, current_dataset_quality: value }),
      ).toThrow(ApiContractError);
      expect(() =>
        parseCapabilities({
          ...capabilities,
          datasets: capabilities.datasets.map((item) => ({
            ...item,
            current_dataset_quality: value,
          })),
        }),
      ).toThrow(ApiContractError);
    }
    expect(
      parseCurrentDatasetQuality("HISTORICAL_DATASET_QUALITY_UNKNOWN"),
    ).toBe("HISTORICAL_DATASET_QUALITY_UNKNOWN");
    expect(parseCurrentDatasetQuality(null)).toBeNull();
  });
  it("requests capabilities from the actual mounted /api route", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(capabilities));
    await expect(experimentApi.capabilities()).resolves.toEqual(capabilities);
    expect(fetch.mock.calls[0][0]).toBe(
      `${API_BASE_URL}/api/workbench/capabilities`,
    );
  });

  it("posts exact configuration and idempotency to /api/experiments", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(jsonResponse(job, 202));
    await expect(
      experimentApi.create(configuration, "request-key"),
    ).resolves.toEqual(job);
    expect(fetch.mock.calls[0][0]).toBe(`${API_BASE_URL}/api/experiments`);
    const init = fetch.mock.calls[0][1];
    expect(init?.method).toBe("POST");
    expect(new Headers(init?.headers).get("Idempotency-Key")).toBe(
      "request-key",
    );
    expect(JSON.parse(String(init?.body))).toEqual(configuration);
  });

  it("loads list and result from mounted routes with bounded pagination", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse({ items: [job], total: 1, limit: 20, offset: 40 }),
      )
      .mockResolvedValueOnce(jsonResponse(result));
    await experimentApi.list(undefined, 20, 40);
    await experimentApi.result(job.job_id);
    expect(fetch.mock.calls.map(([url]) => url)).toEqual([
      `${API_BASE_URL}/api/experiments?limit=20&offset=40`,
      `${API_BASE_URL}/api/experiments/${job.job_id}/result`,
    ]);
  });

  it("rejects a saved study or result returned for a different job ID", async () => {
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        jsonResponse({
          ...job,
          job_id: "00000000-0000-0000-0000-000000000000",
        }),
      )
      .mockResolvedValueOnce(
        jsonResponse({
          ...result,
          job_id: "00000000-0000-0000-0000-000000000000",
        }),
      );
    await expect(experimentApi.get(job.job_id)).rejects.toBeInstanceOf(
      ApiContractError,
    );
    await expect(experimentApi.result(job.job_id)).rejects.toBeInstanceOf(
      ApiContractError,
    );
  });

  it("sends server-wide filters and sort with the page request", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValue(
        jsonResponse({ items: [], total: 0, limit: 20, offset: 20 }),
      );
    await experimentApi.list(undefined, 20, 20, "Alpha", {
      status: "SUCCEEDED",
      mode: "historical_exploration",
      sort: "name_asc",
    });
    expect(fetch.mock.calls[0][0]).toBe(
      `${API_BASE_URL}/api/experiments?limit=20&offset=20&q=Alpha&status=SUCCEEDED&mode=historical_exploration&sort=name_asc`,
    );
  });

  it("uses the same API root for detail, lifecycle commands and all paginated collections", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(job))
      .mockResolvedValueOnce(jsonResponse(job))
      .mockResolvedValueOnce(jsonResponse(job))
      .mockImplementation(async () =>
        jsonResponse({ items: [], total: 0, limit: 20, offset: 0 }),
      );
    await experimentApi.get(job.job_id);
    await experimentApi.cancel(job.job_id);
    await experimentApi.retry(job.job_id, "durable-retry-key");
    await experimentApi.equity(job.job_id, undefined, 100);
    await experimentApi.trades(job.job_id, undefined, 20);
    await experimentApi.decisions(job.job_id, undefined, 20);
    const base = `${API_BASE_URL}/api/experiments/${job.job_id}`;
    expect(fetch.mock.calls.map(([url]) => url)).toEqual([
      base,
      `${base}/cancel`,
      `${base}/retry`,
      `${base}/equity?limit=100&offset=100`,
      `${base}/trades?limit=20&offset=20`,
      `${base}/decisions?limit=20&offset=20`,
    ]);
    expect(
      new Headers(fetch.mock.calls[2][1]?.headers).get("Idempotency-Key"),
    ).toBe("durable-retry-key");
  });

  it("sends inclusive date bounds with bounded collection pages and keeps availability", async () => {
    const fetch = vi.spyOn(globalThis, "fetch").mockImplementation(async () =>
      jsonResponse({
        items: [],
        total: 0,
        limit: 1,
        offset: 0,
        availability: "NOT_RECORDED",
        reason_code: "HOLDINGS_NOT_RECORDED_FOR_THIS_RUN",
      }),
    );
    const range = { start_date: "2031-01-02", end_date: "2031-01-03" };
    await experimentApi.equity(job.job_id, undefined, 100, range);
    await experimentApi.trades(job.job_id, undefined, 20, range);
    await experimentApi.decisions(job.job_id, undefined, 40, range);
    await expect(
      experimentApi.holdings(job.job_id, undefined, 5, range),
    ).resolves.toMatchObject({
      availability: "NOT_RECORDED",
      reason_code: "HOLDINGS_NOT_RECORDED_FOR_THIS_RUN",
    });
    const base = `${API_BASE_URL}/api/experiments/${job.job_id}`;
    expect(fetch.mock.calls.map(([url]) => url)).toEqual([
      `${base}/equity?limit=100&offset=100&start_date=2031-01-02&end_date=2031-01-03`,
      `${base}/trades?limit=20&offset=20&start_date=2031-01-02&end_date=2031-01-03`,
      `${base}/decisions?limit=20&offset=40&start_date=2031-01-02&end_date=2031-01-03`,
      `${base}/holdings?limit=1&offset=5&start_date=2031-01-02&end_date=2031-01-03`,
    ]);
  });

  it("requires exact holdings amounts, allows null weights, and refuses missing availability", async () => {
    const item = {
      sequence: 0,
      trading_date: "2031-01-02",
      timestamp: "2031-01-02T07:00:00Z",
      cash: "999.000000000000000001",
      equity: "0",
      market_value: "0",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      pending_corporate_action_value: "0",
      positions: [
        {
          security_id: "CN:600000",
          quantity: "1",
          average_price: "1.000000000000000001",
          market_price: "0",
          market_value: "0",
          weight: null,
        },
      ],
    };
    const page = {
      items: [item],
      total: 1,
      limit: 1,
      offset: 0,
      availability: "AVAILABLE",
      reason_code: null,
    };
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(page))
      .mockResolvedValueOnce(
        jsonResponse({ ...page, items: [{ ...item, cash: 999 }] }),
      )
      .mockResolvedValueOnce(
        jsonResponse({ items: [], total: 0, limit: 1, offset: 0 }),
      );
    await expect(experimentApi.holdings(job.job_id)).resolves.toMatchObject({
      items: [item],
    });
    await expect(experimentApi.holdings(job.job_id)).rejects.toThrow();
    await expect(experimentApi.holdings(job.job_id)).rejects.toThrow();
  });

  it("downloads unchanged server bytes with filters and preserves structured export failures", async () => {
    const csv = 'record_type,value\nmetadata,"100000.000000000000000001"\n';
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(
        new Response(csv, { headers: { "Content-Type": "text/csv" } }),
      )
      .mockResolvedValueOnce(
        jsonResponse(
          {
            code: "HOLDINGS_NOT_RECORDED_FOR_THIS_RUN",
            message: "Not recorded",
          },
          409,
        ),
      );
    const blob = await experimentApi.export(job.job_id, "csv", "trades", {
      end_date: "2031-01-02",
    });
    expect(await blob.text()).toBe(csv);
    expect(fetch.mock.calls[0][0]).toBe(
      `${API_BASE_URL}/api/experiments/${job.job_id}/export?format=csv&collection=trades&end_date=2031-01-02`,
    );
    await expect(
      experimentApi.export(job.job_id, "csv", "holdings"),
    ).rejects.toMatchObject({
      status: 409,
      code: "HOLDINGS_NOT_RECORDED_FOR_THIS_RUN",
    });
  });

  it("rejects rounded numeric corporate-action fields while preserving absent legacy values", async () => {
    const item = {
      sequence: 0,
      trading_date: "2031-01-02",
      timestamp: "2031-01-02T07:00:00Z",
      cash: "100000",
      equity: "100010.000000000000000001",
      market_value: "10.000000000000000001",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      pending_corporate_action_value: "10.000000000000000001",
      positions: [],
      total_pnl: "10.000000000000000001",
      corporate_action_realized_pnl: "0.000000000000000001",
    };
    const page = {
      items: [item],
      total: 1,
      limit: 1,
      offset: 0,
      availability: "AVAILABLE",
      reason_code: null,
    };
    vi.spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(jsonResponse(page))
      .mockResolvedValueOnce(
        jsonResponse({
          ...page,
          items: [{ ...item, corporate_action_realized_pnl: 0.01 }],
        }),
      );
    await expect(experimentApi.holdings(job.job_id)).resolves.toMatchObject({
      items: [item],
    });
    await expect(experimentApi.holdings(job.job_id)).rejects.toThrow();
  });
});
