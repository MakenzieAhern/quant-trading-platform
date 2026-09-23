import { useTranslation } from "react-i18next";
import { ApiError } from "../../api/client";
const en = {
  title: "Incremental raw-data requests",
  intro:
    "Request only selected securities and dates after the frozen archive. Opening this panel never starts provider acquisition.",
  candidate: "Raw candidate cache — not accepted trading data",
  authority:
    "Completion means bounded provider requests finished, not an authority PASS. Current security master, trading calendar, ST history, rules and corporate actions remain unverified. No adjustment factors are requested; these observations cannot be used for execution or forward acceptance.",
  securities: "Security IDs (1–20)",
  securitiesHelp:
    "Separate IDs with spaces, commas or new lines, for example CN-A:SSE:600000. Use existing archive securities; the server checks their known listing lifecycle. No full-universe download.",
  start: "Start date",
  end: "End date",
  bound: "Permitted date boundary",
  publish: "Latest potentially publishable date",
  dateHelp:
    "1–366 inclusive calendar days, strictly after archive coverage. The publication cutoff is not proof of a trading session or data availability.",
  submit: "Request selected raw data",
  submitting: "Submitting request…",
  confirm:
    "I understand this starts bounded provider requests for private local analysis only; it does not approve data for research or trading.",
  validation:
    "Check 1–20 distinct canonical IDs and a valid 1–366-day date range inside the displayed boundary.",
  storage:
    "Browser storage is unavailable or full. This request has not been submitted without a saved identity. Keep this page open, check storage and retry.",
  saved:
    "One request draft and identity is shared by tabs in this browser; another tab can replace it. Submitted tasks remain on the server. Unchanged resubmissions reuse the same identity.",
  loading: "Loading saved state…",
  refresh: "Refresh",
  permission:
    "The service denied this request. Check access permissions before retrying; do not bypass a source restriction.",
  timedOut:
    "The request timed out. Check service state and saved task history before retrying unchanged inputs.",
  offline:
    "The service could not be reached. Check its status and saved task history, then retry.",
  unavailable: "Acquisition unavailable",
  history: "Update task history",
  empty: "No update tasks yet.",
  open: "Open task",
  task: "Task",
  created: "Created",
  status: "Status",
  requests: "Completed provider requests",
  unknown: "Total requests not yet known",
  cancel: "Request cancellation",
  cancelPending: "Cancellation requested; waiting for the server checkpoint.",
  retry: "Retry this unsuccessful task",
  retryHelp:
    "A retry reuses verified candidate observations. Reopening and retrying the same parent returns the same child; retry that child for a further attempt.",
  working: "Sending command…",
  persisted:
    "The task is stored on the server. You may leave and reopen it from history; no fake progress or automatic restart.",
  completed:
    "Bounded raw requests completed. Candidate-only status is unchanged.",
  cancelled:
    "Stopped tasks can retain already-verified receipts. This is not a complete data-coverage claim.",
  receipts: "Provider receipt evidence",
  noReceipts: "No verified receipt is currently recorded for this task.",
  observations: "Candidate observations",
  cacheView:
    "Observations show the currently verified candidate cache for this request window, including receipts from other tasks. Gap counts are this task's completion snapshot, not a live coverage guarantee.",
  selectSecurity: "Inspect security",
  noObservations:
    "No candidate observations are recorded in this interval. Absence is not evidence of a holiday or suspension.",
  gap: "Unresolved calendar dates",
  gapHelp:
    "Dates without received observations are unresolved calendar dates, not verified missing trading sessions, holidays or suspensions.",
  cached: "Cached observations reused",
  added: "New observations",
  available: "Observations available",
  diagnostics: "Request and gap diagnostics",
  technical: "Exact provenance and authority records",
  received: "Received at (UTC)",
  requested: "Requested at (UTC)",
  source: "Provider source and terms",
  terms: "Use terms",
  termsHelp:
    "Private local analysis trial only. Redistribution and commercial data rights are not established; the software license does not grant a data license.",
  limits: "Bounded request policy",
  limitSecurities: "Maximum securities",
  limitDays: "Maximum calendar days",
  chunks: "Calendar days per request",
  attempts: "Maximum attempts per request",
  timeout: "Request timeout (seconds)",
  interval: "Minimum request interval (seconds)",
  jobTimeout: "Task time budget (seconds)",
  rowCount: "Rows in receipt",
  provider: "Provider",
  parser: "Parser version",
  sha: "Manifest SHA-256",
  rawSha: "Raw response SHA-256",
  snapshot: "Archive master snapshot (not current authority)",
  date: "Trading date (Asia/Shanghai)",
  openPrice: "Raw open",
  high: "Raw high",
  low: "Raw low",
  close: "Raw close",
  volume: "Volume (shares)",
  amount: "Amount (CNY)",
  vendorST: "Vendor ST flag (unverified)",
  vendorSuspend: "Vendor-reported suspension (unverified)",
  raw: "Raw candidate",
  receiptId: "Receipt ID",
  scroll: "Scrollable exact observation table",
  errors: "Request error",
  safeError:
    "Request could not be completed. Check service state and saved task history before retrying unchanged inputs.",
  invalidJob:
    "The update task ID in this link is invalid. Choose a saved task from history.",
  notReady:
    "No successful summary is available; retained receipts and observations may be partial.",
  viewAllGaps: "All unresolved dates for this security",
  yes: "Yes (vendor claim)",
  no: "No (vendor claim)",
  selectPrompt:
    "Open a task to inspect receipts, observations and unresolved dates.",
  statuses: {
    QUEUED: "Queued",
    RUNNING: "Running",
    SUCCEEDED: "Requests completed",
    FAILED: "Failed",
    CANCELLED: "Cancelled",
    INTERRUPTED: "Interrupted",
  },
  phases: {
    QUEUED: "Queued",
    VERIFYING_CACHE: "Verifying existing cache",
    FETCHING_RAW_CANDIDATES: "Requesting raw candidates",
    COMPLETE: "Requests completed",
    FAILED: "Failed",
    CANCELLED: "Cancelled",
    INTERRUPTED: "Interrupted",
  },
};
const zh: typeof en = {
  title: "原始行情增量请求",
  intro: "仅请求冻结档案结束后的指定证券与日期。打开此面板不会启动供应商抓取。",
  candidate: "原始候选缓存——尚未获准用于交易",
  authority:
    "完成只表示有限的供应商请求结束，不代表来源验收通过。当前证券主表、交易日历、ST 历史、规则及公司行动仍未核实。不请求复权因子；这些观察值不能用于交易执行或前向验收。",
  securities: "证券标识（1–20 个）",
  securitiesHelp:
    "使用空格、逗号或换行分隔，例如 CN-A:SSE:600000。仅限已有档案证券；服务器会检查已知上市生命周期。不会下载全市场。",
  start: "开始日期",
  end: "结束日期",
  bound: "允许的日期边界",
  publish: "最晚可能已发布日期",
  dateHelp:
    "含首尾 1–366 个自然日，必须晚于档案覆盖结束日期。发布时间界限不代表已确认交易日或数据可用。",
  submit: "请求所选原始数据",
  submitting: "正在提交请求…",
  confirm:
    "我理解此操作将启动仅供本地私人分析的有限供应商请求，不会批准数据用于研究或交易。",
  validation:
    "请检查 1–20 个不重复的规范证券标识，以及显示边界内有效的 1–366 日区间。",
  storage:
    "浏览器存储不可用或已满。未在缺少持久请求标识的情况下提交。请保留此页面，检查存储后重试。",
  saved:
    "此浏览器的标签页共享一份请求草稿与标识，其他标签页可能替换它。已提交任务保存在服务器。输入不变时重新提交会使用同一标识。",
  loading: "正在读取已保存状态…",
  refresh: "刷新",
  permission: "服务拒绝了此请求。请先核对访问权限；不得绕过数据来源的限制。",
  timedOut: "请求已超时。请先检查服务状态及已保存任务历史，再用不变输入重试。",
  offline: "无法连接服务。请先检查服务状态及已保存任务历史，然后重试。",
  unavailable: "当前无法抓取",
  history: "更新任务历史",
  empty: "尚无更新任务。",
  open: "打开任务",
  task: "任务",
  created: "创建时间",
  status: "状态",
  requests: "已完成供应商请求",
  unknown: "尚未确定请求总数",
  cancel: "请求取消",
  cancelPending: "已请求取消，正在等待服务器检查点。",
  retry: "重试此未成功任务",
  retryHelp:
    "重试会复用已验证候选观察值。重新打开同一父任务并重试会返回同一子任务；如需再次尝试，请重试该子任务。",
  working: "正在发送操作…",
  persisted:
    "任务已持久保存在服务器，可离开后从历史中重新打开；不会显示虚假进度或自动重启。",
  completed: "有限原始请求已完成，仍然仅为候选数据。",
  cancelled: "停止的任务可能保留已验证回执，不代表数据覆盖完整。",
  receipts: "供应商回执证据",
  noReceipts: "此任务目前没有已验证回执。",
  observations: "候选观察值",
  cacheView:
    "观察值来自此请求区间当前已验证的候选缓存，可能含其他任务回执。缺口计数是此任务完成时的快照，不保证当前实时覆盖完整。",
  selectSecurity: "查看证券",
  noObservations: "此区间未记录候选观察值。缺失不能证明休市或停牌。",
  gap: "未解释的自然日期",
  gapHelp:
    "未收到观察值的日期属于未解释自然日期，不是已确认缺失交易日、休市日或停牌日。",
  cached: "复用缓存观察数",
  added: "新增观察数",
  available: "可用观察数",
  diagnostics: "请求与缺口诊断",
  technical: "精确来源及权威记录",
  received: "接收时间（UTC）",
  requested: "请求时间（UTC）",
  source: "供应商来源及使用条款",
  terms: "使用条款",
  termsHelp:
    "仅供本地私人分析试用，尚未确立再分发及商业数据使用权；软件许可证不等于数据许可证。",
  limits: "有限请求策略",
  limitSecurities: "最多证券数",
  limitDays: "最多自然日数",
  chunks: "每次请求自然日数",
  attempts: "每次请求最大尝试次数",
  timeout: "请求超时（秒）",
  interval: "最短请求间隔（秒）",
  jobTimeout: "任务时间预算（秒）",
  rowCount: "回执行数",
  provider: "供应商",
  parser: "解析器版本",
  sha: "清单 SHA-256",
  rawSha: "原始响应 SHA-256",
  snapshot: "档案证券主表快照（非当前权威）",
  date: "交易日期（上海时区）",
  openPrice: "原始开盘",
  high: "原始最高",
  low: "原始最低",
  close: "原始收盘",
  volume: "成交量（股）",
  amount: "成交额（人民币）",
  vendorST: "供应商 ST 标记（未核实）",
  vendorSuspend: "供应商报告停牌（未核实）",
  raw: "原始候选",
  receiptId: "回执标识",
  scroll: "可滚动的精确观察值表",
  errors: "请求错误",
  safeError:
    "无法完成请求。请先检查服务状态及已保存任务历史，再用不变输入重试。",
  invalidJob: "链接中的更新任务标识无效，请从历史选择已保存任务。",
  notReady: "尚无成功摘要，保留的回执及观察值可能不完整。",
  viewAllGaps: "此证券全部未解释日期",
  yes: "是（供应商声明）",
  no: "否（供应商声明）",
  selectPrompt: "打开任务后可查看回执、观察值及未解释日期。",
  statuses: {
    QUEUED: "排队中",
    RUNNING: "运行中",
    SUCCEEDED: "请求已完成",
    FAILED: "失败",
    CANCELLED: "已取消",
    INTERRUPTED: "已中断",
  },
  phases: {
    QUEUED: "排队中",
    VERIFYING_CACHE: "验证已有缓存",
    FETCHING_RAW_CANDIDATES: "请求原始候选数据",
    COMPLETE: "请求已完成",
    FAILED: "失败",
    CANCELLED: "已取消",
    INTERRUPTED: "已中断",
  },
};
export function useUpdateCopy() {
  const { i18n } = useTranslation();
  return i18n.language.startsWith("zh") ? zh : en;
}
const codes: Record<string, [string, string]> = {
  RECEIPT_PERSISTENCE_BLOCKED: [
    "Receipt storage failed. Acquisition and retries are stopped to preserve the original reception evidence. Repair local storage and reconcile the retained receipt before collecting again.",
    "回执存储失败。为保留首次接收证据，抓取与重试已停止。请先修复本地存储并核对保留回执，再恢复采集。",
  ],
  SOURCE_ACCESS_DENIED: [
    "Source access was denied. Acquisition is stopped persistently; do not bypass the provider restriction.",
    "来源拒绝访问，抓取已持久停止；不得绕过供应商限制。",
  ],
  BAOSTOCK_SDK_NOT_INSTALLED: [
    "The required provider SDK is not installed. No acquisition can start.",
    "尚未安装所需供应商 SDK，无法启动抓取。",
  ],
  UPDATE_MUST_FOLLOW_FROZEN_COVERAGE: [
    "Start after the frozen archive ends; historical archive replacement is not allowed.",
    "必须从冻结档案结束后开始，不允许替换历史档案。",
  ],
  UPDATE_DATE_NOT_YET_PUBLISHABLE: [
    "The requested end date has not reached the server's publication cutoff.",
    "请求结束日期尚未到达服务器发布时间界限。",
  ],
  UPDATE_OUTSIDE_KNOWN_LISTING_LIFECYCLE: [
    "The range is outside this security's known listing lifecycle.",
    "区间超出了此证券的已知上市生命周期。",
  ],
  UPDATE_DATE_RANGE_MUST_BE_1_TO_366_DAYS: [
    "Use an inclusive range of 1–366 calendar days.",
    "请使用含首尾 1–366 个自然日的区间。",
  ],
  DATASET_NOT_MOUNTED: [
    "The audited historical archive is not mounted. Candidate requests cannot verify the security snapshot.",
    "尚未挂载已审计历史档案，无法验证证券快照并提交候选请求。",
  ],
  DATASET_INTEGRITY_FAILED: [
    "The archive integrity check failed. Stop and inspect the local data.",
    "档案完整性检查失败，请停止并检查本地数据。",
  ],
  SECURITY_NOT_FOUND: [
    "A requested security is not present in the archive master.",
    "请求的证券不在档案证券主表中。",
  ],
  IDEMPOTENCY_KEY_CONFLICT: [
    "The saved request identity belongs to different inputs. Do not blindly resubmit; review the saved task.",
    "此请求标识属于不同输入，请核对已保存任务，不要盲目重新提交。",
  ],
  MARKET_UPDATE_NOT_FOUND: [
    "This saved update task could not be found.",
    "找不到此已保存更新任务。",
  ],
  RETRY_REQUIRES_UNSUCCESSFUL_TERMINAL_JOB: [
    "Only failed, cancelled or interrupted tasks can be retried.",
    "仅失败、取消或中断的任务可以重试。",
  ],
  WORKER_RESTARTED_RETRY_AVAILABLE: [
    "The worker restarted. Receipts remain; explicitly retry this interrupted task.",
    "工作进程已重启，回执仍保留；请明确重试此中断任务。",
  ],
  UPDATE_WORKER_UNAVAILABLE: [
    "The local update worker is unavailable. Check service health before retrying.",
    "本地更新工作进程不可用，请先检查服务健康。",
  ],
  UPDATE_WORKER_OWNERSHIP_LOST: [
    "The worker lost exclusive ownership and stopped. Check service health before retrying.",
    "工作进程失去独占所有权并停止，请先检查服务健康。",
  ],
  UPDATE_JOB_TIME_BUDGET_EXHAUSTED: [
    "The bounded time budget was reached. Review retained receipts before an explicit retry.",
    "已达到任务时间预算，请核对保留回执后再明确重试。",
  ],
  PRODUCT_CACHE_INTEGRITY_FAILED: [
    "Candidate receipt integrity verification failed. Do not use these observations.",
    "候选回执完整性验证失败，请勿使用这些观察值。",
  ],
  PROVIDER_TIMEOUT: [
    "The provider timed out after bounded attempts. Review history before retrying.",
    "供应商在有限尝试后超时，请核对历史后重试。",
  ],
  PROVIDER_TRANSPORT_FAILED: [
    "The provider connection failed after bounded attempts.",
    "供应商连接在有限尝试后失败。",
  ],
  INVALID_PROVIDER_RESPONSE: [
    "The provider response failed raw-data validation and was not accepted.",
    "供应商响应未通过原始数据校验，未被接受。",
  ],
};
export function explainUpdateCode(code: string, language: string) {
  return (
    codes[code]?.[language.startsWith("zh") ? 1 : 0] ??
    (language.startsWith("zh")
      ? "更新请求未完成，请检查任务诊断与服务状态。"
      : "The update request did not complete. Check task diagnostics and service state.")
  );
}
export function updateError(reason: unknown, language: string) {
  const c = language.startsWith("zh") ? zh : en;
  if (reason instanceof ApiError) {
    if (reason.code && codes[reason.code])
      return explainUpdateCode(reason.code, language);
    if (reason.status === 401 || reason.status === 403) return c.permission;
    if (reason.status === 408) return c.timedOut;
    if (reason.status === 422) return c.validation;
  }
  if (reason instanceof TypeError) return c.offline;
  return c.safeError;
}
