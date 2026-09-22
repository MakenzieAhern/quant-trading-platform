// Presentation settings may work for this tab even when browser storage is blocked.
// Never use this fallback for financial results or persisted research tasks.
const fallback = new Map<string, string>();
const unsaved = new Set<string>();
const eventName = "quant:presentation-settings";
const notify = () => window.dispatchEvent(new Event(eventName));

export function readPresentationSetting(key: string): string | null {
  if (unsaved.has(key)) return fallback.get(key) ?? null;
  try {
    return window.localStorage.getItem(key);
  } catch {
    unsaved.add(key);
    queueMicrotask(notify);
    return fallback.get(key) ?? null;
  }
}

export function writePresentationSetting(key: string, value: string): void {
  fallback.set(key, value);
  try {
    window.localStorage.setItem(key, value);
    unsaved.delete(key);
  } catch {
    unsaved.add(key);
  }
  notify();
}

export function presentationSettingsUnsaved(): boolean {
  return unsaved.size > 0;
}

export function subscribePresentationSettings(listener: () => void) {
  window.addEventListener("storage", listener);
  window.addEventListener(eventName, listener);
  return () => {
    window.removeEventListener("storage", listener);
    window.removeEventListener(eventName, listener);
  };
}
