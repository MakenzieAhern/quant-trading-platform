import { Component, type ReactNode } from "react";

import { i18n } from "../i18n";

export class AppErrorBoundary extends Component<
  { children: ReactNode },
  { failed: boolean }
> {
  state = { failed: false };

  static getDerivedStateFromError() {
    return { failed: true };
  }

  render() {
    if (!this.state.failed) return this.props.children;
    return (
      <main id="main-content" className="readingPage">
        <section className="stateCallout" role="alert">
          <h1>{i18n.t("common:renderFailure.title")}</h1>
          <p>{i18n.t("common:renderFailure.guidance")}</p>
          <div className="welcomeActions">
            <a
              className="button secondary"
              href="/tasks"
              target="_blank"
              rel="noopener noreferrer"
            >
              {i18n.t("common:renderFailure.tasks")}
            </a>
            <a
              className="button secondary"
              href="/paper"
              target="_blank"
              rel="noopener noreferrer"
            >
              {i18n.t("common:renderFailure.accounts")}
            </a>
            <a className="button" href={window.location.href}>
              {i18n.t("common:loadErrors.reload")}
            </a>
          </div>
        </section>
      </main>
    );
  }
}
