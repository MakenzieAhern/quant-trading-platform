import { StrictMode } from "react";
import { createRoot } from "react-dom/client";

import { App } from "./App";
import { AppErrorBoundary } from "./components/AppErrorBoundary";
import "./i18n";
import "./styles.css";

const root = document.getElementById("root");
if (!root) throw new Error("Application root element is missing");

createRoot(root).render(
  <StrictMode>
    <AppErrorBoundary>
      <App />
    </AppErrorBoundary>
  </StrictMode>,
);
