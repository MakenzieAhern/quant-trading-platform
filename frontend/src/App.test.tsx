import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import { App } from "./App";
import { i18n } from "./i18n";
import { experimentApi } from "./product/experiments/api";
import { capabilities } from "./product/experiments/fixtures.test-data";
import { jsonResponse, RUN_ID } from "./test/fixtures";

const health = {
  status: "ok",
  service: "Quant Trading Platform",
  version: "1.0.0",
  environment: "development",
  broker_mode: "paper",
};

describe("routing", () => {
  it("leaves the skip link reachable on direct load and focuses main after navigation", async () => {
    await i18n.changeLanguage("en-US");
    window.history.replaceState({}, "", "/");
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
    render(<App />);
    const main = screen.getByRole("main");
    expect(main).not.toHaveFocus();
    fireEvent.click(screen.getByRole("link", { name: "Strategies" }));
    await waitFor(() => expect(screen.getByRole("main")).toHaveFocus());
  });

  it("closes and restores the strategy drawer with Back and Forward", async () => {
    await i18n.changeLanguage("en-US");
    window.history.replaceState({}, "", "/strategies");
    Object.defineProperties(HTMLDialogElement.prototype, {
      showModal: {
        configurable: true,
        value(this: HTMLDialogElement) {
          this.setAttribute("open", "");
        },
      },
      close: {
        configurable: true,
        value(this: HTMLDialogElement) {
          this.removeAttribute("open");
        },
      },
    });
    vi.spyOn(experimentApi, "capabilities").mockResolvedValue(capabilities);
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
    const view = render(<App />);
    const trigger = await screen.findByRole("button", {
      name: /Explore strategy/,
    });
    trigger.focus();
    fireEvent.click(trigger);
    expect(window.location.hash).toContain(
      capabilities.strategies[0].strategy_id,
    );
    expect(screen.getByRole("dialog")).toBeInTheDocument();
    act(() => window.history.back());
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(window.location.pathname).toBe("/strategies");
    expect(trigger).toHaveFocus();
    act(() => window.history.forward());
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(window.location.hash).toBe("");
    view.unmount();
    window.history.replaceState(
      {},
      "",
      `/strategies#strategy=${capabilities.strategies[0].strategy_id}`,
    );
    render(<App />);
    expect(await screen.findByRole("dialog")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Close" }));
    await waitFor(() =>
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument(),
    );
    expect(window.location.pathname).toBe("/strategies");
    expect(window.location.hash).toBe("");
  });

  it("releases mobile background isolation when resizing to desktop", async () => {
    const desktop = Object.assign(new EventTarget(), { matches: false });
    vi.stubGlobal(
      "matchMedia",
      vi.fn(() => desktop),
    );
    window.history.replaceState({}, "", "/unknown");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
    render(<App />);
    await screen.findByText("Service online");
    fireEvent.click(screen.getByRole("button", { name: "Open navigation" }));
    expect(document.querySelector(".appBody")).toHaveAttribute("inert");
    act(() => {
      desktop.matches = true;
      desktop.dispatchEvent(new Event("change"));
    });
    expect(document.querySelector(".appBody")).not.toHaveAttribute("inert");
    expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
  });

  it("names icon-only search, traps mobile navigation focus and restores it", async () => {
    window.history.replaceState({}, "", "/unknown");
    vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
    render(<App />);
    expect(
      screen.getByRole("button", {
        name: "Search pages, strategies, research and watchlist",
      }),
    ).toBeInTheDocument();
    const menu = screen.getByRole("button", { name: "Open navigation" });
    fireEvent.click(menu);
    expect(
      screen.getByRole("link", { name: /QUANT Research workspace/ }),
    ).toHaveFocus();
    const dialog = screen.getByRole("dialog", { name: "Workspace navigation" });
    const last = within(dialog).getByRole("link", { name: /Settings/ });
    last.focus();
    fireEvent.keyDown(window, { key: "Tab" });
    expect(within(dialog).getByRole("button", { name: "Close" })).toHaveFocus();
    fireEvent.keyDown(window, { key: "Tab", shiftKey: true });
    expect(last).toHaveFocus();
    expect(document.querySelector(".appBody")).toHaveAttribute("inert");
    fireEvent.keyDown(window, { key: "Escape" });
    await waitFor(() => expect(menu).toHaveFocus());
    expect(menu).toHaveAttribute("aria-expanded", "false");
  });

  it("refreshes service health without equating it to data freshness", async () => {
    window.history.replaceState({}, "", "/unknown");
    let online = false;
    vi.spyOn(globalThis, "fetch").mockImplementation((input) => {
      if (String(input).endsWith("/api/health"))
        return Promise.resolve(
          online
            ? jsonResponse(health)
            : jsonResponse({ detail: "Unavailable" }, 503),
        );
      return Promise.resolve(jsonResponse({ detail: "Unavailable" }, 503));
    });
    render(<App />);
    expect(await screen.findByText("Service unavailable")).toBeInTheDocument();
    online = true;
    fireEvent.click(
      screen.getByRole("button", { name: "Refresh service and data status" }),
    );
    expect(await screen.findByText("Service online")).toBeInTheDocument();
    expect(
      screen.getByText("Available data · not an active run"),
    ).toBeInTheDocument();
    expect(screen.getByText(/Service checked at:/)).toHaveTextContent("UTC");
  });

  it.each(["/unknown", "/backtests/not-a-uuid", "/backtests/1234"])(
    "fails safely for %s",
    async (pathname) => {
      window.history.replaceState({}, "", pathname);
      vi.spyOn(globalThis, "fetch").mockResolvedValue(jsonResponse(health));
      render(<App />);
      expect(
        screen.getByRole("heading", { name: "Page not found" }),
      ).toBeInTheDocument();
      expect(await screen.findByText("Service online")).toBeInTheDocument();
      expect(
        screen.queryByTitle("development · paper"),
      ).not.toBeInTheDocument();
    },
  );

  it("supports a direct detail URL and shows a safe 404 state", async () => {
    window.history.replaceState({}, "", `/backtests/${RUN_ID}`);
    vi.spyOn(globalThis, "fetch").mockImplementation((input) =>
      String(input).endsWith("/api/health")
        ? Promise.resolve(jsonResponse(health))
        : Promise.resolve(jsonResponse({ detail: "Run not found" }, 404)),
    );
    render(<App />);
    expect(await screen.findByText("Run not found")).toBeInTheDocument();
    expect(screen.queryByText("Page not found")).not.toBeInTheDocument();
  });

  it("supports a direct research dataset lineage URL", async () => {
    const datasetId = "cn-a-research-20100101-20251231-v1";
    window.history.replaceState(
      {},
      "",
      `/research/a-share/datasets/${datasetId}`,
    );
    vi.spyOn(globalThis, "fetch").mockImplementation((input) =>
      String(input).endsWith("/api/health")
        ? Promise.resolve(jsonResponse(health))
        : Promise.resolve(
            jsonResponse({
              dataset_id: datasetId,
              provider: "official-public-reconstruction",
              provider_version: "v1",
              retrieval_timestamp: "2026-09-21T00:00:00Z",
              coverage_start: "2010-01-01",
              coverage_end: "2025-12-31",
              security_count: 5431,
              canonical_sha256: "a".repeat(64),
              rule_version: "cn-a-v1",
              adjustment_method: "separate factors",
              readiness_status: "PASSED",
              frozen: true,
              manifest: { schema_version: "1" },
            }),
          ),
    );
    render(<App />);
    expect(
      await screen.findByRole("heading", { name: datasetId }),
    ).toBeInTheDocument();
    expect(screen.queryByText("Page not found")).not.toBeInTheDocument();
  });
});
