import { useEffect, useState } from "react";

interface Resource<T> {
  data: T | null;
  loading: boolean;
  error: string | null;
}

export function useApiResource<T>(
  load: (signal: AbortSignal) => Promise<T>,
  dependencies: readonly unknown[],
): Resource<T> {
  const [resource, setResource] = useState<Resource<T>>({
    data: null,
    loading: true,
    error: null,
  });
  useEffect(() => {
    const controller = new AbortController();
    setResource({ data: null, loading: true, error: null });
    void load(controller.signal)
      .then((data) => setResource({ data, loading: false, error: null }))
      .catch((reason: unknown) => {
        if (reason instanceof Error && reason.name !== "AbortError") {
          setResource({ data: null, loading: false, error: reason.message });
        }
      });
    return () => controller.abort();
    // The caller supplies the exact dependency list for its stable loader closure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  return resource;
}
