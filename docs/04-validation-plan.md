# 验证计划

版本：Validation Protocol v0.5
状态：部分执行；公开视频事实 Benchmark 与技术重复已完成，真人招募尚未开始
日期：2026-08-21

## 1. 验证目的

这轮验证不问“AI 像不像人”这个宽泛问题，只回答七个可证伪的问题：

1. 顺序多模态体验是否比“摘要后访谈”更能复现真人发现的问题？
2. Agent 对两个版本的方向判断是否与真人同向？
3. Persona 分层是否产生与真人分层一致的差异，而非只改变说话风格？
4. 相同实验重复运行时，关键问题和版本结论是否稳定？
5. 结果能否在足够低的成本和时间内帮助内容团队采取行动？
6. 当真人明确表达文化参照、身份认同、戏谑或反抗语境时，Agent 是否能找到对应解释，而不是只给出生理／情绪代理量或刻板人群标签？
7. 系统能否把内容独立反应与社会语境敏感性分开，并在已知结果案例中避免事后信息泄漏？

## 2. 基本纪律

1. Agent 数量是运行规模，不是真人样本量。
2. 同一底模生成的多个 Agent 具有相关误差，不能用传统独立同分布假设计算显著性。
3. 真人 N、Agent N、重复运行次数和模型数在报告中分开显示。
4. 先冻结研究问题、指标、版本和人群，再运行；看到结果后新增的问题标记为探索性。
5. A/B 方向、问题召回和证据时间点优先于绝对分数。
6. 所有厂商准确率只作为竞品背景，不作为本项目基准。
7. 私密试点只能在素材方明确授权后开始。
8. 自报、访谈编码、行为、眼动和生理信号分别报告；不把生理波峰当成文化认同或传播动机的真值。
9. 每个 Run 冻结 Reception Context、信息截止时间和 outcome_blinded；已知市场结果不得进入事前实验 Prompt、Persona 或语境种子。

## 3. 验证路线

| 阶段 | 素材 | 目的 | 退出条件 |
| --- | --- | --- | --- |
| V0 技术基线 | 公开短片 | 时间轴、顺序、Trace、成本与安全跑通 | 全链路可复现且每条结论可回链 |
| V1 公开盲测 | 公开短片 + A/B | 比较 Agent 与真人方向和问题 | 达到最低门槛或明确失败原因 |
| V2 私有试点 | 获授权的真实业务素材 | 检验目标人群、真实决策与安全 | 业务方认为至少一项结论改变下一步 |
| V3 前瞻验证 | 新素材、结果尚未知 | 避免用已知答案调 Prompt | 连续两个项目通过预注册门槛 |

## 4. 公开 Demo 素材

### 4.1 首选：《Sintel》

Blender Foundation 的《Sintel》约 15 分钟，具有：

- 连续叙事、角色关系、信息揭示和情绪转折；
- 对白、音乐、动作和强视觉表达；
- 官方多语言字幕和高质量源文件；
- 可公开展示与制作衍生版本。

[官方许可说明](https://durian.blender.org/sharing/) 表明项目成果采用 CC BY 3.0，可在保留适当署名和影片完整片尾等条件下复用与分发；[官方介绍](https://durian.blender.org/about/) 和[下载页](https://durian.blender.org/download/)提供影片与字幕。

执行前需把具体署名、片尾、修改说明和分发方式写入 Rights Manifest。

### 4.2 Demo 设计

Demo 包含两类任务：

1. **全片顺序体验**
   - 原版全片；
   - 检验角色理解、关键揭示、情绪代理量、记忆和放弃风险；
   - 展示完整个体 Trace。
2. **同源营销 A/B**
   - A：官方预告或保持原叙事逻辑的基准版；
   - B：基于 CC BY 素材制作的 clarity-first 变体；
   - 两版保持时长和核心画面尽量接近，只预注册改变一个主因素；
   - 检验信息传达、兴趣、记忆点和继续了解意向。

若无法控制单一变量，报告必须把 A/B 定义为整体版本比较，而非声称某一个剪辑动作造成结果。

### 4.3 第二公开素材

只有第一轮跑通后才加入。可选择：

- 另一部不同风格的 Blender 开放短片；
- 经 EULA 许可的 [LIRIS-ACCEDE](https://liris-accede.ec-lyon.fr/) 片段及连续效价／唤醒数据，用于曲线方向检查。

第二素材用于检验是否过拟合《Sintel》，不用于扩大所谓样本量。

## 5. 实验臂

### 5.1 基线与处理

| Arm | 输入方式 | Persona | 顺序记忆 | 真人校准 | 目的 |
| --- | --- | --- | --- | --- | --- |
| A：Content-only | 全片摘要／字幕与研究问题 | 无 | 无 | 无 | 测普通内容分析基线 |
| B：Persona one-shot | 全片摘要／字幕与研究问题 | 有 | 无 | 无 | 测 Persona 文风与意见基线 |
| C：Sequential | 分层多模态 Timeline 逐事件暴露 | 有 | 有 | 无 | 测顺序体验增量 |
| D：Sequential calibrated | 与 C 相同 | 有 | 有 | 有 | 测少量真人校准增量 |
| E：Alternate model | 与 C 相同 | 有 | 有 | 无 | 测换底模波动 |
| F：Context-conditioned | 与 C 相同，另注入预注册社会线索 | 有 | 有 | 可选 | 测语境敏感性和 Participation Mode 变化，不测语境真实发生概率 |

四周公开 Demo 只把 A、B、C 作为技术实验臂。D、E 和 F 属于后续研究门；Arm D 只有在样本计划包含独立校正集与封存验证集时才能启动，最终评分必须使用封存人群或新素材，避免同一数据既校准又验收。

所有核心实验另跑去标题／去片名副本，检查模型是否用预训练记忆冒充观看。

### 5.2 Audience Panel

公开 Demo 首轮使用 3 个分层，每层 4—6 个 Agent，总计 12—18 个：

1. 动画／奇幻高兴趣；
2. 普通流媒体叙事观众；
3. 低先验兴趣、短视频使用较高。

分层只是实验构造，不能声称代表真实市场比例。公开 Demo 的 8—12 位真人不用于验证这三个分层；分群映射和样本计划在后续私有试点单独预注册。

### 5.3 三层规模基准

在冻结的同一 Timeline、问题和模型配置上分别运行：

1. `K_deep = 12`：完整顺序体验与逐时 Trace；
2. `K_sweep ≈ 100`：冻结摘要或预注册关键检查点的结构化快速运行；
3. `P_projected = 10,000`：用规则或未校准响应面做零逐 Persona LLM 调用的场景投影。

记录每层的模型调用、tokens、墙钟时间、直接成本、失败率、新增独特问题、与 Deep／Human 的重合，以及从 Sweep 升级为 Deep 后是否仍成立。若 Broad Sweep 只是制造重复礼貌意见，应减少规模并改进主动抽样；若 Projection 被误读为 10,000 次体验，界面和报告判定失败。

### 5.4 重复运行

- 每个核心 Arm 至少运行 5 次；
- 固定 Timeline、Panel 与 Prompt，改变种子；
- 第二底模对照属于后续研究门，不是四周原型完成条件；
- A/B 采用独立 Session，禁止同一 Agent 携带另一版本记忆；
- 若真人同时看 A/B，采用 between-subject 或反平衡顺序。

## 6. 真人研究

### 6.1 公开 Demo

首轮招募 8—12 位真人只用于探索性问题集、时点和报告可用性，不做总体或分群推断，也不拟合校正器。每位参与者：

1. 筛查观看习惯与内容先验；
2. 按随机顺序观看一个 Variant，或在探索性 A/B 中完成反平衡观看；
3. 在预注册点位完成轻量连续标记；
4. 观看后回答理解、角色、情绪、记忆、继续了解和 A/B 问题；
5. 完成 20—30 分钟半结构访谈；
6. 允许研究团队将问题编码为匿名 Human Anchor。

真人参与需有知情同意、退出、数据保留和补偿说明。

工程入口为 `audience-mirror prepare-blind-study`：从一个或两个冻结 Timeline 生成匿名槽位、结果盲法、单版本／AB-BA 反平衡、预注册量表和独立研究者密钥。生成槽位只是研究计划，`human_participants_completed` 固定从 0 开始；具体使用与解盲顺序见[真人盲测包](15-blind-study-packet.md)。

每位真人拥有 human_session_id、assignment_id、exposure_order 与 counterbalance_cell。撤回后立即从分析和报告排除，关联 Claim、缓存和导出制品失效，并记录删除 receipt 或合法保留依据。

### 6.2 私有试点

只有素材权利方书面确认后进行：

1. 素材方提供一个 8—20 分钟片段或两个 1—5 分钟营销版本；
2. 共同冻结研究问题、人群和安全要求；
3. 优先复用既有真人问卷／访谈；若需新招，先根据预注册指标、版本、人群和期望精度制定样本计划，10—20 人只用于探索性问题发现；
4. 研究编码者在不知道来源是 Agent 还是真人的情况下整理问题；
   - 对文化语境明显的内容，预先定义“文化参照”、“身份／社群认同”、“戏谑／戲仿”、“反抗／冒犯”和“无法判断”等编码，不凭人口属性补标签；
5. 内容决策者先看匿名问题与证据，不看“AI／Human”标签；
6. 记录哪些结论改变了剪辑、营销、真人研究问题或没有被采用；
7. 素材按 Rights Manifest 到期删除。

不把未公开项目名、人员、商业数据或原始素材写入本仓库。

## 7. 盲测方法

### 7.1 问题集合

两名独立编码者把真人访谈与 Agent Trace 分别编码为：

- 问题类别；
- 时间范围；
- 受影响分群；
- 严重度；
- 证据类型；
- 如果参与者主动表达，记录文化参照、身份／社群语境和传播语言；
- 建议方向。

编码者不知道文本来源。分歧由第三人裁决，并报告 Cohen’s kappa 或简单一致率。

文化解释只对真人访谈或开放回答中明确出现的编码做 Recall／Precision 对齐；没有真人表达时不能因生理信号或 Agent 文风相似而判定命中。公开 Demo 数量不足时只展示定性对照，不设统计门槛。

### 7.2 A/B

在运行前定义每个指标的优选方向。Agent 与真人独立选择：

- A 更好；
- B 更好；
- 无法区分／各有优势。

“无法区分”是有效答案。只有同方向才计一致，不能把模糊措辞人工解释成命中。

方向聚合在运行前冻结：

1. 每个 Agent Run 将 A、无法区分、B 编码为 −1、0、+1；
2. 同一 Persona 的五次 Stability Runs 先取众数；平票或最高票不足 3 次则该 Persona 弃权；
3. Agent Panel 主结果按 Unique Persona 一人一票的多数方向计算，平票或胜方不超过 50%则为“无法区分”；Scenario Weight 只作为单独的敏感性分析；
4. 真人 within-subject A/B 也按一人一票多数方向计算；公开 Demo 至少需要 8 份有效 A/B 回答，否则只展示个体分布；
5. 真人 between-subject 设计按预注册的中心统计量与阈值判断方向；每个版本必须达到样本计划的最小有效人数，否则弃权；
6. 缺失、撤回和无效回答不进入分母，并单独报告。

### 7.3 时间点

真人和 Agent 问题按时间窗口匹配。首轮建议容差：

- 预告／短视频：±3 秒；
- 8—20 分钟叙事：±10 秒；
- 跨场景问题：以 Scene／Event ID 匹配。

## 8. 指标

### 8.1 A/B 方向一致性

    Direction Concordance
    = Agent 与真人方向相同的预注册指标数
      ÷ 双方均给出方向的指标数

同时报告 Direction Coverage、Abstention Rate、最少可判定指标数、包含“无法区分”的三分类混淆矩阵／macro-F1，以及方向翻转率。Direction Concordance 只有在至少 5 个预注册指标且 Direction Coverage 达到 70% 时启用；小样本只做描述，不做虚假显著性。

### 8.2 Top 问题召回与精度

    HumanTopKRecall@K
    = Agent Top-K 命中的 Human Top-K 问题数
      ÷ min(K, Human 问题数)

    Precision@K
    = Agent Top-K 命中的 Human Top-K 问题数
      ÷ min(K, Agent 问题数)

问题先按类别、时间窗与机制去重，再由盲编码者按严重度冻结 Human Top-K。命中必须同时满足类别和时间／事件匹配；若要用全部真人问题作分母，指标另命名为 Coverage@K，门槛按理论上限设定。

### 8.3 时间点匹配

- Point Recall：真人关键时点有 Agent 命中的比例；
- Median Offset：命中时点的绝对时间差中位数；
- False Peak Rate：Agent 强峰值但真人无对应证据的比例。

### 8.4 分群差异

后续私有试点在样本计划支持时才看：

- 差异方向是否一致；
- 三个分层排序是否一致；
- 真人显示差异时 Agent 是否压平；
- Agent 显示差异时是否来自刻板 Persona。

可用 Spearman 排序相关；不在每层数人时宣称总体显著。

### 8.5 重复运行稳定性

- Top-K 问题集合的两两 Jaccard；
- A/B 方向翻转率；
- 关键曲线的 rank／shape correlation；
- 评分的组内相关或变异系数；
- Persona 行为动作的一致性；
- 换模型后的方向保留率。

重复运行衡量模型稳定性，不增加统计样本。

### 8.6 校准

四周公开 Demo 不拟合校正器。后续 C1／C2 按任务选择：

- 二元行为：Brier Score、ECE；
- 序数评分：MAE、Spearman；
- 方向：准确率与混淆矩阵；
- 问题集合：Recall／Precision；
- 曲线：相关、峰值匹配和时间偏差。

同时报告校准前后变化，防止校正器掩盖原模型失败。

### 8.7 证据质量

- Grounded Claim Rate：正式结论中带有效素材与 Trace 引用的比例；
- Evidence Entailment Rate：双人抽检确认引用证据确实支持结论的比例；
- Unsupported Claim Rate：人工抽检无证据或证据不支持的比例；
- Timeline Fact Accuracy：角色、对白、动作和事件抽检准确率；
- Future Leakage Rate：早期 Trace 引用未来事件的比例；
- Contradiction Visibility：报告是否展示关键反例。

抽检在运行前冻结比例，至少覆盖正式 Claim 的 20%和所有高严重度 Claim；关键错误由两人复核。Timeline Fact Accuracy 分视觉、对白／字幕、OCR 和事件关系报告，不能用一个平均数掩盖单模态失败。

### 8.8 负向行为与组内方差

- Negative Behavior Recall：真人出现拒绝、跳过、放弃或不购买时，Agent 是否命中；
- Disengagement Deficit：Agent 与真人的负向行为率差；
- Within-segment Variance Ratio：Agent 组内方差相对真人组内方差；
- Persona Collapse：不同 Persona 的行为与主题是否收敛。

Social Lab 后续另测讨论前后从众率、少数意见保留率和错误传播率，不与独立观看指标混算。

### 8.9 成本与耗时

- 首次 Timeline 分钟／素材分钟；
- 运行分钟／Agent／素材分钟；
- 模型成本／素材分钟；
- Deep Trace 成本／独立 Session；
- Broad Sweep 成本／结构化 Run 与每个新增问题；
- Population Projection 的 CPU 时间、记录数与逐 Persona LLM 调用数（必须为零）；
- A/B 客观解析重用率，以及从最早变化事件重跑 Persona 的真实成本；
- 人工 Timeline 修订时间；
- 从上传到可审查报告的总时间。

Deep Reference Workload 固定为 15 分钟、40—80 个 Event、12 个 Deep Trace、单模型、五次以内结构化重试；不含 Broad Sweep、真人招募、第二模型和人工编码。记录价格日期、采样密度、并发、失败重试与缓存命中。

### 8.10 产品可行动性

让 3 位内容从业者分别看普通 AI 总结与 Trace 报告，盲评：

- 是否相信结论有来源；
- 是否找到新的具体问题；
- 是否知道下一步怎么改；
- 是否改变真人研究问题；
- 是否愿意为新版本再次运行；
- 查到证据所需时间。

### 8.11 语境敏感性与结果泄漏

P1 中对一个公开文化案例做严格回溯：

1. 设置一个事前信息截止时间，只使用截止时间前已公开素材；
2. 为素材、Prompt、Persona Prior、检索库和 Context Seed 生成哈希与泄漏检查表；
3. 比较 `independent_blind` 与多个显式 Context Scenario，只解释 Context Delta；
4. 记录 Participation Mode 的变化、个体反例、重复运行稳定性和跨底模翻转；
5. 若任何输入含有截止时间后的市场结果、热门解释或评论摘要，该 Run 只能标记为 retrospective explanation，不进入预测性验收。

`Context Sensitivity` 衡量同一 Persona 在不同预设语境下的方向、行为和参与模式变化，不是真实市场发生概率。文化市场的社会影响具有路径依赖，因此该实验不设“预测爆款”通过线。

## 9. MVP 成功门槛

以下门槛是产品 Go／Iterate once／Stop 规则，不是科学界通用标准。

### 9.1 必须通过

| 指标 | 最低门槛 |
| --- | ---: |
| Grounded Claim Rate | ≥ 95% |
| Evidence Entailment Rate | ≥ 90% |
| Unsupported Claim Rate | ≤ 5% |
| Timeline Fact Accuracy | 各模态 ≥ 90%，高严重度事实 100% |
| Future Leakage Rate | 0% |
| Human Top-5 Recall | ≥ 60% |
| Top-5 Precision | ≥ 50% |
| 关键时点命中 | ≥ 60% |
| 五次 Top-5 Jaccard 中位数 | ≥ 0.65 |
| A/B 方向翻转 | ≤ 10% |
| 顺序 Arm 相对 one-shot 的 Human Top-5 Recall 增量 | ≥ 10 个百分点 |
| 12 Agent 运行时间 | ≤ 20 分钟 |
| 单次模型直接成本 | ≤ 15 美元 |

### 9.2 探索性 A/B 信号

公开 Demo 同时报告 Direction Coverage、Abstention、完整三分类混淆矩阵与 Direction Concordance。只有至少 5 个预注册指标、Direction Coverage ≥70%、且至少 8 份有效真人 A/B 回答时，才计算 Concordance。

Concordance ≥70%可支持进入下一轮 C1 验证；低于 60%触发一次方法审查。这个探索性信号不单独决定四周 Go，也不替代后续样本计划与封存验证。

### 9.3 商业门槛

至少满足：

- 3 位内容决策者中有 2 位认为 Trace 改变了问题优先级；
- 私有试点方愿意提交第二个版本或第二份素材；
- 素材安全方案通过对方最小评审；
- 业务方接受“方向性辅助工具”而非要求确定性预测。

### 9.4 失败后怎么处理

| 失败模式 | 处理 |
| --- | --- |
| Timeline 错，Persona 反应看似合理 | 先修媒体解析，不扩 Panel |
| one-shot 与 sequential 几乎相同 | 取消复杂 Runtime，转内容分析／真人研究加速 |
| Persona 只改变措辞 | 引入真实行为资料或停止分群主张 |
| 校准前差、校准后可用 | 把真人 Anchor 变成必需输入，定位为混合研究 |
| 方向稳定但绝对分数差 | 只保留版本排序与问题发现 |
| 换模型即翻转 | 固定模型并标记适用期，或停止决策用途 |
| 内容团队不看 Trace | 改为“自动生成真人研究片段与问题”，不继续虚拟观众定位 |

### 9.5 三态决策

- **Go**：全部必须门槛与商业门槛通过。
- **Iterate once**：未达 Go，但高于机会判断中的停止线，且失败能归因于一个预注册的可修正原因；只允许一次方法修订，并用新素材或封存数据重测。
- **Stop／Pivot**：触发停止线，或一次修订后仍未达到 Go。不得持续调 Prompt 直到命中已知真人答案。

## 10. 防止规模数字混淆证据

产品和报告执行以下硬规则：

1. UI 分开显示 Persona Pool Records、Deep Traces、Broad Sweep Runs、Projected Records、Stability Runs、Human Participants；
2. 不显示基于 Agent N 的传统显著性星号或置信区间；
3. Panel Weight 标记为 Scenario Weight，不叫 Sampling Weight；
4. 重复运行标记为 Stability Runs；
5. 任何总体外推都必须引用真实抽样框和 Human Anchor；
6. 报告固定包含“共同底模可能产生相关偏差”；
7. Broad Sweep 只用于搜索边缘场景和覆盖缺口，不缩窄真人统计误差；
8. 对外演示可以展示 10k—1M Persona Universe，但必须同时显示实际执行的 Deep／Sweep 数；
9. Population Projection 不逐人生成回答，不能命名为“10,000 位观众已观看”；
10. 决策问题卡优先展示可审查 Deep Trace、反例和 Human Anchor；规模数字不能替代证据。

## 11. 私有试点安全清单

开始前确认：

- 素材所有方、用途和授权；
- 是否允许第三方模型；
- 数据地域与租户；
- no-training 与保留条款；
- 原片、代理、帧、Trace、报告分别保留多久；
- 谁可以下载或分享；
- 是否需要水印；
- 人工审核者是否可以看原片；
- 删除失败的最长补救窗口；
- 日志和备份的删除范围；
- 真人数据同意与匿名化；
- 真人撤回如何传播到分析、Claim、缓存、导出和删除 receipt；
- 项目结束后的删除证明。

## 12. V1 输出包

公开 Demo 最终交付：

1. 可运行的本地报告；
2. 冻结的 Experiment Manifest；
3. Timeline 与 Trace JSON；
4. A/B Variant 对齐；
5. content-only、persona one-shot 与 sequential 对比；
6. 探索性真人盲测编码结果，不包含数值校准；
7. 指标、成本和稳定性表；
8. 失败案例；
9. 权利与署名说明；
10. 私有试点一页说明。

只有这套输出通过门槛，才进入真实客户素材；calibrated 与 alternate-model 对比属于后续研究门。
