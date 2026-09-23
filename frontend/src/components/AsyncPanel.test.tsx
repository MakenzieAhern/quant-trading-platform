import { act, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it } from "vitest";

import { ApiError } from "../api/client";
import { i18n } from "../i18n";
import { ErrorPanel } from "./AsyncPanel";

afterEach(async () => {
  await act(async () => i18n.changeLanguage("en-US"));
});

describe("ErrorPanel", () => {
  it("explains a timeout in Chinese without exposing the raw diagnostic by default", async () => {
    await act(async () => i18n.changeLanguage("zh-CN"));
    render(
      <ErrorPanel message={new ApiError(408, "The API request timed out.")} />,
    );

    expect(screen.getByRole("alert")).toHaveTextContent("请求超时");
    expect(screen.getByRole("link", { name: "重新加载本页" })).toHaveAttribute(
      "href",
      window.location.href,
    );
    expect(screen.getByText("The API request timed out.")).not.toBeVisible();
  });

  it("offers a safe route out of a missing record", async () => {
    await act(async () => i18n.changeLanguage("zh-CN"));
    render(<ErrorPanel message={new ApiError(404, "Dataset not found")} />);
    expect(screen.getByRole("alert")).toHaveTextContent("这条记录不可用");
    expect(screen.getByRole("link", { name: "返回工作台" })).toHaveAttribute(
      "href",
      "/",
    );
  });
});
