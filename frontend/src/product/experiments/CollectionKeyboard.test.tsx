import { act, render, screen, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, expect, it, vi } from "vitest";
import { i18n } from "../../i18n";
import { experimentApi } from "./api";
import { ExperimentCollections } from "./ExperimentCollections";
import { ExperimentHoldings } from "./ExperimentHoldings";

const point = {
  sequence: 0,
  trading_date: "2031-01-03",
  equity: "100000.000000000000000009",
  benchmark: "100000",
  drawdown: "0",
};
const page = { items: [point], total: 101, limit: 100, offset: 0 };

beforeEach(async () => {
  await i18n.changeLanguage("en-US");
});

it("keeps the chart pager focused through a pending request and a disabled last-page Next", async () => {
  let finish!: (value: typeof page) => void;
  vi.spyOn(experimentApi, "equity")
    .mockResolvedValueOnce(page)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
  render(<ExperimentCollections jobId="saved-job" />);
  const next = await screen.findByRole("button", { name: "Next" });
  const pager = screen.getByLabelText("Pagination");
  next.focus();
  await userEvent.keyboard("{Enter}");
  expect(pager).toBeInTheDocument();
  expect(pager).toHaveFocus();
  expect(within(pager).getByRole("button", { name: "Next" })).toBeDisabled();
  expect(screen.queryByText("1–100 of 101")).not.toBeInTheDocument();
  expect(
    screen.queryByRole("combobox", { name: "Inspect a trading date" }),
  ).not.toBeInTheDocument();
  await act(async () => finish({ ...page, offset: 100 }));
  expect(pager).toHaveFocus();
  expect(within(pager).getByRole("button", { name: "Next" })).toBeDisabled();
  expect(within(pager).getByText("101–101 of 101")).toBeInTheDocument();
  await userEvent.tab();
  expect(within(pager).getByRole("button", { name: "Previous" })).toHaveFocus();
});

it("moves a date-link action to the persistent display filter without stealing later focus", async () => {
  let finish!: (value: typeof page) => void;
  vi.spyOn(experimentApi, "equity")
    .mockResolvedValueOnce(page)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
  vi.spyOn(experimentApi, "trades").mockResolvedValue({
    items: [],
    total: 0,
    limit: 20,
    offset: 0,
  });
  vi.spyOn(experimentApi, "holdings").mockResolvedValue({
    items: [],
    total: 0,
    limit: 1,
    offset: 0,
    availability: "AVAILABLE",
  });
  render(<ExperimentCollections jobId="saved-job" />);
  const inspect = await screen.findByRole("button", {
    name: "Show trades and holdings for this date",
  });
  inspect.focus();
  await userEvent.keyboard("{Enter}");
  const filter = screen.getByRole("region", {
    name: "Displayed trading dates",
  });
  expect(filter).toHaveFocus();
  expect(filter).toHaveTextContent("2031-01-03");
  await userEvent.tab();
  const first = screen.getByLabelText("First trading date");
  expect(first).toHaveFocus();
  await act(async () => finish({ ...page, total: 1 }));
  expect(first).toHaveFocus();
  expect(
    screen.getByRole("combobox", { name: "Inspect a trading date" }),
  ).toHaveValue("2031-01-03");
  await userEvent.click(
    screen.getByRole("button", { name: "Clear linked date" }),
  );
  expect(filter).toHaveFocus();
  await userEvent.tab();
  expect(first).toHaveFocus();
});

it("keeps a holdings pager mounted through an error and retry without late autofocus", async () => {
  const holdings = {
    items: [],
    total: 2,
    limit: 1,
    offset: 0,
    availability: "AVAILABLE" as const,
  };
  let fail!: (reason: Error) => void;
  let finish!: (value: typeof holdings) => void;
  vi.spyOn(experimentApi, "holdings")
    .mockResolvedValueOnce(holdings)
    .mockImplementationOnce(
      () =>
        new Promise((_, reject) => {
          fail = reject;
        }),
    )
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          finish = resolve;
        }),
    );
  render(<ExperimentHoldings jobId="saved-job" range={{}} />);
  const next = await screen.findByRole("button", { name: "Next" });
  const pager = screen.getByRole("group", { name: "Pagination" });
  next.focus();
  await userEvent.keyboard("{Enter}");
  expect(pager).toHaveFocus();
  await act(async () => fail(new Error("offline")));
  expect(pager).toBeInTheDocument();
  expect(pager).toHaveFocus();
  expect(within(pager).getByRole("button", { name: "Previous" })).toBeEnabled();
  expect(within(pager).getByRole("button", { name: "Next" })).toBeDisabled();
  await userEvent.click(screen.getByRole("button", { name: "Retry loading" }));
  expect(pager).not.toHaveFocus();
  await act(async () => finish({ ...holdings, offset: 1 }));
  expect(pager).not.toHaveFocus();
  expect(pager).toHaveTextContent("2–2 of 2");
});

it("ignores a pending old job after replacement without reviving its data or focus", async () => {
  let oldFinish!: (value: typeof page) => void;
  vi.spyOn(experimentApi, "equity")
    .mockResolvedValueOnce(page)
    .mockImplementationOnce(
      () =>
        new Promise((resolve) => {
          oldFinish = resolve;
        }),
    )
    .mockResolvedValueOnce({
      ...page,
      items: [{ ...point, trading_date: "2031-02-05" }],
      total: 1,
    });
  const view = render(
    <>
      <input aria-label="Other task" />
      <ExperimentCollections jobId="job-A" />
    </>,
  );
  await userEvent.click(await screen.findByRole("button", { name: "Next" }));
  const oldPager = screen.getByRole("group", { name: "Pagination" });
  expect(oldPager).toHaveFocus();
  screen.getByLabelText("Other task").focus();
  view.rerender(
    <>
      <input aria-label="Other task" />
      <ExperimentCollections jobId="job-B" />
    </>,
  );
  await screen.findByRole("combobox", { name: "Inspect a trading date" });
  expect(oldPager).not.toBeInTheDocument();
  await act(async () => oldFinish({ ...page, offset: 100 }));
  expect(screen.getByLabelText("Other task")).toHaveFocus();
  expect(
    screen.getByRole("combobox", { name: "Inspect a trading date" }),
  ).toHaveValue("2031-02-05");
  expect(screen.queryByText("101–101 of 101")).not.toBeInTheDocument();
});
