import { describe, expect, it } from "vitest";

import { paperParsers, parseWireEvent } from "./paper";
import { applyPaperEvent } from "../hooks/usePaperStream";
import {
  parsePaperAccountPlan,
  parseSimulationPlan,
} from "../product/experiments/api";
import {
  forwardCommit,
  forwardInput,
  forwardPlan,
  forwardSnapshot,
} from "../test/forwardPaperFixtures";
import { paperSnapshot } from "../test/paperFixtures";

describe("server-bound forward paper read compatibility", () => {
  it("binds coordinated source replacement to the account's saved admission pin", () => {
    const raw = forwardSnapshot();
    const changed = "0".repeat(64);
    for (const input of [
      raw.latest_session.input_provenance,
      raw.latest_portfolio.input_provenance,
      raw.latest_portfolio.plan.input_provenance,
      raw.last_rebalance_plan.input_provenance,
    ])
      input.admission_sha256 = changed;
    raw.latest_portfolio.plan.dataset_sha256 = changed;
    raw.last_rebalance_plan.dataset_sha256 = changed;
    expect(() => paperParsers.snapshot(raw)).toThrow();
  });

  it("rejects a foreign admitted source on the first forward stream batch", () => {
    const raw = forwardSnapshot();
    const current = paperParsers.snapshot({
      ...raw,
      latest_session: null,
      latest_portfolio: null,
      last_rebalance_plan: null,
    });
    const input = { ...forwardInput(), admission_sha256: "0".repeat(64) };
    const market = parseWireEvent({
      sequence: 1,
      type: "market.session",
      occurred_at: input.closed_at,
      payload: { ...raw.latest_session, input_provenance: input },
    });
    expect(() => applyPaperEvent(current, market)).toThrow();
    const portfolio = parseWireEvent({
      sequence: 2,
      type: "portfolio.snapshot",
      occurred_at: input.closed_at,
      payload: {
        ...raw.latest_portfolio,
        input_provenance: input,
        plan: {
          ...forwardPlan(),
          dataset_sha256: input.admission_sha256,
          input_provenance: input,
        },
      },
    });
    expect(() => applyPaperEvent(current, portfolio)).toThrow();
  });

  it.each([undefined, "", "not-a-sha"])(
    "rejects missing or malformed saved forward admission pin %s",
    (pin) => {
      const raw = forwardSnapshot();
      expect(() =>
        paperParsers.snapshot({
          ...raw,
          session: {
            ...raw.session,
            strategy_parameters: {
              ...raw.session.strategy_parameters,
              dataset_sha256: pin,
            },
          },
        }),
      ).toThrow();
    },
  );

  it("retains exact receipt lineage through REST and both existing stream event types", () => {
    const raw = forwardSnapshot();
    const current = paperParsers.snapshot(raw);
    expect(current).toEqual(raw);
    for (const [type, payload] of [
      ["market.session", raw.latest_session],
      ["portfolio.snapshot", raw.latest_portfolio],
    ] as const) {
      const event = parseWireEvent({
        sequence: 1,
        type,
        occurred_at: forwardInput().closed_at,
        payload,
      });
      const next = applyPaperEvent(current, event);
      expect(next.latest_portfolio?.equity).toBe("100000.000000000000000001");
      expect(
        type === "market.session" ? next.latest_session : next.latest_portfolio,
      ).toEqual(payload);
      expect(applyPaperEvent(next, event)).toBe(next);
    }
  });

  it("accepts only the dedicated forward paper plan, never a research plan", () => {
    expect(parsePaperAccountPlan(forwardPlan())).toEqual(forwardPlan());
    expect(() => parseSimulationPlan(forwardPlan())).toThrow();
    expect(() =>
      parsePaperAccountPlan({
        ...forwardPlan(),
        account_mode: "HISTORICAL_PAPER_REPLAY",
      }),
    ).toThrow();
    expect(() =>
      parsePaperAccountPlan({
        ...forwardPlan(),
        mode: "historical_exploration",
      }),
    ).toThrow();
  });

  it("advances an input commit watermark without changing financial state even with an intervening status sequence", () => {
    const current = paperParsers.snapshot(forwardSnapshot());
    const event = parseWireEvent(forwardCommit());
    const next = applyPaperEvent(current, event);
    expect(next.last_sequence).toBe(12);
    expect(next.latest_session).toBe(current.latest_session);
    expect(next.latest_portfolio).toBe(current.latest_portfolio);
    expect(next.last_rebalance_plan).toBe(current.last_rebalance_plan);
    expect(next.fills).toBe(current.fills);
  });

  it.each(["replay", "simulated_a_share", "historical_a_share"] as const)(
    "keeps legacy %s accounts readable without lineage",
    (provider) => {
      const raw = paperSnapshot();
      raw.session.provider_type = provider;
      expect(paperParsers.snapshot(raw)).toEqual(raw);
    },
  );

  it.each([
    { schema_version: "UNKNOWN" },
    { paper_session_id: "wrong" },
    { trading_date: "2026-02-30" },
    { admission_sha256: "x".repeat(64) },
    { receipts: [] },
    { receipts: [forwardInput().receipts[0], forwardInput().receipts[0]] },
    { closed_at: "2026-10-12T07:00:00" },
    { next_open_at: "2026-10-12T06:00:00Z" },
  ])("rejects malformed market lineage %j", (change) => {
    const raw = forwardSnapshot();
    expect(() =>
      paperParsers.marketSession({
        ...raw.latest_session,
        input_provenance: { ...forwardInput(), ...change },
      }),
    ).toThrow();
  });

  it("rejects missing and cross-account/day/source lineage instead of relabeling it", () => {
    const raw = forwardSnapshot();
    const damaged = [
      {
        ...raw,
        latest_session: { ...raw.latest_session, input_provenance: undefined },
      },
      {
        ...raw,
        latest_portfolio: {
          ...raw.latest_portfolio,
          input_provenance: undefined,
        },
      },
      {
        ...raw,
        session: { ...raw.session, provider_type: "historical_a_share" },
      },
      {
        ...raw,
        latest_session: { ...raw.latest_session, trading_date: "2026-10-09" },
      },
      {
        ...raw,
        latest_session: {
          ...raw.latest_session,
          source: "FROZEN_HISTORICAL_A_SHARE_REPLAY_V1",
        },
      },
      {
        ...raw,
        latest_portfolio: {
          ...raw.latest_portfolio,
          timestamp: "2026-10-09T07:00:00Z",
        },
      },
      {
        ...raw,
        latest_portfolio: {
          ...raw.latest_portfolio,
          input_provenance: {
            ...forwardInput(),
            paper_session_id: "bb000000-0000-4000-8000-000000000001",
          },
        },
      },
      {
        ...raw,
        last_rebalance_plan: {
          ...forwardPlan(),
          data_snapshot_sha256: "f".repeat(64),
        },
      },
    ];
    for (const value of damaged)
      expect(() => paperParsers.snapshot(value)).toThrow();
  });

  it("rejects malformed commit envelopes", () => {
    const raw = forwardCommit();
    for (const event of [
      { ...raw, sequence: 10 },
      { ...raw, occurred_at: "2026-10-12T07:02:00.000001Z" },
      { ...raw, payload: { ...raw.payload, journal_first_sequence: 0 } },
      { ...raw, payload: { ...raw.payload, journal_last_sequence: 1 } },
      {
        ...raw,
        payload: {
          ...raw.payload,
          commit_observed_at: raw.payload.next_open_at,
        },
        occurred_at: raw.payload.next_open_at,
      },
    ])
      expect(() => parseWireEvent(event)).toThrow();
  });

  it("keeps an older portfolio and plan while the next market session arrives", () => {
    const raw = forwardSnapshot();
    const nextInput = {
      ...forwardInput(),
      trading_date: "2026-10-13",
      input_sha256: "0".repeat(64),
      closed_at: "2026-10-13T07:00:00Z",
      next_open_at: "2026-10-14T01:30:00Z",
      receipts: [
        {
          ...forwardInput().receipts[0]!,
          first_received_at: "2026-10-13T07:01:00Z",
        },
      ],
    };
    raw.latest_session = {
      ...raw.latest_session,
      trading_date: nextInput.trading_date,
      input_provenance: nextInput,
    };
    expect(paperParsers.snapshot(raw).latest_portfolio).toEqual(
      raw.latest_portfolio,
    );
    expect(paperParsers.snapshot(raw).last_rebalance_plan).toEqual(
      forwardPlan(),
    );
  });

  it("does not ignore unknown lineage assertions or mismatched copied receipt content", () => {
    const raw = forwardSnapshot();
    for (const input of [
      { ...forwardInput(), financial_admission: true },
      {
        ...forwardInput(),
        receipts: [{ ...forwardInput().receipts[0]!, verified: true }],
      },
      {
        ...forwardInput(),
        receipts: [{ ...forwardInput().receipts[0]!, receipt_id: "not-uuid" }],
      },
      {
        ...forwardInput(),
        receipts: [
          {
            ...forwardInput().receipts[0]!,
            first_received_at: "2026-10-12T06:59:59.999999Z",
          },
        ],
      },
      {
        ...forwardInput(),
        receipts: [
          {
            ...forwardInput().receipts[0]!,
            first_received_at: forwardInput().next_open_at,
          },
        ],
      },
    ])
      expect(() =>
        paperParsers.marketSession({
          ...raw.latest_session,
          input_provenance: input,
        }),
      ).toThrow();
    expect(() =>
      paperParsers.snapshot({
        ...raw,
        latest_portfolio: {
          ...raw.latest_portfolio,
          input_provenance: {
            ...forwardInput(),
            authorities_sha256: "0".repeat(64),
          },
        },
      }),
    ).toThrow();
  });

  it("rejects conflicting same-day input across market, portfolio and saved plan", () => {
    const raw = forwardSnapshot();
    const changed = { ...forwardInput(), input_sha256: "0".repeat(64) };
    const market = { ...raw.latest_session, input_provenance: changed };
    expect(() =>
      paperParsers.snapshot({ ...raw, latest_session: market }),
    ).toThrow();
    const current = paperParsers.snapshot(raw);
    expect(() =>
      applyPaperEvent(
        current,
        parseWireEvent({
          sequence: 1,
          type: "market.session",
          occurred_at: changed.closed_at,
          payload: market,
        }),
      ),
    ).toThrow();
    const plan = {
      ...forwardPlan(),
      input_provenance: changed,
      data_snapshot_sha256: changed.input_sha256,
    };
    expect(() =>
      paperParsers.snapshot({ ...raw, last_rebalance_plan: plan }),
    ).toThrow();
    expect(() =>
      paperParsers.portfolio({ ...raw.latest_portfolio, plan: null }),
    ).toThrow();
  });

  it("requires complete sorted receipt coverage and the forward account identity", () => {
    const raw = forwardSnapshot();
    const first = forwardInput().receipts[0]!;
    const second = {
      ...first,
      security_id: "CN-A:SZSE:000002",
      receipt_id: "bb000000-0000-4000-8000-000000000001",
    };
    expect(() =>
      paperParsers.marketSession({ ...raw.latest_session, security_count: 2 }),
    ).toThrow();
    expect(() =>
      paperParsers.marketSession({
        ...raw.latest_session,
        security_count: 2,
        input_provenance: { ...forwardInput(), receipts: [second, first] },
      }),
    ).toThrow();
    expect(
      paperParsers.marketSession({
        ...raw.latest_session,
        security_count: 2,
        input_provenance: { ...forwardInput(), receipts: [first, second] },
      }).security_count,
    ).toBe(2);
    for (const change of [
      { symbol: "AAPL" },
      { strategy_type: "moving_average_crossover" },
      { dataset_id: "" },
    ])
      expect(() =>
        paperParsers.session({ ...raw.session, ...change }),
      ).toThrow();
  });

  it("binds market, portfolio and commit stream payloads to this account before applying them", () => {
    const raw = forwardSnapshot();
    const current = paperParsers.snapshot(raw);
    const other = "bb000000-0000-4000-8000-000000000001";
    const market = parseWireEvent({
      sequence: 1,
      type: "market.session",
      occurred_at: forwardInput().closed_at,
      payload: {
        ...raw.latest_session,
        input_provenance: { ...forwardInput(), paper_session_id: other },
      },
    });
    const portfolio = parseWireEvent({
      sequence: 2,
      type: "portfolio.snapshot",
      occurred_at: forwardInput().closed_at,
      payload: {
        ...raw.latest_portfolio,
        plan: {
          ...forwardPlan(),
          paper_session_id: other,
          input_provenance: { ...forwardInput(), paper_session_id: other },
        },
        input_provenance: { ...forwardInput(), paper_session_id: other },
      },
    });
    const commit = parseWireEvent({
      ...forwardCommit(),
      payload: { ...forwardCommit().payload, paper_session_id: other },
    });
    for (const event of [market, portfolio, commit])
      expect(() => applyPaperEvent(current, event)).toThrow();
    expect(() =>
      applyPaperEvent(paperSnapshot(), parseWireEvent(forwardCommit())),
    ).toThrow();
  });

  it.each([
    { plan_version: "PAPER_ACCOUNT_PLAN_V3" },
    { input_provenance: undefined },
    { account_snapshot_trading_date: "2026-10-09" },
    { paper_session_id: "bb000000-0000-4000-8000-000000000001" },
    { dataset_sha256: "0".repeat(64) },
    { data_snapshot_sha256: "0".repeat(64) },
  ])("rejects drifted forward plan terms %j", (change) => {
    expect(() =>
      parsePaperAccountPlan({ ...forwardPlan(), ...change }),
    ).toThrow();
  });
});
