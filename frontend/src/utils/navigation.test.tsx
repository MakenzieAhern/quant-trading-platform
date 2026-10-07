import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Link } from "../components/Link";
import {
  managedReturnHref,
  navigate,
  navigateBack,
  replaceUrl,
  useNavigationGuard,
  usePathname,
} from "./navigation";

function Guard({ message = "Leave this draft?" }: { message?: string }) {
  useNavigationGuard(() => window.confirm(message));
  return <Link href="/experiments">Experiments</Link>;
}

function RouterHarness() {
  const pathname = usePathname();
  return (
    <>
      <output>{pathname}</output>
      {pathname === "/research/new" && <Guard />}
    </>
  );
}

function TwoLocationReaders() {
  usePathname();
  return <RouterHarness />;
}

describe("shared navigation guard", () => {
  it("finds the nearest same-origin list through nested details without modifying history", () => {
    window.history.replaceState({}, "", "/experiments");
    navigate("/experiments/first");
    const source = "/experiments?compare_from=second#main-content";
    navigate(source);
    navigate("/experiments/compare?ids=first,second");
    navigate("/experiments/second");
    const replace = vi.spyOn(window.history, "replaceState");
    expect(managedReturnHref("/experiments")).toBe(source);
    expect(managedReturnHref("/experiments?explicit=1")).toBe(
      "/experiments?explicit=1",
    );
    expect(managedReturnHref("/experiments#explicit")).toBe(
      "/experiments#explicit",
    );
    expect(replace).not.toHaveBeenCalled();
  });

  it.each([
    {},
    { quantNavigationIndex: -1 },
    {
      quantNavigationIndex: 2,
      quantNavigationUrl: "http://localhost/experiments/unknown",
    },
    {
      quantNavigationIndex: 2,
      quantNavigationReturns: [
        { url: "http://localhost/experiments?wrong=1", index: 0 },
      ],
    },
    {
      quantNavigationIndex: 1,
      quantNavigationReturns: [{ url: "not a URL", index: 0 }],
    },
    {
      quantNavigationIndex: 1,
      quantNavigationReturns: [
        { url: "https://example.invalid/experiments?wrong=1", index: 0 },
      ],
    },
    {
      quantNavigationIndex: 1,
      quantNavigationReturns: [
        {
          url: "http://localhost/experiments/compare?ids=first,second",
          index: 0,
        },
      ],
    },
    {
      quantNavigationIndex: 1,
      quantNavigationReturns: [
        { url: "http://localhost/experiments-other", index: 0 },
      ],
    },
  ])(
    "uses the internal fallback for unknown or unsafe list ancestry %j",
    (patch) => {
      window.history.replaceState(
        { quantNavigationUrl: "http://localhost/experiments/direct", ...patch },
        "",
        "/experiments/direct",
      );
      const replace = vi.spyOn(window.history, "replaceState");
      expect(managedReturnHref("/experiments")).toBe("/experiments");
      expect(managedReturnHref("https://example.invalid/experiments")).toBe(
        "https://example.invalid/experiments",
      );
      expect(replace).not.toHaveBeenCalled();
    },
  );

  it.each(["/help", "/help#help-drawdown"])(
    "reselects only a current fragment without adding history: %s",
    (url) => {
      window.history.replaceState({ saved: true }, "", url);
      const state = window.history.state;
      const length = window.history.length;
      const notified = vi.fn();
      window.addEventListener("popstate", notified);
      try {
        expect(navigate(url)).toBe(true);
        expect(notified).toHaveBeenCalledTimes(url.includes("#") ? 1 : 0);
        expect(window.history.length).toBe(length);
        expect(window.history.state).toBe(state);
        expect(window.location.pathname).toBe("/help");
      } finally {
        window.removeEventListener("popstate", notified);
      }
    },
  );

  it("canonicalizes a managed study-list alias and preserves its native return entry", async () => {
    window.history.replaceState({}, "", "/strategies");
    render(<RouterHarness />);
    act(() => navigate("/experiments/"));
    expect(window.location.pathname).toBe("/experiments");
    expect(window.history.state.quantNavigationUrl).toBe(window.location.href);
    window.history.replaceState(
      { ...window.history.state, retainedSelection: ["first", "second"] },
      "",
    );
    act(() => navigate("/experiments/first"));
    const length = window.history.length;
    act(() => navigateBack("/experiments"));
    await waitFor(() =>
      expect(window.history.state.retainedSelection).toEqual([
        "first",
        "second",
      ]),
    );
    expect(window.history.length).toBe(length);
    act(() => window.history.forward());
    await waitFor(() =>
      expect(window.location.pathname).toBe("/experiments/first"),
    );
  });

  it("returns through nested details to the original list and keeps Forward entries", async () => {
    window.history.replaceState(
      { retainedSelection: ["first", "second"] },
      "",
      "/experiments",
    );
    navigate("/experiments/compare?ids=first,second");
    navigate("/experiments/first");
    navigate("/experiments/second");
    const length = window.history.length;
    render(
      <Link back href="/experiments">
        Back to list
      </Link>,
    );
    await userEvent.click(screen.getByRole("link", { name: "Back to list" }));
    await waitFor(() =>
      expect(window.history.state.retainedSelection).toEqual([
        "first",
        "second",
      ]),
    );
    expect(window.location.pathname).toBe("/experiments");
    expect(window.history.length).toBe(length);
    act(() => window.history.forward());
    await waitFor(() =>
      expect(window.location.pathname).toBe("/experiments/compare"),
    );
    act(() => window.history.forward());
    await waitFor(() =>
      expect(window.location.pathname).toBe("/experiments/first"),
    );
  });

  it("returns a Back link to its own prior list entry without discarding Forward history", async () => {
    window.history.replaceState(
      { retainedSelection: ["first", "second"] },
      "",
      "/experiments",
    );
    navigate("/experiments/compare?ids=first,second");
    const length = window.history.length;
    render(
      <Link back href="/experiments">
        Back to list
      </Link>,
    );
    await userEvent.click(screen.getByRole("link", { name: "Back to list" }));
    await waitFor(() => expect(window.location.pathname).toBe("/experiments"));
    expect(window.history.state.retainedSelection).toEqual(["first", "second"]);
    expect(window.history.length).toBe(length);
    act(() => window.history.forward());
    await waitFor(() =>
      expect(window.location.pathname).toBe("/experiments/compare"),
    );
  });

  it("returns to the nearest matching list when a newer list replaced the context", async () => {
    window.history.replaceState({ original: true }, "", "/experiments");
    navigate("/experiments/first");
    navigate("/experiments");
    window.history.replaceState({ ...window.history.state, newer: true }, "");
    navigate("/experiments/second");
    act(() => navigateBack("/experiments"));
    await waitFor(() => expect(window.history.state.newer).toBe(true));
    expect(window.history.state.original).toBeUndefined();
  });

  it("does not traverse through an unknown native hash change", () => {
    window.history.replaceState({}, "", "/experiments");
    navigate("/experiments/first");
    window.history.replaceState(
      window.history.state,
      "",
      "/experiments/first#unknown",
    );
    const go = vi.spyOn(window.history, "go");
    navigateBack("/experiments");
    expect(window.location.pathname).toBe("/experiments");
    expect(go).not.toHaveBeenCalled();
    go.mockRestore();
  });

  it("does not certify unknown URL changes while replacing a detail URL", () => {
    window.history.replaceState({}, "", "/experiments");
    navigate("/markets#dataset=known&security=CN-A:SSE:600000");
    window.history.replaceState(window.history.state, "", "/markets#unknown");
    replaceUrl("/markets");
    expect(window.history.state.quantNavigationUrl).not.toBe(
      window.location.href,
    );
    const go = vi.spyOn(window.history, "go").mockImplementation(() => {});
    navigateBack("/experiments");
    expect(go).not.toHaveBeenCalled();
    go.mockRestore();
  });

  it.each([
    [null],
    [{ url: "/experiments", index: -1 }],
    [{ url: "/experiments", index: 99 }],
  ])("falls back internally for malformed return history %j", (entries) => {
    window.history.replaceState(
      {
        quantNavigationIndex: 2,
        quantNavigationUrl: window.location.origin + "/experiments/first",
        quantNavigationReturns: entries,
      },
      "",
      "/experiments/first",
    );
    const go = vi.spyOn(window.history, "go");
    navigateBack("/experiments");
    expect(window.location.pathname).toBe("/experiments");
    expect(go).not.toHaveBeenCalled();
    go.mockRestore();
  });

  it("keeps the unsaved-draft guard on a multi-entry return", async () => {
    window.history.replaceState({}, "", "/experiments");
    navigate("/experiments/first");
    navigate("/research/new");
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<RouterHarness />);
    act(() => navigateBack("/experiments"));
    await waitFor(() => expect(confirm).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(window.location.pathname).toBe("/research/new"));
    confirm.mockReturnValue(true);
    act(() => navigateBack("/experiments"));
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("/experiments"),
    );
    expect(confirm).toHaveBeenCalledTimes(2);
  });

  it("uses the internal list fallback for directly opened detail Back links", async () => {
    window.history.replaceState({}, "", "/experiments/direct");
    const back = vi.spyOn(window.history, "back");
    render(
      <Link back href="/experiments">
        Back to list
      </Link>,
    );
    await userEvent.click(screen.getByRole("link", { name: "Back to list" }));
    expect(window.location.pathname).toBe("/experiments");
    expect(back).not.toHaveBeenCalled();
    back.mockRestore();
  });

  it("keeps one listener across draft edits while reading the latest confirmation", async () => {
    window.history.replaceState({}, "", "/research/new");
    const add = vi.spyOn(window, "addEventListener");
    const remove = vi.spyOn(window, "removeEventListener");
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    const view = render(<Guard message="First draft" />);
    view.rerender(<Guard message="Edited draft" />);
    expect(
      add.mock.calls.filter(([event]) => event === "quant:before-traversal"),
    ).toHaveLength(1);
    expect(
      remove.mock.calls.filter(([event]) => event === "quant:before-traversal"),
    ).toHaveLength(0);
    await userEvent.click(screen.getByRole("link", { name: "Experiments" }));
    expect(confirm).toHaveBeenCalledExactlyOnceWith("Edited draft");
    view.unmount();
    expect(
      remove.mock.calls.filter(([event]) => event === "quant:before-traversal"),
    ).toHaveLength(1);
  });

  it("starts new routes at the top without scrolling on same-route or Back", () => {
    const scrollTo = vi.spyOn(window, "scrollTo").mockImplementation(() => {});
    window.history.replaceState({}, "", "/strategies");
    navigate("/experiments");
    expect(scrollTo).toHaveBeenCalledExactlyOnceWith(0, 0);
    navigate("/experiments");
    window.dispatchEvent(new PopStateEvent("popstate"));
    expect(scrollTo).toHaveBeenCalledTimes(1);
    scrollTo.mockRestore();
  });

  it("does not add duplicate history for an exact current URL", () => {
    window.history.replaceState({}, "", "/experiments");
    const push = vi.spyOn(window.history, "pushState");
    expect(navigate("/experiments")).toBe(true);
    expect(push).not.toHaveBeenCalled();
    expect(navigate("/experiments#details")).toBe(true);
    expect(push).toHaveBeenCalledTimes(1);
    push.mockRestore();
  });

  it("asks the guard before a browser traversal updates the route", () => {
    window.history.replaceState({}, "", "/strategies");
    render(<RouterHarness />);
    const deny = (event: Event) => event.preventDefault();
    window.addEventListener("quant:before-traversal", deny);
    act(() => {
      window.history.replaceState({}, "", "/experiments");
      window.dispatchEvent(new PopStateEvent("popstate", { state: {} }));
    });
    expect(screen.getByRole("status")).toHaveTextContent("/strategies");
    window.removeEventListener("quant:before-traversal", deny);
  });

  it("confirms a same-page query traversal once with two location readers", () => {
    window.history.replaceState({}, "", "/research/new?strategy=first");
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(true);
    render(<TwoLocationReaders />);
    act(() => {
      window.history.replaceState({}, "", "/research/new?strategy=second");
      window.dispatchEvent(new PopStateEvent("popstate", { state: {} }));
    });
    expect(confirm).toHaveBeenCalledTimes(1);
  });

  it("blocks sidebar links and programmatic commands once before changing history", async () => {
    window.history.replaceState({}, "", "/research/new");
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<RouterHarness />);
    const length = window.history.length;
    await userEvent.click(screen.getByRole("link", { name: "Experiments" }));
    expect(confirm).toHaveBeenCalledTimes(1);
    expect(window.location.pathname).toBe("/research/new");
    expect(window.history.length).toBe(length);
    act(() => {
      expect(navigate("/settings")).toBe(false);
    });
    expect(confirm).toHaveBeenCalledTimes(2);
    expect(screen.getByRole("status")).toHaveTextContent("/research/new");
    confirm.mockReturnValue(true);
    act(() => {
      expect(navigate("/experiments")).toBe(true);
    });
    expect(confirm).toHaveBeenCalledTimes(3);
    expect(screen.getByRole("status")).toHaveTextContent("/experiments");
  });

  it("restores a cancelled browser Back without truncating Forward history", async () => {
    window.history.replaceState({}, "", "/strategies");
    navigate("/research/new");
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<RouterHarness />);
    const length = window.history.length;
    act(() => window.history.back());
    await waitFor(() => expect(confirm).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(window.location.pathname).toBe("/research/new"));
    expect(screen.getByRole("status")).toHaveTextContent("/research/new");
    expect(window.history.length).toBe(length);
    confirm.mockReturnValue(true);
    act(() => window.history.back());
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("/strategies"),
    );
    expect(confirm).toHaveBeenCalledTimes(2);
    act(() => window.history.forward());
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("/research/new"),
    );
    expect(confirm).toHaveBeenCalledTimes(2);
    expect(window.history.length).toBe(length);
  });

  it("restores a cancelled Forward traversal and preserves both neighbours", async () => {
    window.history.replaceState({}, "", "/research/new");
    navigate("/help");
    act(() => window.history.back());
    await waitFor(() => expect(window.location.pathname).toBe("/research/new"));
    const confirm = vi.spyOn(window, "confirm").mockReturnValue(false);
    render(<RouterHarness />);
    act(() => window.history.forward());
    await waitFor(() => expect(confirm).toHaveBeenCalledTimes(1));
    await waitFor(() => expect(window.location.pathname).toBe("/research/new"));
    expect(screen.getByRole("status")).toHaveTextContent("/research/new");
    confirm.mockReturnValue(true);
    act(() => window.history.forward());
    await waitFor(() =>
      expect(screen.getByRole("status")).toHaveTextContent("/help"),
    );
    expect(confirm).toHaveBeenCalledTimes(2);
  });
});
