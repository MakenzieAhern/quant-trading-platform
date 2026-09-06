import type {
  BacktestResult,
  BacktestRun,
  CreateBacktestRequest,
  CreateBacktestResponse,
  EquityPoint,
  Fill,
  Order,
  Page,
  RiskDecision,
  Signal,
} from "../types/backtests";
import { apiRequest } from "./client";
import {
  parseCreate,
  parseEquityPage,
  parseFillPage,
  parseOrderPage,
  parseResult,
  parseRiskDecisionPage,
  parseRun,
  parseRunPage,
  parseSignalPage,
} from "./contracts";

const pageQuery = (limit: number, offset: number) =>
  `?${new URLSearchParams({ limit: String(limit), offset: String(offset) })}`;

export const backtestsApi = {
  create(
    payload: CreateBacktestRequest,
    idempotencyKey: string,
    signal?: AbortSignal,
  ) {
    return apiRequest<CreateBacktestResponse>(
      "/api/backtests",
      {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "Idempotency-Key": idempotencyKey,
        },
        body: JSON.stringify(payload),
      },
      signal,
      parseCreate,
    );
  },
  list(limit = 20, offset = 0, signal?: AbortSignal) {
    return apiRequest<Page<BacktestRun>>(
      `/api/backtests${pageQuery(limit, offset)}`,
      {},
      signal,
      parseRunPage,
    );
  },
  get(runId: string, signal?: AbortSignal) {
    return apiRequest<BacktestRun>(
      `/api/backtests/${runId}`,
      {},
      signal,
      parseRun,
    );
  },
  result(runId: string, signal?: AbortSignal) {
    return apiRequest<BacktestResult>(
      `/api/backtests/${runId}/result`,
      {},
      signal,
      parseResult,
    );
  },
  signals(runId: string, limit = 50, offset = 0, signal?: AbortSignal) {
    return apiRequest<Page<Signal>>(
      `/api/backtests/${runId}/signals${pageQuery(limit, offset)}`,
      {},
      signal,
      parseSignalPage,
    );
  },
  riskDecisions(runId: string, limit = 50, offset = 0, signal?: AbortSignal) {
    return apiRequest<Page<RiskDecision>>(
      `/api/backtests/${runId}/risk-decisions${pageQuery(limit, offset)}`,
      {},
      signal,
      parseRiskDecisionPage,
    );
  },
  orders(runId: string, limit = 50, offset = 0, signal?: AbortSignal) {
    return apiRequest<Page<Order>>(
      `/api/backtests/${runId}/orders${pageQuery(limit, offset)}`,
      {},
      signal,
      parseOrderPage,
    );
  },
  fills(runId: string, limit = 50, offset = 0, signal?: AbortSignal) {
    return apiRequest<Page<Fill>>(
      `/api/backtests/${runId}/fills${pageQuery(limit, offset)}`,
      {},
      signal,
      parseFillPage,
    );
  },
  equity(runId: string, limit = 200, offset = 0, signal?: AbortSignal) {
    return apiRequest<Page<EquityPoint>>(
      `/api/backtests/${runId}/equity${pageQuery(limit, offset)}`,
      {},
      signal,
      parseEquityPage,
    );
  },
};
