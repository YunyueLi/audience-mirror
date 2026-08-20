# 平台命题：现实之前的人群实验层

版本：Platform Thesis v0.1
日期：2026-08-20
状态：Proposed

## 1. 纠偏结论

Audience Mirror 继续作为整个项目的名称。需要纠正的是产品定义和能力边界，不是名字。

前一版方案把 Audience 近似等同于“影视观众”，又把“先用影视／IP 做出可验证闭环”写成了“不建设通用平台、不扩展通用消费者模拟”。前者是错误的品牌解释，后者会过早限制项目的技术抽象、开源受众和外部叙事。Audience 在这里指面对某项内容、产品、规则或世界的目标人群，可以是观众、用户、玩家、消费者、参与者或社会角色。MVP 顺序与项目边界必须分开：

- **项目愿景要宽**：支持不同人群在现实发生前体验一个内容、产品、游戏、服务或社会情境，形成判断、选择并相互影响；
- **平台内核要通用**：环境、Population、顺序体验、记忆、决策、互动、Trace、校准和复现实验都不绑定影视；
- **首个证明要窄**：先用 Audience Mirror 的视频／叙事环境做出真实、可查、能与真人盲测的端到端 Demo；
- **结论口径要严**：宏大愿景不等于承诺准确预测一切。实验输出必须显示条件、不确定性、反例和校准状态。

一句话平台定位：

> 一个让异质人群在现实发生前进入多模态环境，形成体验、判断、选择并相互影响的开放模拟与评测系统。

人话标语：

> 在现实发生前，先让一万种人走一遍。

英文表达：

> Simulate how people experience, judge, choose, and influence each other—before reality.

上述“一万种人”表达 Persona 覆盖范围，不表示运行了一万次独立高保真 Agent，也不表示统计代表性。

## 2. 三层结构

| 层级 | 负责什么 | 当前实现 |
| --- | --- | --- |
| Audience Mirror 平台愿景 | 现实之前的人群实验：体验、评价、决策、互动与传播 | 对外叙事和长期产品边界 |
| 通用实验内核 | Environment Contract、Population、Experience Runtime、Memory、Trace、Experiment、Calibration、Report | 本仓库逐步抽象；复用 MatrAIx、Foreworld／GAIA 等开放能力 |
| Environment Pack | 为某类对象定义观察、动作、状态、指标和报告 | Media 为 P0；Web／App、Game、Social Scenario 后续按验证信号接入 |

平台与应用的关系：

```text
                                  Audience Mirror
                         Multimodal Population Experiment Platform
                    现实之前的人群体验、判断、选择与互动实验层
                                           │
        ┌──────────────────────┬────────────┼──────────────┬────────────────────┐
        ▼                      ▼            ▼              ▼
  Media Environment       Web / App     Game          Social / Spatial
  Media Lab               User Lab      Player Lab    Scenario Lab
  首个参考环境             候选环境       候选环境       与 Foreworld／GAIA 协同
        └──────────────────────┴────────────┼──────────────┴────────────────────┘
                                           ▼
  Environment Contract → Population → Sequential Experience / Memory
                       → Decision / Interaction → Trace / Evidence
                       → Human Calibration → Reproducible Report
```

应用名只是便于理解的工作标签，不代表现在同时建设四套产品。

## 3. 平台补的空位

公开项目已经分别覆盖了部分能力：

- [MiroFish](https://github.com/666ghj/MiroFish) 用“通用群体智能引擎／预测万物”建立宽阔叙事，公开实现强调种子信息、图谱、社会环境、Agent 互动和报告；
- [MatrAIx](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B) 把自己定义为人口规模、Persona 驱动的 AI 系统与交互产品评测基础设施，提供 Survey、Chatbot、Web 和 App 环境；
- OASIS、Concordia、AgentSociety 等偏社会环境和群体动力学；
- TinyTroupe、Synthetic Users 等偏 Persona 访谈、问卷和概念测试；
- 视频分析、游戏 QA 和真人研究工具则分别覆盖特定输入或验证方式。

本项目不靠“再生成更多 Persona”形成差异。可争取的通用空位是：

> 让同一组可追溯的异质 Persona 真正按顺序经历多模态或交互环境，把观察、记忆、判断、动作和群体影响保存成可回放 Trace，并用同任务真人资料校准。

这比“虚拟观众”宽，也比“预测一切”更容易形成可核查的工程与研究资产。

## 4. 外部输入如何扩大平台

外部输入不应变成新的限制条款，而应被抽象为跨环境能力：

| 外部认知 | 影视表述 | 通用平台抽象 |
| --- | --- | --- |
| 神经美学与真实剧场研究 | 观众如何感知与评价内容 | `Human Anchor` 与 `Evaluation Model`：主观、自报、行为、生理和文化解释分层 |
| 人格规模与 MatrAIx | 大规模虚拟观众 | `Population Universe`：Persona 生成、检索、Cohort、覆盖与低成本投影 |
| 文化现象与群体参与 | 内容可能因戏谑、身份和社交货币改变意义 | `Reception Context`、`Participation Mode` 与 `Social Dynamics`：环境条件和群体路径依赖 |
| 长视频理解 | 逐段观看和叙事记忆 | `Sequential Experience Runtime`：适用于视频、网页流程、游戏关卡、服务旅程和空间体验 |
| 眼动／行为／运营数据 | 观看轨迹校准 | `Calibration Contract`：任意环境中的真人反馈、行为日志和结果数据 |

因此，新增输入强化的是“体验—评价—决策—传播”的通用模型，不是把项目缩成神经美学、审片或单一 IP 工具。

## 5. 通用对象模型

平台最小公共语言应包含：

| 对象 | 含义 | 跨环境例子 |
| --- | --- | --- |
| Environment | Agent 能观察和行动的环境 | 视频、网页、App、游戏、门店／演出模拟、政策情境 |
| Stimulus / World State | 某一时刻可见、可听或可操作的状态 | 镜头、页面、UI、任务、价格、他人行为、规则变化 |
| Population / Persona | 有来源、约束和不确定性的异质个体 | 观众、消费者、玩家、用户、居民、创作者 |
| Experience Session | 按暴露顺序推进的一次独立经历 | 观看、注册、购买、试玩、服务旅程、共同参与 |
| Memory | 个体在过程中形成和遗忘的信息 | 角色关系、产品承诺、失败经历、价格印象、社交线索 |
| Evaluation | 对状态或经历形成的多维判断 | 理解、美感、信任、价值、风险、可用性、公平感 |
| Decision / Action | 可观察或模拟的选择 | 继续、跳过、点击、购买、退出、分享、反对、等待 |
| Interaction | 个体与他人或制度的相互影响 | 讨论、评论、模仿、口碑、规范、网络扩散 |
| Trace / Claim | 可回放事实流与带证据结论 | 时间点、状态前后、证据、反例、置信与模型分歧 |
| Human Anchor | 同任务真人参照与适用范围 | 问卷、访谈、行为流、眼动、生理、真实结果 |

Audience、User、Player 等词只应出现在相应 Environment Pack 中。核心 Schema 后续应把 `Audience Panel` 上收为 `Population Panel`，把 `WATCHING` 等媒体状态留在 Media 扩展中。

## 6. 开源与商业结构

小团队不需要扩招或采购大规模算力，也不应把“规模”误解为每个 Persona 都调用一次昂贵模型。

建议开放：

- Environment Contract 与示例环境；
- Population／Experiment／Trace／Claim／Calibration Schema；
- 模型和运行时 Adapter；
- 本地实验 Runner、固定种子、成本账本和可下钻报告；
- 公开基准、合成 Fixture 和真人校准协议。

可能形成商业价值的部分：

- 经授权的行业数据合同和校准资产；
- 私有素材、VPC／本地部署、权限、水印、审计和删除证明；
- 团队协作、实验资产管理、模型路由和托管运行；
- 领域 Benchmark、企业连接器和持续验证服务。

规模执行继续分层：少量 Deep Trace 负责过程证据，中等 Broad Sweep 负责覆盖扫描，大规模 Projection／Coreset 负责检索和敏感性。聚合报告的边际成本低，但如果每个 Persona 都独立调用大模型，生成成本仍随 Trial 数增长；产品必须准确标记这三种口径。

## 7. 当前路线

### 现在做

1. 以通用 Environment／Population／Trace／Experiment Contract 重构顶层文档和后续 Schema；
2. 保持现有 Audience Mirror 代码为第一个 Reference Environment，完成公开 Demo 和真人盲测；
3. 提供最小的第二环境契约样例，证明内核没有被 `WATCHING`、`scene`、`audience` 等媒体概念锁死；
4. 继续复用 MatrAIx 的 Persona／Cohort／Trial 思路，以及 Foreworld／GAIA 的世界、关系和传播能力；
5. 用外部安装、环境适配、社区贡献和私有试点分别验证开源声量与商业价值。

### 现在不做

- 同时开发媒体、网页、游戏和社会情境四套完整产品；
- 自建 83 亿 Persona 数据集、通用浏览器 Agent 或百万 Agent 基础设施；
- 用一个模型和一组未经校准的 Persona 对所有行业宣称有效；
- 把“预测一切”写成准确性承诺，或用 Agent 数量冒充真人代表性；
- 因为首个 Demo 是影视，就把平台名称、Schema 和融资叙事永久绑定影视。

## 8. 命名决策

`Audience Mirror｜观众镜` 继续作为项目总名。名字本身不要求产品只能服务影视；品牌定义是“映照一个目标人群面对某种可能现实时如何体验、判断、选择和相互影响”。

为了避免再次被理解为单一审片工具，对外表达应满足：

1. 首屏副标题直接覆盖内容、产品、游戏与社会情境；
2. 用 Environment Pack 展示扩展性，不把平台架构写成影视专用流水线；
3. 同时表达模拟和评测，不暗示确定性预言；
4. 与 Foreworld 的关系可解释，但不依赖 Foreworld 才能成立；
5. 适合开源社区、合作方和融资三种语境。

代码包 `audience_mirror` 保持不变。等通用 Contract 抽象完成后，再决定是否拆出 core package；这属于工程边界，不改变 Audience Mirror 的品牌名。
