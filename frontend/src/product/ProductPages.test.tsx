import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { experimentApi } from "./experiments/api";
import { capabilities } from "./experiments/fixtures.test-data";
import {
  DataCenterPage,
  HelpPage,
  ModeGuide,
  ProductError,
  ProductStrategiesPage,
  WorkbenchPage,
} from "./ProductPages";

afterEach(() => vi.restoreAllMocks());

it.each([
  ["en-US", "New-market forward simulation", "Not available yet."],
  ["zh-CN", "新行情前向模拟", "尚未开放。"],
])(
  "states current forward availability in the shared mode guide (%s)",
  async (locale, title, unavailable) => {
    await act(() => i18n.changeLanguage(locale));
    render(<ModeGuide />);
    expect(
      screen.getByRole("heading", { name: title }).closest("section"),
    ).toHaveTextContent(unavailable);
    await act(() => i18n.changeLanguage("en-US"));
  },
);

it("describes guided research without claiming it starts a simulated account", async () => {
  vi.spyOn(experimentApi, "capabilities").mockRejectedValue(
    new Error("offline"),
  );
  vi.spyOn(experimentApi, "list").mockRejectedValue(new Error("offline"));
  await act(() => i18n.changeLanguage("en-US"));
  render(<WorkbenchPage />);
  expect(
    screen.getByText(/Choose a strategy, set your assumptions/),
  ).toHaveTextContent("in a guided backtest");
  expect(
    screen.queryByText(/using a simulated account/),
  ).not.toBeInTheDocument();
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(screen.getByText(/选一个策略，设定你的假设/)).toHaveTextContent(
    "通过模拟研究",
  );
  await act(() => i18n.changeLanguage("en-US"));
});

it("keeps a section-level Retry near its persistent heading", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  render(
    <main>
      <h1>Research</h1>
      <section>
        <h2>Equity chart</h2>
        <ProductError error={new Error("offline")} retry={() => {}} />
      </section>
    </main>,
  );
  screen.getByRole("button", { name: "Try again" }).focus();
  await userEvent.keyboard("{Enter}");
  expect(screen.getByRole("heading", { name: "Equity chart" })).toHaveFocus();
});

it("closes the optional guide when browser storage rejects writes", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  // jsdom has no native dialog methods; browser behavior is checked separately.
  Object.defineProperties(HTMLDialogElement.prototype, {
    showModal: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.setAttribute("open", "");
      },
    },
    close: {
      configurable: true,
      value(this: HTMLDialogElement) {
        this.removeAttribute("open");
      },
    },
  });
  vi.spyOn(experimentApi, "capabilities").mockRejectedValue(
    new Error("offline"),
  );
  vi.spyOn(experimentApi, "list").mockRejectedValue(new Error("offline"));
  vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => {
    throw new DOMException("Denied", "SecurityError");
  });
  render(<WorkbenchPage />);
  fireEvent.click(
    screen.getByRole("button", { name: "How this workspace works" }),
  );
  expect(screen.getByRole("dialog")).toBeInTheDocument();
  fireEvent.click(
    screen.getByRole("button", { name: "Got it, continue exploring" }),
  );
  expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
});

it("keeps an open help answer expanded when its translated label changes", async () => {
  await act(() => i18n.changeLanguage("en-US"));
  render(<HelpPage />);
  fireEvent.click(screen.getByText("What is a backtest?"));
  expect(
    screen.getByText("What is a backtest?").closest("details"),
  ).toHaveAttribute("open");
  await act(() => i18n.changeLanguage("zh-CN"));
  expect(screen.getByText("什么是回测？").closest("details")).toHaveAttribute(
    "open",
  );
  await act(() => i18n.changeLanguage("en-US"));
});

it("distinguishes permission, timeout and offline failures while keeping retry", async () => {
  await i18n.changeLanguage("en-US");
  const retry = vi.fn();
  const view = render(
    <ProductError error={new ApiError(403, "denied")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("Access was denied");
  view.rerender(
    <ProductError error={new ApiError(408, "timeout")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("request timed out");
  view.rerender(
    <ProductError error={new TypeError("offline")} retry={retry} />,
  );
  expect(screen.getByRole("alert")).toHaveTextContent("service is unavailable");
  fireEvent.click(screen.getByRole("button", { name: "Try again" }));
  expect(retry).toHaveBeenCalledOnce();
});

it.each(["success", "error"])(
  "keeps keyboard focus in the Workbench after a capabilities Retry returns %s",
  async (outcome) => {
    await act(() => i18n.changeLanguage("en-US"));
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockRejectedValueOnce(new ApiError(503, "unavailable"));
    if (outcome === "success") read.mockResolvedValue(capabilities);
    else read.mockRejectedValue(new ApiError(403, "denied"));
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [],
      limit: 4,
      offset: 0,
      total: 0,
    });
    render(<WorkbenchPage />);
    const retry = await screen.findByRole("button", { name: "Try again" });
    retry.focus();
    expect(retry).toHaveFocus();
    fireEvent.click(retry);
    await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
    if (outcome === "success")
      await waitFor(() =>
        expect(screen.queryByRole("alert")).not.toBeInTheDocument(),
      );
    else await screen.findByText(/Access was denied/);
    expect(
      screen.getByRole("heading", { name: "Your research data" }),
    ).toHaveFocus();
  },
);

it.each([
  ["Strategies", <ProductStrategiesPage />],
  ["Data Center", <DataCenterPage />],
])(
  "keeps keyboard focus after a %s data Retry replaces its error",
  async (_name, page) => {
    await act(() => i18n.changeLanguage("en-US"));
    let completeRetry: ((value: typeof capabilities) => void) | undefined;
    const read = vi
      .spyOn(experimentApi, "capabilities")
      .mockRejectedValueOnce(new ApiError(503, "unavailable"))
      .mockImplementationOnce(
        () =>
          new Promise((resolve) => {
            completeRetry = resolve;
          }),
      );
    render(<main>{page}</main>);
    const retry = await screen.findByRole("button", { name: "Try again" });
    retry.focus();
    await userEvent.keyboard("{Enter}");
    await waitFor(() => expect(read).toHaveBeenCalledTimes(2));
    const heading = screen.getByRole("heading", { level: 1 });
    expect(heading).toHaveFocus();
    await act(async () => completeRetry?.(capabilities));
    expect(heading).toHaveFocus();
  },
);
