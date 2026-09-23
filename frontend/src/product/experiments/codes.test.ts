import { expect, it } from "vitest";
import { explainExperimentCode } from "./codes";

it("explains corporate-action execution rejections in both languages", () => {
  expect(
    explainExperimentCode("CORPORATE_ACTION_OPENING_UNCERTAINTY", "en-US"),
  ).toContain("no simulated fill");
  expect(
    explainExperimentCode("CORPORATE_ACTION_OPENING_UNCERTAINTY", "zh-CN"),
  ).toContain("模拟中不假定成交");
  expect(explainExperimentCode("CORPORATE_ACTION_NON_ORDERABLE", "en-US"))
    .toContain("unavailable for a new order");
  expect(explainExperimentCode("CORPORATE_ACTION_NON_ORDERABLE", "zh-CN"))
    .toContain("不能提交新订单");
});
