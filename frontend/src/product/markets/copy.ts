import { useTranslation } from "react-i18next";

const en = {
  title: "Markets & watchlist",
  intro:
    "Read the registered historical cache, inspect its gaps and save securities for later. This page does not fetch new market data or place orders.",
  historical: "Inspected historical archive",
  demo: "Synthetic demonstration",
  mode: "Data mode",
  dataset: "Data source",
  unavailable: "Source unavailable",
  noSources: "No registered data sources are available.",
  cacheOnly:
    "Historical cache reader — not live quotes. Request raw candidates and inspect update tasks in the data center.",
  updatesLink: "Open data center",
  demoWarning:
    "Synthetic prices demonstrate the interface only. They are not market prices or investment evidence.",
  historicalWarning:
    "This historical period has already been inspected. Its observations are not new-market or unseen/OOS evidence.",
  loading: "Loading saved data…",
  error:
    "The saved data could not be loaded. Check the local service and registered archive, then retry.",
  retry: "Retry reading cache",
  search: "Search securities",
  searchLabel: "Symbol, code or source-observed name",
  searchHelp:
    "Names are catalogue/source observations, not a claim about a security's name on a historical date.",
  pendingSearch:
    "Press Search securities to apply the text; previous results are hidden.",
  exchange: "Exchange",
  all: "All exchanges",
  sse: "Shanghai (SSE)",
  szse: "Shenzhen (SZSE)",
  empty: "No securities match these filters. Try another code or exchange.",
  security: "Security",
  name: "Catalogue / source-observed name",
  board: "Board",
  sseMain: "Shanghai Main Board",
  star: "STAR Market",
  szseMain: "Shenzhen Main Board",
  chiNext: "ChiNext",
  inspect: "Inspect history",
  detailUnavailable:
    "This security link could not be opened. Check the registered source or search for the security again.",
  closeDetail: "Close detail",
  save: "Save to watchlist",
  remove: "Remove from watchlist",
  saving: "Saving…",
  removing: "Removing…",
  saved: "Saved to your watchlist.",
  removed: "Removed from your watchlist.",
  saveError:
    "The watchlist change was not confirmed. Retry to reconcile with the server; additions and removals are idempotent.",
  watchlist: "Your watchlist",
  watchlistHelp:
    "Saved in the local database. A historical and a synthetic entry remain distinct, even when their codes match.",
  watchlistEmpty:
    "Your watchlist is empty. Save a security from the search results.",
  savedAt: "Added at",
  archivedSource:
    "The saved source is unavailable or has changed. You can still remove this entry.",
  coverage: "Registered coverage",
  asOf: "Archive as-of",
  retrieved: "Archive retrieval time",
  provider: "Provider / version",
  rules: "Market rule version",
  provenance: "Source & audit details",
  sourceName: "Name authority",
  sourceId: "Source identifier",
  sourceUrl: "Official / provider source URL",
  listed: "Recorded listing lifecycle",
  openEnded: "No end recorded",
  notRecorded: "Not recorded",
  checksum: "Dataset SHA-256",
  partitions: "Read partitions and checksums",
  lineage: "Source lineage",
  limitations: "Recorded limitations",
  sourceUnavailableHelp:
    "Optional historical archives must already be mounted and pass integrity checks. Selecting the demo never makes the historical archive available.",
  dates: "Historical trading-date window",
  first: "First date",
  last: "Last date",
  apply: "Read this date window",
  rangeHelp:
    "Use 1–366 calendar days within registered coverage. Dates use Asia/Shanghai; changing language or price view does not change them.",
  invalidRange:
    "Choose an ordered 1–366-day window inside this data source's coverage. Dates have not been changed.",
  raw: "Raw / unadjusted",
  adjusted: "Adjusted research prices",
  priceView: "Price view",
  adjustmentHelp:
    "Adjusted prices are supplied by the server: raw price × the factor effective on that trading date. No end-date rebasing or client-side adjustment is performed. These are research prices, not executable order prices.",
  rawHelp:
    "Raw prices are unadjusted observations. A recorded price alone does not establish that an order could execute.",
  adjustedMissing: "Observations with missing adjustment factors",
  diagnostics: "Coverage diagnosis",
  observed: "Observed OHLCV",
  suspended: "Official suspension evidence",
  uncertainSuspension: "Suspension boundary timing unknown",
  suspensionEvidence: "Original suspension evidence",
  feature: "Feature-only close",
  missing: "Unexplained missing observation",
  outside: "Outside recorded listing lifecycle",
  featureHelp:
    "Feature-only rows provide a partial close for research features. Missing open, high, low, volume and amount remain unknown; these rows are not complete, executable OHLCV bars.",
  gapHelp:
    "Missing observations are not assumed to be suspensions or zero-volume sessions. Gaps stay visible and lines are not drawn across missing prices.",
  suspensionHelp:
    "Suspension labels require recorded evidence. The separate opening-execution flag can block a session that has observations; unknown boundary timing remains Unknown, never No.",
  noBars:
    "No trading-session records were returned for this window. Try another explicit date window; no prices have been filled in.",
  chart: "Historical close price",
  chartHelp:
    "The line shows only this requested window. Hover a point or choose a trading date for exact values; missing prices break the line.",
  geometryUnavailable:
    "Chart geometry is unavailable; inspect exact values in the table.",
  pickDate: "Inspect trading date",
  date: "Trading date",
  status: "Observation status",
  risk: "Recorded risk status",
  normal: "Normal",
  st: "ST — risk-warning designation",
  starSt: "*ST — delisting-risk warning",
  delistingPeriod: "Delisting period",
  unknown: "Unknown",
  unrecognizedRisk: "Unrecognized risk code",
  blocked: "Opening execution blocked",
  yes: "Yes",
  no: "No",
  open: "Open",
  high: "High",
  low: "Low",
  close: "Close",
  volume: "Raw volume (shares)",
  amount: "Raw amount (CNY)",
  factor: "Effective adjustment factor",
  factorDate: "Factor effective date",
  exact: "Exact observations",
  scroll: "Scrollable table; scroll horizontally to see every column.",
  noValue: "N/A",
  units:
    "Prices and amounts are CNY; volume is shares. Missing values stay N/A, never zero.",
};
const zh: typeof en = {
  title: "行情与自选",
  intro:
    "阅读已注册的历史缓存、检查缺口并保存自选证券。本页不会抓取新行情或提交订单。",
  historical: "已查看的历史档案",
  demo: "合成数据演示",
  mode: "数据模式",
  dataset: "数据来源",
  unavailable: "来源不可用",
  noSources: "当前没有可用的已注册数据来源。",
  cacheOnly:
    "历史缓存阅读器——不是实时行情。可到数据中心请求原始候选数据并查看更新任务。",
  updatesLink: "打开数据中心",
  demoWarning: "合成价格仅用于演示界面，不是真实市场价格或投资证据。",
  historicalWarning: "此历史区间已被查看，不属于新市场或未见样本／OOS 证据。",
  loading: "正在读取已保存数据…",
  error: "未能读取已保存数据。请检查本地服务及已注册档案后重试。",
  retry: "重试读取缓存",
  search: "检索证券",
  searchLabel: "股票代码、标识或来源观察名称",
  searchHelp: "名称来自目录／来源观察，不代表该证券在某个历史日期使用此名称。",
  pendingSearch: "请点击“检索证券”应用输入内容；此前的检索结果已隐藏。",
  exchange: "交易所",
  all: "全部交易所",
  sse: "上海（SSE）",
  szse: "深圳（SZSE）",
  empty: "没有符合条件的证券，请尝试其他代码或交易所。",
  security: "证券",
  name: "目录／来源观察名称",
  board: "板块",
  sseMain: "沪市主板",
  star: "科创板",
  szseMain: "深市主板",
  chiNext: "创业板",
  inspect: "查看历史",
  detailUnavailable:
    "无法打开此证券链接。请检查已注册的数据来源，或重新检索该证券。",
  closeDetail: "关闭详情",
  save: "加入自选",
  remove: "移除自选",
  saving: "正在保存…",
  removing: "正在移除…",
  saved: "已保存到自选。",
  removed: "已从自选移除。",
  saveError:
    "尚未确认自选变更。可重试与服务器核对；重复加入或移除不会创建重复记录。",
  watchlist: "我的自选",
  watchlistHelp:
    "保存在本地数据库中。即使证券代码相同，历史档案与合成演示的自选记录仍彼此独立。",
  watchlistEmpty: "自选列表为空，可从检索结果添加证券。",
  savedAt: "加入时间",
  archivedSource: "该记录的数据来源不可用或已变更，但仍可移除自选。",
  coverage: "已注册覆盖区间",
  asOf: "档案数据截至",
  retrieved: "档案获取时间",
  provider: "提供方／版本",
  rules: "市场规则版本",
  provenance: "来源与审计详情",
  sourceName: "名称权威类型",
  sourceId: "来源标识",
  sourceUrl: "官方／提供方来源网址",
  listed: "记录的上市生命周期",
  openEnded: "未记录结束日期",
  notRecorded: "未记录",
  checksum: "数据集 SHA-256",
  partitions: "读取分区与校验和",
  lineage: "来源链路",
  limitations: "已记录限制",
  sourceUnavailableHelp:
    "历史档案须已挂载并通过完整性检查。使用演示不会使历史档案自动可用。",
  dates: "历史交易日期窗口",
  first: "开始日期",
  last: "结束日期",
  apply: "读取此日期窗口",
  rangeHelp:
    "请选择覆盖区间内的 1–366 个自然日。日期使用 Asia/Shanghai；切换语言或价格视图不会改变日期。",
  invalidRange:
    "请选择该数据源覆盖区间内、顺序正确的 1–366 日窗口。日期未被自动修改。",
  raw: "原始／未复权",
  adjusted: "复权研究价格",
  priceView: "价格视图",
  adjustmentHelp:
    "复权价格由服务器提供：原始价格 × 当日生效因子。不按结束日期重新归一，也不在前端计算复权。这是研究价格，不是可执行委托价格。",
  rawHelp: "原始价格为未复权记录。存在价格不代表订单一定能够成交。",
  adjustedMissing: "缺少复权因子的记录数",
  diagnostics: "覆盖诊断",
  observed: "完整 OHLCV 记录",
  suspended: "有官方停牌证据",
  uncertainSuspension: "停复牌边界时点未知",
  suspensionEvidence: "原始停牌证据",
  feature: "仅特征收盘价",
  missing: "原因未明的缺失记录",
  outside: "处于记录的上市生命周期之外",
  featureHelp:
    "仅特征记录提供研究特征所需的部分收盘价。缺失的开盘、最高、最低、成交量与成交额保持未知；这些记录不是完整、可执行的 OHLCV 行情。",
  gapHelp:
    "不会将缺失记录自动认定为停牌或零成交量交易日。缺口保留可见，曲线不跨越缺失价格。",
  suspensionHelp:
    "停牌标签须有已记录证据。即使有行情，独立的开盘执行限制也可能阻止该日成交；边界时点不明时保持“未知”，不视为“否”。",
  noBars: "此窗口没有返回交易日记录。请明确选择其他日期窗口；系统未补造价格。",
  chart: "历史收盘价",
  chartHelp:
    "曲线仅显示所选窗口。悬停数据点或选择交易日可查看精确数值；缺失价格会中断曲线。",
  geometryUnavailable: "无法绘制图形，请查看表中的精确数值。",
  pickDate: "查看交易日",
  date: "交易日",
  status: "记录状态",
  risk: "已记录风险状态",
  normal: "正常",
  st: "ST（风险警示标记）",
  starSt: "*ST（退市风险警示）",
  delistingPeriod: "退市整理期",
  unknown: "未知",
  unrecognizedRisk: "未识别的风险代码",
  blocked: "开盘执行受限",
  yes: "是",
  no: "否",
  open: "开盘",
  high: "最高",
  low: "最低",
  close: "收盘",
  volume: "原始成交量（股）",
  amount: "原始成交额（人民币）",
  factor: "生效复权因子",
  factorDate: "因子生效日期",
  exact: "精确记录",
  scroll: "可横向滚动表格以查看全部列。",
  noValue: "N/A",
  units: "价格和成交额以人民币计，成交量以股计。缺失值显示 N/A，不填零。",
};
export function useMarketCopy() {
  const { i18n } = useTranslation();
  return i18n.language.startsWith("zh") ? zh : en;
}
export type MarketCopy = typeof en;
export function boardLabel(board: string, c: MarketCopy) {
  const labels: Record<string, string> = {
    SSE_MAIN: c.sseMain,
    SSE_STAR: c.star,
    SZSE_MAIN: c.szseMain,
    SZSE_CHINEXT: c.chiNext,
  };
  return Object.hasOwn(labels, board) ? labels[board] : board;
}
export function observationLabel(status: string, c: MarketCopy) {
  const labels: Record<string, string> = {
    OBSERVED: c.observed,
    SUSPENDED: c.suspended,
    SUSPENSION_BOUNDARY_UNCERTAIN: c.uncertainSuspension,
    FEATURE_ONLY: c.feature,
    MISSING_OBSERVATION: c.missing,
    OUTSIDE_LISTING: c.outside,
  };
  return Object.hasOwn(labels, status) ? labels[status] : c.unknown;
}

export function riskLabel(status: string | null, c: MarketCopy) {
  switch (status) {
    case "NORMAL":
      return c.normal;
    case "ST":
      return c.st;
    case "STAR_ST":
      return c.starSt;
    case "DELISTING_PERIOD":
      return c.delistingPeriod;
    case null:
    case "":
      return c.unknown;
    default:
      return `${c.unrecognizedRisk}: ${status}`;
  }
}
