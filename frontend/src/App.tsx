import { AppShell } from "./components/AppShell";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { BacktestHistoryPage } from "./pages/BacktestHistoryPage";
import { CreateBacktestPage } from "./pages/CreateBacktestPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { CreatePaperSessionPage } from "./pages/CreatePaperSessionPage";
import { PaperSessionDetailPage } from "./pages/PaperSessionDetailPage";
import { PaperSessionsPage } from "./pages/PaperSessionsPage";
import { ResearchDatasetPage } from "./pages/research/ResearchDatasetPage";
import { ResearchHomePage } from "./pages/research/ResearchHomePage";
import { ResearchRunPage } from "./pages/research/ResearchRunPage";
import { ResearchStrategiesPage } from "./pages/research/ResearchStrategiesPage";
import { ResearchStrategyPage } from "./pages/research/ResearchStrategyPage";
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
import { ExperimentDetailPage } from "./product/experiments/ExperimentDetailPage";

export function App() {
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
  else if (pathname === "/strategies") page = <ProductStrategiesPage />;
  else if (pathname.startsWith("/strategies/"))
    page = (
      <ProductStrategiesPage
        strategyId={decodeURIComponent(pathname.slice("/strategies/".length))}
      />
    );
  else if (pathname === "/data") page = <DataCenterPage />;
  else if (pathname === "/help") page = <HelpPage />;
  else if (pathname === "/settings") page = <SettingsPage />;
  else if (pathname === "/research/new") page = <CreateExperimentPage />;
  else if (pathname === "/experiments" || pathname === "/experiments/") page = <ExperimentsPage />;
  else if (/^\/experiments\/[0-9a-f-]{36}\/?$/i.test(pathname)) page = <ExperimentDetailPage jobId={pathname.split("/")[2]} />;
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
    page = <ResearchRunPage runId={researchRunMatch[1]} />;
  else if (researchDatasetMatch?.[1])
    page = (
      <ResearchDatasetPage
        datasetId={decodeURIComponent(researchDatasetMatch[1])}
      />
    );
  else if (researchStrategyMatch?.[1])
    page = (
      <ResearchStrategyPage
        strategyId={decodeURIComponent(researchStrategyMatch[1])}
      />
    );
  return <AppShell>{page}</AppShell>;
}
