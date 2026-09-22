import { useState } from "react";
import { useTranslation } from "react-i18next";
import { Link } from "../components/Link";
import { useApiResource } from "../hooks/useApiResource";
import { experimentApi } from "./experiments/api";
import { useProductCopy } from "./copy";
import { Dialog } from "./Dialog";

export function CommandPalette({ onClose }: { onClose: () => void }) {
  const copy = useProductCopy();
  const { i18n } = useTranslation();
  const [query, setQuery] = useState("");
  const capabilities = useApiResource(
    (signal) => experimentApi.capabilities(signal),
    [],
  );
  const jobs = useApiResource(
    (signal) => experimentApi.list(signal, 20, 0),
    [],
  );
  const commands = [
    { label: copy.home, href: "/" },
    { label: copy.markets, href: "/markets" },
    { label: copy.start, href: "/research/new" },
    { label: copy.strategies, href: "/strategies" },
    { label: copy.research, href: "/experiments" },
    { label: copy.archive, href: "/research/a-share" },
    { label: copy.accounts, href: "/paper" },
    { label: copy.data, href: "/data" },
    { label: copy.help, href: "/help" },
    { label: copy.settings, href: "/settings" },
    ...(capabilities.data?.strategies ?? []).map((item) => ({
      label: i18n.language.startsWith("zh") ? item.name_zh : item.name_en,
      href: `/strategies/${encodeURIComponent(item.strategy_id)}`,
    })),
    ...(jobs.data?.items ?? []).map((item) => ({
      label: item.name,
      href: `/experiments/${item.job_id}`,
    })),
  ].filter((item) =>
    item.label.toLocaleLowerCase().includes(query.trim().toLocaleLowerCase()),
  );
  return (
    <Dialog title={copy.search} onClose={onClose}>
      <label>
        <span className="srOnly">{copy.search}</span>
        <input
          type="search"
          value={query}
          onChange={(event) => setQuery(event.target.value)}
          placeholder={copy.search}
        />
      </label>
      <nav className="commandResults" aria-label={copy.search}>
        {commands.map((item) => (
          <Link key={item.href} href={item.href} onClick={onClose}>
            {item.label}
            <span aria-hidden="true">↗</span>
          </Link>
        ))}
        {commands.length === 0 && <p role="status">{copy.emptySearch}</p>}
      </nav>
    </Dialog>
  );
}
