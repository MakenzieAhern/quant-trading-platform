import { plan } from "../product/experiments/fixtures.test-data";
import type { PaperAccountPlan } from "../product/experiments/types";
import type {
  PaperInputProvenance,
  PaperSnapshot,
  PaperWireEvent,
} from "../types/paper";
import { PAPER_ID, paperSession, paperSnapshot } from "./paperFixtures";

// Contract-shape fixtures only: these hashes are not source admission evidence.
export const FORWARD_DAY = "2026-10-12";
export function forwardInput() {
  return {
    schema_version: "PAPER_DAILY_INPUT_V1",
    paper_session_id: PAPER_ID,
    trading_date: FORWARD_DAY,
    admission_sha256: "a".repeat(64),
    calendar_sha256: "b".repeat(64),
    authorities_sha256: "c".repeat(64),
    session_sha256: "d".repeat(64),
    input_sha256: "e".repeat(64),
    closed_at: FORWARD_DAY + "T07:00:00Z",
    next_open_at: "2026-10-13T01:30:00Z",
    receipts: [
      {
        security_id: "CN-A:SZSE:000001",
        receipt_id: "aa000000-0000-4000-8000-000000000001",
        manifest_sha256: "f".repeat(64),
        first_received_at: FORWARD_DAY + "T07:01:00Z",
      },
    ],
  } satisfies PaperInputProvenance;
}
export function forwardPlan() {
  const input = forwardInput();
  return {
    ...plan,
    mode: "forward_paper",
    account_mode: "FORWARD_PAPER",
    paper_session_id: PAPER_ID,
    plan_version: "PAPER_FORWARD_PLAN_V1",
    as_of_trading_date: FORWARD_DAY,
    account_snapshot_trading_date: FORWARD_DAY,
    next_accepted_session: "2026-10-13",
    dataset_sha256: input.admission_sha256,
    data_snapshot_sha256: input.input_sha256,
    submitted_to_account: true,
    input_provenance: input,
  } satisfies PaperAccountPlan;
}
export function forwardSnapshot() {
  const input = forwardInput();
  return {
    ...paperSnapshot("RUNNING"),
    session: {
      ...paperSession("RUNNING"),
      provider_type: "forward_a_share",
      dataset_id: "synthetic-contract-shape-admission",
      symbol: "CN-A",
      strategy_type: "cn_a_cross_sectional_momentum_low_vol_v1",
      strategy_parameters: {
        dataset_sha256: input.admission_sha256,
        plan_version: "PAPER_FORWARD_PLAN_V1",
      },
    },
    latest_session: {
      trading_date: FORWARD_DAY,
      security_count: 1,
      source: "RECEIPT_BOUND_FORWARD_A_SHARE_V1",
      input_provenance: input,
    },
    latest_portfolio: {
      timestamp: input.closed_at,
      cash: "100000.000000000000000001",
      market_value: "0",
      equity: "100000.000000000000000001",
      realized_pnl: "0",
      unrealized_pnl: "0",
      cumulative_commission: "0",
      drawdown: "0",
      positions: [],
      plan: forwardPlan(),
      input_provenance: input,
    },
    last_rebalance_plan: forwardPlan(),
  } satisfies PaperSnapshot;
}
export function forwardCommit() {
  return {
    sequence: 12,
    type: "input.committed",
    occurred_at: FORWARD_DAY + "T07:02:00Z",
    payload: {
      schema_version: "PAPER_INPUT_COMMIT_V1",
      paper_session_id: PAPER_ID,
      trading_date: FORWARD_DAY,
      input_sha256: forwardInput().input_sha256,
      journal_first_sequence: 2,
      journal_last_sequence: 10,
      commit_observed_at: FORWARD_DAY + "T07:02:00Z",
      next_open_at: "2026-10-13T01:30:00Z",
    },
  } satisfies PaperWireEvent;
}
