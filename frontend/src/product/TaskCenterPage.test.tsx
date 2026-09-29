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
