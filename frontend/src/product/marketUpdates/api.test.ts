import { describe, expect, it, vi } from "vitest";
import { ApiContractError } from "../../api/contracts";
import {
  marketUpdateApi,
  parseCapabilities,
  parseJob,
  parseObservations,
} from "./api";
import { caps, job, observations, receipt } from "./fixtures.test-data";
import { invalidUpdateRequestField, validUpdateRequest } from "./intent";
describe("incremental update HTTP contract", () => {
  it("rejects a detail response for a different job", async () => {
    vi.spyOn(globalThis, "fetch").mockResolvedValueOnce(
      new Response(JSON.stringify({ ...job, job_id: "other-job" })),
    );
    await expect(marketUpdateApi.get(job.job_id)).rejects.toBeInstanceOf(
      ApiContractError,
    );
  });
  it("uses /api paths, exact bodies, server idempotency and bounded paginated reads", async () => {
    const fetch = vi
      .spyOn(globalThis, "fetch")
      .mockResolvedValueOnce(new Response(JSON.stringify(caps)))
      .mockResolvedValueOnce(new Response(JSON.stringify(job)))
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ items: [job], total: 1, limit: 20, offset: 20 }),
        ),
      )
      .mockResolvedValueOnce(
        new Response(
          JSON.stringify({ items: [receipt], total: 1, limit: 20, offset: 0 }),
        ),
      )
      .mockResolvedValueOnce(new Response(JSON.stringify(observations)))
      .mockResolvedValueOnce(new Response(JSON.stringify(job)));
    await marketUpdateApi.capabilities();
    await marketUpdateApi.create(job.configuration, "stable-key");
    await marketUpdateApi.list(20);
    await marketUpdateApi.receipts(job.job_id);
    const result = await marketUpdateApi.observations("CN-A:SSE:600000", {
      start_date: "2026-01-05",
      end_date: "2026-01-06",
    });
    await marketUpdateApi.retry(job.job_id);
    expect(fetch.mock.calls[0][0]).toContain(
      "/api/market-updates/capabilities",
    );
    expect(fetch.mock.calls[1][1]).toMatchObject({
      method: "POST",
      headers: { "Idempotency-Key": "stable-key" },
      body: JSON.stringify(job.configuration),
    });
    expect(fetch.mock.calls[2][0]).toContain(
      "/api/market-updates?limit=20&offset=20",
    );
    expect(fetch.mock.calls[3][0]).toContain(
      `/api/market-updates/${job.job_id}/receipts?limit=20&offset=0`,
    );
    expect(fetch.mock.calls[4][0]).toContain(
      "security_id=CN-A%3ASSE%3A600000&start_date=2026-01-05&end_date=2026-01-06",
    );
    expect(fetch.mock.calls[5][1]).toMatchObject({
      headers: { "Idempotency-Key": `market-update-retry-v1:${job.job_id}` },
    });
    expect(result.items[0].raw.open).toBe("12.000000000000000001");
  });
  it("fails closed on numeric financial fields, executable authority or oversized observations", () => {
    expect(() =>
      parseObservations({
        ...observations,
        items: [
          {
            ...observations.items[0],
            raw: { ...observations.items[0].raw, amount: 125000 },
          },
        ],
      }),
    ).toThrow();
    expect(() =>
      parseCapabilities({
        ...caps,
        authority: { ...caps.authority, execution_eligible: true },
      }),
    ).toThrow();
    expect(() =>
      parseObservations({
        ...observations,
        items: Array(367).fill(observations.items[0]),
        total: 367,
      }),
    ).toThrow();
    expect(
      parseJob({
        ...job,
        status: "FAILED",
        summary: { active_request: { security_id: "CN-A:SSE:600000" } },
      }).summary,
    ).toEqual({ active_request: { security_id: "CN-A:SSE:600000" } });
  });
  it("enforces inclusive date boundaries, canonical distinct IDs and maximum scope", () => {
    expect(validUpdateRequest(job.configuration, caps)).toBe(true);
    expect(
      invalidUpdateRequestField(
        {
          ...job.configuration,
          security_ids: ["CN-A:SSE:600000", "CN-A:SSE:600000"],
        },
        caps,
      ),
    ).toBe("security_ids");
    expect(
      invalidUpdateRequestField(
        { ...job.configuration, start_date: "2025-12-31" },
        caps,
      ),
    ).toBe("start_date");
    expect(
      invalidUpdateRequestField(
        { ...job.configuration, end_date: "2026-09-23" },
        caps,
      ),
    ).toBe("end_date");
    for (const config of [
      { ...job.configuration, start_date: "2025-12-31" },
      { ...job.configuration, end_date: "2026-09-23" },
      { ...job.configuration, start_date: "2026-02-30" },
      { ...job.configuration, security_ids: ["600000"] },
      {
        ...job.configuration,
        security_ids: ["CN-A:SSE:600000", "CN-A:SSE:600000"],
      },
      {
        ...job.configuration,
        security_ids: Array.from(
          { length: 21 },
          (_, i) => `CN-A:SSE:${600000 + i}`,
        ),
      },
    ])
      expect(validUpdateRequest(config, caps)).toBe(false);
    const expanded = { ...caps, latest_publishable_date: "2027-12-31" };
    expect(
      validUpdateRequest(
        {
          ...job.configuration,
          start_date: "2026-01-01",
          end_date: "2027-01-01",
        },
        expanded,
      ),
    ).toBe(true);
    expect(
      validUpdateRequest(
        {
          ...job.configuration,
          start_date: "2026-01-01",
          end_date: "2027-01-02",
        },
        expanded,
      ),
    ).toBe(false);
  });
});
