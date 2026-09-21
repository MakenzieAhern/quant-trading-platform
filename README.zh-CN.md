# 量化交易平台

**v1.1 — 中国 A 股研究版**

面向沪深普通 A 股的确定性、时间点正确的量化研究与模拟交易平台。项目覆盖 2010–2025
研究数据、公司行动会计、交易前风控、OMS、模拟执行、PostgreSQL 持久化、REST/WebSocket
以及同一套支持 `zh-CN` / `en-US` 的 React 页面。

> **仅限 PAPER / 模拟执行。不连接实盘券商，不发送真实资金订单。**

研究没有证明稳健的历史 Alpha。正式样本外收益为弱正，但不能证明可靠盈利能力，也不能
推断未来收益。

## v1.1 交付内容

- 5,431 只经审计的历史普通 A 股时间点主数据，覆盖上交所主板/科创板和深交所主板/创业板，
  包含退市证券。
- 2010-01-01 至 2025-12-31 共 3,886 个交易日、13,411,189 条原始日线记录、42,792 条
  公司行动记录。
- 在冻结前审计幸存者偏差、未来 IPO、退市保留、ST/*ST、停牌、历史市场规则和公司行动。
- 原始价格用于执行；独立审计的复权历史仅用于因子，绝不把复权价格当作成交价。
- 使用 `Decimal`、稳定证券 ID、固定排序和 SHA-256 清单的确定性横截面动量/趋势/低波研究。
- 固定的 Development / Validation / Official OOS 协议，以及只能运行一次的不可变 OOS 锁。
- 研究与本地模拟交易共用 RiskEngine → OMS → 模拟经纪商 → Portfolio 会计链路。
- PostgreSQL 研究/模拟账本和双语 React 页面，展示谱系、基准、权益、回撤、滚动指标、
  月收益、持仓、再平衡与交易。

## 科学结果

冻结策略为 `cn_a_cross_sectional_momentum_low_vol_v1`（S4）。验证期没有候选策略通过全部
预注册稳健性门槛，因此未修改的 S4 只作为预先声明的负面/中性基准进入 OOS。

| 切分 | 区间 | 总收益 | 夏普 | 最大回撤 | 相对 CSI300 超额 |
|---|---|---:|---:|---:|---:|
| Development | 2010–2017 | -21.75% | -0.434 | -32.56% | -35.77% |
| Validation | 2018–2021 | -5.17% | -0.141 | -11.98% | -26.04% |
| Official OOS | 2022–2025 | 0.76% | 0.067 | -15.70% | 6.61% |

正式 OOS 仅运行一次。结果 SHA-256 为
`ccf5bd2f82f145c9d14bb6ffb912bf035d276b46b8056883b8a18a61a2d92e8c`。详见
[`OOS_REPORT.md`](docs/research/OOS_REPORT.md) 和
[`STRATEGY_REPORT.md`](docs/research/STRATEGY_REPORT.md)。

## 系统结构

```text
官方/公开来源快照 → 不可变数据集与 SHA-256 清单 → 时间点研究会话
→ 冻结因子策略 → RiskEngine → OMS → 模拟执行 → Portfolio/分析
→ PostgreSQL → REST/WebSocket → React 中文/英文界面
```

金额全程保持 Python `Decimal`、PostgreSQL `NUMERIC(78,38)` 和精确 JSON 字符串。策略只消费
已完成交易日；订单遵循保守的
[`CN_A_DAILY_OPENING_LIMIT_V1`](docs/research/DAILY_EXECUTION_CONVENTION.md) 日线模拟约定，
无法建立成交条件时一律不成交。React 不重新计算权威金融状态。详见
[`ARCHITECTURE.md`](ARCHITECTURE.md)。

## 页面

- `/research/a-share`：冻结数据集与正式 Development/Validation/OOS 账本。
- `/research/a-share/strategies`：因子公式、冻结配置和方法说明。
- `/research/a-share/datasets/:id`：规范化数据谱系和清单。
- `/research/a-share/runs/:id`：指标、CSI300 对比、曲线和审计表。
- `/paper`：持久化的本地 PAPER/模拟会话、REST 快照与 WebSocket 更新。
- `/backtests`：v1.0 保留的确定性注册样例回测。

## 启动与验证

需要 Docker Desktop/Engine 与 Compose。Windows 用户应在 Ubuntu WSL2 内运行，并启用 Docker
Desktop 的 WSL 集成。

```bash
git clone https://github.com/MakenzieAhern/quant-trading-platform.git
cd quant-trading-platform
cp .env.example .env
make setup
make up
```

打开 `http://localhost:5173/research/a-share`。`make down` 不会删除 PostgreSQL/Redis 卷。
大型行情数据不会提交到 Git；本地发布正式研究账本时，应挂载已经审计的数据集和结果目录，
并运行 `backend/scripts/publish_formal_research.py`。该发布器会验证不可变谱系且可幂等重试。
正式 OOS 授权已经消耗，**不得重跑 OOS**。

```bash
make test
make lint
make build
```

更多说明见：[`DATASET.md`](docs/research/DATASET.md)、
[`METHODOLOGY.md`](docs/research/METHODOLOGY.md)、
[`BIAS_CONTROLS.md`](docs/research/BIAS_CONTROLS.md)、
[`REPRODUCIBILITY.md`](docs/research/REPRODUCIBILITY.md) 与
[`LIMITATIONS.md`](docs/research/LIMITATIONS.md)。

## 安全边界

本项目是仅监听本机回环地址、无认证的单用户研究工具。v1.1 不包含实盘券商适配器、券商凭据、
真实资金交易、港股/美股扩展或 ML/GPU 策略，也不适合直接暴露到公网。

仅供研究与教育使用；模拟结果不是投资建议，也不保证未来表现。
