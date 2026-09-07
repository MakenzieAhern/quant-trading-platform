# 量化交易平台

**v1.1 开发中 — 中国 A 股研究版**

这是一个事件驱动的量化研究与模拟交易平台，包含确定性回测、A 股时间点正确数据处理、
横截面因子研究、Portfolio 分析、RiskEngine、OMS、PostgreSQL 持久化、REST/WebSocket API
以及中英文 React 前端。

> **仅限研究和模拟交易。不连接实盘券商，不发送真实资金订单。**

## v1.1 研究能力

- 使用稳定 `security_id` 和有效日期保存交易所、板块、代码、上市/退市与每日 ST/停牌状态。
- BaoStock 作为免费主数据源，AKShare 仅用于独立校验；数据源 SDK 不进入核心研究模块。
- 规范化数据集使用不可变清单与分区 SHA-256；研究计算不会直接调用数据源 API。
- A 股规则、成本、涨跌停、整手、结算和交易可用性按历史有效期解析。
- 动量与低波动横截面策略采用 `Decimal`，订单仍经过既有 RiskEngine、OMS、执行和 Portfolio。
- 研究 API 和同一套 React 组件树支持 `中文 | EN`，权威金额以精确十进制字符串传输。

## 当前科学状态

A 股数据就绪门禁尚未通过：公司行动归一化、退市证券覆盖验证和完整历史例外规则仍有重大缺口。
因此开发集、验证集和正式样本外研究均未运行，也没有任何收益、夏普或 Alpha 声明。详见
[`docs/research/A_SHARE_DATA_READINESS_REPORT.md`](docs/research/A_SHARE_DATA_READINESS_REPORT.md)。

完整安装、测试和架构说明请参阅英文 [`README.md`](README.md)、[`ARCHITECTURE.md`](ARCHITECTURE.md)
和 `docs/research/`。v1.0.0 的美股示例、回测和模拟交易保持向后兼容。
