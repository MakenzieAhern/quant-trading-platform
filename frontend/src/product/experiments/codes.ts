const explanations: Record<string, [string, string]> = {
  EXPERIMENT_WORKER_OWNERSHIP_LOST: [
    "The worker lost ownership of this task. Restart the local service, then retry the interrupted task.",
    "执行进程已失去任务归属。请重启本地服务，再重试中断的任务。",
  ],
  EXPERIMENT_WORKER_UNAVAILABLE: [
    "The experiment worker is unavailable. Restart the local service and retry this request.",
    "实验执行进程不可用。请重启本地服务后重试请求。",
  ],
  INVALID_QUANTITY: [
    "Quantity must follow the permitted trading units",
    "数量需符合允许的交易单位",
  ],
  UNSUPPORTED_ORDER_TYPE: [
    "The execution path does not support this order type",
    "执行路径不支持此订单类型",
  ],
  ORDER_NOTIONAL_LIMIT: [
    "Order value exceeds the configured limit",
    "订单金额超出配置上限",
  ],
  POSITION_LIMIT: [
    "Position quantity exceeds the configured limit",
    "持仓数量超出配置上限",
  ],
  SYMBOL_EXPOSURE_LIMIT: [
    "Single-security exposure exceeds the configured limit",
    "单只证券风险敞口超出配置上限",
  ],
  GROSS_EXPOSURE_LIMIT: [
    "Total exposure exceeds the configured limit",
    "总风险敞口超出配置上限",
  ],
  LEVERAGE_LIMIT: ["Leverage exceeds the configured limit", "杠杆超出配置上限"],
  DRAWDOWN_LIMIT: [
    "The drawdown guard rejected additional risk",
    "回撤约束拒绝继续增加风险",
  ],
  INVALID_PORTFOLIO_STATE: [
    "The portfolio could not be valued safely",
    "无法安全核算组合状态",
  ],
  LIMIT_INSTRUCTION_REQUIRED: [
    "Execution requires a valid precommitted limit order",
    "执行需要有效的预先指定限价订单",
  ],
  EXPIRED_SESSION: [
    "The order's eligible session has passed",
    "订单的可执行交易日已过期",
  ],
  MISSING_STATUS_OR_RULES: [
    "Required point-in-time status or trading rules are missing",
    "缺少对应时点的证券状态或交易规则",
  ],
  IDENTITY_MISMATCH: [
    "The observation and security identity do not match",
    "行情记录与证券标识不一致",
  ],
  NOT_CONFIRMED_TRADEABLE: [
    "The security is not confirmed tradable for this session",
    "该交易日未确认证券可交易",
  ],
  RULE_NOT_EXECUTABLE: [
    "The effective trading rules prohibit execution",
    "生效交易规则不允许执行",
  ],
  UNSUPPORTED_UNBOUNDED_OR_MISSING_REFERENCE: [
    "No supported price bound or reference is available",
    "缺少受支持的价格边界或参考价",
  ],
  SINGLE_PRICE_OR_LOCKED: [
    "A one-price or locked-limit session blocks this fill",
    "一字价格或涨跌停锁定阻止此次成交",
  ],
  INVALID_OR_UNKNOWN_QUANTITY_RULE: [
    "The quantity rule could not be verified",
    "无法验证数量规则",
  ],
  MAXIMUM_QUANTITY: [
    "Quantity exceeds the exchange maximum",
    "数量超出交易所上限",
  ],
  INSUFFICIENT_SETTLED_HOLDING: [
    "Insufficient settled shares are available to sell",
    "可卖出的已结算股份不足",
  ],
  LOT_SIZE: [
    "Quantity does not meet the trading-lot rule",
    "数量不符合交易单位规则",
  ],
  TICK_SIZE: [
    "The order price does not match the tick size",
    "委托价格不符合最小价格变动单位",
  ],
  OBSERVATION_TICK_SIZE: [
    "The observed price does not match the tick size",
    "行情价格不符合最小价格变动单位",
  ],
  LIMIT_OUTSIDE_LEGAL_BOUNDS: [
    "The limit price is outside the permitted price bounds",
    "委托限价超出允许价格范围",
  ],
  BOUNDARY_OR_INVALID_OBSERVATION: [
    "A price-boundary or invalid observation prevents a conservative fill",
    "价格边界或无效行情使保守成交条件不成立",
  ],
  OPEN_OUTSIDE_PRECOMMITTED_LIMIT: [
    "The next opening price is outside the chosen limit",
    "下一开盘价超出预先指定限价",
  ],
  CORPORATE_ACTION_NON_ORDERABLE: [
    "A pending corporate action makes this holding unavailable for a new order",
    "待处理公司行动使该持仓暂时不能提交新订单",
  ],
  CORPORATE_ACTION_OPENING_UNCERTAINTY: [
    "A corporate action or share surrender makes opening execution uncertain; no simulated fill is assumed",
    "公司行动或股份让渡使开盘执行存在不确定性；模拟中不假定成交",
  ],
  DAILY_PARTICIPATION_CAP: [
    "Quantity exceeds the daily volume participation cap",
    "数量超出日成交量参与上限",
  ],
  EXPLORATORY_NOT_UNSEEN_EVIDENCE: [
    "This period has already been inspected; this is exploratory evidence.",
    "该区间已被查看；这里只提供探索性证据。",
  ],
  NO_RETURN_GUARANTEE: ["No future return is guaranteed.", "不保证未来收益。"],
  DAILY_BAR_NEXT_SESSION_EXECUTION: [
    "Daily-bar signals can execute from the next eligible session, subject to market constraints.",
    "日线信号最早在下一可交易日执行，并受市场约束。",
  ],
  "253_SESSION_WARMUP": [
    "The strategy needs 253 sessions of history to form its signals.",
    "策略需使用 253 个交易日的预热历史才能形成信号。",
  ],
  POSITION_WEIGHT_IS_REBALANCE_TARGET_NOT_INTRADAY_GUARANTEE: [
    "The position-weight limit applies to rebalance targets; price moves can change actual weights.",
    "仓位权重限制用于调仓目标；价格变化会改变实际权重。",
  ],
  DRAWDOWN_LIMIT_REJECTS_NEW_RISK_NOT_AUTOMATIC_LIQUIDATION: [
    "The drawdown guard rejects new risk after a breach. It does not automatically liquidate or guarantee a loss limit.",
    "回撤约束在触及阈值后拒绝增加风险，不自动清仓，也不保证亏损上限。",
  ],
  TRADE_COUNT_IS_EXECUTED_FILLS: [
    "Trade counts refer to executed fills, not completed buy-and-sell round trips.",
    "交易次数指实际成交笔数，不是完整买卖往返次数。",
  ],
  SYNTHETIC_DEMO_NOT_MARKET_OR_RESEARCH_EVIDENCE: [
    "Synthetic prices demonstrate the workflow and are not market or research evidence.",
    "合成价格仅演示流程，不是市场或研究证据。",
  ],
  NO_EXECUTED_TRADES_CHECK_WARMUP_LOTS_AND_RISK: [
    "No orders filled. Check the warm-up period, minimum trading lots and risk decisions.",
    "没有成交。请检查预热区间、最小交易单位及风控决策。",
  ],
  LONG_ONLY_NO_LEVERAGE: [
    "Long-only positions; no leverage.",
    "仅做多，不使用杠杆。",
  ],
  APPROVED: ["Approved by the risk checks", "通过风险检查"],
  ALLOWED: ["Approved by the risk checks", "通过风险检查"],
  ELIGIBLE_SIMULATION_ASSUMPTION: [
    "Passed conservative daily-bar simulation execution checks. This is a simulation assumption, not proof of a real market fill.",
    "通过保守日线模拟执行检查。这属于模拟假设，不是真实市场成交的证明。",
  ],
  MISSING_OBSERVATION: [
    "No eligible price observation was available",
    "缺少可用价格记录",
  ],
  END_OF_RUN: [
    "No later session remained for execution",
    "区间结束，无后续交易日执行",
  ],
  BUYING_POWER: ["Insufficient available cash", "可用现金不足"],
  INSUFFICIENT_BUYING_POWER: ["Insufficient available cash", "可用现金不足"],
  MAX_DRAWDOWN: ["Drawdown risk limit reached", "触及回撤风险阈值"],
  MAX_POSITION_QUANTITY: [
    "Position quantity exceeds the limit",
    "持仓数量超出限制",
  ],
  MAX_ORDER_NOTIONAL: ["Order value exceeds the limit", "订单金额超出限制"],
  MAX_SYMBOL_EXPOSURE: [
    "Single-security exposure exceeds the limit",
    "单只证券风险敞口超出限制",
  ],
  MAX_GROSS_EXPOSURE: [
    "Total exposure exceeds the limit",
    "总风险敞口超出限制",
  ],
  MAX_GROSS_LEVERAGE: ["Leverage exceeds the limit", "杠杆超出限制"],
  DATASET_NOT_MOUNTED: [
    "Historical data are not available to the service. Check the data center or use the labeled demo.",
    "服务无法读取历史数据。请检查数据中心，或使用明确标记的演示。",
  ],
  DATASET_INTEGRITY_FAILED: [
    "The data integrity check failed. Check the registered data source before retrying.",
    "数据完整性检查未通过。重试前请检查已注册数据来源。",
  ],
  UNEXPLAINED_HELD_REFERENCE_ADJUSTMENT: [
    "A held security's official price reference changed without an accepted accounting boundary that explains the change. The task stopped before using it for fills or valuation. Check corporate-action coverage in the data center; unchanged retries will not repair the source gap.",
    "持仓证券的官方参考价发生变化，但缺少能解释变化的已接受会计处理边界。任务已在使用该记录成交或估值前停止。请在数据中心检查公司行动覆盖；沿用相同数据重试不能修复来源缺口。",
  ],
  DATASET_NOT_REGISTERED: [
    "This data source is not registered. Choose one of the available sources.",
    "该数据源未注册。请选择当前可用来源。",
  ],
  DATES_OUTSIDE_DATASET: [
    "The requested dates fall outside the available data. Adjust the trading period.",
    "所选日期超出可用数据范围，请调整交易区间。",
  ],
  UNIVERSE_NOT_AVAILABLE: [
    "The selected stock universe is not available in this dataset.",
    "该数据集中没有所选股票范围。",
  ],
  NO_TRADING_SESSIONS_IN_RANGE: [
    "There are no trading sessions in this interval. Choose a wider period.",
    "该区间没有交易日，请扩大日期范围。",
  ],
  DATASET_CHANGED_SINCE_SUBMISSION: [
    "The data version changed after submission. Create a new configuration after checking the data source.",
    "提交后数据版本发生变化，请核查来源后新建配置。",
  ],
  IDEMPOTENCY_KEY_CONFLICT: [
    "This request key already belongs to another configuration. Refresh the saved task before retrying.",
    "该请求标识已对应另一配置，请先刷新已保存任务。",
  ],
  RETRY_REQUIRES_UNSUCCESSFUL_TERMINAL_JOB: [
    "Only failed, interrupted or cancelled tasks can be retried.",
    "仅失败、已中断或已取消的任务可以重试。",
  ],
  RESULT_NOT_READY: [
    "The task has not produced a complete result yet.",
    "任务尚未生成完整结果。",
  ],
  EXPERIMENT_NOT_FOUND: [
    "This experiment could not be found. Return to your experiment list.",
    "找不到该实验，请返回实验列表。",
  ],
  WORKER_RESTARTED_RETRY_AVAILABLE: [
    "The server restarted during execution. You can start a linked retry with the same configuration.",
    "运行期间服务重启。可沿用配置创建关联重试。",
  ],
  WORKER_STOPPED_RETRY_AVAILABLE: [
    "The worker stopped before completion. You can start a linked retry.",
    "执行进程在完成前停止，可创建关联重试。",
  ],
  EXPERIMENT_EXECUTION_FAILED: [
    "The execution engine stopped safely. Inspect the saved configuration and data before retrying.",
    "执行引擎已安全停止。请检查已保存配置与数据后重试。",
  ],
};

export function explainExperimentCode(
  code: string,
  language: string,
  fallback?: string,
): string {
  const chinese = language.startsWith("zh");
  return (
    explanations[code]?.[chinese ? 1 : 0] ??
    fallback ??
    (chinese
      ? "此代码尚无已登记的通俗解释；请展开技术详情查看原始代码。"
      : "No plain-language explanation is registered for this code; expand technical details to inspect it.")
  );
}
