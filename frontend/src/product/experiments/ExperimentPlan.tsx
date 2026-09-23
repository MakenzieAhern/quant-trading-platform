import { useTranslation } from "react-i18next";
import { formatDecimal, formatPercent, shortId } from "../../utils/format";
import { explainExperimentCode } from "./codes";
import type { SimulationPlan } from "./types";

const en = {
  title: "Simulated rebalance preview",
  legacy: "This older result has no saved plan preview. A new exploratory run can record one.",
  warning: "Historical replay or synthetic demonstration only. Not today's trading advice, and no order has been sent to a simulated account.",
  demo: "Synthetic demonstration; prices and returns are not market evidence.",
  replay: "Account shown here is the replayed portfolio for this experiment, not a separate live or forward account.",
  asOf: "Completed trading date (Asia/Shanghai)",
  next: "Next accepted session",
  nextUnknown: "Not available in this dataset",
  cash: "Replayed cash (CNY)",
  equity: "Replayed equity (CNY)",
  needed: "Estimated cash for risk-approved buys at reference close (CNY)",
  estimate: "The next session's open and actual costs can differ. This preview cannot execute by itself.",
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
  approved: "Approved for simulation",
  rejected: "Rejected",
  unavailable: "No executable proposal",
  buy: "Buy",
  sell: "Sell",
  hold: "Hold",
  noCandidates: "No eligible candidate or account change was produced for this date.",
  scroll: "Scroll this table horizontally to inspect every risk decision.",
  details: "Data and configuration provenance",
  dataset: "Dataset checksum",
  snapshot: "Observed data snapshot checksum",
  account: "Replayed account snapshot checksum",
  configuration: "Configuration checksum",
  strategy: "Strategy version",
  statuses: {
    ACCOUNT_SNAPSHOT_UNAVAILABLE: "No account snapshot is available; no plan was produced.",
    NEXT_SESSION_UNAVAILABLE: "The dataset has no accepted next session; no executable plan is available.",
    INSUFFICIENT_WARMUP: "The strategy has not completed its 253-session warm-up; no plan was produced.",
    NOT_REBALANCE_SESSION: "This completed date is not a configured rebalance session; no new plan was produced.",
    NO_ELIGIBLE_CANDIDATES: "No eligible security or account change was produced.",
    SIMULATION_PREVIEW: "Candidate changes were evaluated by the existing risk and order path.",
  },
};
const zh: typeof en = {
  title: "模拟调仓预览",
  legacy: "这份较早的结果未保存计划预览。新建探索性实验后可记录计划。",
  warning: "仅供历史回放或合成演示；不是今日交易建议，且未向模拟账户提交任何订单。",
  demo: "合成演示；价格和收益并非真实市场证据。",
  replay: "此处账户是该实验回放出的组合，不是独立的实时或前向模拟账户。",
  asOf: "已完成交易日（Asia/Shanghai）",
  next: "下一个已验收交易日",
  nextUnknown: "当前数据集不可用",
  cash: "回放账户现金（人民币）",
  equity: "回放账户权益（人民币）",
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
    NEXT_SESSION_UNAVAILABLE: "数据集缺少已验收的下一交易日，不能生成可执行计划。",
    INSUFFICIENT_WARMUP: "策略尚未完成 253 个交易日预热，未生成计划。",
    NOT_REBALANCE_SESSION: "该日期不是配置规定的调仓日，未生成新计划。",
    NO_ELIGIBLE_CANDIDATES: "未产生合格证券或账户变动。",
    SIMULATION_PREVIEW: "候选变动已通过现有风控与订单路径评估。",
  },
};

export function ExperimentPlan({ plan }: { plan: SimulationPlan | null }) {
  const { i18n } = useTranslation();
  const c = i18n.language.startsWith("zh") ? zh : en;
  return (
    <section className="experimentPanel" id="simulation-plan" aria-label={c.title}>
      <h2>{c.title}</h2>
      {!plan ? <p>{c.legacy}</p> : <>
        <p className="experimentNotice">{c.warning}</p>
        <p>{plan.mode === "synthetic_demo" ? c.demo : c.replay}</p>
        <p role="status">{c.statuses[plan.status as keyof typeof c.statuses] ?? plan.status}</p>
        <dl className="experimentExecution">
          <div><dt>{c.asOf}</dt><dd>{plan.as_of_trading_date}</dd></div>
          <div><dt>{c.next}</dt><dd>{plan.next_accepted_session ?? c.nextUnknown}</dd></div>
          <div><dt>{c.cash}</dt><dd>{formatDecimal(plan.account?.cash ?? null)}</dd></div>
          <div><dt>{c.equity}</dt><dd>{formatDecimal(plan.account?.equity ?? null)}</dd></div>
          <div><dt>{c.needed}</dt><dd>{formatDecimal(plan.estimated_cash_required)}</dd></div>
        </dl>
        <p className="experimentHelp">{c.estimate}</p>
        {plan.candidates.length ? <><p className="experimentHelp" id="simulation-plan-scroll">{c.scroll}</p><div className="experimentTableScroll" tabIndex={0} aria-label={c.title} aria-describedby="simulation-plan-scroll">
          <table>
            <thead><tr>
              {[c.security, c.side, c.trigger, c.weight, c.held, c.target, c.proposed, c.price, c.risk].map(label => <th scope="col" key={label}>{label}</th>)}
            </tr></thead>
            <tbody>{plan.candidates.map(item => <tr key={item.security_id}>
              <th scope="row">{item.security_id}</th>
              <td>{item.side === "BUY" ? c.buy : item.side === "SELL" ? c.sell : c.hold}</td>
              <td>{item.trigger_reason === "TOP_DECILE_MOMENTUM_LOW_VOL" ? c.triggerTop : c.triggerExit}</td>
              <td>{formatPercent(item.target_weight)}</td>
              <td>{formatDecimal(item.held_quantity)}</td>
              <td>{formatDecimal(item.target_quantity)}</td>
              <td>{formatDecimal(item.proposed_quantity)}</td>
              <td>{formatDecimal(item.reference_raw_close)}</td>
              <td>{item.risk_approved === true ? c.approved : item.risk_approved === false ? `${c.rejected}: ${explainExperimentCode(item.risk_reason_code, i18n.language)}` : c.unavailable}</td>
            </tr>)}</tbody>
          </table>
        </div></> : <p>{c.noCandidates}</p>}
        <details className="experimentTechnical">
          <summary>{c.details}</summary>
          <dl>
            <dt>{c.dataset}</dt><dd title={plan.dataset_sha256}>{shortId(plan.dataset_sha256)}</dd>
            <dt>{c.snapshot}</dt><dd title={plan.data_snapshot_sha256}>{shortId(plan.data_snapshot_sha256)}</dd>
            <dt>{c.account}</dt><dd title={plan.account?.snapshot_sha256}>{plan.account ? shortId(plan.account.snapshot_sha256) : c.nextUnknown}</dd>
            <dt>{c.configuration}</dt><dd title={plan.configuration_sha256}>{shortId(plan.configuration_sha256)}</dd>
            <dt>{c.strategy}</dt><dd>{plan.strategy_id} v{plan.strategy_version}</dd>
          </dl>
        </details>
      </>}
    </section>
  );
}
