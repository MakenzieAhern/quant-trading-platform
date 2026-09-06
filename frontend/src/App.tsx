import { AppShell } from "./components/AppShell";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { BacktestHistoryPage } from "./pages/BacktestHistoryPage";
import { CreateBacktestPage } from "./pages/CreateBacktestPage";
import { NotFoundPage } from "./pages/NotFoundPage";
import { usePathname } from "./utils/navigation";

export function App() {
  const pathname = usePathname();
  const detailMatch =
    /^\/backtests\/([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\/?$/i.exec(
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
  return <AppShell>{page}</AppShell>;
}
