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
  const first = total === 0 ? 0 : offset + 1;
  const last = Math.min(offset + limit, total);
  return (
    <div className="pagination" aria-label="Pagination">
      <span>
        {first}–{last} of {total}
      </span>
      <button
        type="button"
        onClick={() => onChange(Math.max(0, offset - limit))}
        disabled={offset === 0}
      >
        Previous
      </button>
      <button
        type="button"
        onClick={() => onChange(offset + limit)}
        disabled={offset + limit >= total}
      >
        Next
      </button>
    </div>
  );
}
