import { useEffect, useState } from "react";

const BEFORE_NAVIGATION = "quant:before-navigation";
const HISTORY_INDEX = "quantNavigationIndex";
const APPROVED_NAVIGATION = "quantNavigationApproved";

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
  if (
    destination.pathname !== window.location.pathname ||
    destination.search !== window.location.search
  ) {
    const request = new CustomEvent(BEFORE_NAVIGATION, { cancelable: true });
    if (!window.dispatchEvent(request)) return false;
  }
  window.history.pushState({ [HISTORY_INDEX]: historyIndex() + 1 }, "", path);
  window.dispatchEvent(
    new PopStateEvent("popstate", { state: { [APPROVED_NAVIGATION]: true } }),
  );
  return true;
}

/** One confirmation boundary for links, commands and browser traversal. */
export function useNavigationGuard(allowLeave: () => boolean): void {
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
      if (!allowLeave()) event.preventDefault();
    };
    const traversal = (event: PopStateEvent) => {
      if (event.state?.[APPROVED_NAVIGATION]) return;
      if (restoring) {
        restoring = false;
        return;
      }
      if (
        `${window.location.pathname}${window.location.search}` ===
          guardedPath ||
        allowLeave()
      )
        return;
      event.stopImmediatePropagation();
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
    window.addEventListener("popstate", traversal, true);
    return () => {
      window.removeEventListener(BEFORE_NAVIGATION, request);
      window.removeEventListener("popstate", traversal, true);
    };
  }, [allowLeave]);
}

export function usePathname(): string {
  const [pathname, setPathname] = useState(window.location.pathname);
  useEffect(() => {
    historyIndex();
    const update = () => setPathname(window.location.pathname);
    window.addEventListener("popstate", update);
    return () => window.removeEventListener("popstate", update);
  }, []);
  return pathname;
}
