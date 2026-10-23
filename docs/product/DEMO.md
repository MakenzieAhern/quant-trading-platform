# v1.2 A-share workstation demo (development build)

This is a **synthetic, local-only** walkthrough, not a released v1.2.0,
market-data result, investment recommendation, or forward-simulation test. It
does not connect to a broker or send real-money orders.

开始前请在顶栏选择“中文”或“EN”，与下面的步骤语言一致；界面可能保留上次的语言。

Before starting, choose `中文` or `EN` in the top bar to match the walkthrough;
the app may remember a previous language.

## 中文：从首页到保存的演示结果

1. 在本机服务运行后打开[工作台](http://localhost:5173/)。若网页无法打开，先从 Windows 开始菜单启动已安装的 Docker Desktop，待引擎就绪后刷新；登录后自动启动尚未通过验收。不要清空数据库或 Docker 卷。
2. 查看顶部的服务状态，再到[数据中心](http://localhost:5173/data)核对模式和日期。服务在线不等于行情新鲜。回到工作台，点击“开始引导式回测”。如已有**其他研究**的草稿，选“备份草稿并新建”，不要为演示改写它；只有原草稿就是本次演示时才选继续。两种选择都不会自动运行研究。
3. 第 1 步阅读已注册策略的简短说明并选择策略；完整规则和风险可到[策略中心](http://localhost:5173/strategies)查看。第 2 步明确选择“合成演示”数据，核对页面给出的本金、日期、证券范围。没有私有历史档案时，历史数据会显示不可用，合成演示仍可用。第 3 步核对模拟成本与风险设置；第 4 步阅读合成数据警告和配置摘要，主动勾选确认后才点击运行。
4. 任务创建后查看真实阶段/工作量；切换到[研究列表](http://localhost:5173/experiments)或[任务中心](http://localhost:5173/tasks)，再打开**同一个**任务。只将“已完成”的任务当作完整结果；刷新结果页，确认仍能读到已保存的指标、成本、交易与风险原因。
5. 结果中的合成收益和基准只是界面/执行链路演示，不代表 A 股历史或未来表现。若没有被接受的下一交易日，页面不会提供可执行的模拟调仓计划。不要把本演示标成真实新行情前向模拟。

## English: from home to a saved demo result

1. With the local services running, open the [workbench](http://localhost:5173/). If it is unavailable, open the already-installed Docker Desktop from the Windows Start menu, wait for its engine, then refresh. Automatic start after sign-in has not passed acceptance. Do not clear the database or Docker volumes.
2. Check service status, then inspect mode and date in the [data center](http://localhost:5173/data). An online service does not mean fresh prices. Return home and choose “Start guided backtest.” If there is an **unrelated saved draft**, choose “Back up draft and start new” rather than editing it for this demo. Continue only if that draft is already this demo. Neither choice runs a study.
3. In step 1, read the registered strategy's short description and select it; the [Strategies center](http://localhost:5173/strategies) has its full rules and risks. In step 2, explicitly select “Synthetic demo” data and check the displayed capital, dates and universe. Without the private historical archive, historical data are unavailable while the synthetic demo remains available. Review simulated costs and risk in step 3; in step 4, read the synthetic warning and configuration summary, then acknowledge it before choosing Run.
4. After creation, inspect the actual task stage/work count. Navigate to [Experiments](http://localhost:5173/experiments) or the [Task center](http://localhost:5173/tasks), then reopen the **same** task. Treat only “Complete” as a complete result. Refresh its page to check persisted metrics, costs, trades and risk reasons.
5. Synthetic return and benchmark figures demonstrate the interface/execution path, not historical or future A-share performance. Without an accepted next trading day, the page withholds an executable rebalance plan. Do not call this new-market forward simulation.

For other modes, uncertain submissions, account recovery and release limits, see
the [中文指南](USER_GUIDE.zh-CN.md) or [English guide](USER_GUIDE.en-US.md).
This script is an agent-validated flow, **not** an independent novice-user test
or final M5 acceptance. The two historical paper-account ledgers remain lost;
the user accepted explicit loss disposition on October 16, 2026, without replay
fabrication or deletion. That disposition no longer blocks continuation on the
verified post-incident baseline and does not restore the records. See the
[incident and recovery limits](USER_GUIDE.en-US.md#simulated-accounts-and-recovery).
Historical financial/source admission, lawful genuine forward-market execution
and remaining required quality/delivery/release gates are still open.
Independent physical backup is additional assurance, not a newly imposed gate.

## Six-flow media index (2026-10-03 checkpoint)

These are real captures, not generated mockups. Local evidence remains outside
Git; links below address this PC's evidence directory through its WSL mount.
Dates/builds differ: reuse proves only the captured flow, not current-head full
acceptance. `NOT_CAPTURED` is an evidence gap, not a fabricated before view.
The Oct3 reconstruction below uses fixed `v1.1.0` frontend source on the current
read-only restored backend, not an old database or an original Sep22 capture.
[Exact build and guard provenance](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/provenance.json)
and [hashes](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/sha256-manifest.json)
explain the mixed-version limits. No research or paper account was started.

| Flow | Before | After / interaction proof | Scope and remaining gap |
|---|---|---|---|
| Home | [Old home](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/home.png) | [Current workbench](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261002-local-running/workbench-current.jpg); [actual walkthrough](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/product-walkthrough-zh-1280-v2.webm) | The current home has an existing draft; it is not a clean-user capture. |
| Guided creation | [Old long form](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/create-backtest.png) | [Four-mode orientation](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m1/guide-zh-light.png); [guided start](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/guided-start-zh-1280.png); [actual synthetic full flow](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-full-flow-zh-1280.webm) | The M1 orientation's offline background does not prove service health. The video uses registered synthetic data, not market returns. |
| Strategy | [Loaded old detail — Oct3 reconstruction](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/03-v11-strategy-loaded.jpg); [original loading diagnostic](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/strategy.png) | [Same strategy, current detail](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/08-v12-strategy-loaded.jpg); [context-preserving panel](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/07-v12-strategy-context-dialog.jpg); strategy section in the walkthrough above | Same registered strategy, actual1280x800/ZH capture. The reconstructed loaded detail is not the original loading screen or a v1.1 backend deployment. |
| Research running | [Old saved formal report — Oct3 reconstruction](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/04-v11-existing-validation-report.jpg); [original old research entry](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/before/research-loaded.png) | [Video-player frame](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/isolated-demo-video-frame-07s.png); actual synthetic full-flow video above | The video contains a registered personal job and completion. Old formal-report browsing is read-only: no equivalent personal-job workflow/running state is fabricated or rerun. |
| Comparison | No equivalent comparison view in v1.1.0; [actual old research context — Oct3 reconstruction](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/02-v11-research-context.jpg) | [Three saved studies (historical and synthetic)](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261002-restored-ui/03-comparison-zh-light.jpg); [actual read-only interaction video](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20260929-chrome-media/current-head-readonly-interaction-1440x900.webm) | The video compares two studies. The old context is not a comparison. This three-study view explicitly warns about mixed modes; configuration warnings are not proof of a controlled financial comparison. |
| Paper account | [Old STOPPED synthetic account — Oct3 reconstruction](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/05-v11-stopped-synthetic-account.jpg) | [Same STOPPED synthetic account, current labels](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261003-v11-baseline/09-v12-same-stopped-synthetic-account.jpg); [separate historical account-native plan](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261002-account-plan/04-plan-zh-metadata.jpg); [sampled historical lifecycle](../../../../../../mnt/c/Users/1/Documents/ChatGPT/量化交易/product-evidence/v1.2/m5/20261002-3184281-paper-lifecycle/paper-lifecycle-uniform-sampled.webm) | Matched synthetic account is clearly2030, has no orders/fills and was not started. Separate historical lifecycle uses40 actual screenshots at1fps, time-compressed, not continuous recording. Neither establishes forward arrival or recovers missing ledgers. |

Old personal-task/comparison views do not exist and are not invented. These scoped
reconstructions close loaded strategy/account and old-context evidence gaps, not
all M5. These captures do not establish lawful
forward simulation, broad accessibility/performance, a real novice study or a
released v1.2.0. See [acceptance](ACCEPTANCE.md) for individual proof and limits.
