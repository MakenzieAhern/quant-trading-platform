import {
  act,
  fireEvent,
  render,
  screen,
  waitFor,
} from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { i18n } from "../i18n";
import { job } from "../product/experiments/fixtures.test-data";
import { jsonResponse } from "../test/fixtures";
import { paperCapabilities, paperSession } from "../test/paperFixtures";
import { CreatePaperSessionPage } from "./CreatePaperSessionPage";
import {
  PAPER_CREATE_PENDING_PREFIX,
  confirmPaperCreate,
  preparePaperCreate,
} from "./paperCreateRecovery";

const capabilityPath = "/api/paper-trading/sessions/capabilities";

describe("paper creation capabilities", () => {
  beforeEach(() => {
    window.localStorage.clear();
    window.history.replaceState({}, "", "/paper/new");
    Object.defineProperty(window.navigator, "locks", {
      configurable: true,
      value: {
        request: async (_name: string, work: () => Promise<unknown>) => work(),
      },
    });
  });
  afterEach(async () => {
    window.localStorage.clear();
    Reflect.deleteProperty(window.navigator, "locks");
    await i18n.changeLanguage("en-US");
  });

  it("disables unavailable historical creation and rejects forced submit before saving a key", async () => {
    const capabilities = paperCapabilities();
    capabilities.providers[2]!.available = false;
    capabilities.providers[2]!.reason_code = "SOURCE_CONTRACT_INTEGRITY_FAILED";
    const fetch = vi.fn<typeof globalThis.fetch>(async () =>
      jsonResponse(capabilities),
    );
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    expect(
      screen.getByRole("option", {
        name: "A-share historical replay (frozen archive)",
      }),
    ).toBeDisabled();
    fireEvent.change(screen.getByLabelText("Provider"), {
      target: { value: "historical_a_share" },
    });
    fireEvent.submit(
      screen
        .getByRole("button", { name: "Create paper session" })
        .closest("form")!,
    );
    expect(fetch.mock.calls.every((call) => !call[1]?.method)).toBe(true);
    expect(
      Object.keys(window.localStorage).some((key) =>
        key.startsWith(PAPER_CREATE_PENDING_PREFIX),
      ),
    ).toBe(false);
  });

  it("shows unavailable forward mode without making it a create request mode", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(async () => jsonResponse(paperCapabilities())),
    );
    await act(async () => render(<CreatePaperSessionPage />));
    expect(
      screen.getByRole("option", {
        name: "New-market forward simulation · unavailable",
      }),
    ).toBeDisabled();
    expect(
      screen.getByText(
        /Lawful data-use rights, current source and rule checks/,
      ),
    ).toBeVisible();
    expect(
      screen.getByRole("link", { name: "Check data readiness" }),
    ).toHaveAttribute("href", "/data");
  });

  it("blocks new requests while capabilities are pending without generating an intent", async () => {
    const fetch = vi.fn<typeof globalThis.fetch>(
      () => new Promise<Response>(() => {}),
    );
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    fireEvent.submit(
      screen
        .getByRole("button", { name: "Create paper session" })
        .closest("form")!,
    );
    await act(async () => {});
    expect(fetch.mock.calls.every((call) => !call[1]?.method)).toBe(true);
    expect(
      Object.keys(window.localStorage).some((key) =>
        key.startsWith(PAPER_CREATE_PENDING_PREFIX),
      ),
    ).toBe(false);
  });

  it.each(["failed", "pending"])(
    "keeps confirmed receipt verification available when capability reads are %s",
    async (capabilityState) => {
      const original = paperSession();
      const intent = preparePaperCreate({
        provider_type: "replay",
        dataset_id: "AAPL_fixture",
        symbol: "AAPL",
        strategy: {
          type: "moving_average_crossover",
          parameters: { short_period: 2, long_period: 3 },
        },
        initial_cash: "100000",
        default_order_quantity: "10",
        risk: { enforce_buying_power: true },
      });
      confirmPaperCreate(intent, original.session_id);
      const fetch = vi.fn(async (input: RequestInfo | URL) =>
        String(input).endsWith(capabilityPath)
          ? capabilityState === "pending"
            ? new Promise<Response>(() => {})
            : jsonResponse({ detail: "unavailable" }, 503)
          : jsonResponse(original),
      );
      vi.stubGlobal("fetch", fetch);
      await act(async () => render(<CreatePaperSessionPage />));
      await userEvent.click(
        screen.getByRole("button", { name: /Verify and open/ }),
      );
      await waitFor(() =>
        expect(window.location.pathname).toBe(`/paper/${original.session_id}`),
      );
      expect(
        window.localStorage.getItem(
          `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
        ),
      ).toContain(original.session_id);
    },
  );

  it.each(["navigate", "unmount", "availability"])(
    "does not create another account after %s during receipt verification",
    async (leave) => {
      const original = paperSession();
      const intent = preparePaperCreate({
        provider_type: "replay",
        dataset_id: "AAPL_fixture",
        symbol: "AAPL",
        strategy: {
          type: "moving_average_crossover",
          parameters: { short_period: 2, long_period: 3 },
        },
        initial_cash: "100000",
        default_order_quantity: "10",
        risk: { enforce_buying_power: true },
      });
      confirmPaperCreate(intent, original.session_id);
      const saved = window.localStorage.getItem(
        `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
      );
      let finishReceipt: ((value: Response) => void) | undefined;
      const fetch = vi.fn<typeof globalThis.fetch>((input) => {
        if (String(input).endsWith(capabilityPath)) {
          const capabilities = paperCapabilities();
          if (finishReceipt && leave === "availability") {
            capabilities.providers[1]!.available = false;
            capabilities.providers[1]!.reason_code =
              "PAPER_CAPABILITY_CHECK_FAILED";
          }
          return Promise.resolve(jsonResponse(capabilities));
        }
        if (String(input).endsWith("/receipt"))
          return new Promise((resolve) => {
            finishReceipt = resolve;
          });
        return Promise.resolve(jsonResponse(original, 201));
      });
      vi.stubGlobal("fetch", fetch);
      const view = await act(async () => render(<CreatePaperSessionPage />));
      await userEvent.click(
        screen.getByRole("button", { name: "Create another paper account" }),
      );
      await waitFor(() => expect(finishReceipt).toBeDefined());
      if (leave === "navigate")
        await userEvent.click(screen.getByRole("link", { name: "Cancel" }));
      else if (leave === "unmount") view.unmount();
      else {
        await userEvent.click(
          screen.getByRole("button", { name: "Recheck availability" }),
        );
        await waitFor(() =>
          expect(
            screen.getByRole("button", { name: "Creating…" }),
          ).toBeDisabled(),
        );
      }
      await act(async () => finishReceipt!(jsonResponse(original)));
      expect(
        fetch.mock.calls.filter((call) => call[1]?.method === "POST"),
      ).toHaveLength(0);
      expect(
        Object.keys(window.localStorage).filter((key) =>
          key.startsWith(PAPER_CREATE_PENDING_PREFIX),
        ),
      ).toEqual([`${PAPER_CREATE_PENDING_PREFIX}${intent.key}`]);
      expect(
        window.localStorage.getItem(
          `${PAPER_CREATE_PENDING_PREFIX}${intent.key}`,
        ),
      ).toBe(saved);
      expect(window.location.pathname).toBe(
        leave === "navigate" ? "/paper" : "/paper/new",
      );
    },
  );

  it.each(["en-US", "zh-CN"])(
    "preserves copied historical settings and explains denied creation (%s)",
    async (locale) => {
      await i18n.changeLanguage(locale);
      window.history.replaceState(
        {},
        "",
        `/paper/new?from_experiment=${job.job_id}`,
      );
      const capabilities = paperCapabilities();
      capabilities.providers[2]!.available = false;
      capabilities.providers[2]!.reason_code =
        "SOURCE_CONTRACT_INTEGRITY_UNVERIFIED";
      const historicalJob = {
        ...job,
        status: "SUCCEEDED",
        result_available: true,
        mode: "historical_exploration",
        dataset_id: "cn-a-research-20100101-20251231-v1",
        configuration: {
          ...job.configuration,
          dataset_id: "cn-a-research-20100101-20251231-v1",
        },
      };
      const fetch = vi.fn<typeof globalThis.fetch>(async (input) =>
        jsonResponse(
          String(input).endsWith(capabilityPath) ? capabilities : historicalJob,
        ),
      );
      vi.stubGlobal("fetch", fetch);
      await act(async () => render(<CreatePaperSessionPage />));
      const chinese = locale === "zh-CN";
      expect(
        screen.getByLabelText(chinese ? "数据源" : "Provider"),
      ).toHaveValue("historical_a_share");
      expect(
        screen.getByLabelText(chinese ? "初始资金" : "Initial cash"),
      ).toHaveValue(job.configuration.initial_cash);
      expect(
        screen.getByText(
          chinese
            ? /来源完整性尚未核实/
            : /Source integrity has not been verified/,
        ),
      ).toBeVisible();
      expect(
        screen.getByRole("option", {
          name: chinese
            ? "新行情前向模拟 · 尚未开放"
            : "New-market forward simulation · unavailable",
        }),
      ).toBeDisabled();
      const create = screen.getByRole("button", {
        name: chinese ? "创建模拟交易会话" : "Create paper session",
      });
      expect(create).toBeDisabled();
      fireEvent.submit(create.closest("form")!);
      expect(fetch.mock.calls.some((call) => call[1]?.method === "POST")).toBe(
        false,
      );
      expect(
        Object.keys(window.localStorage).some((key) =>
          key.startsWith(PAPER_CREATE_PENDING_PREFIX),
        ),
      ).toBe(false);
    },
  );

  it("retains edited cash through a failed check and successful retry before allowing creation", async () => {
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(jsonResponse({ detail: "offline" }, 503))
      .mockResolvedValue(jsonResponse(paperCapabilities()));
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    const cash = screen.getByLabelText("Initial cash");
    fireEvent.change(cash, { target: { value: "123456.000000000000000001" } });
    const create = screen.getByRole("button", { name: "Create paper session" });
    expect(create).toBeDisabled();
    expect(screen.getByRole("alert")).toHaveTextContent(
      "New creation is blocked",
    );
    await userEvent.click(
      screen.getByRole("button", { name: "Recheck availability" }),
    );
    await waitFor(() => expect(create).toBeEnabled());
    expect(
      screen.getByRole("button", { name: "Recheck availability" }),
    ).toHaveFocus();
    expect(screen.getByLabelText("Initial cash")).toBe(cash);
    expect(cash).toHaveValue("123456.000000000000000001");
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(fetch.mock.calls.every((call) => !call[1]?.method)).toBe(true);
  });

  it("retains historical dates and cash when a refreshed capability revokes creation", async () => {
    const blocked = paperCapabilities();
    blocked.providers[2]!.available = false;
    blocked.providers[2]!.reason_code = "DATASET_EXECUTION_NOT_ACCEPTED";
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(jsonResponse(paperCapabilities()))
      .mockResolvedValue(jsonResponse(blocked));
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    await userEvent.selectOptions(
      screen.getByLabelText("Provider"),
      "historical_a_share",
    );
    fireEvent.change(screen.getByLabelText("Initial cash"), {
      target: { value: "4321.5" },
    });
    fireEvent.change(screen.getByLabelText("Start date"), {
      target: { value: "2011-03-01" },
    });
    await userEvent.click(
      screen.getByRole("button", { name: "Recheck availability" }),
    );
    expect(screen.getByLabelText("Provider")).toHaveValue("historical_a_share");
    expect(screen.getByLabelText("Initial cash")).toHaveValue("4321.5");
    expect(screen.getByLabelText("Start date")).toHaveValue("2011-03-01");
    const create = screen.getByRole("button", { name: "Create paper session" });
    expect(create).toBeDisabled();
    fireEvent.submit(create.closest("form")!);
    expect(fetch.mock.calls.some((call) => call[1]?.method === "POST")).toBe(
      false,
    );
  });

  it("recovers a prior pending request with the same key despite a denied capability", async () => {
    const original = paperSession();
    const request = {
      provider_type: "replay" as const,
      dataset_id: "AAPL_fixture" as const,
      symbol: "AAPL" as const,
      strategy: {
        type: "moving_average_crossover" as const,
        parameters: { short_period: 2, long_period: 3 },
      },
      initial_cash: "100000",
      default_order_quantity: "10",
      risk: { enforce_buying_power: true },
    };
    const intent = preparePaperCreate(request);
    const blocked = paperCapabilities();
    blocked.providers[0]!.available = false;
    blocked.providers[0]!.reason_code = "REPLAY_DATA_UNAVAILABLE";
    const fetch = vi.fn<typeof globalThis.fetch>(async (input, options) => {
      if (String(input).endsWith(capabilityPath)) return jsonResponse(blocked);
      return options?.method === "POST"
        ? jsonResponse({ detail: "dataset unavailable" }, 422)
        : jsonResponse(original);
    });
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    await userEvent.click(
      screen.getByRole("button", { name: /Retry saved request/ }),
    );
    await waitFor(() =>
      expect(window.location.pathname).toBe(`/paper/${original.session_id}`),
    );
    const post = fetch.mock.calls.find((call) => call[1]?.method === "POST")!;
    expect(post[1]?.body).toBe(intent.body);
    expect(new Headers(post[1]?.headers).get("Idempotency-Key")).toBe(
      intent.key,
    );
    expect(
      Object.keys(window.localStorage).filter((key) =>
        key.startsWith(PAPER_CREATE_PENDING_PREFIX),
      ),
    ).toEqual([`${PAPER_CREATE_PENDING_PREFIX}${intent.key}`]);
  });

  it("rechecks the latest capability after waiting for the cross-tab lock", async () => {
    let releaseLock: (() => Promise<unknown>) | undefined;
    Object.defineProperty(window.navigator, "locks", {
      configurable: true,
      value: {
        request: (_name: string, work: () => Promise<unknown>) =>
          new Promise((resolve, reject) => {
            releaseLock = () => work().then(resolve, reject);
          }),
      },
    });
    const denied = paperCapabilities();
    denied.providers[1]!.available = false;
    denied.providers[1]!.reason_code = "PAPER_CAPABILITY_CHECK_FAILED";
    const fetch = vi
      .fn<typeof globalThis.fetch>()
      .mockResolvedValueOnce(jsonResponse(paperCapabilities()))
      .mockResolvedValue(jsonResponse(denied));
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    await userEvent.click(
      screen.getByRole("button", { name: "Create paper session" }),
    );
    expect(releaseLock).toBeDefined();
    await userEvent.click(
      screen.getByRole("button", { name: "Recheck availability" }),
    );
    await act(async () => releaseLock!());
    expect(screen.getByRole("alert")).toHaveTextContent(
      "not currently available",
    );
    expect(fetch.mock.calls.some((call) => call[1]?.method === "POST")).toBe(
      false,
    );
    expect(
      Object.keys(window.localStorage).some((key) =>
        key.startsWith(PAPER_CREATE_PENDING_PREFIX),
      ),
    ).toBe(false);
  });

  it("does not substitute a synthetic account for an unavailable copied paper provider", async () => {
    const source = paperSession("STOPPED");
    window.history.replaceState(
      {},
      "",
      `/paper/new?from_session=${source.session_id}`,
    );
    const capabilities = paperCapabilities();
    capabilities.providers[0]!.available = false;
    capabilities.providers[0]!.reason_code = "REPLAY_DATA_UNAVAILABLE";
    const fetch = vi.fn<typeof globalThis.fetch>(async (input) =>
      jsonResponse(
        String(input).endsWith(capabilityPath) ? capabilities : source,
      ),
    );
    vi.stubGlobal("fetch", fetch);
    await act(async () => render(<CreatePaperSessionPage />));
    expect(screen.getByLabelText("Provider")).toHaveValue("replay");
    expect(screen.getByLabelText("Initial cash")).toHaveValue(
      source.initial_cash,
    );
    expect(
      screen.getByRole("link", { name: "Review original session" }),
    ).toHaveAttribute("href", `/paper/${source.session_id}`);
    expect(
      screen.getByRole("button", { name: "Create paper session" }),
    ).toBeDisabled();
    expect(
      screen.getByText("The local replay fixture is unavailable.", {
        exact: false,
      }),
    ).toBeVisible();
    expect(fetch.mock.calls.some((call) => call[1]?.method === "POST")).toBe(
      false,
    );
  });
});
