import { AppShell } from "./components/AppShell";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { BacktestHistoryPage } from "./pages/BacktestHistoryPage";
import { CreateBacktestPage } from "./pages/CreateBacktestPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { CreatePaperSessionPage } from "./pages/CreatePaperSessionPage";
import { PaperSessionDetailPage } from "./pages/PaperSessionDetailPage";
import { PaperSessionsPage } from "./pages/PaperSessionsPage";
import { usePathname } from "./utils/navigation";

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
  let page = <NotFoundPage />;
  if (
    pathname === "/" ||
    pathname === "/backtests" ||
    pathname === "/backtests/"
  )
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
  return <AppShell>{page}</AppShell>;
}
