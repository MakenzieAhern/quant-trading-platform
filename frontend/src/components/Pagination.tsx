import { useEffect, useLayoutEffect, useRef } from "react";
import { useTranslation } from "react-i18next";

export function Pagination({
  offset,
  limit,
  total,
  loading = false,
  label,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number | null;
  loading?: boolean;
  label?: string;
  onChange: (offset: number) => void;
}) {
  const { t } = useTranslation("common");
  const anchor = useRef<HTMLDivElement>(null);
  const keepVisible = useRef(false);
  const unavailable = loading || limit <= 0;
  const first = total === 0 ? 0 : offset + 1;
  const last = total === null ? 0 : Math.min(offset + limit, total);
  useEffect(() => {
    const forgetIfHidden = () => {
      if (!keepVisible.current) return;
      const rect = anchor.current?.getBoundingClientRect();
      const headerBottom =
        document.querySelector(".topbar")?.getBoundingClientRect().bottom ?? 0;
      if (rect && (rect.top < headerBottom || rect.bottom > innerHeight))
        keepVisible.current = false;
    };
    window.addEventListener("scroll", forgetIfHidden, true);
    return () => window.removeEventListener("scroll", forgetIfHidden, true);
  }, []);
  useLayoutEffect(() => {
    if (!keepVisible.current) return;
    const pager = anchor.current;
    const scroll = () => {
      if (!keepVisible.current) return;
      if (!pager || document.activeElement !== pager) {
        keepVisible.current = false;
        return;
      }
      const headerBottom =
        document.querySelector(".topbar")?.getBoundingClientRect().bottom ?? 0;
      pager.style.scrollMarginTop = `${Math.ceil(Math.max(0, headerBottom)) + 8}px`;
      pager.scrollIntoView?.({ block: "nearest", inline: "nearest" });
    };
    scroll();
    if (!loading) return;
    const frame = requestAnimationFrame(scroll);
    return () => cancelAnimationFrame(frame);
  }, [offset, loading, total]);
  function change(next: number) {
    if (unavailable || (total === null && next >= offset)) return;
    // Focus before loading can remove/disable the button. Never steal later focus.
    anchor.current?.focus();
    keepVisible.current = document.activeElement === anchor.current;
    onChange(next);
  }
  return (
    <div
      ref={anchor}
      className="pagination"
      role="group"
      tabIndex={-1}
      aria-label={label ? `${label} — ${t("pagination")}` : t("pagination")}
      aria-busy={loading}
    >
      <span aria-live="polite">
        {unavailable || total === null
          ? loading
            ? t("loading", { label: "" })
            : t("unavailable")
          : t("pageOf", { start: first, end: last, total })}
      </span>
      <button
        type="button"
        onClick={() => change(Math.max(0, offset - limit))}
        disabled={unavailable || offset === 0}
      >
        {t("previous")}
      </button>
      <button
        type="button"
        onClick={() => change(offset + limit)}
        disabled={unavailable || total === null || offset + limit >= total}
      >
        {t("next")}
      </button>
    </div>
  );
}
