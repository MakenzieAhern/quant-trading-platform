import { useEffect, useRef, type ReactNode } from "react";
import { useProductCopy } from "./copy";
export function Dialog({
  title,
  children,
  onClose,
  drawer = false,
}: {
  title: string;
  children: ReactNode;
  onClose: () => void;
  drawer?: boolean;
}) {
  const ref = useRef<HTMLDialogElement>(null);
  const copy = useProductCopy();
  useEffect(() => {
    const dialog = ref.current;
    const trigger = document.activeElement;
    dialog?.showModal();
    return () => {
      dialog?.close();
      if (trigger instanceof HTMLElement && trigger.isConnected)
        trigger.focus();
      else if (document.activeElement === document.body)
        document.getElementById("main-content")?.focus({ preventScroll: true });
    };
  }, []);
  return (
    <dialog
      ref={ref}
      className={drawer ? "productDialog productDrawer" : "productDialog"}
      aria-label={title}
      onCancel={onClose}
      onKeyDown={(event) => {
        if (
          event.key !== "Tab" ||
          event.defaultPrevented ||
          event.altKey ||
          event.ctrlKey ||
          event.metaKey
        )
          return;
        const items = Array.from(
          event.currentTarget.querySelectorAll<HTMLElement>(
            "a[href], button, input, select, textarea, summary, [tabindex]",
          ),
        ).filter(
          (item) =>
            item.tabIndex >= 0 &&
            !item.matches(":disabled") &&
            !item.closest("[inert]") &&
            !["hidden", "collapse"].includes(
              getComputedStyle(item).visibility,
            ) &&
            item.getClientRects().length > 0,
        );
        const first = items[0];
        const last = items.at(-1);
        const edge = event.shiftKey ? first : last;
        if (edge && document.activeElement === edge) {
          event.preventDefault();
          (event.shiftKey ? last : first)?.focus();
        }
      }}
    >
      <div className="dialogHeading">
        <h2>{title}</h2>
        <button
          type="button"
          className="iconButton"
          onClick={onClose}
          aria-label={copy.close}
        >
          ×
        </button>
      </div>
      {children}
    </dialog>
  );
}
