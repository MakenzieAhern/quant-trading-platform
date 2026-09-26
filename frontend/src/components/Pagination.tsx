import { useRef } from "react";
import { useTranslation } from "react-i18next";

export function Pagination({
  offset,
  limit,
  total,
  loading = false,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number | null;
  loading?: boolean;
  onChange: (offset: number) => void;
}) {
  const { t } = useTranslation("common");
  const anchor = useRef<HTMLDivElement>(null);
  const unavailable = loading || total === null || limit <= 0;
  const first = total === 0 ? 0 : offset + 1;
  const last = total === null ? 0 : Math.min(offset + limit, total);
  function change(next: number) {
    if (unavailable) return;
    // Focus before loading can remove/disable the button. Never steal later focus.
    anchor.current?.focus();
    onChange(next);
  }
  return (
    <div
      ref={anchor}
      className="pagination"
      role="group"
      tabIndex={-1}
      aria-label={t("pagination")}
      aria-busy={loading}
    >
      <span>
        {unavailable
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
        disabled={unavailable || offset + limit >= (total ?? 0)}
      >
        {t("next")}
      </button>
    </div>
  );
}
