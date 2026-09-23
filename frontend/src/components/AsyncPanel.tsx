import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

import { ApiError } from "../api/client";

export function LoadingPanel({ label }: { label: string }) {
  const { t } = useTranslation("common");
  return (
    <div className="panelState" role="status">
      <span className="loader" aria-hidden="true" /> {t("loading", { label })}
    </div>
  );
}

export function ErrorPanel({ message }: { message: string | Error }) {
  const { t } = useTranslation("common");
  const kind =
    message instanceof ApiError
      ? message.status === 404
        ? "notFound"
        : message.status === 401 || message.status === 403
          ? "permission"
          : message.status === 408
            ? "timeout"
            : "unknown"
      : message instanceof TypeError
        ? "offline"
        : "unknown";
  return (
    <div className="panelState errorPanel" role="alert">
      <p>{t(`loadErrors.${kind}`)}</p>
      <a
        className="button"
        href={kind === "notFound" ? "/" : window.location.href}
      >
        {t(kind === "notFound" ? "loadErrors.workbench" : "loadErrors.reload")}
      </a>
      <details>
        <summary>{t("loadErrors.diagnostic")}</summary>
        <code>{message instanceof Error ? message.message : message}</code>
      </details>
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="emptyState">{children}</div>;
}
