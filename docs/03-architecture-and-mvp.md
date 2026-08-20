# 技术架构与 MVP 方案

版本：Architecture Baseline v0.5
状态：Core contracts and Media vertical slice implemented；production architecture proposed
日期：2026-08-20

## 1. 架构目标

Audience Mirror 要在模型持续变化、环境数据可能高度敏感、科学有效性尚需验证的前提下，稳定支持六件事：

1. 用统一 Environment Contract 表达可观察状态、动作、版本、终止条件和真实结果；
2. 让不同 Persona 只按暴露顺序经历环境，并保留长期记忆；
3. 支持独立体验、群体互动和显式 Context Scenario；
4. 把每个结论追溯到环境证据与个体 Trace；
5. 用同任务真人数据校准，同时保存未校准结果、误差和实验指纹；
6. 先交付 Media Environment，同时保证核心对象不绑定视频、观众或审片流程。

### 1.1 2026-08-20 实现快照

当前代码已经实现 Environment Contract、Media Timeline Adapter、真实本地视频 Ingest、Gemini 原生视频 Adapter、Future-blind 模型顺序运行时、Trace 哈希链、Human Anchor 校准器和本地证据工作台。生产级异步队列、数据库、完整 Rights Manifest、ASR／OCR／说话人、Agentic 局部复核、Social Lab 和非 Media Adapter 仍属于下述目标架构。精确状态与验证记录见[可运行工程基线](08-implementation-baseline.md)，视频 Provider 与论文选择见[视频理解技术版图](10-video-understanding-landscape-2026-08-20.md)。

## 2. 设计原则

### 2.1 模型可替换

业务 Schema 不携带供应商专属字段。ASR、视觉、音频、语言推理、Embedding 和校准器都通过能力接口调用，模型选择属于 Experiment Spec。

### 2.2 素材理解与 Persona 体验分离

原片只做一次客观内容解析。多个 Agent 共享冻结的 Timeline，再根据 Persona 和记忆形成不同反应。客观 Timeline 可以只重解析 A/B 的变更片段；Persona Session 默认从最早变化事件重跑到片尾，避免早期变化通过记忆污染后续缓存。

### 2.3 观察、反应、文化解释、行为分层

- Observed Content：画面、对白、声音、角色、动作和事件；
- Simulated Response：理解、预期、情绪代理量、好感和记忆；
- Interpretive Context：某个 Persona 如何结合媒介经验、文化参照、身份语境和社群语言解读同一事件；
- Behavioral Decision：继续、回看、跳过、放弃、分享或考虑购买。

四层分开存储，防止“画面悲伤”被自动推成“所有观众被感动并愿意付费”，也防止“眼动停留”被推成“文化认同”。Interpretive Context 是带来源和不确定性的解释假设，不是从人口属性自动推断的标签。

### 2.4 证据优先

报告只是 Trace 的索引与聚合。没有时间点、证据引用和支持 Session 的结论不能进入正式报告。

### 2.5 校准范围明确

校准只对指定素材类型、问题、语言、人群和模型版本成立。不存在一个“总体拟真度”数字。

### 2.6 开放生态优先

不从零自建通用 Persona 数据集、浏览器 Agent 或百万 Agent 社会模拟。本仓库拥有 Environment／Experiment／Trace／Calibration 公共合同和首个 Media Environment，通过固定版本 Adapter 复用 MatrAIx、TinyTroupe、Foreworld／GAIA 等能力。Web／App、Game 与 Social Environment 可以后续新增或接入，不被写成永久非目标。第三方代码、模型权重和数据分别审查许可证，不能用代码许可证替代数据权利判断。

### 2.7 内容效应与语境效应分离

观看体验不只由素材决定，也受共同观看、口碑、社群语言和争议的影响。Experiment Spec 必须将 Reception Context 视为独立自变量，冻结信息截止时间、结果盲法状态和 Context Seed 哈希。默认主结果只来自 `independent_blind`；条件语境只用于测敏感性，不输出它在真实市场会发生的概率。

## 3. 总体架构

平台公共链路：

    内容／产品／游戏／规则／世界状态 + Context + Rights
                         │
                         ▼
              Versioned Environment Adapter
                         │
          ┌──────────────┴──────────────┐
          ▼                             ▼
    Population Universe            Experiment Spec
          └──────────────┬──────────────┘
                         ▼
         Sequential Experience + Memory Runtime
                         │
                         ▼
          Decision / Action / Interaction Trace
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
    Independent       Social Lab     Human Anchors
    Aggregation       （可选）        + Calibration
          └──────────────┼───────────────┘
                         ▼
          Evidence Report + Reproducibility Ledger

首个 Media Environment 把公共链路具体化为：

    未发布素材／公开 Demo／脚本／字幕／版本说明
          + Reception Context／信息截止时间／结果盲法
                         │
                         ▼
              Asset Vault + Rights Manifest
                         │
                         ▼
        Ingestion：转码、哈希、代理文件、音画分离
                         │
                         ▼
        Multimodal Extractors：ASR／Shot／OCR／Audio／Vision
                         │
                         ▼
       Timeline Fusion：shot → scene → event → act + 版本对齐
                         │
               ┌─────────┴─────────┐
               ▼                   ▼
   Persona Universe／Adapter    Experiment Spec
        + Audience Panel
               │                   │
               └─────────┬─────────┘
                         ▼
             Sequential Experience Runtime
                         │
                         ▼
           Event-sourced Trace + Memory Store
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
    Independent       Social Lab     Human Anchors
    Aggregation       （可选）        + Calibration
          └──────────────┼───────────────┘
                         ▼
        Evidence Report：时间轴、个体、分群、A/B、误差

### 3.1 部署单元

| 单元 | 责任 | 初版部署 |
| --- | --- | --- |
| Product API | Project、Asset、Experiment、权限、任务和报告 | 单体后端即可 |
| Media Worker | 转码、抽帧、ASR、OCR、音频特征 | 独立异步 Worker |
| Model Gateway | 供应商适配、配额、重试、缓存和审计 | 进程内接口，保持可拆分 |
| Persona／Eval Adapter | Persona 检索、Cohort、Trial 与外部运行时映射 | MatrAIx 固定版本外部进程／Python Adapter；内置 Stub 兜底 |
| Runtime Worker | Media 顺序体验与 Trace 写入 | 异步队列；可由本地实现或外部 Runtime 驱动 |
| Trace Store | 不可变事件、状态、记忆引用和运行指纹 | PostgreSQL JSONB 或本地 SQLite 原型 |
| Object Store | 原片、代理、帧、音频片段和报告制品 | 本地受控目录；私有试点换 S3 兼容私桶 |
| Report Web | Timeline、Trace Inspector、Variant Diff | 本地 React／静态 HTML 原型均可 |
| Calibration Worker | 真人对齐、指标和校正 | 离线 Job |

2—4 周原型不需要微服务化。逻辑边界和 Schema 先稳定，部署可保持简单。

## 4. Asset 与权利层

每个 Asset 必须携带 Rights Manifest：

| 字段 | 说明 |
| --- | --- |
| asset_id／variant_id | 稳定 ID |
| content_hash | 原文件哈希 |
| owner／controller | 权利控制方的内部标识，不在报告暴露真实身份 |
| permitted_purposes | 解析、模拟、真人测试、演示、导出 |
| allowed_regions | 允许处理地域 |
| allowed_processors | 可用模型供应商或本地模式 |
| retention_policy | 原片、代理、帧、Trace、报告分别保留多久 |
| sharing_policy | 谁能看、是否可下载、是否可生成分享链接 |
| watermark_policy | 是否需要个性化水印 |
| deletion_status | 删除时间、结果与审计引用 |

素材文本、字幕和画面内文字都属于不可信数据。Model Gateway 在系统 Prompt 中明确禁止执行素材中出现的指令，并对高风险输出做 Schema 验证。

## 5. 模型无关的多模态管线

### 5.1 Ingestion

1. 计算原片 SHA-256；
2. 生成统一帧率、音轨和低清代理；
3. 提取技术元数据；
4. 生成可寻址时间范围；
5. 验证字幕、剧本和原片的时间轴一致性；
6. 生成去标题／去片名的评测副本，检查模型是否用预训练记忆冒充观看；
7. 记录所有派生文件与原片哈希关系。

### 5.2 基础提取器

| 能力 | 输入 | 输出 | 可替换实现 |
| --- | --- | --- | --- |
| Shot Detector | 视频 | 镜头边界、转场类型、置信 | PySceneDetect／视觉模型 |
| ASR | 音频 | 词级时间戳、语言、置信 | 本地 Whisper／企业语音服务 |
| Diarization | 音频 | 说话人片段 | pyannote 类模型／供应商 |
| OCR | 关键帧 | 文本、位置、时间、置信 | 本地 OCR／多模态模型 |
| Audio Event | 音频 | 音乐、静默、爆点、音效、能量 | 传统 DSP／音频模型 |
| Vision Caption | 自适应帧组 | 人物、动作、场景、镜头信息 | 任意视频／视觉语言模型 |
| Character Linker | 帧、剧本、角色表 | 角色实体与出场 | Embedding + VLM + 人工纠正 |
| Event Extractor | 上述结果 | 事件、因果候选、角色关系变化 | LLM／规则组合 |

### 5.3 自适应采样

固定 1 FPS 只能作为低成本底图。采样策略为：

1. 每个 Shot 至少保留首、中、尾帧；
2. 快速动作、OCR、角色切换、镜头运动和音频突变触发高 FPS 重查；
3. Timeline 置信低或 Agent 产生争议时，按时间段请求高分辨率回查；
4. 关键帧缓存按 Asset Hash、时间段、采样策略和模型版本寻址；
5. 用户可以手工固定“不可漏帧”区间。

### 5.4 分层 Timeline

Timeline 不使用固定 N 秒摘要，而是四层：

| 层级 | 典型长度 | 作用 |
| --- | ---: | --- |
| Shot | 1—10 秒 | 视觉连续单元、关键帧和镜头语言 |
| Scene | 20 秒—5 分钟 | 地点／时间／人物相对稳定的场景 |
| Event | 数秒—数分钟 | 对理解或角色状态有意义的动作／信息 |
| Act | 数分钟—整片 | 叙事目标、转折与阶段 |

每个节点保存：

- 时间范围与父子关系；
- 观察事实和来源模态；
- 证据引用；
- 置信与冲突；
- 人工修订；
- 版本对齐 ID；
- 可能的显著性标签，但不预先写入观众反应。

可执行 Schema 见 [timeline.schema.json](../schemas/timeline.schema.json)。

JSON Schema 只负责结构。仓库级语义校验器还必须检查 node_id／observation_id 唯一、t_end 大于 t_start、父节点存在、父子时间包含、层级无环、Evidence 时间落在 Asset 范围内，以及 Alignment 指向精确的对方 Timeline 哈希；正反 fixture 与校验器一起进入实现门禁。

### 5.5 A/B 版本对齐

对齐顺序：

1. 用音频指纹、字幕和视觉 Embedding 找候选对应段；
2. 建立 unchanged、modified、inserted、deleted、moved 五类映射；
3. 人工确认关键变更；
4. 确定最早变化事件并使该点之后的 Persona 状态与记忆缓存全部失效；
5. 重跑时只复用不受影响的客观内容解析，Persona Session 从最早变化事件运行到片尾；
6. 只有状态向量和记忆摘要通过预注册的重新收敛检查，才允许复用更晚的 Session 区间；Trace 必须记录 invalidation 起点、复用范围和收敛证据。

## 6. Model Gateway

### 6.1 能力接口

| 接口 | 最小输入 | 最小输出 |
| --- | --- | --- |
| transcribe | 音频引用、语言提示 | 词级片段与置信 |
| inspect_frames | 帧引用、任务、上下文 | 结构化视觉观察与证据 |
| inspect_video_clip | 视频段、任务 | 时间化观察 |
| reason_event | Persona、既有记忆、当前事件 | 状态变化、动作、证据和不确定性 |
| summarize_memory | 近期事件与既有摘要 | 新的情节／角色／个人记忆 |
| embed | 文本／图像 | 向量与模型指纹 |
| aggregate | Trace 集与预注册问题 | 有引用的候选结论 |

每个响应必须通过 JSON Schema；失败时重试或降级，不能把自由文本静默写入权威 Trace。

### 6.2 路由策略

- 低成本模型处理 ASR 后清洗、普通事件与记忆压缩；
- 强模型处理低置信视觉、跨场景因果和矛盾裁决；
- 私密素材优先本地或企业 no-training／zero-retention 端点；
- Provider Adapter 负责 token、费用、延迟、重试和删除记录；
- 新模型上线必须先跑固定 Benchmark，不能直接替换生产默认值。

## 7. Audience Panel

### 7.1 Panel Spec

Panel 由 Persona Universe、Target Frame、Persona Instances 和 Weighting Policy 组成：

- Persona Universe：可查询的 Persona 记录池及其来源、许可证、覆盖和索引版本；
- Target Frame：这次业务希望覆盖谁；
- Persona Instance：一个稳定的模拟个体；
- Weighting Policy：用于场景汇总的业务权重，不等于抽样概率；
- Evidence Base：每个属性来自何种真人数据、研究或假设；
- Coverage Gap：没有数据或难以模拟的群体。

### 7.2 Persona 最小字段

| 维度 | 示例 | 规则 |
| --- | --- | --- |
| stable_identity | 年龄段、地区、生活阶段、职业语境 | 只保留任务必要粒度 |
| content_prior | IP／类型／角色知识 | 必须约束未来知识 |
| preferences | 题材、节奏、审美、观看习惯 | 可追溯到来源或显式假设 |
| interpretive_context | 媒介经验、文化参照、身份语境、社群语言 | 仅保留与当前任务有关且来源明确的摘要；不由年龄、地区等标签自动补齐 |
| constraints | 时间、设备、预算、注意环境 | 决定跳过／付费等行为 |
| behavior_history | 已授权的真实行为摘要 | 不复制原始个人记录 |
| personality | OCEAN 等 | 只作为弱特征，不当作行为真值 |
| social_context | 关系、社区和影响来源 | 群体实验才启用 |
| uncertainty | 缺失、冲突和低置信字段 | 不能由模型偷偷补齐 |

### 7.3 防止 Persona 收敛

1. 先从目标分层和真实资料构建差异，不依赖温度制造“多样性”；
2. 使用 Persona Pair Test：相反偏好的两人必须在预注册对照素材上产生可解释差异；
3. 检查回答 Embedding、评分方差、用词和行为动作是否收敛；
4. 对照真人检查组内方差覆盖，避免只有分群均值相似；
5. 单独测拒绝、跳过、放弃和不购买的负向行为召回；
6. 跨底模重跑至少一个小 Panel；
7. 报告 Persona Coverage，不报告“拟真率”总分。

## 8. 顺序体验运行时

### 8.1 Session 状态机

| 当前状态 | 触发 | 下一状态 | Trace |
| --- | --- | --- | --- |
| READY | 实验开始 | WATCHING | session.started |
| WATCHING | 正常消费事件 | WATCHING | perception／state.updated |
| WATCHING | 信息不足或回看意向 | REVIEW_MARKED | action.rewind_requested |
| REVIEW_MARKED | 记录后继续 | WATCHING | memory.updated |
| WATCHING | 跳过意向 | SKIPPED_WINDOW | action.skip |
| SKIPPED_WINDOW | 到下一事件 | WATCHING | exposure.gap |
| WATCHING | 放弃阈值达到 | ABANDONED | action.abandon |
| WATCHING | 最后事件完成 | COMPLETED | session.completed |
| 任意非终态 | 运行失败 | FAILED | session.failed |

首版可以记录“想暂停／回看／跳过”，无需真的控制视频播放器；游戏和交互原型阶段再让动作改变后续输入。

### 8.2 内部状态向量

每个事件更新：

- attention_proxy：模型估计的继续投入程度；
- valence／arousal：模型估计的情绪效价与唤醒；
- comprehension：当前理解；
- confusion：困惑；
- expectation：对后续的预期；
- character_affinity：角色好感；
- trust：对叙事／品牌／产品的信任；
- continue_intent；
- share_intent；
- consider_paying；
- interpretive_frames：带证据、来源和不确定性的定性解释集，不是数值总分；
- participation_modes：带证据的多标签状态，例如沉浸、分析、戏谑、合看或社交货币；允许同时存在并随事件变化；
- uncertainty。

所有值都是模拟状态，不是生理测量。

### 8.3 事件循环

    读取下一个 Timeline Event
      → 过滤未来知识
      → 检索 Persona 相关长期记忆与最近窗口
      → 生成结构化观察
      → 更新理解、情绪代理量、角色与行为状态
      → 如达到阈值，发出反应／动作
      → 写入 Trace
      → 压缩近期记忆并保留证据引用
      → 继续、跳过、放弃或结束

### 8.4 记忆模型

记忆分四层：

| 层 | 内容 | 生命周期 |
| --- | --- | --- |
| Working | 最近 1—3 个事件的细节 | 每事件更新 |
| Episodic | 重要时点、误解、惊喜和行为 | Session 内长期 |
| Character／World | 人物、关系、设定和因果 | Session 内长期 |
| Persona Prior | 观看前知识、偏好和约束 | 实验冻结 |

记忆条目必须引用来源事件。合并时保留“模型认为”“画面观察”“用户提供事实”等 epistemic status，避免推断变成事实。

## 9. Trace Schema

权威 Schema 位于 [trace.schema.json](../schemas/trace.schema.json)。核心字段包括：

- Experiment、Run、Session、Agent、Asset 与 Variant；
- Session 顺序号、前序事件／哈希、事件哈希、幂等键与流版本；
- Timeline 事件和暴露顺序；
- event_type；
- state_before／state_after；
- observation 与 evidence_refs；
- action／reaction；
- memory_reads／memory_writes；
- decision_basis_summary；
- 模型、Prompt、种子、代码和缓存指纹；
- 延迟、token 与费用；
- 数据分级、导出策略、保留等级与脱敏状态；
- 校准状态和人工审核。

### 9.1 Trace 不保存的内容

- 模型隐藏思维链；
- 未经授权的原始 Persona 资料；
- 与任务无关的个人身份信息；
- 报告无法展示的供应商内部字段；
- 未来剧情或当前 Agent 尚未暴露的信息。

### 9.2 Event Sourcing

Trace Event 不可原地覆盖。状态由事件重放得到；人工修正通过 review.override 新事件表达。这样可比较不同聚合器、Prompt 和校准器，而不破坏原始运行。

每个事件还必须携带 session_sequence_no、previous_trace_event_id、previous_event_hash、event_hash、idempotency_key 和 stream_version。存储层保证同一 Session 的 sequence 唯一、只追加和乐观并发检查；JSON Schema 只验证结构。

## 10. 群体互动

### 10.1 三类条件分层

1. Independent Blind：所有 Agent 只使用素材与预注册先验独立体验，不知道市场结果或事后评论；
2. Context-conditioned Independent：为隔离 Session 注入明确的社会线索，仍先个体判断；
3. Social Phase：只在个体判断冻结后，按关系图进行有限讨论、评论和转述。

三者使用不同 `reception_context.condition` 与 `run_type`，指标分开。四周 MVP 只要求 Independent Blind；其余为 P1 研究门。

### 10.2 后续研究范围

- 3—5 人、1—2 轮观看后讨论；
- 只研究观点变化、争议点和传播语言；
- 记录 influence_edge：谁的哪条信息影响了谁；
- 不模拟“全网热度”和大规模销量。
- 可对一组预注册语境种子做 Context Delta，但不模拟该语境的真实发生概率。

### 10.3 防止从众伪装成证据

- 讨论前评分锁定；
- 聚合报告默认使用独立结果；
- 单独显示讨论后变化；
- 不把同一观点在讨论中被复述多次计作多个独立证据。
- 报告从众率、少数意见保留率、错误信息传播率和“更强 Agent”影响集中度。

## 11. 聚合与报告

### 11.1 聚合器规则

1. 只回答 Experiment Spec 中预注册的问题；
2. 聚类问题时保留每个 Trace 引用；
3. 同时统计支持、反对、无感和未观察；
4. 业务权重只用于场景比较，明确标注来源；
5. 不从 Agent 数量计算传统置信区间；
6. 重复运行用于稳定性，不用于“扩大样本”；
7. 低证据结论进入“待真人验证”，不进入推荐。

### 11.2 Claim Ledger

每条报告结论保存：

- claim_id 与文本；
- 问题类别；
- 支持／反对 Trace；
- 关联素材证据；
- Segment 与 Variant；
- 生成器版本；
- 人工审核状态；
- 真人一致／冲突状态；
- 适用范围和限制。

## 12. 真人校准

### 12.1 Human Anchor 类型

- 逐时拨盘／连续评分；
- 时间点问题标记；
- 观看后量表；
- 开放访谈编码；
- 跳过、完成和选择行为；
- A/B 选择；
- 已有眼动或生理信号。

不同类型不能混成一个“真人真值”。例如眼动是视觉注意信号，不等于喜欢或购买；脑电／生理唤醒不等于身份认同，也不能单独解释戏谑、反抗、亚文化或群体传播。文化解释的参照应来自同任务访谈编码、开放回答和行为语境。

真人数据使用独立的 [human-anchor.schema.json](../schemas/human-anchor.schema.json)，记录匿名参与者、同意、Human Session、随机分配、暴露顺序、反平衡单元、测量工具、时间点、编码者和来源哈希；它不要求 Agent、Prompt、模型或随机种子字段。撤回后必须标记 analysis_excluded，使关联 Claim、缓存和导出制品失效，并记录删除 receipt 或合法保留依据。

### 12.2 校准层级

| 等级 | 条件 | 报告措辞 |
| --- | --- | --- |
| U0 未校准 | 只有模型输出 | 假设／模拟反应 |
| U1 技术校验 | 时间轴与事实经人工抽检 | 可核查内容观察 |
| C1 方向校准 | 同任务有预注册真人计划，且在新素材或封存人群上通过方向验证 | 方向性辅助证据 |
| C2 指标校准 | 多素材、多分群有稳定误差模型 | 在明确范围内的校正指标 |
| C3 前瞻验证 | 预注册、封存预测在新项目持续通过 | 可用于指定决策流程 |

四周公开 Demo 的目标是 U0／U1 加探索性 Human Convergence；8—12 位真人不用于拟合校正器。C1 属于后续私有试点，需要独立校正集与封存验证集。

### 12.3 校正方法

- 二元／多分类：混淆矩阵、Brier Score、概率校准；
- 连续／序数：MAE、Spearman、isotonic 或 ordinal calibration；
- 问题集合：Recall@K、Precision@K、时间容差匹配；
- 分群：方向与排序，不在小样本上强行做显著性；
- 报告原始值、校正值和样本量，保留版本化 Calibration Profile。

### 12.4 误差分解

分别测量：

1. Timeline 事实错误；
2. Persona 抽样差异；
3. 同模型重复运行波动；
4. 换底模波动；
5. 与真人的系统偏差；
6. 真人自身的复测与编码者差异。

## 13. 复现实验

Experiment Manifest 必须冻结：

- Asset／Variant 哈希；
- Timeline 版本；
- Audience Panel 与 Persona 快照；
- 研究问题和量表；
- 模型供应商、模型 ID、接口版本；
- System／Task Prompt 哈希；
- 温度、top_p、种子和输出 Schema；
- 代码 Git SHA；
- Calibration Profile；
- 缓存策略；
- 运行地域；
- 开始／结束时间和费用。
- Reception Context 条件、信息截止时间、结果盲法状态、Context Seed 来源与哈希。

供应商模型更新可能导致无法逐字复现。项目验收比较结构化状态、问题集合和方向，并保留原始响应哈希。

## 14. 规模与成本控制

### 14.1 四种规模

| 数量 | 定义 | 默认用途 |
| --- | --- | --- |
| `P_pool` | 可检索 Persona 记录量 | 人群覆盖、分层、去重和抽样；不默认产生模型调用 |
| `K_deep` | 完整顺序体验与逐时 Trace 数 | 12—18，性能允许时扩至 32 |
| `K_sweep` | 摘要／关键检查点的结构化快速运行数 | 先 100，验证单位成本后再扩至 1,000 |
| `P_projected` | 由规则、校准响应面或小模型做场景投影的记录数 | 10k+；不逐条生成长文本，不算独立体验 |

MatrAIx 的官方文档明确区分 Persona Pool 与 Trial：`N personas = N trials`，10 个 Trial 约 10 次 LLM 调用。并发只缩短墙钟时间，不能消除独立 Trial 的推理量。相反，Persona 检索、最终确定性聚合和无 LLM 投影可以在普通 CPU 上低成本扩展。

变量成本近似为：

```text
C_total
  = C_timeline_once
  + V × R × (K_deep × E × C_state_step)
  + V × R × (K_sweep × C_sweep)
  + C_projection(P_projected)
  + C_deterministic_report
```

其中 `E` 为 Timeline 事件数、`V` 为版本数、`R` 为稳定性重复数。产品必须分别显示 Pool、Deep、Sweep、Projected 与 Human 数量，禁止把投影记录或重复运行写成独立观众。

### 14.2 主要成本项

- 媒体转码与特征提取；
- 多模态模型解析；
- 每个 Persona 的事件推理；
- 记忆压缩；
- 聚合与报告；
- 重复运行与多模型对照；
- 私有部署基础设施。

### 14.3 控制策略

1. Timeline 只构建一次；
2. 共享客观内容观察，不共享 Persona 反应；
3. 普通事件用轻模型，低置信与关键段用强模型；
4. 只有状态显著变化时生成自然语言反应；
5. 先跑每层 1—2 个 Pilot Agent，再扩到 Deep Trace Cohort；
6. A/B 客观解析使用版本对齐；Persona Session 从最早变化事件失效并重跑；
7. 每阶段设置 token／费用硬预算；
8. 缓存必须包含模型与 Prompt 指纹，避免错误复用；
9. 成本面板按“每素材分钟、每 Agent、每实验”展示。
10. 大 Persona 池先做索引检索；只有能扩大覆盖、模型分歧或不确定性的记录才升级为 Sweep／Deep；
11. Broad Sweep 使用冻结摘要或少量关键检查点，不伪装成完整顺序观看；
12. Population Projection 只输出分布敏感性，不逐人生成自然语言；没有同任务真人 Anchor 时不拟合现实人口率；
13. Batch、并发和 Prefix Cache 用于降低单价与耗时，但每个独立 Persona 保留独立状态和调用账本。

### 14.4 原型预算目标

| 指标 | 目标 |
| --- | ---: |
| 15 分钟首次 Timeline | 小于 30 分钟 |
| 12 Agent 独立运行 | 小于 20 分钟 |
| 单次模型直接成本 | 小于 15 美元 |
| 100 Persona Broad Sweep | 单独记录调用数与成本硬上限；超过预算则减少检查点或改用小模型，不采购算力 |
| 10k Persona Projection | 普通 CPU 可运行；零逐 Persona LLM 调用 |
| 相同 Timeline 重跑 | 不重复媒体解析 |
| Variant 小改重跑 | 客观 Timeline 只重解析变更；Persona 从最早变化点重跑 |

这些是待验证产品门槛，不是现有性能数据。

15 美元门槛只针对 Deep Reference Workload：15 分钟视频、40—80 个 Event、12 个 Deep Trace、单模型、五次以内结构化重试；不含 Broad Sweep、第二模型、真人招募和人工编码。结果必须附模型与价格日期、采样密度、并发度、失败重试和缓存命中率，避免通过降级模型或少跑事件“达标”。

## 15. 安全

### 15.1 未发布素材

- 原片默认不可下载；
- 代理文件与原片分桶；
- 服务账号最小权限；
- 全链路加密；
- 上传、访问、模型传输和删除有审计；
- 默认成功后删除原片，保留期由 Rights Manifest 覆盖；
- 报告只嵌时间码缩略图或受控片段；
- 分享链接有时效、权限和撤销。
- Object Ref 只能是内部 opaque ID，禁止写入签名 URL、本地绝对路径或凭据；
- Timeline、Trace、Memory 和报告字段携带数据分级、导出策略、保留等级与脱敏状态；
- 公共导出不携带未发布对白、真人原话或可还原个人的 excerpt。

### 15.2 模型供应商

- 明确 no-training、retention、region 与 subprocessors；
- 未满足条件的端点不能处理私密素材；
- VPC／客户云与共享 SaaS 是两种产品模式；
- 本地开源模型质量不足时，报告必须显示降级；
- 不把 API Key 交给前端或第三方适配器。

### 15.3 Persona 与真人数据

- 数据最小化；
- 个人资料先生成任务相关摘要，再与身份分离；
- 眼动、生理、交易和未成年人数据单独审批；
- 删除 Persona 时能定位所有派生对象；
- 报告禁止还原真实个人。

## 16. 与开源运行时、Foreworld／MiroFish 的工程边界

### 16.1 本仓库拥有

- Asset／Variant／Rights；
- Multimodal Timeline；
- Audience Panel Spec；
- Sequential Experience Runtime；
- Timeline 与 Trace 的 v0.1 权威 Schema；
- Asset／Rights、Audience／Persona、Experiment、Human Anchor、Claim 与 Calibration 的领域设计；
- 内容实验 API 与报告 UI；
- Adapter 接口。

当前只有 Timeline、Trace 和单独的 Human Anchor 进入可执行 Schema。其余合同在进入私有试点前必须落成 Schema 和正反 fixture；不能把设计表格当作已经可执行的契约。

### 16.2 MatrAIx 可提供

- 大规模 Persona Schema、检索与 Cohort；
- Task／Trial／Verifier／Telemetry 和成本账本；
- Survey／Chat／Web／App 环境与实验工作台；
- 固定种子、运行清单和轨迹聚合。

当前采用固定 Commit 的 Adapter Spike，不把 4.17 GB Persona 1M 数据并入本仓库。MatrAIx 代码为 MIT；公开 Persona Coreset 未声明统一数据许可证，并要求继续遵守底层来源条款。商业或再分发前必须完成逐来源审计。Media Environment、动态长程记忆和真人校准仍由本仓库拥有。

### 16.3 TinyTroupe 可提供

- 小型 Persona／World 实验、A/B Runner、结果抽取与校验；
- 图像输入、成本追踪和经验数据验证的对照实现。

它作为第二基线，不与 MatrAIx 同时成为 P0 主依赖。先用同一公开任务比较集成成本、Trace 可追溯性和重复运行稳定性。

### 16.4 Foreworld 可提供

- WMG 中的实体、关系和长期世界知识；
- GAIA 的群体讨论与传播；
- Project／Branch／Task 的长期整合；
- 现实证据与背景研究。

接入前提是版本化合同、租户隔离和未发布素材不进入公共 Reality 分支。

### 16.5 MiroFish 可提供

- 图谱／Persona／社媒模拟方法参考；
- 在许可允许时，以独立部署服务接入讨论／传播实验。

MiroFish 公开代码不进入本仓库。进程或 API 隔离只是风险控制建议，最终边界需结合 AGPL、通信语义和商业部署单独确认。

## 17. 2—4 周 MVP

### 17.1 两周最小可运行版本

**第 1 周**

- 建立 Project／Asset／Experiment 基础模型；
- 对 MatrAIx 固定版本运行 Smoke，并实现最小 Persona／Cohort／Trial Adapter Spike；
- 记录代码、Persona 数据、模型与素材的独立许可证清单；
- 接入本地转码、Shot、ASR、关键帧和一个多模态模型；
- 生成可编辑 Timeline；
- 从已审计小型 Persona Pool 检索／补充 12 个 Deep Persona，并生成 Panel JSON；
- 固化 Timeline 与 Trace Schema。

**第 2 周**

- 实现顺序事件循环与四层记忆；
- 运行 one-shot 与 sequential 两个实验臂；
- 生成本地 HTML：Timeline、问题卡、个体 Session；
- 记录模型、Prompt、费用和耗时；
- 用《Sintel》跑通全片。

两周版不做登录、多租户、社交传播和自动校准。

### 17.2 四周原型与探索性研究

**第 3 周**

- 制作并对齐两个 CC BY 合法 Variant；
- 运行约 100 个 Broad Sweep，并把少量异常 Persona 升级为 Deep Trace；
- 用 10k 条合成／公开许可 Persona 特征完成零逐人 LLM 调用的 Projection 演示；
- 实现 Variant Diff、五次重复运行和稳定性；
- 固定技术版本、问题去重、证据复核和缓存失效规则；
- 生成真人盲测包。

**第 4 周**

- 导入 8—12 位真人探索性盲测，不拟合校正器、不验证三分群；
- 完成本地素材删除与访问审计；
- 让少量内容从业者盲评报告可行动性；
- 输出公开 Demo、限制说明、失败案例和私有试点包；
- 根据验证门槛做 Go／Pivot／Stop 决策。

第二模型、自动校正器、Social Lab 和客户云路由进入后续研究门，不作为四周原型完成条件。

## 18. 原型验收

### 18.1 正确性

- Timeline 抽检的角色、对白和事件错误率可量化；
- 所有 Trace 通过 Schema；
- 未来事件不可出现在早期记忆；
- A/B Session 不交叉污染。

### 18.2 可追溯

- 任一报告结论三次点击内到达素材、时间点、Agent 和证据；
- 所有自然语言建议引用 Claim Ledger；
- 人工修订有审计。

### 18.3 研究有效性

- one-shot 与 sequential 结果可独立比较；探索性 Human Convergence 保持 U0／U1；
- 报告 Agent-only、Human-only、冲突和一致项；
- Agent 数与真人数分开显示；
- 不输出未经校准的统计显著性。

### 18.4 成本与恢复

- 任务失败可从阶段检查点恢复；
- 缓存命中可证明没有重复解析原片；
- 成本按阶段和 Agent 可查；
- 模型或 Schema 失败返回结构化错误。

### 18.5 安全

- 公开 Demo 只有获许可素材；
- 私密原片不进入仓库；
- 删除策略可执行并有记录；
- 日志不含密钥、原始个人资料或可下载媒体 URL。
