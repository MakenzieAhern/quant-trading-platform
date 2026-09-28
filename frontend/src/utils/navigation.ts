import { useEffect, useLayoutEffect, useRef, useState } from "react";

const BEFORE_NAVIGATION = "quant:before-navigation";
const BEFORE_TRAVERSAL = "quant:before-traversal";
const HISTORY_INDEX = "quantNavigationIndex";
const APPROVED_NAVIGATION = "quantNavigationApproved";
const checkedTraversals = new WeakSet<PopStateEvent>();
type ReturnEntry = { url: string; index: number };

function returnEntries(index: number): ReturnEntry[] {
  const entries: unknown = window.history.state?.quantNavigationReturns;
  if (
    window.history.state?.quantNavigationUrl !== window.location.href ||
    !Array.isArray(entries) ||
    entries.length > 32 ||
    !entries.every(
      (entry, offset): entry is ReturnEntry =>
        entry !== null &&
        typeof entry === "object" &&
        typeof entry.url === "string" &&
        Number.isSafeInteger(entry.index) &&
        entry.index >= 0 &&
        entry.index === index - entries.length + offset,
    )
  )
    return [];
  return entries;
}

function historyIndex(): number {
  const index: unknown = window.history.state?.[HISTORY_INDEX];
  if (typeof index === "number" && Number.isSafeInteger(index)) return index;
  window.history.replaceState(
    { ...window.history.state, [HISTORY_INDEX]: 0 },
    "",
  );
  return 0;
}

export function navigate(path: string): boolean {
  const destination = new URL(path, window.location.href);
  if (destination.href === window.location.href) return true;
  const changingLocation =
    destination.pathname !== window.location.pathname ||
    destination.search !== window.location.search;
  if (changingLocation) {
    const request = new CustomEvent(BEFORE_NAVIGATION, { cancelable: true });
    if (!window.dispatchEvent(request)) return false;
  }
  const index = historyIndex();
  const parents = returnEntries(index);
  window.history.pushState(
    {
      [HISTORY_INDEX]: index + 1,
      quantNavigationUrl: destination.href,
      // ponytail: retain 32 managed ancestors; older/unknown history uses the internal fallback.
      quantNavigationReturns: [
        ...parents,
        { url: window.location.href, index },
      ].slice(-32),
    },
    "",
    path,
  );
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: { [APPROVED_NAVIGATION]: true } }),
  );
  if (changingLocation) window.scrollTo(0, 0);
  return true;
}

/** Keep managed return entries valid when an owned detail replaces its own URL. */
export function replaceUrl(path: string): void {
  const before = window.location.href;
  const state = window.history.state;
  window.history.replaceState(
    state?.quantNavigationUrl === before
      ? { ...state, quantNavigationUrl: new URL(path, before).href }
      : state,
    "",
    path,
  );
}

export function navigateBack(path: string): void {
  const index = historyIndex();
  const url = new URL(path, window.location.href).href;
  const parent = returnEntries(index)
    .slice()
    .reverse()
    .find((entry) => entry.url === url);
  if (parent) window.history.go(parent.index - index);
  else navigate(path);
}

/** One confirmation boundary for links, commands and browser traversal. */
export function useNavigationGuard(allowLeave: () => boolean): void {
  const allowLeaveRef = useRef(allowLeave);
  useLayoutEffect(() => {
    allowLeaveRef.current = allowLeave;
  });
  useEffect(() => {
    const guardedPath = `${window.location.pathname}${window.location.search}`;
    const guardedIndex = historyIndex();
    // Native entry indices include same-document entries from before this app boot.
    // https://developer.chrome.com/docs/web-platform/navigation-api#navigation_entries
    const navigation = (
      window as Window & { navigation?: { currentEntry?: { index: number } } }
    ).navigation;
    const guardedNativeIndex = navigation?.currentEntry?.index;
    let restoring = false;
    const request = (event: Event) => {
      if (!allowLeaveRef.current()) event.preventDefault();
    };
    const traversal = (request: Event) => {
      const event = (request as CustomEvent<PopStateEvent>).detail;
      if (event.state?.[APPROVED_NAVIGATION]) return;
      if (restoring) {
        restoring = false;
        return;
      }
      if (
        `${window.location.pathname}${window.location.search}` ===
          guardedPath ||
        allowLeaveRef.current()
      )
        return;
      request.preventDefault();
      const targetIndex: unknown = event.state?.[HISTORY_INDEX];
      const nativeIndex = navigation?.currentEntry?.index;
      const delta =
        guardedNativeIndex !== undefined && nativeIndex !== undefined
          ? guardedNativeIndex - nativeIndex
          : typeof targetIndex === "number"
            ? guardedIndex - targetIndex
            : 1;
      // Undo the traversal, not its history entries; accepted Back/Forward stays intact.
      restoring = true;
      window.history.go(delta);
    };
    window.addEventListener(BEFORE_NAVIGATION, request);
    window.addEventListener(BEFORE_TRAVERSAL, traversal);
    return () => {
      window.removeEventListener(BEFORE_NAVIGATION, request);
      window.removeEventListener(BEFORE_TRAVERSAL, traversal);
    };
  }, []);
}

function currentPathname(): string {
  // This accepted legacy alias must use the same list/history identity before mount.
  if (window.location.pathname === "/experiments/") {
    const source = window.location.href;
    const canonical = new URL(source);
    canonical.pathname = "/experiments";
    const state = window.history.state;
    window.history.replaceState(
      state?.quantNavigationUrl === source
        ? { ...state, quantNavigationUrl: canonical.href }
        : state,
      "",
      canonical.href,
    );
  }
  return window.location.pathname;
}

export function usePathname(): string {
  const [pathname, setPathname] = useState(currentPathname);
  useEffect(() => {
    historyIndex();
    const update = (event: PopStateEvent) => {
      if (
        !event.state?.[APPROVED_NAVIGATION] &&
        !checkedTraversals.has(event)
      ) {
        // App and shell both read the location; one traversal needs one decision.
        checkedTraversals.add(event);
        if (
          !window.dispatchEvent(
            new CustomEvent(BEFORE_TRAVERSAL, {
              cancelable: true,
              detail: event,
            }),
          )
        ) {
          event.stopImmediatePropagation();
          return;
        }
      }
      setPathname(currentPathname());
    };
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return pathname;
}
