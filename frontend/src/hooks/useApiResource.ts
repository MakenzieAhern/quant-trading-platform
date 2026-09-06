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
    void load(controller.signal)
      .then((data) => {
        if (active)
          setResource({ dependencies, data, loading: false, error: null });
      })
      .catch((reason: unknown) => {
        if (active && reason instanceof Error && reason.name !== "AbortError") {
          setResource({
            dependencies,
            data: null,
            loading: false,
            error: reason.message,
          });
        }
      });
    return () => {
      active = false;
      controller.abort();
    };
    // The caller supplies the exact dependency list for its stable loader closure.
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, dependencies);
  const current =
    dependencies.length === resource.dependencies.length &&
    dependencies.every((value, index) =>
      Object.is(value, resource.dependencies[index]),
    );
  return current ? resource : { data: null, loading: true, error: null };
}
