import { describe, expect, it } from "vitest";
import { parsePaperInput } from "./paperInput";
import { paperParsers, parseWireEvent } from "./paper";
import { forwardInput, forwardSnapshot } from "../test/forwardPaperFixtures";

function dynamicInput() {
  const original = forwardInput();
  return {
    ...original,
    schema_version: "PAPER_DAILY_INPUT_V2",
    context: {
      candidate_id: original.paper_session_id,
      candidate_sha256: "a".repeat(64),
      observation_sha256: "b".repeat(64),
      verifier: "SYNTHETIC_TEST_ONLY",
      first_captured_at: original.closed_at,
      registered_at: original.closed_at,
      sources: [
        {
          authority_names: [
            "ADJUSTMENTS",
            "CALENDAR",
            "CORPORATE_ACTIONS",
            "MARKET_RULES",
            "SECURITY_MASTER",
            "SSE_ST",
            "SUSPENSIONS",
            "SZSE_ST",
            "TRANSACTION_COSTS",
          ],
          evidence_sha256: "c".repeat(64),
          receipt_sha256: "d".repeat(64),
          published_at: original.closed_at,
          completed_at: original.closed_at,
          first_observed_at: original.closed_at,
        },
      ],
    },
  };
}

describe("qualified context wire lineage, not source certification", () => {
  it("preserves legacy input shape and dynamic context without dropping fields", () => {
    expect(parsePaperInput(forwardInput())).toEqual(forwardInput());
    expect(parsePaperInput(dynamicInput())).toEqual(dynamicInput());
  });

  it("retains V2 in actual REST snapshot, market and portfolio WebSocket parsers", () => {
    const base = forwardSnapshot();
    const input = dynamicInput();
    const plan = { ...base.last_rebalance_plan, input_provenance: input };
    const raw = {
      ...base,
      latest_session: { ...base.latest_session, input_provenance: input },
      latest_portfolio: {
        ...base.latest_portfolio,
        input_provenance: input,
        plan,
      },
      last_rebalance_plan: plan,
    };
    expect(paperParsers.snapshot(raw)).toEqual(raw);
    for (const [type, payload] of [
      ["market.session", raw.latest_session],
      ["portfolio.snapshot", raw.latest_portfolio],
    ] as const) {
      const event = {
        sequence: 1,
        type,
        occurred_at: input.closed_at,
        payload,
      };
      expect(parseWireEvent(event)).toEqual(event);
    }
  });

  it.each([
    "missing",
    "extra",
    "late",
    "capture_after_registration",
    "missing_coverage",
    "duplicate_source",
    "duplicate_authority",
    "unknown_authority",
    "source_after_capture",
    "published_after_completed",
    "completed_after_observed",
    "hash",
    "uuid",
    "verifier",
  ])("rejects corrupt context %s", (fault) => {
    const input = dynamicInput();
    const context = input.context;
    const source = context.sources[0]!;
    const altered: Record<string, unknown> = input;
    switch (fault) {
      case "missing":
        delete altered.context;
        break;
      case "extra":
        Object.assign(context, { approved: true });
        break;
      case "late":
        context.registered_at = input.next_open_at;
        break;
      case "capture_after_registration":
        context.first_captured_at = input.next_open_at;
        break;
      case "missing_coverage":
        source.authority_names.pop();
        break;
      case "duplicate_source":
        context.sources.push({ ...source });
        break;
      case "duplicate_authority":
        source.authority_names.push("TRANSACTION_COSTS");
        break;
      case "unknown_authority":
        source.authority_names.push("UNKNOWN");
        break;
      case "source_after_capture":
        source.first_observed_at = input.next_open_at;
        break;
      case "published_after_completed":
        source.published_at = input.next_open_at;
        break;
      case "completed_after_observed":
        source.completed_at = input.next_open_at;
        break;
      case "hash":
        source.receipt_sha256 = "bad";
        break;
      case "uuid":
        context.candidate_id = "bad";
        break;
      case "verifier":
        context.verifier = "x".repeat(129);
        break;
    }
    expect(() => parsePaperInput(altered)).toThrow();
  });

  it("refuses silently relabeling V2 context as V1", () => {
    expect(() =>
      parsePaperInput({
        ...dynamicInput(),
        schema_version: "PAPER_DAILY_INPUT_V1",
      }),
    ).toThrow();
  });
});
