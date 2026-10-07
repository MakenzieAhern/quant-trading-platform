import { fireEvent, render, screen } from "@testing-library/react";
import { beforeEach, describe, expect, it, vi } from "vitest";
import { Dialog } from "./Dialog";
import { i18n } from "../i18n";

beforeEach(async () => {
  await i18n.changeLanguage("en-US");
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.open = true;
        this.querySelector<HTMLElement>("button")?.focus();
      },
    },
    close: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.open = false;
      },
    },
  });
  // JSDOM has no layout; only the visibility measurement is supplied here.
  vi.spyOn(HTMLElement.prototype, "getClientRects").mockImplementation(
    function (this: HTMLElement) {
      const hidden =
        this.closest("[hidden]") || getComputedStyle(this).display === "none";
      return (hidden
        ? []
        : [new DOMRect(0, 0, 40, 40)]) as unknown as DOMRectList;
    },
  );
});

describe("shared native modal keyboard edges", () => {
  it.each([false, true])(
    "wraps the %s Tab edge past ineligible controls",
    (reverse) => {
      render(
        <Dialog title="Keyboard fixture" onClose={() => undefined}>
          <input aria-label="Interior field" />
          <a href="/help">Last visible control</a>
          <button disabled>Disabled last control</button>
          <fieldset disabled>
            <button>Disabled by fieldset</button>
          </fieldset>
          <div hidden>
            <button>Hidden descendant</button>
          </div>
          <button style={{ display: "none" }}>CSS hidden</button>
          <button style={{ visibility: "hidden" }}>
            Invisible but laid out
          </button>
          <div inert>
            <button>Inert descendant</button>
          </div>
          <button tabIndex={-1}>Programmatic only</button>
        </Dialog>,
      );
      const first = screen.getByRole("button", { name: "Close" });
      const last = screen.getByRole("link", { name: "Last visible control" });
      (reverse ? first : last).focus();
      expect(
        fireEvent.keyDown(document.activeElement!, {
          key: "Tab",
          shiftKey: reverse,
        }),
      ).toBe(false);
      expect(reverse ? last : first).toHaveFocus();
    },
  );

  it("leaves interior Tab and handled child keys to their existing behavior", () => {
    render(
      <Dialog title="Keyboard fixture" onClose={() => undefined}>
        <input aria-label="Interior field" />
        <button onKeyDown={(event) => event.preventDefault()}>
          Child handled
        </button>
      </Dialog>,
    );
    const field = screen.getByRole("textbox", { name: "Interior field" });
    field.focus();
    expect(fireEvent.keyDown(field, { key: "Tab" })).toBe(true);
    expect(field).toHaveFocus();
    const child = screen.getByRole("button", { name: "Child handled" });
    child.focus();
    fireEvent.keyDown(child, { key: "Tab" });
    expect(child).toHaveFocus();
    expect(fireEvent.keyDown(child, { key: "Escape" })).toBe(false);
  });

  it.each([false, true])(
    "keeps a lone close button focused at the %s edge",
    (reverse) => {
      render(
        <Dialog title="Keyboard fixture" onClose={() => undefined}>
          {null}
        </Dialog>,
      );
      const close = screen.getByRole("button", { name: "Close" });
      close.focus();
      expect(fireEvent.keyDown(close, { key: "Tab", shiftKey: reverse })).toBe(
        false,
      );
      expect(close).toHaveFocus();
    },
  );

  it("preserves cancel and restores the live trigger after closing", () => {
    const close = vi.fn();
    const view = render(<button>Open fixture</button>);
    const trigger = screen.getByRole("button", { name: "Open fixture" });
    trigger.focus();
    view.rerender(
      <>
        <button>Open fixture</button>
        <Dialog title="Keyboard fixture" onClose={close}>
          {null}
        </Dialog>
      </>,
    );
    fireEvent(
      screen.getByRole("dialog"),
      new Event("cancel", { bubbles: true }),
    );
    expect(close).toHaveBeenCalledOnce();
    view.rerender(<button>Open fixture</button>);
    expect(trigger).toHaveFocus();
  });

  it("does not intercept browser-modified Tab shortcuts", () => {
    render(
      <Dialog title="Keyboard fixture" onClose={() => undefined}>
        {null}
      </Dialog>,
    );
    const close = screen.getByRole("button", { name: "Close" });
    close.focus();
    for (const modifier of ["ctrlKey", "metaKey", "altKey"]) {
      expect(fireEvent.keyDown(close, { key: "Tab", [modifier]: true })).toBe(
        true,
      );
    }
  });
});
