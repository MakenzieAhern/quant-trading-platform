import { expect, it } from "vitest";
import { explainExperimentCode } from "./codes";

it("uses transport guidance only for an unregistered code, preserving registered explanations", () => {
  expect(explainExperimentCode("NEW_ERROR", "en-US", "Retry loading")).toBe(
    "Retry loading",
  );
  expect(explainExperimentCode("NEW_ERROR", "zh-CN", "重新加载")).toBe(
    "重新加载",
  );
  expect(
    explainExperimentCode("DATASET_INTEGRITY_FAILED", "en-US", "Retry loading"),
  ).toContain("integrity check failed");
  expect(explainExperimentCode("NEW_ERROR", "en-US")).toContain(
    "technical details",
  );
});

it("explains corporate-action execution rejections in both languages", () => {
  expect(
    explainExperimentCode("CORPORATE_ACTION_OPENING_UNCERTAINTY", "en-US"),
  ).toContain("no simulated fill");
  expect(
    explainExperimentCode("CORPORATE_ACTION_OPENING_UNCERTAINTY", "zh-CN"),
  ).toContain("模拟中不假定成交");
  expect(
    explainExperimentCode("CORPORATE_ACTION_NON_ORDERABLE", "en-US"),
  ).toContain("unavailable for a new order");
  expect(
    explainExperimentCode("CORPORATE_ACTION_NON_ORDERABLE", "zh-CN"),
  ).toContain("不能提交新订单");
});

it("explains the held-reference integrity stop without promising a retry repairs data", () => {
  expect(
    explainExperimentCode("UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT", "en-US"),
  ).toContain("unchanged retries will not repair");
  expect(
    explainExperimentCode("UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT", "zh-CN"),
  ).toContain("重试不能修复来源缺口");
});

it("explains an ordinary distribution input stop with a source repair next step", () => {
  expect(
    explainExperimentCode("UNSUPPORTED_ORDINARY_DISTRIBUTION_INPUT", "en-US"),
  ).toContain("unchanged retries will not repair");
  expect(
    explainExperimentCode("UNSUPPORTED_ORDINARY_DISTRIBUTION_INPUT", "zh-CN"),
  ).toContain("重试不能修复来源缺口");
});

it("separates registered inspection from economic execution approval in both languages", () => {
  expect(
    explainExperimentCode("DATASET_EXECUTION_NOT_ACCEPTED", "en-US"),
  ).toContain("inspection only");
  expect(
    explainExperimentCode("DATASET_EXECUTION_NOT_ACCEPTED", "zh-CN"),
  ).toContain("仅注册用于查看");
});
