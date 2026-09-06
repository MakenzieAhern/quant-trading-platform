import { render, screen } from "@testing-library/react";
import { useState } from "react";
import { describe, expect, it } from "vitest";

import { useApiResource } from "./useApiResource";

function deferred<T>() {
  let resolve!: (value: T) => void;
  const promise = new Promise<T>((done) => {
    resolve = done;
  });
  return { promise, resolve };
}

describe("useApiResource", () => {
  it("clears completed A when switching B then back to A", async () => {
    const oldA = deferred<string>();
    const nextA = deferred<string>();
    const pendingB = deferred<string>();
    function Fixture({
      identity,
      again,
    }: {
      identity: string;
      again: boolean;
    }) {
      const resource = useApiResource(
        () =>
          identity === "B"
            ? pendingB.promise
            : again
              ? nextA.promise
              : oldA.promise,
        [identity],
      );
      return <span>{resource.loading ? "loading" : resource.data}</span>;
    }
    const view = render(<Fixture identity="A" again={false} />);
    oldA.resolve("old A");
    expect(await screen.findByText("old A")).toBeInTheDocument();
    view.rerender(<Fixture identity="B" again={false} />);
    view.rerender(<Fixture identity="A" again={true} />);
    expect(screen.getByText("loading")).toBeInTheDocument();
    expect(screen.queryByText("old A")).not.toBeInTheDocument();
    nextA.resolve("new A");
    expect(await screen.findByText("new A")).toBeInTheDocument();
  });
  it("does not allow an old request to overwrite a new dependency", async () => {
    const first = deferred<string>();
    const second = deferred<string>();
    function Fixture() {
      const [identity, setIdentity] = useState("A");
      const resource = useApiResource(
        () => (identity === "A" ? first.promise : second.promise),
        [identity],
      );
      return (
        <>
          <button onClick={() => setIdentity("B")}>switch</button>
          <span>{resource.loading ? "loading" : resource.data}</span>
        </>
      );
    }
    render(<Fixture />);
    screen.getByRole("button", { name: "switch" }).click();
    second.resolve("B result");
    expect(await screen.findByText("B result")).toBeInTheDocument();
    first.resolve("A stale result");
    await Promise.resolve();
    expect(screen.getByText("B result")).toBeInTheDocument();
    expect(screen.queryByText("A stale result")).not.toBeInTheDocument();
  });
});
