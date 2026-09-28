import { useEffect, useState } from "react";

interface Resource<T> {
  data: T | null;
  loading: boolean;
  error: Error | null;
}

export function useApiResource<T>(
  load: (signal: AbortSignal) => Promise<T>,
  dependencies: readonly unknown[],
  poll?: { intervalMs: number; while: (data: T) => boolean },
): Resource<T> {
  const [resource, setResource] = useState<
    Resource<T> & { dependencies: readonly unknown[] }
  >({
    dependencies,
    data: null,
    loading: true,
    error: null,
  });
  useEffect(() => {
    const controller = new AbortController();
    let active = true;
    let timer: number | undefined;
    function refresh() {
      void load(controller.signal)
        .then((data) => {
          if (!active) return;
          setResource({ dependencies, data, loading: false, error: null });
          if (poll?.while(data))
            timer = window.setTimeout(refresh, poll.intervalMs);
        })
        .catch((reason: unknown) => {
          if (
            active &&
            reason instanceof Error &&
            reason.name !== "AbortError"
          ) {
            setResource({
              dependencies,
              data: null,
              loading: false,
              error: reason,
            });
          }
        });
    }
    refresh();
    return () => {
      active = false;
      controller.abort();
      window.clearTimeout(timer);
    };
    // The caller supplies the exact dependency list for its stable loader closure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  const current =
    dependencies.length === resource.dependencies.length &&
    dependencies.every((value, index) =>
      Object.is(value, resource.dependencies[index]),
    );
  if (!current) {
    // Reset on identity changes during render so A → B → A cannot revive stale A.
    setResource({ dependencies, data: null, loading: true, error: null });
  }
  return current ? resource : { data: null, loading: true, error: null };
}
