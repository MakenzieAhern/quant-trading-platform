import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { Link } from "../components/Link";
import { navigate, useNavigationGuard, usePathname } from "./navigation";

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
