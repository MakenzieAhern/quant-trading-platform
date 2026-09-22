import type { ReactNode } from "react";
import { useTranslation } from "react-i18next";

export function LoadingPanel({ label }: { label: string }) {
  const { t } = useTranslation("common");
  return (
    <div className="panelState" role="status">
      <span className="loader" aria-hidden="true" /> {t("loading", { label })}
    </div>
  );
}

export function ErrorPanel({ message }: { message: string }) {
  return (
    <div className="panelState errorPanel" role="alert">
      {message}
    </div>
  );
}

export function EmptyState({ children }: { children: ReactNode }) {
  return <div className="emptyState">{children}</div>;
}
