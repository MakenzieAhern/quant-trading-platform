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
