import { useEffect, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";
import {
  PAPER_WS_BASE_URL,
  paperApi,
  paperParsers,
  parseWireEvent,
} from "../api/paper";
import type { PaperSnapshot, PaperWireEvent } from "../types/paper";

export type PaperConnection =
  "connecting" | "connected" | "reconnecting" | "closed";

function replaceBy<T>(items: T[], next: T, identity: (item: T) => string): T[] {
  const key = identity(next);
  const index = items.findIndex((item) => identity(item) === key);
  if (index < 0) return [...items, next];
  return items.map((item, itemIndex) => (itemIndex === index ? next : item));
}

export function applyPaperEvent(
  current: PaperSnapshot,
  event: PaperWireEvent,
): PaperSnapshot {
  if (event.sequence === null || event.sequence <= current.last_sequence)
    return current;
  const next = { ...current, last_sequence: event.sequence };
  if (event.type === "session.status") {
    const status = event.payload.status;
    if (typeof status === "string")
      return {
        ...next,
        session: {
          ...current.session,
          status: status as PaperSnapshot["session"]["status"],
        },
      };
  }
  if (event.type === "market.bar")
    return { ...next, latest_bar: paperParsers.marketBar(event.payload) };
  if (event.type === "market.session")
    return {
      ...next,
      latest_session: paperParsers.marketSession(event.payload),
    };
  if (event.type === "signal.created") {
    const signal = paperParsers.signal(event.payload);
    return {
      ...next,
      signals: replaceBy(
        current.signals,
        signal,
        (item) => `${item.strategy_id}:${item.timestamp}:${item.signal_type}`,
      ),
    };
  }
  if (event.type === "risk.decision") {
    const decision = paperParsers.decision(event.payload);
    return {
      ...next,
      risk_decisions: replaceBy(
        current.risk_decisions,
        decision,
        (item) => item.proposal_id,
      ),
    };
  }
  if (event.type === "order.updated") {
    const order = paperParsers.order(event.payload);
    return {
      ...next,
      orders: replaceBy(current.orders, order, (item) => item.order_id),
    };
  }
  if (event.type === "fill.created") {
    const fill = paperParsers.fill(event.payload);
    return {
      ...next,
      fills: replaceBy(current.fills, fill, (item) => item.order_id),
    };
  }
  if (event.type === "portfolio.snapshot") {
    const portfolio = paperParsers.portfolio(event.payload);
    if (
      portfolio.plan &&
      (current.session.provider_type !== "historical_a_share" ||
        portfolio.plan.paper_session_id !== current.session.session_id)
    )
      throw new Error("Paper plan does not belong to this account.");
    return {
      ...next,
      latest_portfolio: portfolio,
      last_rebalance_plan:
        portfolio.plan?.status === "SIMULATION_PREVIEW"
          ? portfolio.plan
          : current.last_rebalance_plan,
    };
  }
  return next;
}

export function usePaperStream(sessionId: string) {
  const { t } = useTranslation("paper");
  const [snapshot, setSnapshot] = useState<PaperSnapshot | null>(null);
  const [connection, setConnection] = useState<PaperConnection>("connecting");
  const [error, setError] = useState<{
    sessionId: string;
    message: string | Error;
  } | null>(null);

  useEffect(() => {
    let active = true;
    let socket: WebSocket | null = null;
    let retry: number | undefined;
    let hydrationController: AbortController | null = null;
    let firstConnection = true;
    let buffered: PaperWireEvent[] = [];
    let terminal = false;
    let hydrating = false;
    let reconnectAttempts = 0;

    const hydrate = () => {
      hydrationController?.abort();
      const controller = new AbortController();
      hydrationController = controller;
      hydrating = true;
      void paperApi
        .snapshot(sessionId, controller.signal)
        .then((hydrated) => {
          if (!active || controller.signal.aborted) return;
          const complete = buffered.reduce(applyPaperEvent, hydrated);
          buffered = [];
          hydrating = false;
          setSnapshot(complete);
          setError(null);
          firstConnection = false;
          reconnectAttempts = 0;
          terminal = ["STOPPED", "FAILED", "INTERRUPTED"].includes(
            complete.session.status,
          );
          setConnection(terminal ? "closed" : "connected");
          if (terminal) socket?.close();
        })
        .catch((reason: unknown) => {
          if (!active || controller.signal.aborted) return;
          hydrating = false;
          setError({
            sessionId,
            message:
              reason instanceof Error ? reason : t("detail.hydrateError"),
          });
          if (
            reason instanceof ApiError &&
            [401, 403, 404].includes(reason.status)
          )
            terminal = true;
          socket?.close();
        });
    };

    const connect = () => {
      if (!active) return;
      setConnection(firstConnection ? "connecting" : "reconnecting");
      socket = new WebSocket(
        `${PAPER_WS_BASE_URL}/api/paper-trading/sessions/ws/${sessionId}`,
      );
      socket.onopen = hydrate;
      socket.onmessage = (message) => {
        if (!active) return;
        try {
          const event = parseWireEvent(JSON.parse(String(message.data)));
          if (event.type === "stream.connected") return;
          if (event.type === "stream.resync_required") {
            socket?.close();
            return;
          }
          if (
            event.type === "session.status" &&
            ["STOPPED", "FAILED", "INTERRUPTED"].includes(
              String(event.payload.status),
            )
          ) {
            terminal = true;
          }
          if (hydrating && buffered.length >= 256) {
            buffered = [];
            terminal = false;
            socket?.close();
            return;
          }
          if (hydrating) buffered.push(event);
          else
            setSnapshot((current) =>
              current?.session.session_id === sessionId
                ? applyPaperEvent(current, event)
                : current,
            );
          // Status events carry no lifecycle timestamps or sanitized failure text.
          // Refresh REST, buffering subsequent incremental events until it completes.
          if (event.type === "session.status") hydrate();
          if (terminal) {
            setConnection("closed");
            socket?.close();
          }
        } catch {
          setError({
            sessionId,
            message: t("detail.malformedEvent"),
          });
          socket?.close();
        }
      };
      socket.onerror = () => socket?.close();
      socket.onclose = () => {
        if (!active) return;
        if (terminal) {
          setConnection("closed");
          return;
        }
        hydrationController?.abort();
        hydrationController = null;
        if (reconnectAttempts >= 3) {
          setConnection("closed");
          setError((current) =>
            current?.sessionId === sessionId
              ? current
              : { sessionId, message: t("detail.connectionError") },
          );
          return;
        }
        setConnection("reconnecting");
        retry = window.setTimeout(connect, 1000 * 2 ** reconnectAttempts);
        reconnectAttempts += 1;
      };
    };

    connect();
    return () => {
      active = false;
      hydrationController?.abort();
      if (retry !== undefined) window.clearTimeout(retry);
      socket?.close();
    };
  }, [sessionId, t]);

  return {
    snapshot: snapshot?.session.session_id === sessionId ? snapshot : null,
    connection,
    error: error?.sessionId === sessionId ? error.message : null,
  };
}
