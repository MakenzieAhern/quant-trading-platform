import { useTranslation } from "react-i18next";

const en = {
  compare: "Compare selected experiments",
  select: "Select for comparison",
  chooseManually: "Choose studies manually",
  selectHelp:
    "Choose 2–3 completed experiments. Selection is kept while you browse pages.",
  selected: "Selected",
  remove: "Remove",
  comparison: "Compare experiments",
  comparisonHelp:
    "Compare saved results under their actual conditions. Higher historical returns do not establish a better future strategy.",
  invalidIds:
    "Choose 2–3 different completed experiments from your list. This comparison URL has missing, duplicate or invalid identifiers.",
  notReady: "This experiment does not have a successful complete result yet.",
  incomplete:
    "Comparison is incomplete. Resolve the listed task errors; no requested experiment has been omitted.",
  share: "Shareable comparison URL",
  compatibility: "Are these conditions the same?",
  same: "Same",
  different: "Different",
  differences:
    "Some conditions differ. These results are not a controlled comparison; review the differences before interpreting returns.",
  matching:
    "These six conditions, including requested and actual result intervals, match. This does not establish future performance or independent evidence.",
  versionBoundary:
    "These checks compare saved configuration and result date boundaries, not every observation within the interval. Implementation fingerprints, execution-model versions and effective statutory cost schedules are not verified here and may differ or be missing in older runs. Check the exported report metadata before assuming the same implementation or effective costs.",
  dataCondition: "Data version & stock universe",
  periodCondition: "Trading period",
  requestedPeriod: "Requested interval",
  actualPeriod: "Actual result interval",
  costCondition: "Cost configuration",
  cashCondition: "Starting capital",
  riskCondition: "Risk configuration",
  strategyCondition: "Strategy version & settings",
  condition: "Condition",
  setting: "Setting",
  reports: "Download a report",
  exportHelp:
    "Reports include saved configuration, data provenance, limitations and full-period summary metrics. Collection filters only change the exported records, never the summary metrics.",
  exportJson: "Download metadata report (JSON)",
  exportCsv: "Download records (CSV)",
  collection: "Records to export",
  exporting: "Preparing download…",
  exported:
    "Download prepared. Check your browser downloads. If it did not start, use the save link below.",
  savePrepared: "Save prepared report",
  holdings: "Account & holdings",
  notRecorded:
    "This older run did not record account snapshots. Its holdings cannot be reconstructed from a missing record; existing results remain unchanged.",
  notReadyRecords:
    "These records are not ready. Refresh after the experiment finishes.",
  allCash:
    "No open positions at this snapshot; the account holds cash and any separately shown receivables.",
  cash: "Cash (CNY)",
  marketValue: "Market value (CNY)",
  accountValue: "Positions + pending assets (CNY)",
  realized: "Trading realized profit / loss (CNY)",
  corporateRealized: "Corporate-action realized profit / loss (CNY)",
  totalPnl: "Total profit / loss (CNY)",
  pendingIncluded:
    "Pending corporate-action value is already included in positions + pending assets. It is not additional equity. Missing legacy profit / loss fields are shown as N/A, not zero.",
  unrealized: "Unrealized profit / loss (CNY)",
  pendingActions: "Pending corporate-action value (CNY)",
  commissionTotal: "Cumulative commission (CNY)",
  averagePrice: "Average cost",
  marketPrice: "Mark price",
  weight: "Portfolio weight",
  filterTitle: "Displayed trading dates",
  fullSavedInterval: "Full saved interval (no date filter)",
  noStartLimit: "No start-date limit",
  noEndLimit: "No end-date limit",
  apply: "Apply dates",
  reset: "Show full interval",
  rangeHelp:
    "This limits displayed records only. The complete-run return and risk metrics above stay unchanged.",
  invalidRange:
    "Choose a valid date range with the first date no later than the last.",
  inspectActivity: "Show trades and holdings for this date",
  focusedDate: "Linked trading date",
  clearFocus: "Clear linked date",
  viewTradeDate: "Inspect this trading date",
  filteredEmpty:
    "No records match these dates. Clear the date selection or widen the interval.",
  comparisonMetrics: "Saved full-period results",
  fullPrecision: "Show full precision",
  roundedSummary:
    "Summary values are rounded for reading. Full precision and exports retain the saved values.",
  noRecommendation:
    "Exploration only. This page does not rank, recommend or automatically choose a strategy.",
  unavailableHoldings: "Holdings were not recorded for this run",
  downloadError:
    "The report could not be downloaded. Check the task and service status, then retry.",
  serverDefinitions: "Metric definitions",
  notRecordedMetadata:
    "Some legacy metadata were not recorded. Consult the exported availability notes.",
};
const zh: typeof en = {
  compare: "比较所选实验",
  select: "选择用于比较",
  chooseManually: "手动选择实验",
  selectHelp: "选择 2–3 个已完成实验。切换列表页时会保留选择。",
  selected: "已选择",
  remove: "移除",
  comparison: "实验比较",
  comparisonHelp:
    "结合真实配置条件比较已保存结果。较高的历史收益不能证明策略未来更好。",
  invalidIds:
    "请从列表选择 2–3 个不同的已完成实验。此比较链接包含缺失、重复或无效的任务标识。",
  notReady: "该实验尚无成功完成的完整结果。",
  incomplete: "比较尚不完整。请处理下列任务错误；不会忽略任何所选实验。",
  share: "可分享的比较链接",
  compatibility: "这些条件是否一致？",
  same: "一致",
  different: "不同",
  differences: "部分条件不同，这不是受控比较。解读收益前请先检查差异。",
  matching:
    "这六项条件（包括请求与实际结果区间）一致，但不代表未来表现或独立证据已得到验证。",
  versionBoundary:
    "这里只比较已保存配置和结果日期边界，不逐一核对区间内的观测。实现指纹、执行模型版本及实际生效的法定费用表未核对；这些信息可能不同，也可能在旧实验中缺失。认定实现或实际成本一致前，请核查导出报告的元数据。",
  dataCondition: "数据版本与股票范围",
  periodCondition: "交易区间",
  requestedPeriod: "请求区间",
  actualPeriod: "实际结果区间",
  costCondition: "成本配置",
  cashCondition: "初始本金",
  riskCondition: "风险配置",
  strategyCondition: "策略版本与参数",
  condition: "条件",
  setting: "设置",
  reports: "下载研究报告",
  exportHelp:
    "报告包含已保存配置、数据来源、限制和完整区间指标。日期筛选仅影响导出记录，不改变汇总指标。",
  exportJson: "下载含元数据的报告（JSON）",
  exportCsv: "下载明细（CSV）",
  collection: "导出记录类型",
  exporting: "正在准备下载…",
  exported:
    "已准备下载，请查看浏览器下载记录。如果没有开始，可点击下方保存链接。",
  savePrepared: "保存已准备的报告",
  holdings: "账户与持仓",
  notRecorded:
    "该旧实验未记录账户快照。缺失记录不能重建为真实持仓；已有研究结果保持原样。",
  notReadyRecords: "记录尚未就绪。请在实验完成后刷新。",
  allCash: "该快照无未平仓证券；账户持有现金及单独列示的应收项目。",
  cash: "现金（人民币）",
  marketValue: "证券市值（人民币）",
  accountValue: "持仓与待处理资产价值（人民币）",
  realized: "交易已实现损益（人民币）",
  corporateRealized: "公司行动已实现损益（人民币）",
  totalPnl: "总损益（人民币）",
  pendingIncluded:
    "待处理公司行动价值已包含在持仓与待处理资产价值中，不应再次计入权益。旧记录缺失的损益字段显示为 N/A，而不是零。",
  unrealized: "未实现损益（人民币）",
  pendingActions: "待处理公司行动价值（人民币）",
  commissionTotal: "累计佣金（人民币）",
  averagePrice: "平均成本",
  marketPrice: "估值价格",
  weight: "组合权重",
  filterTitle: "显示的交易日期",
  fullSavedInterval: "完整已保存区间（未筛选日期）",
  noStartLimit: "不限制开始日期",
  noEndLimit: "不限制结束日期",
  apply: "应用日期",
  reset: "查看完整区间",
  rangeHelp: "仅筛选显示记录。上方完整区间的收益和风险指标保持不变。",
  invalidRange: "请输入有效日期范围，开始日期不可晚于结束日期。",
  inspectActivity: "查看该日交易与持仓",
  focusedDate: "联动交易日",
  clearFocus: "清除日期联动",
  viewTradeDate: "查看此交易日",
  filteredEmpty: "此日期范围没有记录。请清除日期选择或扩大区间。",
  comparisonMetrics: "已保存的完整区间结果",
  fullPrecision: "显示完整精度",
  roundedSummary:
    "汇总数值默认四舍五入以便阅读。完整精度和导出保留已保存的原值。",
  noRecommendation: "仅供探索。此页不进行策略排名、推荐或自动选择。",
  unavailableHoldings: "该实验未记录持仓",
  downloadError: "报告下载未完成。请检查任务及服务状态后重试。",
  serverDefinitions: "指标定义",
  notRecordedMetadata: "部分旧版元数据未被记录，请查阅导出报告中的可用性说明。",
};
export function useComparisonCopy() {
  const { i18n } = useTranslation();
  return i18n.language.startsWith("zh") ? zh : en;
}
