import { act, render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";

import { i18n } from "../../i18n";
import { jsonResponse } from "../../test/fixtures";
import { marketUpdateApi } from "./api";
import { job, observations, receipt } from "./fixtures.test-data";
import { UpdateRecords } from "./UpdateRecords";

afterEach(async () => {
  await i18n.changeLanguage("en-US");
});

function server(readerDiagnostics?: unknown) {
  const record = {
    ...receipt,
    ...(readerDiagnostics === undefined
      ? {}
      : { reader_diagnostics: readerDiagnostics }),
  };
  vi.spyOn(globalThis, "fetch").mockImplementation(async (input) =>
    jsonResponse(
      String(input).includes("/receipts?")
        ? { items: [record], total: 1, limit: 20, offset: 0 }
        : observations,
    ),
  );
  return record;
}

describe("retained receipt reader diagnostics", () => {
  it.each(["en-US", "zh-CN"])(
    "shows the server-marked legacy caveat without changing original provenance (%s)",
    async (language) => {
      await act(async () => i18n.changeLanguage(language));
      server(["PARSER_LABEL_MISMATCH_READ_ONLY"]);
      const view = render(<UpdateRecords job={job} revision={0} />);
      try {
        const summary = await screen.findByText(
          new RegExp(
            language === "zh-CN" ? "回执行数: 1" : "Rows in receipt: 1",
          ),
        );
        expect(summary).toHaveTextContent(
          language === "zh-CN"
            ? "旧回执仅供只读"
            : "Legacy receipt · read-only",
        );
        await userEvent.click(summary);
        expect(await screen.findByRole("note")).toHaveTextContent(
          language === "zh-CN"
            ? "服务器标记了保留回执的解析器标签不一致"
            : "The server marked a parser-label mismatch",
        );
        expect(screen.getByRole("note")).toHaveTextContent(
          language === "zh-CN"
            ? "不能用于执行或前向准入"
            : "not eligible for execution or forward admission",
        );
        expect(
          screen.getByText(receipt.parser_version, { selector: "dd" }),
        ).toBeVisible();
        expect(
          screen.getByText(receipt.manifest_sha256, { selector: "dd" }),
        ).toBeVisible();
      } finally {
        view.unmount();
      }
    },
  );

  it.each([{ diagnostics: undefined }, { diagnostics: [] }])(
    "does not infer a mismatch from an old parser label when diagnostics are $diagnostics",
    async ({ diagnostics }) => {
      const raw = server(diagnostics);
      const result = await marketUpdateApi.receipts(job.job_id);
      expect(result.items[0]).toEqual(raw);
      const view = render(<UpdateRecords job={job} revision={0} />);
      try {
        await userEvent.click(await screen.findByText(/Rows in receipt: 1/));
        expect(screen.queryByRole("note")).not.toBeInTheDocument();
        expect(
          screen.queryByText(/Legacy receipt · read-only/),
        ).not.toBeInTheDocument();
      } finally {
        view.unmount();
      }
    },
  );

  it.each([
    { diagnostics: null },
    { diagnostics: "PARSER_LABEL_MISMATCH_READ_ONLY" },
    { diagnostics: ["UNKNOWN"] },
    {
      diagnostics: [
        "PARSER_LABEL_MISMATCH_READ_ONLY",
        "PARSER_LABEL_MISMATCH_READ_ONLY",
      ],
    },
  ])(
    "rejects malformed or unknown receipt diagnostics $diagnostics",
    async ({ diagnostics }) => {
      server(diagnostics);
      await expect(marketUpdateApi.receipts(job.job_id)).rejects.toThrow();
    },
  );
});
