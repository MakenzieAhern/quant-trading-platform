import { useMemo, useState, type ReactNode } from "react";
import { ProductDataContext, type PageData } from "./dataContext";

export function ProductDataProvider({ children }: { children: ReactNode }) {
  const [current, setCurrent] = useState<PageData | null>(null);
  const value = useMemo(() => ({ current, setCurrent }), [current]);
  return (
    <ProductDataContext.Provider value={value}>
      {children}
    </ProductDataContext.Provider>
  );
}
