import { act, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { ApiError } from "../../api/client";
import { i18n } from "../../i18n";
import { experimentApi } from "./api";
import { EXPERIMENT_VIEW_KEY, ExperimentsPage } from "./ExperimentsPage";
import { job } from "./fixtures.test-data";
import type { Experiment, Page } from "./types";

const complete: Experiment = {
  ...job,
  status: "SUCCEEDED",
  result_available: true,
};
const page: Page<Experiment> = {
  items: [complete],
  total: 21,
  limit: 20,
  offset: 20,
};
const view = {
  q: "Precision",
  status: "SUCCEEDED",
  mode: "",
  sort: "name_asc",
  columns: { mode: true, period: true, created: false },
};

it("consumes the row return entry so later non-row navigation keeps ordinary saved scrolling", async () => {
  window.history.replaceState(
    { experimentScrollY: 932, experimentReturn: saved() },
    "",
  );
  vi.spyOn(experimentApi, "list").mockResolvedValue(page);
  const first = render(<ExperimentsPage />);
  await screen.findByRole("link", { name: /^Open experiment:/ });
  expect(window.history.state.experimentReturn).toBeNull();
  first.unmount();
  window.history.replaceState(
    { ...window.history.state, experimentScrollY: 725 },
    "",
  );
  vi.mocked(window.scrollTo).mockClear();
  render(<ExperimentsPage />);
  await screen.findByRole("link", { name: /^Open experiment:/ });
  expect(target("open")).not.toHaveFocus();
  expect(window.scrollTo).toHaveBeenCalledExactlyOnceWith({
    top: 725,
    left: 0,
    behavior: "instant",
  });
});
function saved(kind = "open") {
  return {
    url: window.location.href,
    href: `/experiments/${job.job_id}`,
    kind,
    scrollLeft: 123,
  };
}
function target(kind: string) {
  return screen.getByRole("link", {
    name:
      kind === "name"
        ? /^Precision exploration ·/
        : /^Open experiment: Precision exploration/,
  });
}
beforeEach(async () => {
  await i18n.changeLanguage("en-US");
  window.localStorage.removeItem(EXPERIMENT_VIEW_KEY);
  window.history.replaceState({}, "", "/experiments");
});

it.each(["name", "open"])(
  "restores the exact %s link, both scroll axes and retained view only after rows load",
  async (kind) => {
    const ancestry = {
      quantNavigationIndex: 4,
      quantNavigationReturns: [{ url: "http://localhost/", index: 3 }],
    };
    window.history.replaceState(
      {
        ...ancestry,
        experimentView: view,
        experimentOffset: 20,
        experimentScrollY: 932,
        experimentReturn: saved(kind),
      },
      "",
    );
    let finish!: (value: Page<Experiment>) => void;
    const list = vi.spyOn(experimentApi, "list").mockReturnValue(
      new Promise((done) => {
        finish = done;
      }),
    );
    render(<ExperimentsPage />);
    expect(window.scrollTo).not.toHaveBeenCalled();
    await act(async () => finish(page));
    expect(target(kind)).toHaveFocus();
    expect(
      screen.getByRole("region", { name: "Your experiments" }).scrollLeft,
    ).toBe(123);
    expect(window.scrollTo).toHaveBeenCalledExactlyOnceWith({
      top: 932,
      left: 0,
      behavior: "instant",
    });
    expect(screen.getByLabelText("Search saved studies")).toHaveValue(
      "Precision",
    );
    expect(screen.getByLabelText("Sort studies")).toHaveValue("name_asc");
    expect(
      screen.queryByRole("columnheader", { name: "Created (UTC)" }),
    ).not.toBeInTheDocument();
    expect(list).toHaveBeenLastCalledWith(
      expect.any(AbortSignal),
      20,
      20,
      "Precision",
      { status: "SUCCEEDED", mode: undefined, sort: "name_asc" },
    );
    expect(window.history.state).toMatchObject(ancestry);
  },
);

it.each(["name", "open"])(
  "captures the %s entry at click-time without saving a persistent view",
  async (kind) => {
    vi.stubGlobal("scrollY", 932);
    vi.spyOn(experimentApi, "list").mockResolvedValue({ ...page, offset: 0 });
    const replace = vi.spyOn(window.history, "replaceState");
    render(<ExperimentsPage />);
    await screen.findByRole("link", { name: /^Open experiment:/ });
    screen.getByRole("region", { name: "Your experiments" }).scrollLeft = 123;
    await userEvent.click(target(kind));
    const state = replace.mock.calls
      .filter(([value]) => value?.experimentReturn)
      .at(-1)?.[0];
    expect(state).toMatchObject({
      experimentScrollY: 932,
      experimentReturn: {
        href: `/experiments/${job.job_id}`,
        kind,
        scrollLeft: 123,
      },
    });
    expect(window.localStorage.getItem(EXPERIMENT_VIEW_KEY)).toBeNull();
  },
);

it.each(["missing", "error"])(
  "focuses a visible %s fallback instead of an obsolete scroll",
  async (reason) => {
    window.history.replaceState(
      { experimentScrollY: 932, experimentReturn: saved() },
      "",
    );
    const list = vi.spyOn(experimentApi, "list");
    if (reason === "error")
      list.mockRejectedValue(new ApiError(503, "unavailable"));
    else list.mockResolvedValue({ ...page, items: [], total: 0, offset: 0 });
    render(<ExperimentsPage />);
    await waitFor(() =>
      expect(
        reason === "error"
          ? screen.getByRole("alert")
          : screen.getByRole("heading", { name: "Your experiments" }),
      ).toHaveFocus(),
    );
    expect(window.scrollTo).not.toHaveBeenCalled();
  },
);

it("does not steal focus or scroll when the user leaves main during loading", async () => {
  window.history.replaceState(
    { experimentScrollY: 932, experimentReturn: saved() },
    "",
  );
  let finish!: (value: Page<Experiment>) => void;
  vi.spyOn(experimentApi, "list").mockReturnValue(
    new Promise((done) => {
      finish = done;
    }),
  );
  render(
    <>
      <input aria-label="Other task" />
      <ExperimentsPage />
    </>,
  );
  screen.getByLabelText("Other task").focus();
  await act(async () => finish(page));
  expect(screen.getByLabelText("Other task")).toHaveFocus();
  expect(window.scrollTo).not.toHaveBeenCalled();
});

it("discards a pending return when filters change before the rows arrive", async () => {
  window.history.replaceState(
    { experimentScrollY: 932, experimentReturn: saved() },
    "",
  );
  vi.spyOn(experimentApi, "list")
    .mockReturnValueOnce(new Promise(() => {}))
    .mockResolvedValueOnce(page);
  render(<ExperimentsPage />);
  await userEvent.type(screen.getByLabelText("Search saved studies"), "P");
  await screen.findByRole("link", { name: /^Open experiment:/ });
  expect(target("open")).not.toHaveFocus();
  expect(window.scrollTo).not.toHaveBeenCalled();
});

it.each([
  { url: "https://example.invalid/experiments" },
  { kind: "other" },
  { scrollLeft: -1 },
  { scrollLeft: Infinity },
])("rejects malformed detail-return metadata %j", async (patch) => {
  window.history.replaceState(
    { experimentReturn: { ...saved(), ...patch } },
    "",
  );
  vi.spyOn(experimentApi, "list").mockResolvedValue(page);
  render(<ExperimentsPage />);
  await screen.findByRole("link", { name: /^Open experiment:/ });
  expect(target("open")).not.toHaveFocus();
  expect(window.scrollTo).not.toHaveBeenCalled();
});
