# 视频理解、视频 Agent 与 Audience Mirror 技术版图

版本：Research Note v1.0
检索截止：2026-08-20
结论性质：官方产品能力、论文／代码证据与产品推导分开记录

## 1. 结论

用户的判断成立：视频理解已经越过“抽几帧写摘要”的阶段。原生视频模型、长视频索引、主动取证 Agent、视频创作 Agent 和平台内的陪看问答都已形成可用能力。Audience Mirror 不应自研一个基础视频模型，也不能把“能看懂视频”本身当成壁垒。

真正需要自建的是视频理解之上的实验层：把同一份经校验的多模态事实时间轴，交给稳定且异质的 Persona 按暴露顺序体验；保存个体状态、记忆、动作、反例和成本；最后与同任务真人数据对齐。现有产品已经较好解决“视频里发生了什么”“帮我找片段／改片／生成内容”，公开资料仍很少同时覆盖“不同人群会如何理解、评价和决策”“每条群体结论如何回到个体 Trace”“与真人误差如何呈现”。

因此采用三层技术策略：

1. **全局事实底图**：调用可替换的原生视频模型或企业视频理解服务，一次处理音画、对白、OCR、事件和时间戳；
2. **Agentic 局部复核**：遇到快动作、争议、低置信或具体研究问题时，主动裁剪相关区间，提高采样密度并回看原始像素／音频；
3. **人群实验运行时**：Persona 只能看到当前及过去事件，形成可哈希的顺序 Trace；大 Persona 池、深度体验和真人样本分别记账。

## 2. 用户观察的三个产品信号

### 2.1 抖音“AI 解析”

用户提供的产品截图显示，抖音评论区已出现“AI 解析”入口，能先分析视频，再给出内容解释、相关追问和对话输入。这是重要的产品信号：普通用户已经开始把“点开任意视频即可问 AI”视为平台级体验，不再需要单独上传、切换工具或理解模型参数。

截图能证明产品界面和任务形态，不能单独证明其后台模型、最大视频时长或长程准确率。可由火山引擎官方资料交叉确认的能力包括：

- [Aideo Agent](https://www.volcengine.com/docs/4/1900367?lang=zh) 将视频云工具和多模态模型组合成对话式 Agent，厂商宣称可处理 90 分钟、甚至 2 小时以上的视频；视频理解输出摘要、标题、关键词和情节分析；剧本还原输出人物、分镜、对白和结构化 JSON；
- [视频陪看助手](https://www.volcengine.com/docs/85296/2249538?lang=zh) 支持导入总计不超过 10 GB、3 小时的视频，通过大模型建立视频索引，并在观看中回答剧情、角色和片段问题；
- [AI 数据湖视频算子](https://www.volcengine.com/docs/6492/2192001?lang=en) 提供视觉、字幕、剧情分析、时间戳剪辑决策和电影／长录像的自适应处理。

这些是 B／A2 级官方能力说明，足以支持“国内头部平台已系统化建设长视频理解”的判断，不足以支持“它已经准确理解所有长片”或“它能预测观众反应”。Audience Mirror 应借鉴其无缝入口、先索引后追问和时间点回跳，不复制其通用陪看助手定位。

### 2.2 LibTV／Liblib

[LibTV](https://www.liblib.tv/) 和 [LibTV CLI](https://www.liblib.tv/cli) 把视频、图像、角色和创作 Skill 接入 Kimi Code、MiniMax Agent、Trae 等通用 Agent 工作流。其公开产品主线是“导演／创作编排”：从需求、脚本、分镜、素材到生成和交付，以 Skill 复用生产流程。

它对 Audience Mirror 的启示有两点：

- 视频能力应成为 Agent 可调用的工具，而不是封闭页面中的一次性 Prompt；
- 产品需要可安装、可组合、可分享的 Environment／Experiment Pack，才能形成开源扩散。

它不是目前最直接的竞品：公开定位解决如何制作和修改视频，Audience Mirror 解决哪些人为什么在何处理解、喜欢、拒绝、放弃或传播，以及这些判断是否与真人一致。未来可以把 Audience Mirror 的证据结论输出成 LibTV 可消费的剪辑修改任务。

### 2.3 MiniMax Design

[MiniMax Design](https://design.minimax.io/) 官方定位为本地多 Agent 创作指挥台：多个 Agent 协作完成脚本、视觉、配音和剪辑，面向创作者、工作室与品牌。它证明模型厂商正在直接把多模态模型、工具调用和并行 Agent 做成完整产品，而不只销售 API。

这同样是创作侧产品。它会压缩“做一版视频”的成本，却会增加“如何从大量版本中判断哪一版值得上线”的需求。Audience Mirror 与其更可能形成上下游关系：Design 生成变体，Mirror 用冻结 Panel 和同任务真人锚点比较变体。

## 3. 可直接采购或适配的视频能力

| 类别 | 代表能力 | 公开支持 | 适合放在 Audience Mirror 的位置 | 主要限制 |
| --- | --- | --- | --- | --- |
| 原生通用视频模型 | [Gemini Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding)／[Gemini 3.7 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash) | 音画视频输入、描述／分段／问答／时间戳；Files API 面向 10 分钟以上长视频；3.7 Flash 支持视频和结构化输出 | 首个真实 Provider Adapter、全局事实底图 | 官方说明默认视觉采样可能遗漏快动作；公有 API 的保留、地域和训练条款需按素材确认 |
| 国内原生／Agentic 模型 | [Seed1.8](https://seed.bytedance.com/en/blog/official-release-of-seed1-8-a-generalized-agentic-model) | 厂商报告长视频推理、VideoCut 局部高帧率复核、GUI Agent | 国内模型 Benchmark 与未来方舟 Adapter | 公开结果主要为厂商评测；接入和私有素材边界需另审 |
| 企业视频智能 | [Twelve Labs](https://docs.twelvelabs.io/docs/guides/analyze-videos) | 视觉、语音、声音和画面文字联合分析、索引、结构化响应 | 长视频搜索／检索基线、第二 Provider | 商业服务；不是 Persona 体验或真人校准层 |
| 开放权重 VLM | [Qwen2.5-VL](https://qwenlm.github.io/blog/qwen2.5-vl/) | 官方宣称可理解一小时以上视频并定位片段；支持本地部署 | 私密素材与成本可控路线 | 需要自管采样、推理资源和基准；官方演示不等于业务准确率 |
| 视频云 Agent | [火山 Aideo](https://www.volcengine.com/docs/4/1900367?lang=zh) | 长视频理解、剧本还原、高光、翻译、剪辑 | 中国市场产品基准或企业服务 Adapter | 厂商闭环；公开资料没有人群模拟与真人校准 |
| 创作 Agent | [LibTV](https://www.liblib.tv/)、[MiniMax Design](https://design.minimax.io/) | 需求到脚本／分镜／生成／剪辑的多 Agent 编排 | 下游修改任务或上游版本生成 | 创作效率不等于受众判断有效性 |

MVP 不需要同时接完所有服务。当前仓库先实现 Gemini Files API 的模型无关 Adapter 合同；下一批 Provider 按“境内可用、长视频时间戳质量、保留政策、成本、结构化输出”跑同一基准再选择。

## 4. 头部论文与开源项目说明了什么

### 4.1 单次长上下文并不够

[LongVideoBench](https://arxiv.org/abs/2407.15754) 和 [LVBench](https://arxiv.org/abs/2406.08035) 表明小时级视频的长距离依赖、位于中段的稀疏事件和细粒度时间定位仍然困难。即使上下文窗口容得下视频，均匀降采样也会把决定性片段稀释掉。

[Gemini 官方文档](https://ai.google.dev/gemini-api/docs/video-understanding)支持直接传视频和时间戳问答，但同时给出采样边界。这意味着“原生整片输入”应作为全局底图，不应成为唯一证据源。

### 4.2 主动寻找证据是当前主线

以下项目都把视频视作可反复观察的环境，而不是一次压缩成摘要：

- [LongVideoAgent](https://github.com/longvideoagent/LongVideoAgent)：Master Agent 协调 grounding 与 vision Agent，先定位相关片段，再提取定向视觉事实；
- [Deep Video Discovery](https://github.com/microsoft/DeepVideoDiscovery)：面向超长视频的 deep-research 式问答，先建立全局描述，再以工具搜索局部证据；
- [Active Video Perception](https://openaccess.thecvf.com/content/CVPR2026F/html/Wang_Active_Video_Perception_Iterative_Evidence_Seeking_for_Agentic_Long_Video_CVPRF_2026_paper.html)：以 plan–observe–reflect 循环主动决定看什么、何时看、看哪里；
- [LensWalk](https://openaccess.thecvf.com/content/CVPR2026/papers/Li_LensWalk_Agentic_Video_Understanding_by_Planning_How_You_See_in_CVPR_2026_paper.pdf)：让推理器动态控制时间范围和采样密度；
- [VideoHV-Agent](https://github.com/Haorane/VideoHV-Agent)：先形成假设，再通过多个观察者验证；
- [VideoMind](https://videomind.github.io/) 与 [LongVT](https://github.com/agentic-practice/agentic_longvideo)：把定位、推理和工具调用串成可训练的 Agent 路径；
- [DrVideo](https://github.com/Upper9527/DrVideo)：先将视频转成可检索长文档，再循环补取缺失帧证据。

共同设计模式是：粗粒度浏览 → 形成问题／假设 → 时间定位 → 局部高密度观察 → 充分性判断 → 继续或停止。Audience Mirror 应把这个循环用于事实层复核和争议定位，不让每个 Persona 从头重复解码整片。

### 4.3 记忆和特征层可复用，但不是人群模拟

[MovieChat](https://openaccess.thecvf.com/content/CVPR2024/papers/Song_MovieChat_From_Dense_Token_to_Sparse_Memory_for_Long_Video_CVPR_2024_paper.pdf)证明稀疏记忆对长视频对话有价值；[VideoPrism](https://github.com/google-deepmind/videoprism) 和 [Neptune](https://github.com/google-deepmind/neptune) 提供通用视频表征／理解研究资产。这些适合做检索、相似镜头和低成本特征层。

Audience Mirror 仍需另存 Persona 的情节记忆、角色记忆、个人解释和决策状态。模型的“视频记忆”回答发生了什么，Persona 记忆回答这个人以怎样的先验记住了什么、误解了什么、接下来如何行动。

## 5. Persona 规模与成本：必须纠正的口径

[MatrAIx](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B)非常适合复用，但“83 亿 Persona”指可生成／筛选的 Persona 记录空间。论文公开的是约 100 万质量过滤 Coreset、18,189 次实际 Trial 和 400 次 Persona adherence 受控实验；仓库文档明确实际运行需要模型 Key，`N personas = N trials`。并发可降低墙钟时间，不能把 10,000 个独立体验折叠成一次模型调用。

成本应拆成四层：

| 层 | 10k 规模是否可行 | 边际成本来源 | 当前做法 |
| --- | --- | --- | --- |
| Persona Universe／检索 | 可行 | 存储、索引、筛选 | 可接 MatrAIx 1M，但先审数据许可和来源 |
| Population Projection | 可行 | 本地规则／小模型／向量计算 | 零逐人 LLM，明确 `completed_experience=false` |
| Broad Sweep | 可到数百／数千 | 压缩后的问卷／摘要推理 | 只做方向扫描，不冒充完整观看 |
| Deep Sequential Experience | 首版 6—32 | Persona × Event × 模型调用，加记忆与复核 | 设调用、预算、失败硬上限；只对高信息价值人群运行 |

视频事实层只需对同一素材解析一次，确实可以被许多 Persona 复用；但 Persona 在每个事件的独立状态更新仍有真实推理成本。后续可用批处理、缓存、蒸馏和本地小模型降低成本，不能先假定成本为零。

## 6. Audience Mirror 的实现决策

### 6.1 本轮已经落地

- PyAV／Pillow 本地视频解码、时长与 SHA-256、关键帧／场景差分采样、音轨抽取；
- Gemini 原生整片视频 Adapter：显式远程授权、机密素材拒绝、结构化结果、用量／延迟与远端删除尝试；
- 稠密镜头证据到最多 16 个语义体验事件的重建，Provider 未覆盖时段显式保留；
- 通用 Environment Contract 及 Media Timeline Adapter；
- Future-blind 顺序体验运行时：每个 Persona 只看到当前事件、既有状态和过去记忆；
- Codex CLI／Claude Code 双结构化 Reasoner、逐次远程授权和可复现 Run Manifest；
- 个体 Trace 哈希链、模型／Prompt／Persona／Seed／成本指纹；
- Human Anchor 校准：实验／Timeline／素材哈希强对齐、Top 问题召回、时间点召回、代理量 MAE、A/B 方向一致性和撤回排除；
- 可交互工作台：真实视频导入、原视频／声音回放与时间片 seek、时间轴、聚合→个体→证据下钻、真人校准和规模分账。

### 6.2 仍需通过真实基准后才能说“支持”

- Gemini 远程整片调用已实现，但本轮没有可用 Key，未执行真实远端推理；
- GPT-5.6 Sol／xhigh 已在公开合成 Timeline 完成 1 Persona × 4 Event 的真实顺序 Session；尚未在真实视频语义 Timeline 上运行，也没有跨模型稳定性结果；Claude Code 认证有效，但当次团队额度尚未重置；
- ASR、OCR、说话人分离、局部高 FPS 复核器和 Ark／Aideo／Qwen Provider 尚未实现；
- 没有真人数据时，界面的注意、情绪、理解、购买仍只能叫预测代理量；
- 当前校准器能运行合同和指标，不代表已经得到可靠校准系数。

## 7. 下一轮基准，不再做产品页比较

使用一段公开授权的 8—15 分钟叙事视频和一个 30—90 秒快动作／强 OCR 片段，冻结 25—40 个可人工核查问题：

1. 事件和角色：谁在何时做了什么；
2. 时间定位：答案片段是否覆盖人工标注区间；
3. 对白／OCR／声音：仅视觉、仅音频和跨模态问题；
4. 长程理解：前后呼应、角色目标变化和因果；
5. 快动作漏失：全局默认采样与局部高 FPS 的增益；
6. 成本：素材解析一次、单 Persona 完整体验、每新增 Persona 的增量；
7. 稳定性：相同模型／Prompt／Seed 的重复运行和跨模型敏感性。

对 Gemini、Seed／方舟、Qwen 本地和 Twelve Labs 至少跑两种；产品选择依据同一问题集的证据准确率、时间定位、成本、延迟和数据边界，不依据官网 Demo 的观感。

## 8. 产品边界

Audience Mirror 的扩圈来自通用 Environment Contract，不来自把首个界面做成“预测一切”。Media 是第一块可验证的 Environment；同一套 Population、Sequential Experience、Trace 和 Calibration 可以后续接 Web、App、Game、Commerce 和 Social。

首版对外表达仍应具体：**上传一段视频，让不同人按顺序看完，并把每条群体判断下钻到时间点和个体轨迹。** 这能被看懂、能演示、能与真人比较。平台级扩展通过代码合同和新增 Environment Pack 展示，而不是在第一个 Demo 中同时实现所有行业。
