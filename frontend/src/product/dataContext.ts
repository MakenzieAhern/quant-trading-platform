import {
  createContext,
  useContext,
  useEffect,
  type Dispatch,
  type SetStateAction,
} from "react";

export interface PageData {
  mode: "historical_exploration" | "synthetic_demo";
  asOf: string | null;
  dateKind: "requested" | "observed" | "snapshot";
}
export const ProductDataContext = createContext<{
  current: PageData | null;
  setCurrent: Dispatch<SetStateAction<PageData | null>>;
} | null>(null);

export function usePageDataContext(
  mode: PageData["mode"] | null,
  asOf: string | null,
  dateKind: PageData["dateKind"] = "requested",
) {
  const setCurrent = useContext(ProductDataContext)?.setCurrent;
  useEffect(() => {
    setCurrent?.(mode ? { mode, asOf, dateKind } : null);
    return () => setCurrent?.(null);
  }, [mode, asOf, dateKind, setCurrent]);
}

export function useCurrentPageData() {
  return useContext(ProductDataContext)?.current ?? null;
}
