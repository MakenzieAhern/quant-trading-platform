import { describe, expect, it, vi } from "vitest";
import { API_BASE_URL } from "../../api/config";
import { jsonResponse } from "../../test/fixtures";
import { experimentApi } from "./api";
import { capabilities, configuration, job, result } from "./fixtures.test-data";

describe("experiment HTTP boundary", () => {
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
});
