import type {
  PaperContextPin,
  PaperInputCommit,
  PaperInputProvenance,
} from "../types/paper";

const UUID = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
const SHA = /^[a-f0-9]{64}$/;
const MAX_SEQUENCE = 2147483647;

function fields(value: unknown, keys: string[]): Record<string, unknown> {
  if (typeof value !== "object" || value === null || Array.isArray(value))
    throw new Error("Invalid paper input provenance.");
  const item = value as Record<string, unknown>;
  if (
    Object.keys(item).length !== keys.length ||
    keys.some((key) => !Object.hasOwn(item, key))
  )
    throw new Error("Invalid paper input provenance fields.");
  return item;
}

function text(value: unknown, pattern?: RegExp): string {
  if (
    typeof value !== "string" ||
    !value.trim() ||
    (pattern && !pattern.test(value))
  )
    throw new Error("Invalid paper input provenance value.");
  return value;
}

export function paperInputDate(value: unknown): string {
  const result = text(value, /^\d{4}-\d{2}-\d{2}$/);
  const date = new Date(`${result}T00:00:00Z`);
  if (
    result.startsWith("0000") ||
    !Number.isFinite(date.getTime()) ||
    date.toISOString().slice(0, 10) !== result
  )
    throw new Error("Invalid paper input date.");
  return result;
}

export function paperInputUtc(value: unknown): string {
  const match =
    /^(\d{4}-\d{2}-\d{2})T(\d{2}):(\d{2}):(\d{2})(?:\.(\d{1,6}))?(?:Z|\+00:00)$/.exec(
      text(value),
    );
  if (
    !match ||
    Number(match[2]) > 23 ||
    Number(match[3]) > 59 ||
    Number(match[4]) > 59
  )
    throw new Error("Invalid paper input UTC timestamp.");
  paperInputDate(match[1]);
  // Keep microseconds when comparing server ordering evidence.
  return `${match[1]}T${match[2]}:${match[3]}:${match[4]}.${(match[5] ?? "").padEnd(6, "0")}Z`;
}

// Validate the wire contract, not the source's legal rights or cryptographic admission.
export function parsePaperInput(value: unknown): PaperInputProvenance {
  const dynamic =
    typeof value === "object" &&
    value !== null &&
    "schema_version" in value &&
    value.schema_version === "PAPER_DAILY_INPUT_V2";
  const item = fields(value, [
    "schema_version",
    "paper_session_id",
    "trading_date",
    "admission_sha256",
    "calendar_sha256",
    "authorities_sha256",
    "session_sha256",
    "input_sha256",
    "closed_at",
    "next_open_at",
    "receipts",
    ...(dynamic ? ["context"] : []),
  ]);
  const closed = paperInputUtc(item.closed_at);
  const nextOpen = paperInputUtc(item.next_open_at);
  if (
    (!dynamic && item.schema_version !== "PAPER_DAILY_INPUT_V1") ||
    closed >= nextOpen ||
    !Array.isArray(item.receipts) ||
    item.receipts.length === 0
  )
    throw new Error("Invalid paper daily input.");
  const receipts = item.receipts.map((value) => {
    const receipt = fields(value, [
      "security_id",
      "receipt_id",
      "manifest_sha256",
      "first_received_at",
    ]);
    const received = paperInputUtc(receipt.first_received_at);
    if (received < closed || received >= nextOpen)
      throw new Error("Invalid paper receipt timing.");
    return {
      security_id: text(receipt.security_id, /^CN-A:(SSE|SZSE):[0-9]{6}$/),
      receipt_id: text(receipt.receipt_id, UUID),
      manifest_sha256: text(receipt.manifest_sha256, SHA),
      first_received_at: text(receipt.first_received_at),
    };
  });
  if (
    receipts.some(
      (receipt, index) =>
        index > 0 && receipts[index - 1]!.security_id >= receipt.security_id,
    )
  )
    throw new Error("Invalid paper receipt order.");
  return {
    ...(dynamic
      ? {
          schema_version: "PAPER_DAILY_INPUT_V2" as const,
          context: parseContext(item.context, nextOpen),
        }
      : { schema_version: "PAPER_DAILY_INPUT_V1" as const }),
    paper_session_id: text(item.paper_session_id, UUID),
    trading_date: paperInputDate(item.trading_date),
    admission_sha256: text(item.admission_sha256, SHA),
    calendar_sha256: text(item.calendar_sha256, SHA),
    authorities_sha256: text(item.authorities_sha256, SHA),
    session_sha256: text(item.session_sha256, SHA),
    input_sha256: text(item.input_sha256, SHA),
    closed_at: text(item.closed_at),
    next_open_at: text(item.next_open_at),
    receipts,
  };
}

const CONTEXT_AUTHORITIES = [
  "ADJUSTMENTS",
  "CALENDAR",
  "CORPORATE_ACTIONS",
  "MARKET_RULES",
  "SECURITY_MASTER",
  "SSE_ST",
  "SUSPENSIONS",
  "SZSE_ST",
  "TRANSACTION_COSTS",
];

function parseContext(value: unknown, nextOpen: string): PaperContextPin {
  const item = fields(value, [
    "candidate_id",
    "candidate_sha256",
    "observation_sha256",
    "verifier",
    "first_captured_at",
    "registered_at",
    "sources",
  ]);
  const captured = paperInputUtc(item.first_captured_at);
  const registered = paperInputUtc(item.registered_at);
  if (
    captured > registered ||
    registered >= nextOpen ||
    !Array.isArray(item.sources) ||
    !item.sources.length ||
    item.sources.length > 64
  )
    throw new Error("Invalid paper context timing or coverage.");
  const coverage = new Set<string>();
  const sources = item.sources.map((value) => {
    const source = fields(value, [
      "authority_names",
      "evidence_sha256",
      "receipt_sha256",
      "published_at",
      "completed_at",
      "first_observed_at",
    ]);
    if (
      !Array.isArray(source.authority_names) ||
      !source.authority_names.length
    )
      throw new Error("Invalid paper context authorities.");
    const names = source.authority_names.map((name) => text(name));
    if (
      names.some(
        (name, i) =>
          !CONTEXT_AUTHORITIES.includes(name) ||
          (i > 0 && names[i - 1]! >= name),
      ) ||
      paperInputUtc(source.published_at) > paperInputUtc(source.completed_at) ||
      paperInputUtc(source.completed_at) >
        paperInputUtc(source.first_observed_at) ||
      paperInputUtc(source.first_observed_at) > captured
    )
      throw new Error("Invalid paper context source observation.");
    names.forEach((name) => coverage.add(name));
    return {
      authority_names: names,
      evidence_sha256: text(source.evidence_sha256, SHA),
      receipt_sha256: text(source.receipt_sha256, SHA),
      published_at: text(source.published_at),
      completed_at: text(source.completed_at),
      first_observed_at: text(source.first_observed_at),
    };
  });
  const keys = sources.map(
    (source) => source.evidence_sha256 + source.receipt_sha256,
  );
  if (
    coverage.size !== CONTEXT_AUTHORITIES.length ||
    keys.some((key, i) => i > 0 && keys[i - 1]! >= key)
  )
    throw new Error("Invalid paper context source coverage or ordering.");
  const verifier = text(item.verifier);
  if (verifier.length > 128) throw new Error("Invalid paper context verifier.");
  return {
    candidate_id: text(item.candidate_id, UUID),
    candidate_sha256: text(item.candidate_sha256, SHA),
    observation_sha256: text(item.observation_sha256, SHA),
    verifier,
    first_captured_at: text(item.first_captured_at),
    registered_at: text(item.registered_at),
    sources,
  };
}

export function parsePaperInputCommit(value: unknown): PaperInputCommit {
  const item = fields(value, [
    "schema_version",
    "paper_session_id",
    "trading_date",
    "input_sha256",
    "journal_first_sequence",
    "journal_last_sequence",
    "commit_observed_at",
    "next_open_at",
  ]);
  if (
    item.schema_version !== "PAPER_INPUT_COMMIT_V1" ||
    !Number.isSafeInteger(item.journal_first_sequence) ||
    !Number.isSafeInteger(item.journal_last_sequence) ||
    Number(item.journal_first_sequence) < 1 ||
    Number(item.journal_last_sequence) < Number(item.journal_first_sequence) ||
    Number(item.journal_last_sequence) > MAX_SEQUENCE ||
    paperInputUtc(item.commit_observed_at) >= paperInputUtc(item.next_open_at)
  )
    throw new Error("Invalid paper input commit.");
  return {
    schema_version: "PAPER_INPUT_COMMIT_V1",
    paper_session_id: text(item.paper_session_id, UUID),
    trading_date: paperInputDate(item.trading_date),
    input_sha256: text(item.input_sha256, SHA),
    journal_first_sequence: item.journal_first_sequence as number,
    journal_last_sequence: item.journal_last_sequence as number,
    commit_observed_at: text(item.commit_observed_at),
    next_open_at: text(item.next_open_at),
  };
}
