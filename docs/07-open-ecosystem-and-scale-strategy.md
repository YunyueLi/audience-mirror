# 开源生态、规模成本与产品形态

版本：Strategy Update v0.1
日期：2026-08-19
状态：Proposed

## 1. 结论

这次更新确认三件事：

1. **不应从零建设通用 Persona 或多 Agent 引擎。** [MatrAIx](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B)、[TinyTroupe](https://github.com/microsoft/TinyTroupe)、[genagents](https://github.com/StanfordHCI/genagents)、[OASIS](https://github.com/camel-ai/oasis) 和 [Concordia](https://github.com/google-deepmind/concordia) 已经覆盖 Persona 语料、任务运行、实验、个体记忆或社会模拟的不同部分。本项目应集中建设尚未被这些项目完整覆盖的 Media Environment、顺序体验 Trace、版本对齐和真人校准。
2. **“1 人与 10,000 人的报告生成成本接近”基本成立；“1 人与 10,000 人的独立完整体验成本接近”不成立。** 媒体解析和最终聚合可以高度复用，Persona 记录的抽样也很便宜；每个 Persona 的长程状态、独立判断和可下钻 Trace 仍需计算。解决办法不是采购大规模算力，而是把“Persona 宇宙”“高保真执行样本”和“低成本人群投影”分成三层。
3. **开源与产品不是二选一。** 当前最有利的路线是“开放实验内核 + 保留企业与校准层”，先用公开 Demo 验证社区传播，再用授权私有试点验证商业价值。是否完全开源，推迟到两类信号出现以后决定。

因此，当前工程建议从“独立实现一套 12—18 Persona 引擎”调整为：

> 在本仓库实现多模态 Media Environment 和证据工作台，通过版本化适配器接入 MatrAIx 等开源 Persona／实验运行时；默认运行少量高保真 Trace，可选运行中等规模扫描，再对更大 Persona 池做低成本投影。

## 2. MatrAIx 核验

### 2.1 它是什么

[MatrAIx 技术报告](https://arxiv.org/abs/2608.04205)于 2026-08-04 提交，通讯作者分别来自 Harvard 和 MIT，作者来自多家机构。公开系统包括：

- 1,290 个分类维度定义的 Persona Schema；
- 内部构造的 8.3B Persona 记录空间；
- 约 1M 条公开 coreset，其中约 600k 为多来源资料提取、400k 为合成记录；
- Survey、AI Chatbot、Web、App 四类环境；
- Task、Cohort、Trial、Verifier、Telemetry 和报告运行时；
- 代码采用 [MIT License](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B/blob/07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9/LICENSE)。

截至 2026-08-19，公开仓库页面显示约 1.2k Star、183 Fork，发布不足一个月。这是值得跟进的早期社区信号，不是成熟度或效果证明。

### 2.2 它没有证明什么

MatrAIx 对本项目最重要的价值是工程和实验设计，不是“8.3B 个虚拟人已经能准确预测真实人群”。其论文和代码反而明确给出了边界：

1. **Persona 库规模不等于执行规模。** 论文写明，一条记录只有与模型、接口和任务绑定后才成为 Persona Agent；实验只实例化抽中的 Cohort。公开 Quickstart 进一步写明 `N personas = N trials`，并给出“10 trials 约等于 10 次 LLM 调用”的成本提示。
2. **验证重点不是人类预测准确率。** 91.5% 指标测的是模型是否表达或抑制预设 Persona 行为，不是模拟结果与真人购买、留存或内容反应的一致率。
3. **相同 Cohort 对底模非常敏感。** 论文的同任务三模型结果中，Candy Land 涨价后的犹豫比例为 27.0%—98.3%，Notion 付费方案选择为 23.2%—93.9%；22 个跨模型分群排序比较的中位 Spearman 相关仅为 +0.29。论文因此把结果定位为假设生成，并要求在同任务上做人类验证。
4. **不是概率样本。** 论文明确称 Persona Cohort 不是现实人口的概率样本；公开 1M 数据卡也声明只校准了有限边际分布，不能修复联合分布和来源选择偏差。
5. **本项目需要的能力仍是空白。** Media／长视频环境不在当前四类环境内；动态 Persona、长程记忆仍被列为未来工作；多 Agent 社会世界被明确列为非目标。

### 2.3 许可证和数据边界

MatrAIx 代码是 MIT，但代码许可证不能自动覆盖所有数据：

- 当前 Hugging Face 数据卡没有声明统一 `license` 字段；
- 数据卡明确写明底层来源的许可证与条款继续适用；
- Wiki、Amazon、Stack Overflow、GSS、PRISM 和真人问卷记录具有不同来源与使用边界；
- “human-grounded”记录仍可能包含模型提取错误，也不等于经过本人核实。

当前可以做：

- 以固定 Commit `07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9` 审查和试接 MIT 代码；
- 参考 Task／Trial／Cohort／Verifier 合同；
- 用仓库内小型公开 Dev Sample 做本地技术试验，但在发布衍生数据前复核其来源说明；
- 为 Media Environment 建立外部 Adapter 或上游扩展。

当前不应做：

- 把 4.17 GB Persona 1M 数据直接再分发进本仓库；
- 默认把 1M 数据用于商业客户人群；
- 把公开 Coreset 写成“全球人口数字孪生”；
- 仅凭 MIT 代码许可证宣称所有 Persona 数据可商用。

## 3. 应参考和复用的开源项目

| 项目 | 已有能力 | 对本项目的用途 | 当前不承担 |
| --- | --- | --- | --- |
| [MatrAIx](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B) | 1M Persona Coreset、Cohort、四类环境、Task／Trial／Verifier、轨迹与报告；MIT | **P0 首选复用候选**：Persona 检索、实验清单、成本记录、任务运行合同 | 长视频时间轴、动态长程记忆、真人预测有效性、社交世界 |
| [TinyTroupe](https://github.com/microsoft/TinyTroupe) | Persona／World、A/B Runner、校验、成本跟踪、图像输入、经验数据验证；MIT | 小 Panel 与实验工具的第二基线；用于交叉验证我们的 Runtime 是否过度定制 | 完整长视频理解、人口代表性 |
| [genagents](https://github.com/StanfordHCI/genagents) | 访谈驱动个体 Agent、记忆与反思；MIT | 设计“少量高质量真人资料如何增强 Persona”的方法基线 | 未经授权的个体资料复用；大规模廉价 Persona 生成 |
| [OASIS](https://github.com/camel-ai/oasis) | 最多百万 Agent 的 Twitter／Reddit 社交模拟、推荐与传播；Apache-2.0 | 后期 Social Lab／传播实验的候选 Adapter | 媒体顺序观看；百万个高保真多模态观众 |
| [Concordia](https://github.com/google-deepmind/concordia) | Game Master、组件式记忆和社会环境；Apache-2.0 | 小组讨论、关系和规则清晰的社会实验参考 | Persona 人口构造、媒体解析 |
| [AgentSociety](https://github.com/tsinghua-fib-lab/agentsociety) | 大规模社会环境、可执行社会实验；核心 Apache-2.0，含单独 commercial 目录 | 研究大规模社会模拟与 open-core 边界 | 首版媒体实验；未经审查的 commercial 模块复用 |
| [SimTube](https://yukai0928.github.io/simtube/) | 视频多模态摘要、Persona 检索、模拟评论和评论交互 | 必须比较的相邻学术基线 | 顺序状态 Trace；其公开流程主要在整片理解后生成评论 |
| [MovieChat](https://github.com/rese1f/MovieChat)、[LongVideoBench](https://github.com/longvideobench/LongVideoBench) | 长视频稀疏记忆与小时级理解评测 | 设计 Timeline、记忆和 Benchmark | 受众模拟与商业报告 |
| MiroFish／Foreworld | 社媒模拟；现实证据、世界记忆与群体推演 | 分别作为许可受限的传播候选与后期产品底座 | 首版 Media Environment 与真人校准 |

这张表是复用路线，不是“列过就算研究”。每个候选进入依赖前仍需固定版本、跑 Smoke、确认许可证、检查数据来源并记录实际复用文件。

## 4. 规模成本：四种数量必须分开

### 4.1 定义

| 数量 | 含义 | 是否直接产生 LLM／VLM 成本 |
| --- | --- | --- |
| `P_pool` | 可查询的 Persona 记录总量，例如 1M | 通常否；筛选和抽样主要是 CPU／索引成本 |
| `K_deep` | 完整顺序体验、独立记忆和逐时 Trace 的 Persona 数 | 是，通常是主要变量成本 |
| `K_sweep` | 只看摘要、关键检查点或一次结构化任务的人数 | 是，但每人远低于 Deep Trace |
| `P_projected` | 用已校准响应模型做分布投影的人数 | 通常不逐人调用 LLM，可由 CPU／小模型批量计算 |

最终报告聚合从 1 人扩大到 10,000 人，计算成本可能仍然很小；真正的差异发生在生成报告之前。

### 4.2 成本式

设素材时间轴包含 `E` 个事件、版本数为 `V`、稳定性重复为 `R`，则近似变量成本为：

```text
C_total
  = C_timeline_once
  + V × R × (K_deep × E × C_state_step)
  + V × R × (K_sweep × C_sweep)
  + C_projection(P_projected)
  + C_deterministic_report
```

`C_timeline_once` 和 `C_deterministic_report` 可以跨 Persona 大量复用；`K_deep × E` 不会因为多写几条 Persona 画像而消失。Batch、并发和 Prompt Prefix Cache 可以降低单价与墙钟时间，但不能把 10,000 个独立状态轨迹变成 1 个轨迹。

如果把 10,000 个 Persona 塞进一次 Prompt 并要求模型批量回答，输出可能很便宜，但它们共享一次生成过程，容易出现顺序污染、相关偏差和方差压平，不能再称作 10,000 次独立体验。

## 5. 三层执行架构

```text
Persona Universe（10k—1M 条可查询记录）
                   │
      Target Frame + 分层检索 + 覆盖检查
                   │
       ┌───────────┼────────────┐
       ▼           ▼            ▼
Deep Trace      Broad Sweep   Population Projection
12—32 人        100—1,000 人  10,000+ 记录
完整顺序体验     摘要／关键点    校准响应面／规则／小模型
逐时记忆与证据   结构化结果      不逐人生成长文本
       └───────────┼────────────┘
                   ▼
      一份报告：分别显示三层证据，不混成一个 N
```

### 5.1 Deep Trace

用途：发现具体时点的问题，验证叙事理解、状态变化、跳过／放弃原因和 A/B 路径。

- 默认 12—18，性能允许时扩到 32；
- 每个 Persona 有完整独立 Session；
- 可下钻到 Timeline、观察、记忆、状态和证据；
- 五次 Stability Run 只用于测同一 Persona 稳定性，不增加“人数”。

### 5.2 Broad Sweep

用途：搜索边缘人群、极端约束和问题覆盖，不承担逐秒体验。

- 默认 100，验证单位成本后再扩到 1,000；
- 共享已经冻结的内容摘要或少量关键检查点；
- 每人输出结构化选择、短理由和不确定性；
- 从 Sweep 中挑出反常、冲突和高价值样本升级为 Deep Trace。

### 5.3 Population Projection

用途：回答“如果把已经验证的差异应用到更大 Persona 池，覆盖结构如何变化”，不生成 10,000 篇伪访谈。

- 输入是 Persona 特征、Deep／Sweep 结果和真人 Anchor；
- 首版只能做场景投影和敏感性分析；
- 只有真人数据足够时才训练或拟合响应模型；
- 输出必须显示模型适用范围、外推比例和未覆盖人群；
- `P_projected` 不计入 Synthetic Runs，也不产生真人置信区间。

## 6. 不采购大规模算力的实现策略

1. **媒体只解析一次。** Timeline、ASR、镜头、音频和版本对齐按素材哈希缓存。
2. **先检索、后执行。** 1M Persona 池用于覆盖与抽样，不把整池变成 Agent。
3. **两阶段模型路由。** 规则／小模型处理普通事件和结构化 Sweep；强模型只处理关键转折、低置信和争议段。
4. **共享前缀、隔离状态。** Persona 共用冻结的 Timeline Prompt Prefix，但记忆和行为状态独立。
5. **只在状态变化时写长文本。** 其余事件只记录小型状态向量和证据引用。
6. **主动抽样。** 优先运行能扩大人群覆盖、模型分歧或不确定性的 Persona，停止重复相似个体。
7. **升级而非全量。** Broad Sweep 发现异常后，才把对应 Persona 升级成 Deep Trace。
8. **先 API／已有本地设备，后再谈部署。** 原型设置硬成本上限，不购买 GPU；如果私密素材限制第三方模型，再评估客户算力或按需租用。
9. **蒸馏属于通过验证后的优化。** 只有积累同任务真人与高保真 Trace 后，才训练小型响应模型；首版不先造一个未经校准的“观众模型”。

## 7. 开源与商业化分层

### 7.1 三种路线

| 路线 | 能获得什么 | 主要风险 | 适用条件 |
| --- | --- | --- | --- |
| 全开源 | 最大信任、传播和外部贡献；有机会成为 Media Eval 标准 | 企业功能和托管收入更难形成；数据／模型责任更复杂 | 社区采用强、商业需求弱或主要靠服务／托管变现 |
| 开放内核／商业产品 | 用开放 Schema、Runner 和 Benchmark 获取声量；以安全、校准、协作和托管变现 | 需要清楚解释边界，避免“伪开源”反感 | **当前最可能**：社区与商业信号同时存在 |
| 闭源产品 | 更容易保护工作流、校准和客户交付 | 失去开源生态分发，难与已有研究工具建立信任 | 私有试点强、客户明确付费，外部开发者价值很低 |

### 7.2 建议开放的层

- Timeline、Trace、Experiment 和 Human Anchor Schema；
- Media Environment 与模型适配接口；
- 公共素材 Demo、合成 Fixture 和验证脚本；
- One-shot／Sequential／Broad Sweep 基线；
- 证据报告的本地只读版本；
- 与 MatrAIx／TinyTroupe／Foreworld 的版本化 Adapter；
- 公开 Benchmark、失败案例和复现实验协议。

候选许可证为 Apache-2.0，原因是允许商业使用并包含明确专利授权。正式选择前仍需完成第三方依赖与素材清单；不把 MiroFish AGPL 代码混入该内核。

### 7.3 建议保留的层

- 未公开客户素材、Persona 原始资料和 Human Anchor；
- 按客户／品类形成的 Calibration Profile 与校准数据；
- SSO、细粒度权限、水印、审计、VPC／客户云路由和合规删除；
- 多项目协作、评审流、版本决策记录和企业报告模板；
- 托管服务的运行优化、配额、监控和 SLA；
- 受商业许可或来源条款限制的数据连接器。

这不是永久承诺。若后续证明校准数据和企业工作流没有商业价值，应把更多层开放；若社区复用很弱而客户强烈要求闭源部署，应减少公开维护面。

## 8. 用信号决定产品形态

公开 Demo 完成后，用两组独立信号决策，不把 Star 当作唯一目标。

### 8.1 开源声量门

在发布后 6—8 周内至少出现：

- 3 个非团队成员独立完成安装和 Demo 复现；
- 2 个有实质内容的外部 Issue、PR、Media Task 或 Adapter；
- 至少 1 个外部团队把 Schema／Runner 用到自己的素材或评测中；
- Star、Fork、下载量和页面访问作为辅助趋势，不单独触发继续投入。

这些门槛目前是 H 级经营假设，可在发布前根据现有社区渠道调整。

### 8.2 商业价值门

至少出现：

- 1 个获得授权的私有试点；
- 对方愿意提供同任务真人资料或安排真人对照；
- 报告促成一次具体版本、剪辑、营销或研究设计变更；
- 对方愿意为第二个版本、第二个项目、私有部署或持续服务付费。

### 8.3 决策矩阵

| 开源信号 | 商业信号 | 建议 |
| --- | --- | --- |
| 强 | 强 | 开放内核 + 商业控制面／私有校准，正式产品化 |
| 强 | 弱 | 继续作为开源研究／开发工具，控制商业投入 |
| 弱 | 强 | 以私有产品／项目服务为主，只维护必要开放标准 |
| 弱 | 弱 | 停止虚拟观众产品，保留通用 Timeline／Trace 资产 |

## 9. 对 2—4 周 MVP 的修改

### 必须新增

1. 固定版本审查 MatrAIx，并完成一个最小 Cohort／Trial Adapter Spike；
2. 把本项目定义为第五类 `Media` 环境实验，不重写 Persona Pool 与通用 Job Runner；
3. 同时跑三种基线：12 个 Deep Trace、约 100 个 Broad Sweep、一个 10k Persona 的无 LLM 投影演示；
4. 报告分别显示 `Pool Records`、`Deep Traces`、`Sweep Runs`、`Projected Records`、`Human Participants`；
5. 记录三个规模层的模型调用、tokens、墙钟时间和边际成本；
6. 对 MatrAIx 与本地 Persona 来源做许可证和数据卡审计。

### 仍然不做

- 下载并执行整个 1M Persona 池；
- 采购 GPU 或建设分布式集群；
- 训练新的 Persona 基座模型；
- 把 10,000 投影记录写成 10,000 个独立观众；
- 在首版引入 OASIS／AgentSociety 的百万 Agent 社交世界；
- 在没有真人 Anchor 时输出总体购买率、票房或收入区间。

### 新的 Demo 叙事

> 我们可以从大规模 Persona 宇宙中快速找到目标人群，但只对最有信息量的一小组运行完整顺序体验；其余规模用于覆盖扫描和敏感性分析。每个数字都说明它来自深度 Trace、快速 Sweep、投影还是真人。

这比展示一个未经校准的“10,000 人平均分”更能同时证明规模能力、工程克制和研究可信度。

## 10. 当前决策

1. **继续把 Audience Mirror 做成通用多环境实验平台，但不从零建设 Persona Runtime。** 通用产品定位不等于所有底层能力都要自研。
2. **把 MatrAIx 设为 P0 复用候选，TinyTroupe 设为对照基线。**
3. **首版仍做影视／IP Media Environment；它是第一个可核查证明，不是平台边界。**
4. **不扩招、不买算力。** 公开 Demo 采用固定成本上限、分层执行和按需模型 API／本地工具。
5. **产品形态暂定“开放内核倾向”，不立即承诺全部开源。** 先验证社区复用和私有试点两个信号，再决定最终许可证与商业边界。
