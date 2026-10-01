import { lazy, Suspense } from "react";
import { useTranslation } from "react-i18next";

import { AppShell } from "./components/AppShell";
import { LoadingPanel } from "./components/AsyncPanel";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { BacktestHistoryPage } from "./pages/BacktestHistoryPage";
import { CreateBacktestPage } from "./pages/CreateBacktestPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { CreatePaperSessionPage } from "./pages/CreatePaperSessionPage";
import { PaperSessionDetailPage } from "./pages/PaperSessionDetailPage";
import { PaperSessionsPage } from "./pages/PaperSessionsPage";
import { usePathname } from "./utils/navigation";
import {
  WorkbenchPage,
  ProductStrategiesPage,
  DataCenterPage,
  HelpPage,
  SettingsPage,
} from "./product/ProductPages";
import { CreateExperimentPage } from "./product/experiments/CreateExperimentPage";
import { ExperimentsPage } from "./product/experiments/ExperimentsPage";
import { ProductDataProvider } from "./product/ProductDataProvider";
import { MarketsPage } from "./product/markets";
import { TaskCenterPage } from "./product/TaskCenterPage";

const ResearchDatasetPage = lazy(() =>
  import("./pages/research/ResearchDatasetPage").then(
    ({ ResearchDatasetPage }) => ({
      default: ResearchDatasetPage,
    }),
  ),
);
const ResearchHomePage = lazy(() =>
  import("./pages/research/ResearchHomePage").then(({ ResearchHomePage }) => ({
    default: ResearchHomePage,
  })),
);
const ResearchRunPage = lazy(() =>
  import("./pages/research/ResearchRunPage").then(({ ResearchRunPage }) => ({
    default: ResearchRunPage,
  })),
);
const ResearchStrategiesPage = lazy(() =>
  import("./pages/research/ResearchStrategiesPage").then(
    ({ ResearchStrategiesPage }) => ({ default: ResearchStrategiesPage }),
  ),
);
const ResearchStrategyPage = lazy(() =>
  import("./pages/research/ResearchStrategyPage").then(
    ({ ResearchStrategyPage }) => ({
      default: ResearchStrategyPage,
    }),
  ),
);
const ExperimentDetailPage = lazy(() =>
  import("./product/experiments/ExperimentDetailPage").then(
    ({ ExperimentDetailPage }) => ({ default: ExperimentDetailPage }),
  ),
);
const ExperimentComparePage = lazy(() =>
  import("./product/experiments/ExperimentComparePage").then(
    ({ ExperimentComparePage }) => ({ default: ExperimentComparePage }),
  ),
);

function decodeRouteId(value: string): string | null {
  try {
    return decodeURIComponent(value);
  } catch {
    return null;
  }
}

export function App() {
  const { t } = useTranslation("navigation");
  const pathname = usePathname();
  const detailMatch =
    /^\/backtests\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i.exec(
      pathname,
    );
  const paperDetailMatch =
    /^\/paper\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i.exec(
      pathname,
    );
  const researchRunMatch =
    /^\/research\/a-share\/runs\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i.exec(
      pathname,
    );
  const researchDatasetMatch =
    /^\/research\/a-share\/datasets\/([^/]+)\/?$/i.exec(pathname);
  const researchStrategyMatch =
    /^\/research\/a-share\/strategies\/([^/]+)\/?$/i.exec(pathname);
  let page = <NotFoundPage />;
  if (pathname === "/") page = <WorkbenchPage />;
  else if (pathname === "/markets" || pathname === "/markets/")
    page = <MarketsPage />;
  else if (pathname === "/strategies") page = <ProductStrategiesPage />;
  else if (pathname.startsWith("/strategies/")) {
    const strategyId = decodeRouteId(pathname.slice("/strategies/".length));
    if (strategyId !== null)
      page = <ProductStrategiesPage strategyId={strategyId} />;
  } else if (pathname === "/data") page = <DataCenterPage />;
  else if (pathname === "/tasks") page = <TaskCenterPage />;
  else if (pathname === "/help") page = <HelpPage />;
  else if (pathname === "/settings") page = <SettingsPage />;
  else if (pathname === "/research/new") page = <CreateExperimentPage />;
  else if (
    pathname === "/experiments/compare" ||
    pathname === "/experiments/compare/"
  )
    page = <ExperimentComparePage />;
  else if (pathname === "/experiments" || pathname === "/experiments/")
    page = <ExperimentsPage />;
  else if (/^\/experiments\/[0-9a-f-]{36}\/?$/i.test(pathname))
    page = <ExperimentDetailPage jobId={pathname.split("/")[2]} />;
  else if (pathname === "/backtests" || pathname === "/backtests/")
    page = <BacktestHistoryPage />;
  else if (pathname === "/backtests/new" || pathname === "/backtests/new/")
    page = <CreateBacktestPage />;
  else if (detailMatch?.[1])
    page = <BacktestDetailPage runId={detailMatch[1]} />;
  else if (pathname === "/paper" || pathname === "/paper/")
    page = <PaperSessionsPage />;
  else if (pathname === "/paper/new" || pathname === "/paper/new/")
    page = <CreatePaperSessionPage />;
  else if (paperDetailMatch?.[1])
    page = <PaperSessionDetailPage sessionId={paperDetailMatch[1]} />;
  else if (
    pathname === "/research" ||
    pathname === "/research/" ||
    pathname === "/research/a-share" ||
    pathname === "/research/a-share/"
  )
    page = <ResearchHomePage />;
  else if (
    pathname === "/research/a-share/strategies" ||
    pathname === "/research/a-share/strategies/"
  )
    page = <ResearchStrategiesPage />;
  else if (researchRunMatch?.[1])
    page = (
      <ResearchRunPage key={researchRunMatch[1]} runId={researchRunMatch[1]} />
    );
  else if (researchDatasetMatch?.[1]) {
    const datasetId = decodeRouteId(researchDatasetMatch[1]);
    if (datasetId !== null)
      page = <ResearchDatasetPage datasetId={datasetId} />;
  } else if (researchStrategyMatch?.[1]) {
    const strategyId = decodeRouteId(researchStrategyMatch[1]);
    if (strategyId !== null)
      page = <ResearchStrategyPage strategyId={strategyId} />;
  }
  return (
    <ProductDataProvider>
      <AppShell notFound={page.type === NotFoundPage}>
        <Suspense fallback={<LoadingPanel label={t("research")} />}>
          {page}
        </Suspense>
      </AppShell>
    </ProductDataProvider>
  );
}
