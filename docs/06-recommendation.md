# 明确建议与下一步

版本：Decision Memo v0.4
日期：2026-08-20

## 1. 是否值得做

**值得用宽平台命题吸引开源、合作和产品关注，同时以一个有明确停止条件的 Media 原型与真人盲测建立可信度。**

理由：

- 两条脱敏一手需求、Largo 的公开套餐、aiScreeningRoom 的整片 Beta、传统试映和广告前测共同证明该采购类别与竞争投入已经出现；实际预算、成交和复购仍需买方访谈与试点。
- 多模态模型已经允许 8—20 分钟端到端原型。
- MatrAIx、TinyTroupe、genagents、OASIS 与 Concordia 等开放项目已经提供 Persona、实验或社会模拟基础设施，使小团队无需扩招和自建算力即可验证垂直增量。
- 独立研究明确警告纯合成 Panel 的偏差、方差压平和效应夸大，迫使项目以校准和证据为核心。
- 最接近的竞品已经覆盖“上传视频、得到曲线和预测”，所以只有在顺序个体 Trace、分层差异、真人校准和中国私有工作流上做出可验证增量，项目才值得继续。
- 真实演出研究和文化市场实验共同表明，接受语境会改变体验，而社会影响又会增加结果的路径依赖和不可预测性。产品应做 Context Sensitivity，不做“爆款预测”。

建议把未来四周视为首个 Environment Thesis Test，而不是整个平台想象力的上限。通过门槛后扩展第二环境并推进合作；失败则修正 Media 的有效性主张，不自动否定通用 Environment、Trace、群体互动与实验基础设施的价值。

## 2. 最佳首个垂直

### 推荐

**影视／IP 的 8—20 分钟叙事片段与同源营销版本，聚焦内容叙事与观看体验。**

新增一手交流进一步确认：潜在合作需求更接近“观众如何理解、感受和解释内容”，不是通用商品消费决策。这不改变首个垂直，但改变产品措辞与输出优先级：理解断点、叙事预期、角色认同、文化解释、流失原因与传播语言优先于单一好感度、购买分或市场预测。

它位于三类强竞品之间：

- 比 15—30 秒广告更依赖角色、叙事和长期记忆，避开短广告脑电／眼动数据壁垒的正面竞争；
- 比 60—120 分钟整片更易在四周内做 A/B、真人盲测和成本迭代；
- 比通用合成用户多出真实的连续多模态体验和时点证据。

眼动、脑电／生理感知可作为未来私有试点的 Human Anchor，但不应成为首版的采购前提或主解释框架。真正可持续的数据资产是带授权和版本的“内容时间轴—脱敏受众背景—观看行为／访谈—历史结果”合同。

### 第一个业务决策

优先选择：

> 同一 IP 或故事的两个 1—5 分钟预告／片花版本，在不同 IP 熟悉度的人群中，哪个更容易被理解和记住，差异来自哪些具体时点？

同时用 8—20 分钟母片验证长期记忆，形成“母片体验 + 营销 A/B”的完整 Demo。两类实验保持 Session 隔离，预告 Agent 只拥有预注册的 IP 先验；报告再把预告中的角色／事件与母片 Timeline 对齐。差异点是叙事承接、分层个体 Trace 和真人冲突检查；快速注意／购买意愿预测本身已有 [Kantar LINK AI](https://marketplacesupport.kantar.com/support/solutions/articles/77000525256-what-is-link-ai-for-digital-link-ai) 与明略 AdEff 等强方案。

### 第二阶段游戏切口

顺序建议：

1. PV／宣传片；
2. 皮肤与角色外观；
3. Battle Pass 奖励结构与展示；
4. 商城 UI 与可点击购买原型；
5. 教程／玩法录像；
6. 卡牌／回合制／结构化交互；
7. 最后才是完整 3D Build 和 GUI Agent。

游戏首轮仍以玩家审美、理解、价值感和购买链路为问题，不进入 Bug、性能和通关能力已经高度竞争的 QA 赛道。

## 3. 仓库与产品形态选择

### 3.1 三种方案

| 方案 | 优点 | 主要问题 | 当前建议 |
| --- | --- | --- | --- |
| 新建独立仓库 | 能定义通用 Environment、Experiment、Trace、校准和安全；可独立形成开源社区与品牌 | 需要维护 Adapter；不应重复实现已有 Persona／Task Runtime | **现在采用：Audience Mirror 独立平台，Media 先实现** |
| 直接作为 Foreworld 子产品 | 复用 WMG、GAIA、关系和工作台；品牌与长期世界模型统一 | 会把 Audience Mirror 的开源受众、发布节奏和环境边界绑定到 Foreworld 当前架构 | **保持 Adapter 与协同，不预设未来必须迁入** |
| 只做适配层 | 代码最少，快速调用现有引擎 | Timeline、顺序观看、Trace、校准和报告都是新核心，现有引擎没有；“薄适配”无法形成产品 | **不采用** |

### 3.2 决策

本仓库作为 Audience Mirror 的独立平台与实验事实源，先实现公共合同和首个 Media Environment：

- Environment／Experiment／Population 公共合同；
- Asset／Variant／Rights；
- Multimodal Timeline；
- Audience Panel；
- Sequential Runtime；
- Trace／Claim／Calibration；
- 验证报告；
- MatrAIxAdapter、TinyTroupeBaseline、ForeworldAdapter、GaiaAdapter、MiroFishAdapter 接口。

Persona 检索、Cohort、Task／Trial／Verifier 与基础运行账本优先由 MatrAIx 固定版本提供，内置 Stub 只承担回退和契约测试。Audience Mirror 通过版本化 Adapter 使用 Foreworld 的世界记忆、关系和 GAIA 群体推演能力；是否共用账户、Project、Task 和 Artifact 在两个项目的真实复用出现后再决定，不预设 Audience Mirror 只是 Foreworld 的垂直页面。

### 3.3 MatrAIx 边界

MatrAIx 代码为 MIT，当前是 P0 复用候选。它的 8.3B 是 Persona 记录空间，不是已执行 8.3B 个 Agent；公开实验实际运行 18,189 个 Trial，官方 Quickstart 明确 `N personas = N trials`。本项目应复用其 Persona／Cohort／Trial 合同，并新增第五类 Media Environment。

公开 Persona 1M 数据卡没有统一 License 字段，并声明底层来源条款继续适用。因此：代码可做固定版本 Adapter Spike；完整数据不进入本仓库，商业与再分发使用等待逐来源审计。MatrAIx 对动态长程记忆、Media 和人类预测有效性没有现成保证。

### 3.4 MiroFish 边界

MiroFish 公开版适合参考图谱、Persona、社媒模拟和 ReportAgent，也可在许可明确后以独立服务接入群体传播。当前不复制其代码、不链接其内部库、不把闭源产品建立在 AGPL 修改版上。

AGPL 的远程源码义务和“独立程序／组合程序”边界取决于实际修改、通信机制和数据语义；进程／API 方案降低耦合，但不能被写成法律免责结论。正式商业部署前需要维护者授权或专业许可审查。

### 3.5 开源与商业产品

现在不承诺“全部开源”或“全部闭源”，按开放内核设计：

- 优先开放：Timeline／Trace／Experiment Schema、Media Environment、公开 Demo、验证脚本、模型／运行时 Adapter、本地只读报告；
- 优先保留：客户素材、Human Anchor、Calibration Profile、SSO／权限／水印／审计／VPC、协作工作台和托管运维；
- 候选内核许可证：Apache-2.0；正式确定前完成第三方依赖和素材清单；
- 发布 6—8 周后用独立安装、外部 Task／PR／Adapter 和下游复用判断开源声量，Star 只做辅助；
- 用授权私有试点、真实版本变更和第二次付费／复用判断商业价值。

两类信号都强则做开放内核产品；只有社区强则做开源研究工具；只有商业强则缩小公开面；两者都弱则停止虚拟观众产品。

## 4. 项目名称与传播表达

### Audience Mirror｜观众镜

- 含义：让决策者看到不同人怎样面对同一内容、产品、游戏、规则或可能世界；
- 与 Foreworld 的 World Mirror 有家族关系；
- 能覆盖观众、用户、玩家、消费者、参与者与社会角色；
- 风险：英文词组通用，正式商标与域名需另查。

标语：

> 在现实发生前，先让一万种人走一遍。

项目名称保持 Audience Mirror，不因本轮战略纠偏更换。需要变化的是副标题、平台结构和 Demo 命名：总品牌表达跨环境的人群实验，Media、Web／App、Game 与 Social Scenario 分别作为 Environment Pack；商标与域名仍需在公开发布前独立核查。

## 5. 下一步直接做哪一个 Demo

### Demo 名称

**Sintel Audience Mirror：母片顺序体验 + 预告 A/B**

### 素材

- Blender Foundation《Sintel》完整约 15 分钟影片；
- 官方字幕和音轨；
- 一个保持原叙事的基准预告；
- 一个基于同一 CC BY 3.0 素材制作的 clarity-first 变体；
- 完整片尾、署名和修改说明。

### Audience 与执行规模

Persona Universe 可接入 10k—1M 条已审计记录，三层执行保持分开：

- 12—18 个 Deep Trace Persona：完整顺序体验和逐时证据；
- 约 100 个 Broad Sweep Persona：摘要／关键检查点结构化反馈；
- 10k 条 Population Projection：零逐 Persona LLM 调用，只展示覆盖与敏感性。

Deep Trace 使用 3 个分层：

1. 动画／奇幻高兴趣；
2. 普通流媒体叙事观众；
3. 低先验兴趣、短视频使用较高。

每个 Persona 公开其构造依据和不确定字段。Pool、Deep、Sweep、Projected、Stability 与 Human 数量分别显示；Panel 不模拟市场份额。

### Demo 必须展示的四个本地视图

1. **Timeline Builder**：镜头、场景、对白、角色、音乐和事件；
2. **Audience + Trace Inspector**：分层、Persona、时间点、画面／声音、记忆、状态前后和反例；
3. **Experience + Variant Diff**：理解、困惑、角色好感、行为、A/B 对齐与运行波动；
4. **Human Convergence**：Agent-only、Human-only、一致和冲突；公开 Demo 仅作探索性对照。

### 实验

- one-shot；
- Persona one-shot；
- sequential；
- sequential + exploratory human comparison；
- 每个核心条件 5 次稳定性运行；
- 8—12 位真人同素材探索性盲测，不拟合校正器，也不验证三分群代表性。

### Demo 的一句话成功

> 一个内容决策者能在 15 分钟内找到三个具体、可回看的问题，并知道哪些只是 Agent 假设、哪些获得真人支持。

## 6. 四周执行顺序

### 第 1 周：客观内容层

- 下载并登记公开素材权利；
- 固定 MatrAIx Commit，完成 Smoke、最小 Cohort／Trial Adapter 和数据权利清单；
- 生成代理文件、Shot、ASR、OCR、角色和音频事件；
- 完成人工可修订的分层 Timeline；
- 固化 Timeline 与 Trace Schema；
- 建立 one-shot 基线。

### 第 2 周：个体体验层

- 从已审计 Persona Universe 检索／补充 12—18 个 Deep Persona；
- 实现顺序事件循环和记忆；
- 运行 sequential；
- 完成 Trace Inspector 与问题卡；
- 测首次成本、时间和未来信息泄露。

### 第 3 周：版本与稳定性层

- 制作并对齐 A/B；
- 运行约 100 个 Broad Sweep，把异常样本升级为 Deep Trace；
- 完成 10k 零逐人 LLM 调用的 Population Projection 演示；
- 完成五次重复运行；
- 固定技术版本、问题去重和 A/B 指标；
- 修复未来信息泄露与缓存失效问题；
- 生成可供真人研究使用的盲测包。

### 第 4 周：探索性真人与决策层

- 招募 8—12 位真人，只做问题集、时间点和报告可用性的探索性对照；
- 按预注册门槛计算问题命中、稳定性、成本和证据质量；
- 让少量内容从业者盲评普通总结与 Trace 报告；
- 完成本地删除演练；
- 输出 Go／Pivot／Stop；
- 通过后再准备私有试点，不自动对外联系。

第二模型、自动校正器、Social Lab 和客户云路由属于后续研究门，不作为四周原型完成条件。

Context Scenario 也属于后续研究门。首个 Demo 固定为 `independent_blind`，把 Reception Context 和 outcome_blinded 写入 Run Manifest；等基础盲测证明顺序 Trace 有增量后，再选一个可严格锁定事前信息的公开案例做语境敏感性对照。

## 7. 通过后 60 天路线

### 30 天

- 获得一个授权私有素材；
- 复用对方既有真人问卷／访谈；
- 完成境内模型或客户云路由；
- 支持业务方自定义指标；
- 记录第二版本是否实际提交。

### 60 天

- 完成第二个不同品类素材；
- 形成第一版 Calibration Profile；
- 增加小组讨论前后变化；
- 决定是否接 Foreworld Project／Task；
- 决定是否以服务、私有部署或 SaaS 交付。

## 8. 商业化顺序

首批不按“无限 Agent 席位”收费，建议按项目交付：

1. 研究设计与安全配置；
2. 一份母片 Timeline；
3. 两个 Variant；
4. 一个 Audience Panel；
5. 五次稳定性运行；
6. 一个真人对照；
7. 决策工作坊与报告。

这能让客户为决策结果付费，也能迫使团队积累真正的校准数据。连续三个项目出现相同工作流后，再产品化为年度订阅或私有部署。

开放内核的收入不依赖出售 Persona 数量。更可持续的付费层是私密素材托管、数据驻留、权限审计、客户校准、持续版本对比、企业协作与 SLA。开源版本必须能够独立跑公开素材 Demo，否则无法形成真实社区；商业版本必须比“自己部署开源代码”显著降低安全与研究交付成本，否则没有购买理由。

## 9. 需要用户确认的三个问题

1. **真实首个决策对象**：是否同意先用预告／营销 A/B 进入私有试点，而把完整粗剪放到第二次？
2. **真人参照**：授权方能否提供既有问卷／访谈编码，或支持按预注册指标与版本设计真人样本？10—20 人只适合探索性问题发现，不足以同时验证三分群并拆出校准／封存样本。
3. **部署边界**：私有素材是否要求境内 VPC／客户云、不进入境外第三方模型、以及成功后立即删除原片？

这三个答案会改变技术和试点设计，值得用户确认。其余普通选择可以在公开 Demo 中直接做合理默认。

## 10. 最终建议

现在直接做 Sintel Demo，同时把它放进 Audience Mirror 的通用平台叙事与 Environment Contract 中；不接触未经授权的真实客户素材。

四周后只依据三类证据继续：

- 与真人的方向和问题召回；
- 内容决策者是否真的使用 Trace；
- 成本与安全是否支持频繁版本迭代。

若通过，Audience Mirror 以开放实验内核和 Media Reference Environment 起步，再用 Web／App 或 Game 的最小环境验证通用性，并与 Foreworld／GAIA 保持适配关系；若未通过，放弃“未校准虚拟观众能代表目标人群”的主张，但保留 Environment、Timeline、Trace、Adapter 和真人研究加速器继续寻找有效场景。
