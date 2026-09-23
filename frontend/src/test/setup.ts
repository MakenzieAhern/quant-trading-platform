import "@testing-library/jest-dom/vitest";
import "../i18n";
import { cleanup } from "@testing-library/react";
import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => vi.stubGlobal("scrollTo", vi.fn()));

afterEach(() => {
  cleanup();
  vi.restoreAllMocks();
  vi.unstubAllGlobals();
  vi.useRealTimers();
  window.history.replaceState({}, "", "/backtests");
});
