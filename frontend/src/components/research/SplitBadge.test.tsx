import { render, screen } from "@testing-library/react";
import { afterEach, expect, test } from "vitest";

import { i18n } from "../../i18n";
import { SplitBadge } from "./SplitBadge";

afterEach(async () => {
  await i18n.changeLanguage("en-US");
});

test("research split is understandable in both languages while retaining its audit code", async () => {
  await i18n.changeLanguage("zh-CN");
  const view = render(<SplitBadge period="PILOT_SMOKE" />);
  expect(screen.getByText("工程冒烟测试（非研究证据）")).toHaveAttribute(
    "title",
    "PILOT_SMOKE",
  );

  await i18n.changeLanguage("en-US");
  view.rerender(<SplitBadge period="PILOT_SMOKE" />);
  expect(
    screen.getByText("Engineering smoke test (not research evidence)"),
  ).toBeInTheDocument();
});
