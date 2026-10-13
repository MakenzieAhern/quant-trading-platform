import { useEffect, useRef, useState } from "react";
import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";
import {
  PAPER_WS_BASE_URL,
  paperApi,
  paperParsers,
  parseWireEvent,
  validatePaperAccountEvent,
  validatePaperInputState,
} from "../api/paper";
import type {
  PaperSession,
  PaperSessionStatus,
  PaperSnapshot,
  PaperState,
  PaperWireEvent,
} from "../types/paper";

export type PaperConnection =
  "connecting" | "connected" | "reconnecting" | "closed";

type FillAnnouncement = {
  sequence: number;
  language: string;
  text: string;
};

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
  const next = applyPaperStateEvent(current, event);
  if (next === current) return current;
  if (event.type === "signal.created") {
    const signal = paperParsers.signal(event.payload);
    return { ...next, signals: [...current.signals, signal] };
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
    return { ...next, fills: [...current.fills, fill] };
  }
  return next;
}

function applyPaperStateEvent<T extends PaperState>(
  current: T,
  event: PaperWireEvent,
): T {
  if (event.sequence === null || event.sequence <= current.last_sequence)
    return current;
  validatePaperAccountEvent(current.session, event);
  const next = { ...current, last_sequence: event.sequence };
  if (event.type === "session.status") {
    const status = event.payload.status;
    if (typeof status === "string")
      return {
        ...next,
        session: {
          ...current.session,
          status: status as PaperState["session"]["status"],
        },
      };
  }
  if (event.type === "market.bar")
    return { ...next, latest_bar: paperParsers.marketBar(event.payload) };
  if (event.type === "market.session") {
    const updated = {
      ...next,
      latest_session: paperParsers.marketSession(event.payload),
    };
    validatePaperInputState(updated);
    return updated;
  }
  if (event.type === "portfolio.snapshot") {
    const portfolio = paperParsers.portfolio(event.payload);
    const updated = {
      ...next,
      latest_portfolio: portfolio,
      last_rebalance_plan:
        portfolio.plan?.status === "SIMULATION_PREVIEW"
          ? portfolio.plan
          : current.last_rebalance_plan,
    };
    validatePaperInputState(updated);
    return updated;
  }
  return next;
}

export function usePaperStream(sessionId: string) {
  const { t, i18n } = useTranslation("paper");
  const hydrateRef = useRef<(() => Promise<void>) | null>(null);
  const acceptedSequence = useRef<number | null>(null);
  const [snapshot, setSnapshot] = useState<PaperState | null>(null);
  const [collectionSequence, setCollectionSequence] = useState<{
    sessionId: string;
    sequence: number;
  } | null>(null);
  const [collectionInvalidation, setCollectionInvalidation] = useState<{
    sessionId: string;
    sequence: number;
  } | null>(null);
  const [announcementState, setAnnouncementState] = useState<{
    sessionId: string;
    value: FillAnnouncement | null;
  }>({ sessionId, value: null });
  if (
    announcementState.sessionId !== sessionId ||
    (announcementState.value !== null &&
      announcementState.value.language !== i18n.language)
  )
    setAnnouncementState({ sessionId, value: null });
  const [connection, setConnection] = useState<PaperConnection>("connecting");
  const [error, setError] = useState<{
    sessionId: string;
    message: string | Error;
  } | null>(null);

  useEffect(() => {
    acceptedSequence.current = null;
    let active = true;
    let socket: WebSocket | null = null;
    let retry: number | undefined;
    let hydrationController: AbortController | null = null;
    let firstConnection = true;
    let buffered: PaperWireEvent[] = [];
    let terminal = false;
    let hydrating = false;
    let hydrationWork: Promise<void> | null = null;
    let hydrateAgain = false;
    let collectionRefresh: number | undefined;
    let verifiedSequence = 0;
    // Validate incremental state synchronously inside onmessage's error boundary.
    let accountState: PaperState | null = null;
    let reconnectAttempts = 0;
    let openingChecked = false;
    let openingController: AbortController | null = null;

    const hydrate = (replacePending = false): Promise<void> => {
      if (
        hydrating &&
        !hydrationController?.signal.aborted &&
        !replacePending
      ) {
        hydrateAgain = true;
        return hydrationWork ?? Promise.resolve();
      }
      hydrationController?.abort();
      const controller = new AbortController();
      hydrationController = controller;
      hydrating = true;
      hydrateAgain = false;
      hydrationWork = paperApi
        .state(sessionId, controller.signal)
        .then((hydrated) => {
          if (!active || controller.signal.aborted) return;
          if (
            hydrated.last_sequence <
            Math.max(verifiedSequence, acceptedSequence.current ?? 0)
          )
            throw new Error("Paper state watermark moved backwards.");
          const complete = buffered.reduce(applyPaperStateEvent, hydrated);
          buffered = [];
          verifiedSequence = hydrated.last_sequence;
          accountState = complete;
          acceptedSequence.current = Math.max(
            acceptedSequence.current ?? complete.last_sequence,
            complete.last_sequence,
          );
          setSnapshot(complete);
          setCollectionSequence({
            sessionId,
            sequence: hydrated.last_sequence,
          });
          setError(null);
          firstConnection = false;
          const socketOpen = socket?.readyState === WebSocket.OPEN;
          if (socketOpen) reconnectAttempts = 0;
          terminal = ["STOPPED", "FAILED", "INTERRUPTED"].includes(
            complete.session.status,
          );
          setConnection(
            terminal ? "closed" : socketOpen ? "connected" : "reconnecting",
          );
          if (terminal) socket?.close();
        })
        .catch((reason: unknown) => {
          if (!active || controller.signal.aborted) return;
          buffered = [];
          verifiedSequence = Math.max(
            verifiedSequence,
            acceptedSequence.current ?? 0,
          );
          acceptedSequence.current = null;
          setSnapshot(null);
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
        })
        .finally(() => {
          if (hydrationController !== controller) return;
          hydrating = false;
          hydrationWork = null;
          if (hydrateAgain && active && !controller.signal.aborted) {
            hydrateAgain = false;
            queueCollectionRefresh();
          }
        });
      return hydrationWork;
    };
    const queueCollectionRefresh = () => {
      if (!active || collectionRefresh !== undefined) return;
      // Coalesce a financial event burst into one authoritative watermark read.
      collectionRefresh = window.setTimeout(() => {
        collectionRefresh = undefined;
        void hydrate();
      }, 100);
    };
    hydrateRef.current = () => hydrate(true);

    const connect = () => {
      if (!active || terminal) return;
      setConnection(firstConnection ? "connecting" : "reconnecting");
      socket = new WebSocket(
        `${PAPER_WS_BASE_URL}/api/paper-trading/sessions/ws/${sessionId}`,
      );
      let opened = false;
      socket.onopen = () => {
        opened = true;
        openingController?.abort();
        hydrate();
      };
      socket.onmessage = (message) => {
        if (!active) return;
        try {
          const event = parseWireEvent(JSON.parse(String(message.data)));
          if (event.type === "stream.connected") return;
          if (event.type === "stream.resync_required") {
            socket?.close();
            return;
          }
          const advances =
            event.sequence !== null &&
            (acceptedSequence.current === null ||
              event.sequence > acceptedSequence.current);
          const incremental =
            !hydrating && advances && accountState
              ? applyPaperStateEvent(accountState, event)
              : null;
          if (incremental) accountState = incremental;
          if (hydrating && buffered.length >= 256) {
            buffered = [];
            terminal = false;
            socket?.close();
            return;
          }
          if (hydrating) buffered.push(event);
          else {
            if (
              event.sequence !== null &&
              acceptedSequence.current !== null &&
              event.sequence > acceptedSequence.current
            ) {
              acceptedSequence.current = event.sequence;
              if (event.type === "fill.created") {
                const fill = paperParsers.fill(event.payload);
                setAnnouncementState((current) =>
                  current.sessionId === sessionId
                    ? {
                        sessionId,
                        value: {
                          sequence: event.sequence!,
                          language: i18n.language,
                          text: t("detail.fillAnnouncement", {
                            side: t(`detail.directions.${fill.side}`, {
                              defaultValue: fill.side,
                            }),
                            quantity: fill.quantity,
                            symbol: fill.symbol,
                            price: fill.price,
                          }),
                        },
                      }
                    : current,
                );
              }
            }
            setSnapshot((current) =>
              current?.session.session_id === sessionId
                ? (incremental ?? current)
                : current,
            );
          }
          // Status events carry no lifecycle timestamps or sanitized failure text.
          // Refresh REST, buffering subsequent incremental events until it completes.
          if (event.type === "session.status") hydrate(true);
          if (
            advances &&
            [
              "signal.created",
              "risk.decision",
              "order.updated",
              "fill.created",
            ].includes(event.type)
          ) {
            setCollectionInvalidation((current) =>
              current?.sessionId === sessionId &&
              current.sequence >= event.sequence!
                ? current
                : { sessionId, sequence: event.sequence! },
            );
            queueCollectionRefresh();
          }
          if (terminal) {
            setConnection("closed");
            socket?.close();
          }
        } catch {
          verifiedSequence = Math.max(
            verifiedSequence,
            acceptedSequence.current ?? 0,
          );
          acceptedSequence.current = null;
          setSnapshot(null);
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
        if (!opened && firstConnection && !openingChecked) {
          openingChecked = true;
          const controller = new AbortController();
          openingController = controller;
          void paperApi
            .state(sessionId, controller.signal)
            .then((openingSnapshot) => {
              if (!active || controller.signal.aborted || !firstConnection)
                return;
              if (
                !["STOPPED", "FAILED", "INTERRUPTED"].includes(
                  openingSnapshot.session.status,
                )
              )
                return;
              terminal = true;
              firstConnection = false;
              acceptedSequence.current = Math.max(
                acceptedSequence.current ?? openingSnapshot.last_sequence,
                openingSnapshot.last_sequence,
              );
              if (retry !== undefined) window.clearTimeout(retry);
              setSnapshot(openingSnapshot);
              setCollectionSequence({
                sessionId,
                sequence: openingSnapshot.last_sequence,
              });
              verifiedSequence = openingSnapshot.last_sequence;
              accountState = openingSnapshot;
              setError(null);
              setConnection("closed");
              socket?.close();
            })
            .catch((reason: unknown) => {
              if (!active || controller.signal.aborted || !firstConnection)
                return;
              if (
                reason instanceof ApiError &&
                [401, 403, 404].includes(reason.status)
              ) {
                terminal = true;
                if (retry !== undefined) window.clearTimeout(retry);
                socket?.close();
                setConnection("closed");
                setError({ sessionId, message: reason });
              }
            });
        }
        if (terminal) {
          setConnection("closed");
          return;
        }
        hydrationController?.abort();
        hydrationController = null;
        hydrationWork = null;
        hydrating = false;
        hydrateAgain = false;
        buffered = [];
        if (collectionRefresh !== undefined)
          window.clearTimeout(collectionRefresh);
        collectionRefresh = undefined;
        if (reconnectAttempts >= 3) {
          acceptedSequence.current = null;
          setSnapshot(null);
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
      hydrateRef.current = null;
      acceptedSequence.current = null;
      hydrationController?.abort();
      openingController?.abort();
      if (retry !== undefined) window.clearTimeout(retry);
      if (collectionRefresh !== undefined)
        window.clearTimeout(collectionRefresh);
      socket?.close();
    };
  }, [sessionId, t, i18n.language]);

  return {
    snapshot: snapshot?.session.session_id === sessionId ? snapshot : null,
    collectionSequence:
      collectionSequence?.sessionId === sessionId
        ? collectionSequence.sequence
        : null,
    collectionsPending:
      collectionInvalidation?.sessionId === sessionId &&
      (collectionSequence?.sessionId !== sessionId ||
        collectionInvalidation.sequence > collectionSequence.sequence),
    fillAnnouncement:
      announcementState.sessionId === sessionId
        ? announcementState.value
        : null,
    connection,
    error: error?.sessionId === sessionId ? error.message : null,
    acknowledge: (before: PaperSessionStatus, accepted: PaperSession) => {
      if (accepted.session_id !== sessionId) {
        acceptedSequence.current = null;
        setSnapshot(null);
        setError({
          sessionId,
          message: new Error("Paper command account mismatch"),
        });
        return;
      }
      setSnapshot((current) =>
        current?.session.session_id === sessionId &&
        current.session.status === before
          ? { ...current, session: accepted }
          : current,
      );
    },
    refresh: () => hydrateRef.current?.() ?? Promise.resolve(),
  };
}
