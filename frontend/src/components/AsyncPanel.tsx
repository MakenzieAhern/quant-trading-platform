import type { ReactNode } from "react";

export function LoadingPanel({ label }: { label: string }) {
  return (
    <div className="panelState" role="status">
      <span className="loader" aria-hidden="true" /> Loading {label}…
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
