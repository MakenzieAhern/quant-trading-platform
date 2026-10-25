import { act, render, screen, waitFor, within } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { experimentApi } from "./experiments/api";
import { job as researchJob } from "./experiments/fixtures.test-data";
import { marketUpdateApi } from "./marketUpdates/api";
import { job as updateJob } from "./marketUpdates/fixtures.test-data";
import { TaskCenterPage } from "./TaskCenterPage";

describe("task center", () => {
  it.each(["research", "updates"])(
    "restores the %s task, independent pages and scroll after both streams load",
    async (stream) => {
      await i18n.changeLanguage("en-US");
      const href =
        stream === "research"
          ? `/experiments/${researchJob.job_id}`
          : `/data?updateJob=${updateJob.job_id}`;
      window.history.replaceState(
        {
          taskCenterReturn: {
            url: new URL("/tasks", window.location.href).href,
            href,
            scrollY: 1200,
            researchOffset: 40,
            updateOffset: 20,
          },
        },
        "",
        "/tasks",
      );
      const research = vi.spyOn(experimentApi, "list").mockResolvedValue({
        items: [researchJob],
        total: 61,
        limit: 20,
        offset: 40,
      });
      let finishUpdates!: (value: {
        items: (typeof updateJob)[];
        total: number;
        limit: number;
        offset: number;
      }) => void;
      const updates = vi.spyOn(marketUpdateApi, "list").mockImplementation(
        () =>
          new Promise((resolve) => {
            finishUpdates = resolve;
          }),
      );
      render(
        <main id="main-content" tabIndex={-1}>
          <TaskCenterPage />
        </main>,
      );
      const main = screen.getByRole("main");
      main.focus();
      await screen.findByRole("link", { name: /^Open experiment:/ });
      expect(main).toHaveFocus();
      await act(async () =>
        finishUpdates({ items: [updateJob], total: 41, limit: 20, offset: 20 }),
      );
      const link = screen.getByRole("link", {
        name: stream === "research" ? /^Open experiment:/ : /^Open task:/,
      });
      expect(link).toHaveFocus();
      expect(window.history.state.taskCenterReturn).toBeNull();
      expect(window.scrollTo).toHaveBeenCalledWith({
        top: 1200,
        left: 0,
        behavior: "instant",
      });
      expect(research).toHaveBeenCalledWith(expect.any(AbortSignal), 20, 40);
      expect(updates).toHaveBeenCalledWith(20, expect.any(AbortSignal));
    },
  );

  it("preserves the task return entry without replacing navigation ancestry", async () => {
    await i18n.changeLanguage("en-US");
    window.history.replaceState({ owner: "preserved" }, "", "/tasks");
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [researchJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    const replace = vi.spyOn(window.history, "replaceState");
    render(<TaskCenterPage />);
    await userEvent.click(
      await screen.findByRole("link", { name: /^Open task:/ }),
    );
    expect(replace).toHaveBeenCalledWith(
      expect.objectContaining({
        owner: "preserved",
        taskCenterReturn: expect.objectContaining({
          href: `/data?updateJob=${updateJob.job_id}`,
          researchOffset: 0,
          updateOffset: 0,
          scrollY: 0,
        }),
      }),
      "",
    );
  });

  it("does not steal focus when the user leaves main before saved rows load", async () => {
    await i18n.changeLanguage("en-US");
    window.history.replaceState(
      {
        taskCenterReturn: {
          url: new URL("/tasks", window.location.href).href,
          href: `/experiments/${researchJob.job_id}`,
          scrollY: 1200,
          researchOffset: 0,
          updateOffset: 0,
        },
      },
      "",
      "/tasks",
    );
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [researchJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    const refresh = screen.getByRole("button", { name: "Refresh" });
    refresh.focus();
    await screen.findByRole("link", { name: /^Open experiment:/ });
    expect(refresh).toHaveFocus();
    expect(window.scrollTo).not.toHaveBeenCalled();
  });

  it.each([
    ["research", "missing"],
    ["research", "error"],
    ["updates", "missing"],
    ["updates", "error"],
  ])(
    "keeps the %s %s fallback visible instead of restoring obsolete scroll",
    async (stream, state) => {
      await i18n.changeLanguage("en-US");
      window.history.replaceState(
        {
          taskCenterReturn: {
            url: new URL("/tasks", window.location.href).href,
            href:
              stream === "research"
                ? `/experiments/${researchJob.job_id}`
                : `/data?updateJob=${updateJob.job_id}`,
            scrollY: 1200,
            researchOffset: 0,
            updateOffset: 0,
          },
        },
        "",
        "/tasks",
      );
      const research = vi.spyOn(experimentApi, "list");
      const updates = vi.spyOn(marketUpdateApi, "list");
      if (stream === "research" && state === "error")
        research.mockRejectedValue(new ApiError(503, "unavailable"));
      else
        research.mockResolvedValue({
          items: stream === "research" ? [] : [researchJob],
          total: 0,
          limit: 20,
          offset: 0,
        });
      if (stream === "updates" && state === "error")
        updates.mockRejectedValue(new ApiError(503, "unavailable"));
      else
        updates.mockResolvedValue({
          items: stream === "updates" ? [] : [updateJob],
          total: 1,
          limit: 20,
          offset: 0,
        });
      render(<TaskCenterPage />);
      await screen.findByRole("link", {
        name: stream === "research" ? /^Open task:/ : /^Open experiment:/,
      });
      expect(
        state === "error"
          ? screen.getByRole("alert")
          : screen.getByRole("heading", {
              name:
                stream === "research"
                  ? "Research tasks"
                  : "Raw-data request tasks",
            }),
      ).toHaveFocus();
      expect(window.scrollTo).not.toHaveBeenCalled();
    },
  );

  it.each([
    { researchOffset: -20 },
    { updateOffset: 1 },
    { scrollY: Number.POSITIVE_INFINITY },
    { url: "https://example.invalid/tasks" },
  ])("rejects malformed task return context %j", async (patch) => {
    await i18n.changeLanguage("en-US");
    window.history.replaceState(
      {
        taskCenterReturn: {
          url: new URL("/tasks", window.location.href).href,
          href: `/experiments/${researchJob.job_id}`,
          scrollY: 1200,
          researchOffset: 40,
          updateOffset: 20,
          ...patch,
        },
      },
      "",
      "/tasks",
    );
    const research = vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [researchJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    const updates = vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    await screen.findByRole("link", { name: /^Open experiment:/ });
    expect(research).toHaveBeenCalledWith(expect.any(AbortSignal), 20, 0);
    expect(updates).toHaveBeenCalledWith(0, expect.any(AbortSignal));
    expect(window.scrollTo).not.toHaveBeenCalled();
  });

  it("refreshes only active research and update rows without restarting work", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    const research = vi
      .spyOn(experimentApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...researchJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [{ ...researchJob, status: "SUCCEEDED" }],
        total: 1,
        limit: 20,
        offset: 0,
      });
    const updates = vi
      .spyOn(marketUpdateApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...updateJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [updateJob],
        total: 1,
        limit: 20,
        offset: 0,
      });
    const createResearch = vi.spyOn(experimentApi, "create");
    const createUpdate = vi.spyOn(marketUpdateApi, "create");
    render(<TaskCenterPage />);
    await act(async () => {});
    const study = screen.getByRole("region", { name: "Research tasks" });
    const raw = screen.getByRole("region", { name: "Raw-data request tasks" });
    expect(study).toHaveClass("experimentPanel");
    expect(raw).toHaveClass("experimentPanel");
    expect(within(study).getByRole("status")).toHaveTextContent("Running");
    expect(within(raw).getByRole("status")).toHaveTextContent("Running");
    await act(async () => vi.advanceTimersByTime(5000));
    expect(within(study).getByRole("status")).toHaveTextContent("Complete");
    expect(within(raw).getByRole("status")).toHaveTextContent(
      "Requests completed",
    );
    await act(async () => vi.advanceTimersByTime(10000));
    expect(research).toHaveBeenCalledTimes(2);
    expect(updates).toHaveBeenCalledTimes(2);
    expect(createResearch).not.toHaveBeenCalled();
    expect(createUpdate).not.toHaveBeenCalled();
  });
  it("moves focus to the stream error when a focused saved task disappears on poll failure", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...researchJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockRejectedValueOnce(new ApiError(503, "unavailable"));
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    await act(async () => {});
    const research = screen.getByRole("region", { name: "Research tasks" });
    within(research)
      .getByRole("link", { name: /^Open experiment:/ })
      .focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(within(research).getByRole("alert")).toHaveFocus();
    expect(
      within(research).queryByRole("link", { name: /^Open experiment:/ }),
    ).not.toBeInTheDocument();
  });
  it("moves focus to the research heading when a successful poll replaces its focused task", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...researchJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [
          {
            ...researchJob,
            job_id: "aaaaaaaa-bbbb-4ccc-8ddd-000000000001",
            name: "Newer task",
          },
        ],
        total: 2,
        limit: 20,
        offset: 0,
      });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    await act(async () => {});
    const research = screen.getByRole("region", { name: "Research tasks" });
    const open = within(research).getByRole("link", {
      name: /^Open experiment:/,
    });
    open.focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(open).not.toBeInTheDocument();
    expect(
      within(research).getByRole("heading", { name: "Research tasks" }),
    ).toHaveFocus();
  });
  it("moves focus to the raw-task heading when a successful poll replaces its focused task", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(marketUpdateApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...updateJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [
          { ...updateJob, job_id: "aaaaaaaa-bbbb-4ccc-8ddd-000000000002" },
        ],
        total: 2,
        limit: 20,
        offset: 0,
      });
    render(<TaskCenterPage />);
    await act(async () => {});
    const raw = screen.getByRole("region", { name: "Raw-data request tasks" });
    const open = within(raw).getByRole("link", { name: /^Open task:/ });
    open.focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(open).not.toBeInTheDocument();
    expect(
      within(raw).getByRole("heading", { name: "Raw-data request tasks" }),
    ).toHaveFocus();
  });
  it("does not steal focus after the user leaves a task link before a successful replacement", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...researchJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockResolvedValueOnce({
        items: [
          { ...researchJob, job_id: "aaaaaaaa-bbbb-4ccc-8ddd-000000000004" },
        ],
        total: 2,
        limit: 20,
        offset: 0,
      });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    await act(async () => {});
    const open = screen.getByRole("link", { name: /^Open experiment:/ });
    open.focus();
    const refresh = screen.getByRole("button", { name: "Refresh" });
    refresh.focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(open).not.toBeInTheDocument();
    expect(refresh).toHaveFocus();
  });
  it("moves focus to the raw-task error without touching the unaffected research stream", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [researchJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(marketUpdateApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...updateJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockRejectedValueOnce(new ApiError(503, "unavailable"));
    render(<TaskCenterPage />);
    await act(async () => {});
    const updates = screen.getByRole("region", {
      name: "Raw-data request tasks",
    });
    within(updates)
      .getByRole("link", { name: /^Open task:/ })
      .focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(within(updates).getByRole("alert")).toHaveFocus();
    expect(
      screen.getByRole("link", { name: /^Open experiment:/ }),
    ).toBeInTheDocument();
  });
  it("does not steal focus after the user leaves a task link before a failed poll", async () => {
    await i18n.changeLanguage("en-US");
    vi.useFakeTimers();
    vi.spyOn(experimentApi, "list")
      .mockResolvedValueOnce({
        items: [{ ...researchJob, status: "RUNNING" }],
        total: 1,
        limit: 20,
        offset: 0,
      })
      .mockRejectedValueOnce(new ApiError(503, "unavailable"));
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    await act(async () => {});
    screen.getByRole("link", { name: /^Open experiment:/ }).focus();
    const refresh = screen.getByRole("button", { name: "Refresh" });
    refresh.focus();
    await act(async () => vi.advanceTimersByTime(5000));
    expect(screen.getByRole("alert")).toBeInTheDocument();
    expect(refresh).toHaveFocus();
  });
  it("reopens independent saved tasks and pages research without starting work", async () => {
    await i18n.changeLanguage("en-US");
    const research = vi
      .spyOn(experimentApi, "list")
      .mockImplementation(async (_signal, limit = 20, offset = 0) => ({
        items: offset === 0 ? [researchJob] : [],
        total: 21,
        limit,
        offset,
      }));
    const updates = vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    const createResearch = vi.spyOn(experimentApi, "create");
    const createUpdate = vi.spyOn(marketUpdateApi, "create");
    render(<TaskCenterPage />);
    const study = screen.getByRole("region", { name: "Research tasks" });
    const raw = screen.getByRole("region", { name: "Raw-data request tasks" });
    expect(
      await within(study).findByText(researchJob.name),
    ).toBeInTheDocument();
    expect(
      within(study).getByRole("link", {
        name: /^Open experiment: Precision exploration · 2026-09-22/,
      }),
    ).toHaveAttribute("href", `/experiments/${researchJob.job_id}`);
    expect(await within(raw).findByText(/CN-A:SSE:600000/)).toBeInTheDocument();
    expect(
      within(raw).getByRole("link", {
        name: /^Open task: CN-A:SSE:600000 · 2026-01-05–2026-01-06 · 2026-09-22/,
      }),
    ).toHaveAttribute("href", `/data?updateJob=${updateJob.job_id}`);
    expect(raw).toHaveTextContent("not approved for simulated execution");
    await userEvent.click(within(study).getByRole("button", { name: "Next" }));
    await waitFor(() =>
      expect(research).toHaveBeenLastCalledWith(
        expect.any(AbortSignal),
        20,
        20,
      ),
    );
    expect(updates).toHaveBeenCalledTimes(1);
    expect(createResearch).not.toHaveBeenCalled();
    expect(createUpdate).not.toHaveBeenCalled();
  });

  it.each([
    [
      "en-US",
      "Research tasks — Pagination",
      "Raw-data request tasks — Pagination",
    ],
    ["zh-CN", "研究任务 — 分页", "原始数据请求任务 — 分页"],
  ])("names both pagers in %s", async (language, researchName, updateName) => {
    await i18n.changeLanguage(language);
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [],
      total: 0,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    expect(
      screen.getByRole("group", { name: researchName }),
    ).toBeInTheDocument();
    expect(screen.getByRole("group", { name: updateName })).toBeInTheDocument();
  });

  it("keeps one task stream usable when the other fails and can refresh", async () => {
    await i18n.changeLanguage("en-US");
    const research = vi
      .spyOn(experimentApi, "list")
      .mockRejectedValueOnce(new ApiError(403, "denied"))
      .mockRejectedValueOnce(new TypeError("Failed to fetch"))
      .mockResolvedValue({
        items: [researchJob],
        total: 1,
        limit: 20,
        offset: 0,
      });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Access was denied",
    );
    expect(
      await screen.findByRole("link", { name: /^Open task: CN-A:SSE:600000/ }),
    ).toHaveAttribute("href", `/data?updateJob=${updateJob.job_id}`);
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Could not confirm a response from the service.",
    );
    await userEvent.click(screen.getByRole("button", { name: "Refresh" }));
    expect(
      await screen.findByRole("link", {
        name: /^Open experiment: Precision exploration/,
      }),
    ).toHaveAttribute("href", `/experiments/${researchJob.job_id}`);
    expect(research).toHaveBeenCalledTimes(3);
  });

  it("distinguishes task links in Chinese without exposing internal IDs", async () => {
    await i18n.changeLanguage("zh-CN");
    vi.spyOn(experimentApi, "list").mockResolvedValue({
      items: [researchJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    vi.spyOn(marketUpdateApi, "list").mockResolvedValue({
      items: [updateJob],
      total: 1,
      limit: 20,
      offset: 0,
    });
    render(<TaskCenterPage />);
    expect(
      await screen.findByRole("link", {
        name: /^查看实验: Precision exploration · 2026\/09\/22/,
      }),
    ).toHaveAttribute("href", `/experiments/${researchJob.job_id}`);
    expect(
      await screen.findByRole("link", {
        name: /^打开任务: CN-A:SSE:600000 · 2026-01-05–2026-01-06 · 2026\/09\/22/,
      }),
    ).toHaveAttribute("href", `/data?updateJob=${updateJob.job_id}`);
  });
});
