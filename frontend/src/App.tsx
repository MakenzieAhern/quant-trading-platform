import { AppShell } from "./components/AppShell";
import { BacktestDetailPage } from "./pages/BacktestDetailPage";
import { BacktestHistoryPage } from "./pages/BacktestHistoryPage";
import { CreateBacktestPage } from "./pages/CreateBacktestPage";
import { usePathname } from "./utils/navigation";

export function App() {
  const pathname = usePathname();
  const detailMatch = /^\/backtests\/([0-9a-f-]+)\/?$/i.exec(pathname);
  let page = <BacktestHistoryPage />;
  if (pathname === "/backtests/new" || pathname === "/backtests/new/")
    page = <CreateBacktestPage />;
  else if (detailMatch?.[1])
    page = <BacktestDetailPage runId={detailMatch[1]} />;
  return <AppShell>{page}</AppShell>;
}
