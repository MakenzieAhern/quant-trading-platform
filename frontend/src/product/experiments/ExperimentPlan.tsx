import { useTranslation } from "react-i18next";
import { formatDecimal, formatPercent, shortId } from "../../utils/format";
import { explainExperimentCode } from "./codes";
import type {
  CurrentDatasetQuality,
  PaperAccountPlan,
  SimulationPlan,
} from "./types";

const en = {
  title: "Simulated rebalance preview",
  paperTitle: "This account's historical rebalance plan",
  legacy:
    "This older result has no saved plan preview. A new exploratory run can record one.",
  paperLegacy:
    "This older account has no saved account-native plan. Its orders and fills remain available below.",
  warning:
    "Historical replay or synthetic demonstration only. Not today's trading advice, and no order has been sent to a simulated account.",
  paperWarning:
    "Historical replay in this simulated account only. No broker order or current-day advice.",
  paperRouted:
    "At this completed date, proposals were routed through this account's simulated risk and order path. Later fills or cancellations are recorded below.",
  paperNoOrder:
    "No proposal was routed to this account at this completed date.",
  paperReplay:
    "This plan used this account's historical snapshot. The account summary above shows its latest state, not the balance at plan time.",
  paperEstimate:
    "Cash uses completed raw closes; the next accepted session's open and actual costs can differ. This historical plan cannot place a live order.",
  demo: "Synthetic demonstration; prices and returns are not market evidence.",
  replay:
    "Account shown here is the replayed portfolio for this experiment, not a separate live or forward account.",
  asOf: "Completed trading date (Asia/Shanghai)",
  next: "Next accepted session",
  nextUnknown: "Not available in this dataset",
  accountDate: "Account snapshot trading date (Asia/Shanghai)",
  dateNotRecorded: "Not recorded",
  unverifiedDate:
    "The account snapshot date is missing or differs from this plan's date. Treat this as an unverified historical record, not an executable plan. Original amounts, risk decisions, orders and fills are preserved. For a newly verified preview, create a separate exploratory run or account; do not overwrite this record.",
  recordedCash: "Recorded account cash (CNY)",
  recordedEquity: "Recorded account equity (CNY)",
  cash: "Replayed cash (CNY)",
  equity: "Replayed equity (CNY)",
  paperCash: "Cash at plan time (CNY)",
  paperEquity: "Equity at plan time (CNY)",
  needed: "Estimated cash for risk-approved buys at reference close (CNY)",
  estimate:
    "The next session's open and actual costs can differ. This preview cannot execute by itself.",
  security: "Security",
  side: "Change",
  weight: "Target weight",
  held: "Held shares",
  target: "Target shares",
  proposed: "OMS proposal shares",
  price: "Raw reference close (CNY)",
  risk: "Risk/OMS decision",
  trigger: "Why selected",
  triggerTop: "Top-ranked eligible momentum/low-volatility share",
  triggerExit: "No longer in the strategy target",
  triggerUnknown: "Unrecognized recorded reason",
  approved: "Approved for simulation",
  rejected: "Rejected",
  unavailable: "No executable proposal",
  buy: "Buy",
  sell: "Sell",
  hold: "Hold",
  noCandidates:
    "No eligible candidate or account change was produced for this date.",
  scroll: "Scroll this table horizontally to inspect every risk decision.",
  details: "Data and configuration provenance",
  dataset: "Dataset checksum",
  snapshot: "Observed data snapshot checksum",
  account: "Replayed account snapshot checksum",
  configuration: "Configuration checksum",
  strategy: "Strategy version",
  statuses: {
    ACCOUNT_SNAPSHOT_UNAVAILABLE:
      "No account snapshot is available; no plan was produced.",
    NEXT_SESSION_UNAVAILABLE:
      "The dataset has no accepted next session; no executable plan is available.",
    INSUFFICIENT_WARMUP:
      "The strategy has not completed its 253-session warm-up; no plan was produced.",
    NOT_REBALANCE_SESSION:
      "This completed date is not a configured rebalance session; no new plan was produced.",
    NO_ELIGIBLE_CANDIDATES:
      "No eligible security or account change was produced.",
    SIMULATION_PREVIEW:
      "Candidate changes were evaluated by the existing risk and order path.",
  },
};
const zh: typeof en = {
  title: "模拟调仓预览",
  paperTitle: "此模拟账户的历史调仓计划",
  legacy: "这份较早的结果未保存计划预览。新建探索性实验后可记录计划。",
  paperLegacy: "该较早账户未保存账户专属计划；下方仍可查看原有订单与成交。",
  warning:
    "仅供历史回放或合成演示；不是今日交易建议，且未向模拟账户提交任何订单。",
  paperWarning:
    "仅在此模拟账户内进行历史回放；没有真实券商订单，也不是今日交易建议。",
  paperRouted:
    "在这个已完成交易日，拟单已进入本账户的模拟风控和订单路径；后续成交或撤销记录见下方。",
  paperNoOrder: "该已完成交易日没有拟单进入本账户。",
  paperReplay:
    "本计划使用此账户的历史快照；上方账户概览是最新状态，并非生成计划时的余额。",
  paperEstimate:
    "现金按已完成日原始收盘价估算；下一已验收交易日开盘价和实际费用可能不同。本历史计划不能发出真实订单。",
  demo: "合成演示；价格和收益并非真实市场证据。",
  replay: "此处账户是该实验回放出的组合，不是独立的实时或前向模拟账户。",
  asOf: "已完成交易日（Asia/Shanghai）",
  next: "下一个已验收交易日",
  nextUnknown: "当前数据集不可用",
  accountDate: "账户快照交易日（Asia/Shanghai）",
  dateNotRecorded: "未记录",
  unverifiedDate:
    "账户快照日期缺失或与计划日期不一致。请将其视为未经日期核验的历史记录，而非可执行计划。原金额、风控决定、订单和成交均保留。如需新核验的预览，请另建探索性实验或模拟账户，不要覆盖本记录。",
  recordedCash: "记录的账户现金（人民币）",
  recordedEquity: "记录的账户权益（人民币）",
  cash: "回放账户现金（人民币）",
  equity: "回放账户权益（人民币）",
  paperCash: "计划时账户现金（人民币）",
  paperEquity: "计划时账户权益（人民币）",
  needed: "按收盘参考价估算的获风控批准买入现金需求（人民币）",
  estimate: "下一交易日开盘价与实际费用可能不同。本预览本身不能执行。",
  security: "证券",
  side: "变动方向",
  weight: "目标权重",
  held: "现持股数",
  target: "目标股数",
  proposed: "订单系统拟发股数",
  price: "原始收盘参考价（人民币）",
  risk: "风控／订单决策",
  trigger: "入选原因",
  triggerTop: "动量／低波动因子排序靠前且符合条件",
  triggerExit: "不再属于策略目标持仓",
  triggerUnknown: "未识别的已记录原因",
  approved: "模拟风控通过",
  rejected: "已拒绝",
  unavailable: "没有可执行拟单",
  buy: "买入",
  sell: "卖出",
  hold: "保持",
  noCandidates: "该日期未产生可用候选证券或账户变动。",
  scroll: "可横向滚动此表，查看完整的风控决策。",
  details: "数据与配置来源",
  dataset: "数据集校验和",
  snapshot: "已观察数据快照校验和",
  account: "回放账户快照校验和",
  configuration: "配置校验和",
  strategy: "策略版本",
  statuses: {
    ACCOUNT_SNAPSHOT_UNAVAILABLE: "缺少账户快照，未生成计划。",
    NEXT_SESSION_UNAVAILABLE:
      "数据集缺少已验收的下一交易日，不能生成可执行计划。",
    INSUFFICIENT_WARMUP: "策略尚未完成 253 个交易日预热，未生成计划。",
    NOT_REBALANCE_SESSION: "该日期不是配置规定的调仓日，未生成新计划。",
    NO_ELIGIBLE_CANDIDATES: "未产生合格证券或账户变动。",
    SIMULATION_PREVIEW: "候选变动已通过现有风控与订单路径评估。",
  },
};

export function ExperimentPlan({
  plan,
  account = false,
  quality,
}: {
  plan: SimulationPlan | PaperAccountPlan | null;
  account?: boolean;
  quality?: CurrentDatasetQuality;
}) {
  const { i18n } = useTranslation();
  const c = i18n.language.startsWith("zh") ? zh : en;
  const title = account ? c.paperTitle : c.title;
  const unverifiedDate = Boolean(
    plan?.account &&
    plan.account_snapshot_trading_date !== plan.as_of_trading_date,
  );
  return (
    <section
      className="experimentPanel"
      id="simulation-plan"
      aria-label={title}
    >
      <h2>{title}</h2>
      {quality && (
        <p className="experimentNotice" role="note">
          {explainExperimentCode(quality, i18n.language)}
        </p>
      )}
      {!plan ? (
        <p>{account ? c.paperLegacy : c.legacy}</p>
      ) : (
        <>
          <p className="experimentNotice">
            {account ? c.paperWarning : c.warning}
          </p>
          {unverifiedDate && (
            <p className="stateCallout" role="alert">
              {c.unverifiedDate}
            </p>
          )}
          <p>
            {account
              ? c.paperReplay
              : plan.mode === "synthetic_demo"
                ? c.demo
                : c.replay}
          </p>
          {account && (
            <p>{plan.submitted_to_account ? c.paperRouted : c.paperNoOrder}</p>
          )}
          <p role="status">
            {c.statuses[plan.status as keyof typeof c.statuses] ?? plan.status}
          </p>
          <dl className="experimentExecution">
            <div>
              <dt>{c.asOf}</dt>
              <dd>{plan.as_of_trading_date}</dd>
            </div>
            <div>
              <dt>{c.accountDate}</dt>
              <dd>{plan.account_snapshot_trading_date ?? c.dateNotRecorded}</dd>
            </div>
            <div>
              <dt>{c.next}</dt>
              <dd>{plan.next_accepted_session ?? c.nextUnknown}</dd>
            </div>
            <div>
              <dt>
                {unverifiedDate
                  ? c.recordedCash
                  : account
                    ? c.paperCash
                    : c.cash}
              </dt>
              <dd>{formatDecimal(plan.account?.cash ?? null)}</dd>
            </div>
            <div>
              <dt>
                {unverifiedDate
                  ? c.recordedEquity
                  : account
                    ? c.paperEquity
                    : c.equity}
              </dt>
              <dd>{formatDecimal(plan.account?.equity ?? null)}</dd>
            </div>
            <div>
              <dt>{c.needed}</dt>
              <dd>{formatDecimal(plan.estimated_cash_required)}</dd>
            </div>
          </dl>
          <p className="experimentHelp">
            {account ? c.paperEstimate : c.estimate}
          </p>
          {plan.candidates.length ? (
            <>
              <p className="experimentHelp" id="simulation-plan-scroll">
                {c.scroll}
              </p>
              <div
                className="experimentTableScroll"
                role="region"
                tabIndex={0}
                aria-label={`${title} · ${c.scroll}`}
                aria-describedby="simulation-plan-scroll"
              >
                <table aria-label={title}>
                  <thead>
                    <tr>
                      {[
                        c.security,
                        c.side,
                        c.trigger,
                        c.weight,
                        c.held,
                        c.target,
                        c.proposed,
                        c.price,
                        c.risk,
                      ].map((label) => (
                        <th scope="col" key={label}>
                          {label}
                        </th>
                      ))}
                    </tr>
                  </thead>
                  <tbody>
                    {plan.candidates.map((item) => (
                      <tr key={item.security_id}>
                        <th scope="row">{item.security_id}</th>
                        <td>
                          {item.side === "BUY"
                            ? c.buy
                            : item.side === "SELL"
                              ? c.sell
                              : c.hold}
                        </td>
                        <td>
                          {item.trigger_reason === "TOP_DECILE_MOMENTUM_LOW_VOL"
                            ? c.triggerTop
                            : item.trigger_reason === "EXITED_STRATEGY_TARGET"
                              ? c.triggerExit
                              : `${c.triggerUnknown} (${item.trigger_reason})`}
                        </td>
                        <td>{formatPercent(item.target_weight)}</td>
                        <td>{formatDecimal(item.held_quantity)}</td>
                        <td>{formatDecimal(item.target_quantity)}</td>
                        <td>{formatDecimal(item.proposed_quantity)}</td>
                        <td>{formatDecimal(item.reference_raw_close)}</td>
                        <td>
                          {item.risk_approved === true
                            ? c.approved
                            : item.risk_approved === false
                              ? `${c.rejected}: ${explainExperimentCode(item.risk_reason_code, i18n.language)}`
                              : c.unavailable}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </>
          ) : (
            <p>{c.noCandidates}</p>
          )}
          <details className="experimentTechnical">
            <summary>{c.details}</summary>
            <dl>
              <dt>{c.dataset}</dt>
              <dd title={plan.dataset_sha256}>
                {shortId(plan.dataset_sha256)}
              </dd>
              <dt>{c.snapshot}</dt>
              <dd title={plan.data_snapshot_sha256}>
                {shortId(plan.data_snapshot_sha256)}
              </dd>
              <dt>{c.account}</dt>
              <dd title={plan.account?.snapshot_sha256}>
                {plan.account
                  ? shortId(plan.account.snapshot_sha256)
                  : c.nextUnknown}
              </dd>
              <dt>{c.configuration}</dt>
              <dd title={plan.configuration_sha256}>
                {shortId(plan.configuration_sha256)}
              </dd>
              <dt>{c.strategy}</dt>
              <dd>
                {plan.strategy_id} v{plan.strategy_version}
              </dd>
            </dl>
          </details>
        </>
      )}
    </section>
  );
}
