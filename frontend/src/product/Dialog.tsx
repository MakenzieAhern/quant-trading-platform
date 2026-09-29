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
