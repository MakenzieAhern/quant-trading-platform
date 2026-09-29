import { useState } from "react";
import { useTranslation } from "react-i18next";

import type { ResearchPoint } from "../../types/research";
import { Pagination } from "../Pagination";

const PAGE_SIZE = 100;

export function ResearchPointTable({
  label,
  series,
}: {
  label: string;
  series: { label: string; points: ResearchPoint[] }[];
}) {
  const { t } = useTranslation("research");
  const [open, setOpen] = useState(false);
  const [offset, setOffset] = useState(0);
  const total = series.reduce((count, item) => count + item.points.length, 0);
  const rows = open
    ? series.flatMap((item) =>
        item.points.map((point) => ({ label: item.label, point })),
      )
    : [];
  const pageOffset = Math.min(
    offset,
    Math.max(0, Math.floor((total - 1) / PAGE_SIZE) * PAGE_SIZE),
  );
  return (
    <details onToggle={(event) => setOpen(event.currentTarget.open)}>
      <summary>{t("chartData", { count: total })}</summary>
      {open && (
        <>
          <div
            className="tableScroll"
            tabIndex={0}
            aria-label={`${label} — ${t("scrollTable")}`}
          >
            <table aria-label={label}>
              <thead>
                <tr>
                  <th scope="col">{t("columns.series")}</th>
                  <th scope="col">{t("columns.date")}</th>
                  <th scope="col">{t("columns.value")}</th>
                </tr>
              </thead>
              <tbody>
                {rows.slice(pageOffset, pageOffset + PAGE_SIZE).map((row) => (
                  <tr
                    key={`${row.label}-${row.point.sequence}-${row.point.trading_date}`}
                  >
                    <td>{row.label}</td>
                    <td>{row.point.trading_date}</td>
                    <td>{row.point.value}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          {total > PAGE_SIZE && (
            <Pagination
              offset={pageOffset}
              limit={PAGE_SIZE}
              total={total}
              onChange={setOffset}
            />
          )}
        </>
      )}
    </details>
  );
}
