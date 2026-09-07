import { useTranslation } from "react-i18next";

export function Pagination({
  offset,
  limit,
  total,
  onChange,
}: {
  offset: number;
  limit: number;
  total: number;
  onChange: (offset: number) => void;
}) {
  const { t } = useTranslation("common");
  const first = total === 0 ? 0 : offset + 1;
  const last = Math.min(offset + limit, total);
  return (
    <div className="pagination" aria-label={t("pagination")}>
      <span>{t("pageOf", { start: first, end: last, total })}</span>
      <button
        type="button"
        onClick={() => onChange(Math.max(0, offset - limit))}
        disabled={offset === 0}
      >
        {t("previous")}
      </button>
      <button
        type="button"
        onClick={() => onChange(offset + limit)}
        disabled={offset + limit >= total}
      >
        {t("next")}
      </button>
    </div>
  );
}
