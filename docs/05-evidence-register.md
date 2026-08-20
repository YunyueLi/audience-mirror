# 证据登记册

版本：Evidence Register v0.5
检索截止：2026-08-20

## 1. 用途

本文件记录产品判断依赖的证据、来源等级和限制。它不保存私密逐字稿、真实姓名、未公开客户名称、本地资料路径或受限商业细节。

### 1.1 等级

| 等级 | 定义 | 可支持 |
| --- | --- | --- |
| A1 | 同行评审论文或正式录用的会议论文 | 任务范围内的独立实验结论 |
| A2 | 官方技术文档、许可证或可复核代码 | 实现能力、接口、许可与代码边界 |
| A3 | 方法和数据清楚、尚未同行评审的预印本 | 前沿信号与待复核结论 |
| B | 厂商官方产品、定价、方法和案例 | 产品公开销售什么、目标买方和厂商自述指标 |
| C | 经脱敏的一手访谈、业务经历、体验记录 | 需求发现、工作流、场景优先级 |
| D | 公开访谈、二级报道或行业评论 | 研究方向、公众叙事、案例线索和待验证机制 |
| H | 由多条证据推导、尚未验证 | 产品假设和实验设计 |

厂商自述的客户数、准确率、成本和效果仍为 B 级，不能因为数字具体就升级为 A 级。D 级中的数字、因果归因和产品宣传必须回到论文、代码、官方数据或其他一级来源后才能用于决策。

## 2. 脱敏一手资料

| ID | 脱敏事实 | 等级 | 使用范围 | 不得进入仓库的内容 |
| --- | --- | --- | --- | --- |
| INT-01 | 影视业务决策者描述：制作周期长、发行窗口短、真人预映扩大泄密面，希望获得逐段、人群分层和完整报告 | C | 真实问题、影视首垂直、保密需求 | 人名、公司、影片名、ASR 原文、未公开关系 |
| INT-02 | 同一来源同时强调团队技术尚未 ready，应先用更可验证的 Eval 数据证明能力，再进入电影 | C | Conditional Go、先公开 Demo 后私有试点 | 会议原句、内部计划和人员安排 |
| INT-03 | 潜在合作方最初讨论模拟用户消费决策；后续明确首要兴趣是内容叙事与观看体验的受众反应，不是通用商品消费模拟 | C | 收窄首个垂直、研究问题和产品措辞 | 合作方、行业组合特征、项目名、私聊原文和商业状态 |
| INT-04 | 一个高投入 IP 内容案例经历多年筹备、多轮共创和封闭测试，上线后仍出现扩圈与持续经营问题 | C | 证明真人链路昂贵、间断且不能消除发布风险 | 具体作品、经营数据、未公开问题 |
| INT-05 | 团队具备游戏发行、商业化、用户反馈自动化与 AI 产品试点经验 | C | 游戏第二阶段、购买链路和人群设计 | 公司组合、具体内部项目、指标、同事与客户信息 |
| INT-06 | 一份深度体验报告能把问题定位到场景、路线、角色、声音、空间、服务与传播，并给出人群条件 | C | 定义输出颗粒度和 Trace 下钻 | 原问卷、姓名、场次和未公开观察 |
| INT-07 | 潜在合作方自述曾在内容叙事研究中采集观看过程的眼动、脑电／生理感知与用户反应数据 | C | 潜在 Human Anchor 类型和校准协作方向 | 实验室、研究者、原数据、数据规模和未核验效果 |
| INT-08 | 潜在合作方强调，垂直群体模拟的难点是优质数据结构，需要联系内容结构、脱敏画像、真实行为／运营语境和已验证历史轨迹 | C | 将数据合同、来源和校准放在通用 Persona 生成之前 | 原始画像、运营数据、个人轨迹和合作方 know-how |
| INT-09 | 潜在合作方认为，部分内容突围不能只用生理感受解释，还可能涉及亚文化、戏谑、身份认同、反抗和群体情绪语境 | C／H | 定义“文化解释”研究层和真人编码任务 | 私聊案例、未公开内容和将观点当成已验证因果 |

这些资料只能支持方向性判断，不能证明市场规模、签约意愿或模型有效性。

### 2.1 用户提供的公开文章

2026-08-20，用户提供了三篇公开文章的完整正文。原页受平台限制未能独立抓取；下表的标题—链接对应按用户提供顺序记录，不复制受版权保护的原文。

| ID | 来源 | 可用结论 | 等级 | 不可直接推导 |
| --- | --- | --- | --- | --- |
| PUB-01 | [神经美学研究者年度访谈](https://mp.weixin.qq.com/s/nF880iVvm251ooAbPPfB_g) | 公开研究方向从“感知美”延伸到“评价美”；强调自然情境、个体差异和文化语境，并把 EEG 明确限定为审美体验的一个替代层面 | D／公开专家自述 | 不证明 EEG 能单独解释喜爱、文化认同、传播或市场表现 |
| PUB-02 | [MatrAIx 传播性报道](https://mp.weixin.qq.com/s/Hy-G4O5MoeGInAb40nS7iQ) | “人口规模虚拟用户”对产品与媒体有强传播力，可作为开源声量信号 | D／二级报道 | “83 亿”是 Persona 记录宇宙，不是 83 亿次已运行体验；91.5% 是受控 Persona adherence，不是真人行为预测准确率 |
| PUB-03 | [一部动画电影的爆红归因评论](https://mp.weixin.qq.com/s/TcgjKE8xUnP3vF2gED2mgg) | 提出社交货币、戏谑参与、反工业化情绪、身份与群体语境等候选机制，可转化为可证伪的接受语境实验 | D／行业评论 | 文章的票房数字、七层因果归因和未来市场含义均未经本项目独立验证；不能用已知爆红结果反向证明发布前可预测 |
| PUB-04 | [清华大学：他们用脑电图解码美](https://www.tsinghua.edu.cn/info/1182/117553.htm) | 官方校级报道确认团队在真实演出情境采集脑电、眼动和其他生理数据，同时公开承认自然情境信噪比和文化适配难题 | D／机构官方报道 | 实验存在不等于其指标已可作为产品真值或爆款预测器 |

PUB-01 的方向性主张另用 RES-12A／12B 核对自然情境 EEG 的可测部分和解释边界；PUB-02 的技术数字以 RES-00／00A、OSS-04／05／06 为准；PUB-03 只用于生成研究假设，并用 RES-06D 界定社会影响下的不可预测性。

## 3. 直接竞品与替代方案

### 3.1 影视与长叙事

| ID | 公开证据 | 结论 | 等级 | 限制 |
| --- | --- | --- | --- | --- |
| VEN-01 | [aiScreeningRoom 产品页](https://aiscreeningroom.com/) | 宣称观看整部真实影片、多次独立观看、逐分钟参与度、时间戳证据和版本复测 | B | 邀请制 Beta；公开效果由厂商自证 |
| VEN-02 | [aiScreeningRoom FAQ](https://aiscreeningroom.com/faq/) | 公开完整报告、20—90 分钟处理、真人 CSV Convergence Map、短留存和客户私有云路线 | B | 短片／预告目前只有定性报告；完整校准分数限长片 |
| VEN-03 | [aiScreeningRoom Validation](https://aiscreeningroom.com/validation/) | 35,666 份问卷、42,936 条逐时反应；8 部封存片 AI→Panel ρ=0.762、MAE=0.286 | B | n=8 极小；有高分压缩、低分高估；不能当独立验证 |
| VEN-04 | [Largo Content Insights](https://home.largo.io/largo-content-insights/) | 脚本／视频、数字孪生焦点组、情绪、受众、票房和流媒体预测 | B | 能力和客户效果是官方表述 |
| VEN-05 | [Largo Rapid Insights](https://home.largo.io/largo-rapid-insights/) | 微人群、量化／定性、Persona 对话和文本／视频版本比较 | B | 未公开个体是否按时间顺序体验及校准细节 |
| VEN-06 | [Largo 公开套餐](https://home.largo.io/business-model/) | 内容产品公开年费约 2,500—60,000 美元，包含模拟／合成／真人受众档位 | B | 标价不是成交或留存证据 |
| VEN-07 | [ScriptBook](https://www.scriptbook.io/) | 剧本、受众、角色、类型、票房和市场定位 | B | 准确率为厂商自述；脚本级为主 |
| VEN-08 | [Cinelytic](https://www.cinelytic.com/platform/) | 绿灯、选角、财务、发行和收入预测 | B | 不等于顺序观看与个体 Trace |
| VEN-09 | [Screen Engine/ASI](https://www.screenengineasi.com/solutions/) 与 [iScreeningRoom](https://iscreeningroom.com/) | 真人线上／线下试映、逐时反馈、问卷与保密链路 | B | 作为成熟替代与验证基准，不是 AI 效果证据 |

### 3.2 通用合成用户

| ID | 公开证据 | 结论 | 等级 | 限制 |
| --- | --- | --- | --- | --- |
| VEN-10 | [Synthetic Users](https://www.syntheticusers.com/) 与 [Core Concepts](https://docs.syntheticusers.com/guides/core-concepts) | 多 Agent、OCEAN、Audience、访谈、文件／图片、报告、RAG 和跟进 | B | 官方明确是真人研究的 discovery co-pilot；公开核心仍是访谈 |
| VEN-11 | [火山引擎 AI 虚拟调研](https://www.volcengine.com/docs/85637/1873420?lang=zh) | 人群包、虚拟受访者、典型访谈、问卷回收和报告 | B | Beta／邀测；问卷流程，不是连续视频体验 |
| VEN-12 | [火山引擎用户研究 Agent](https://www.volcengine.com/docs/85637/1861523?lang=zh) | 结合行为流、画像和虚拟调研 | B | 公开说明不能证明推断准确率 |
| VEN-13 | [Atypica](https://atypica.ai/) 与[特赞官方案例](https://www.tezign.com/industries/fonterra) | 中国企业市场已有合成 Persona、AI 访谈与厂商案例 | B | 交付与效果均为厂商口径，未见独立对照 |

### 3.3 广告、注意与情绪

| ID | 公开证据 | 结论 | 等级 | 限制 |
| --- | --- | --- | --- | --- |
| VEN-14 | [明略 AdEff](https://www.mininglamp.com/news/7336/) 与 [Mingjing MLLM](https://www.mininglamp.com/en/card/) | 用广告视频、脑电、眼动和超图模型预测逐时注意／情绪并给建议 | B | 厂商称 89% 等一致性，未独立复核；核心为短广告 |
| VEN-15 | [HMLLM 论文](https://arxiv.org/abs/2407.08150) | 公开研究把广告视频、人口属性、EEG 和眼动连接到主观反应 | A3／预印本 | 数据规模、短视频时长和任务限制其对长叙事外推 |
| VEN-15A | [Kantar LINK AI](https://marketplacesupport.kantar.com/support/solutions/articles/77000525256-what-is-link-ai-for-digital-link-ai) | 官方称可拆解视频帧、图像、音频、语音和文字等至多 20,000 个特征，基于 230k+ 测试和 30M+ 真人交互预测品牌、创意与行为指标 | B | 厂商数据库与效果口径未独立复核；直接挑战营销 A/B 切口 |
| VEN-16 | [Realeyes Human Testing](https://www.realeyesit.com/preview/human-testing-how-it-works/) | 真人摄像头注意、表情、识别和喜好 | B | 广告场景；厂商指标 |
| VEN-17 | [iMotions](https://imotions.com/) | 眼动、GSR、EEG、EMG、ECG 和远程真人研究 | B | 生理测量平台，不是虚拟受众 |
| VEN-18 | [Entropik](https://www.entropik.io/) | 眼动／情绪、真人用研和预测创意 | B | 厂商准确率自述；偏广告与 UX |

### 3.4 游戏

| ID | 公开证据 | 结论 | 等级 | 限制 |
| --- | --- | --- | --- | --- |
| VEN-19 | [modl.ai](https://modl.ai/) | 黑盒视觉、OCR、输入控制、Build、视频／日志和缺陷报告 | B | 官方称更适合结构化交互；目标是测试而非像高手获胜 |
| VEN-20 | [modl.ai FAQ 段落](https://modl.ai/) | 快节奏／时序关键玩法尚不完全支持，高技能测试仍需真人 | B | 厂商自述边界 |
| VEN-21 | [PlaytestCloud](https://www.playtestcloud.com/) 与[功能总览](https://help.playtestcloud.com/en/articles/1148747-everything-you-need-to-know-about-playtestcloud) | 真人玩家录屏、出声思考、问卷、概念／原型、多次和纵向测试 | B | 是真人基准，不是合成 Agent |
| VEN-22 | [腾讯 UDT](https://udt.tencent.com/) 与 [WeTest](https://cloud.tencent.com/product/wetest) | 国内已有游戏自动化、云真机、兼容、性能和安全测试 | B | 质量保障，不是审美／付费受众研究 |
| VEN-23 | [网易 Athena](https://csr.neteasegames.com/news/ai/20230209/38497_1043929.html) | AI 智能体用于游戏平衡性测试 | B | 官方简述，未公开完整产品验证 |

### 3.5 视频理解与创作 Agent

| ID | 公开证据 | 结论 | 等级 | 限制 |
| --- | --- | --- | --- | --- |
| VEN-24 | [火山引擎 Aideo Agent](https://www.volcengine.com/docs/4/1900367?lang=zh) | 厂商公开提供长视频理解、摘要／情节、剧本还原、高光、翻译和剪辑，宣称可处理 90 分钟至 2 小时以上视频 | B | “高精度”及业务效果为厂商口径；不等于受众反应模拟 |
| VEN-25 | [火山视频陪看助手](https://www.volcengine.com/docs/85296/2249538?lang=zh) | 先对总计不超过 10 GB、3 小时的视频建立理解索引，再支持观看中剧情／角色／片段问答 | B | 产品文档不能证明所有问题的时间定位和长程推理准确率 |
| VEN-26 | 用户提供的抖音“AI 解析”产品截图 | 评论区内已经出现自动分析、内容解释、建议追问和对话入口 | D／产品观察 | 只证明可见交互，不能确认后台模型、最大时长或准确率 |
| VEN-27 | [LibTV](https://www.liblib.tv/) 与 [LibTV CLI](https://www.liblib.tv/cli) | 把视频／图像／角色 Skill 接入多种通用 Agent，形成从需求到生成／剪辑的创作工作流 | B／A2 | 创作编排与受众评价是相邻任务；公开资料未见真人校准 |
| VEN-28 | [MiniMax Design](https://design.minimax.io/) | 官方定位为本地多 Agent 创作指挥台，协作完成脚本、视觉、配音和剪辑 | B | 厂商自述的效率数字未独立复核；不是人群实验产品 |
| VEN-29 | [Twelve Labs Analyze](https://docs.twelvelabs.io/docs/guides/analyze-videos) | 面向视频的视觉、语音、声音、画面文字联合分析、索引与结构化响应 | B／A2 | 商业模型和 API；不提供 Persona 顺序体验与真人校准 |

## 4. 引擎与代码边界

| ID | 证据 | 结论 | 等级 | 限制 |
| --- | --- | --- | --- | --- |
| OSS-01 | [MiroFish README](https://github.com/666ghj/MiroFish) | 官方定位为“简洁通用的群体智能引擎，预测万物”；流程为种子信息、图谱、环境、OASIS 双平台模拟、ReportAgent 和交互 | A2／官方自述与代码 | 宽叙事显著扩大用例想象与社区关注，但“预测万物”不等于跨领域有效性已经验证 |
| OSS-02 | [固定审查提交](https://github.com/666ghj/MiroFish/tree/117ed37758cdc96f73b7d5e0d22713c50439695f) | 2026-08-18 审查 main：Twitter／Reddit 脚本和 OASIS 配置明显，没有完整媒体时间轴／连续观看管线 | A2／代码 | 只代表该提交；后续可能变化 |
| OSS-03 | [MiroFish License](https://github.com/666ghj/MiroFish/blob/main/LICENSE) | AGPL-3.0 | A2／代码 | 商业边界需结合具体组合方式评估 |
| OSS-04 | [MatrAIx 固定审查提交](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B/tree/07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9)与[许可证](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B/blob/07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9/LICENSE) | MIT 代码；Persona、Cohort、Survey／Chat／Web／App Task、Trial、Verifier、Telemetry 与报告骨架可复核 | A2／代码 | 0.1.0 早期工程；没有 Media 环境、动态长程记忆或真人预测保证 |
| OSS-05 | [MatrAIx Quickstart](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B/blob/07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9/docs/quickstart.md) | 官方文档明确 `N personas = N trials`，10 trials 约 10 次 LLM 调用；并发改变墙钟时间，不把多 Persona 合成一次独立 Trial | A2／官方代码文档 | 不同环境一次 Trial 的真实调用数不同；未公开统一价格基准 |
| OSS-06 | [MatrAIx Persona 1M 数据卡](https://huggingface.co/datasets/MatrAIx2026/MatrAIx_Persona_1M) | 999,847 条、1,290 维、约 4.17 GB；只校准有限边际，公开卡未声明统一 License，并要求继续遵守底层来源条款 | A2／官方数据卡 | 不能因代码 MIT 推定数据整体可再分发或商用；不是现实人口概率样本 |
| OSS-07 | [Microsoft TinyTroupe](https://github.com/microsoft/TinyTroupe) | MIT；Persona／World、A/B Runner、校验、成本跟踪、图像输入和经验数据验证，可作为小 Panel 实验基线 | A2／代码 | 官方仍标研究／实验工具；图像能力不等于长视频顺序体验 |
| OSS-08 | [OASIS](https://github.com/camel-ai/oasis)、[Concordia](https://github.com/google-deepmind/concordia)、[AgentSociety](https://github.com/tsinghua-fib-lab/agentsociety) | 分别提供大规模社媒、Game Master 社会环境和大规模社会实验；OASIS／Concordia 为 Apache-2.0，AgentSociety 核心 Apache-2.0 且另有 commercial 目录 | A2／代码 | 适合后期 Social Lab；不是首版媒体观看运行时，具体模块仍需逐文件许可核验 |
| LIC-01 | [GNU AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0) | 修改版本经网络交互需向用户提供对应源码 | A2／许可证 | 不是针对本项目的法律意见 |
| LIC-02 | [GNU GPL FAQ](https://www.gnu.org/licenses/gpl-faq.en.html) | 进程、socket、RPC 与数据交换紧密程度会影响是否构成单一组合程序；容器不是决定因素 | A2／官方解释 | 最终由具体事实与法律判断决定 |
| SYS-01 | 受控本地 Foreworld 工程基线 | 当前链路为 DRA→WMG→GAIA→Web，擅长现实证据、世界记忆、关系和分支；GAIA 合同仍在演进 | A2／本地代码与文档 | 不公开原始本地路径与私有档案 |

公开 GitHub 页面在检索日显示 MiroFish 约 71.1k Star、11.1k Fork；这些数字会变化，只用于说明社区关注，不证明产品有效性。

## 5. 学术与技术证据

### 5.1 个体与群体模拟

| ID | 来源 | 主要结果 | 等级 | 产品含义 |
| --- | --- | --- | --- | --- |
| RES-00 | [MatrAIx: Simulating the World with 8.3 Billion Persona Agents](https://arxiv.org/abs/2608.04205) | 8.3B Persona 记录空间、约 1M 公开 Coreset、18,189 个实际 Trial；400 个控制 Trial 的 Persona 行为遵循为 91.5% | A3／2026 预印本 | 证明可复用的规模化 Persona／Eval 基础设施；记录规模不等于执行规模，遵循 Persona 不等于预测真人 |
| RES-00A | [MatrAIx 完整结果](https://arxiv.org/html/2608.04205v1) | 相同 Cohort 在三底模下，涨价犹豫比例为 27.0%—98.3%，付费方案选择为 23.2%—93.9%；22 个跨模型分群排序比较的中位 Spearman 相关为 +0.29 | A3／2026 预印本 | 大 Panel 不能消除共同底模和模型选择偏差；至少需要跨模型敏感性与同任务真人对照 |
| RES-01 | [LLM Agents Grounded in Self-Reports](https://arxiv.org/abs/2411.10109) | 1,052 人；访谈／调查 Agent 达真人复测一致性的 82%—86%，人口统计为 74% | A3／v3 预印本 | 详细真人资料有增量；指标不是影视购买准确率 |
| RES-02 | [Can LLMs Replace Human Subjects?](https://arxiv.org/abs/2409.00128) | 156 实验；主效应 73%—81%，交互 46%—63%；效应量偏大、零效应误报高 | A3／预印本 | 用于筛查方向，不能替代真人统计 |
| RES-03 | [Valid Survey Simulations with Limited Human Data](https://aclanthology.org/2026.acl-long.498/) | 纯合成偏差 24%—86%；配合真人校正后特定任务低于 5% | A1／ACL 2026 | 真人预算优先用于校正与验收 |
| RES-04 | [Synthetic Replacements for Human Survey Data?](https://www.cambridge.org/core/journals/political-analysis/article/synthetic-replacements-for-human-survey-data-the-perils-of-large-language-models/B92267DC26195C7F36E63EA04A47D2FE) | 总体均值有时接近，方差过小、子群和关系结构失真，对 Prompt 与时间敏感 | A1／同行评审 | 1000 Agent 不会自动恢复真实分布 |
| RES-05 | [LLMs Display Social Desirability Biases](https://academic.oup.com/pnasnexus/article/3/12/pgae533/7919163) | 多模型在 Big Five 上向社会期许方向偏移，部分达到约一个真人标准差 | A1／PNAS Nexus | OCEAN Persona 不能直接当行为真值 |
| RES-06 | [Using LLMs to Simulate Multiple Humans](https://proceedings.mlr.press/v202/aher23a) | 可复现部分经典实验，也发现 hyper-accuracy distortion | A1／ICML 2023 | 验证应同时寻找系统性失真 |
| RES-06A | [Identity-group flattening](https://www.nature.com/articles/s42256-025-00986-z) | 四模型、3,200 名真人、16 类身份显示群体误描与组内差异压平，温度不能消除 | A1／Nature Machine Intelligence | Panel 必须检查组内方差，身份标签不能充当真人经验 |
| RES-06B | [Simulated Customers Never Walk Away](https://arxiv.org/abs/2606.20708) | 2,790 段真实销售对话中，模拟客户显著少拒绝、更多犹豫；负向决策保真度不足 | A3／预印本 | 放弃、跳过、不买需要单独校准和召回指标 |
| RES-06C | [Group Conformity](https://aclanthology.org/2025.findings-acl.265/) 与 [Mind the Belief Gap](https://aclanthology.org/2025.findings-acl.948/) | 多 Agent 会向人数优势／更强 Agent 从众，并放大信念一致与错误传播 | A1／ACL Findings 2025 | 独立判断和讨论结果必须分开，Social Lab 需测少数意见保留 |
| RES-06D | [Experimental Study of Inequality and Unpredictability in an Artificial Cultural Market](https://pubmed.ncbi.nlm.nih.gov/16469928/) | 14,341 名真人参与人工音乐市场；社会影响增强时，成功结果更不平等也更不可预测，质量只能部分决定结果 | A1／Science 2006 | 不从内容独立反应直接推导爆款；盲测内容反应与显式注入的社会语境需分开实验 |

### 5.2 长视频与多模态

| ID | 来源 | 主要结果 | 等级 | 产品含义 |
| --- | --- | --- | --- | --- |
| RES-07 | [Gemini Video Understanding](https://ai.google.dev/gemini-api/docs/video-understanding) 与 [Gemini 3.7 Flash](https://ai.google.dev/gemini-api/docs/models/gemini-3.7-flash) | 3.7 Flash 为 2026-08 稳定原生多模态模型，支持视频和结构化输出；Files API 默认视觉 1 FPS，1M 上下文在默认／低分辨率约支持 1／3 小时，快动作可能漏失 | A2／官方文档 | 需要主动局部高帧率复核、成本路由和证据回查；模型效果仍需同一公开素材独立评测 |
| RES-08 | [LongVideoBench](https://arxiv.org/abs/2407.15754) | 小时级视频仍难；更多帧有帮助，长距离与中段事件更难 | A1／NeurIPS 2024 | 不能靠极稀疏帧与一次 Prompt |
| RES-09 | [Video-MME-v2](https://arxiv.org/abs/2604.05015) | 最新前沿模型与人仍有明显差距；事实聚合与时间错误会传递到高层推理 | A3／2026 预印本 | Timeline 事实层必须独立校验 |
| RES-10 | [MovieChat](https://openaccess.thecvf.com/content/CVPR2024/papers/Song_MovieChat_From_Dense_Token_to_Sparse_Memory_for_Long_Video_CVPR_2024_paper.pdf) | 双记忆与稀疏表示支持长视频理解 | A1／CVPR 2024 | 支持工作／长期记忆和选择性回查 |
| RES-11 | [SimTube](https://arxiv.org/abs/2411.09577) | 视频、音频、Persona 可生成可信、有帮助的模拟评论 | A3／预印本 | 证明相邻可行；其摘要后评论是必须比较的基线 |
| RES-12 | [Audience immersion validation](https://pmc.ncbi.nlm.nih.gov/articles/PMC10113978/) | 反应时、心率和皮电与自报沉浸有关系 | A1／同行评审 | 内容情绪、模拟情绪与真人生理信号必须分开 |
| RES-12A | [Delta-band audience brain synchrony tracks engagement with live and recorded dance](https://www.sciencedirect.com/science/article/pii/S2589004225011836) | 三场现场舞蹈演出的最终 EEG 样本为 59 人；δ 频段观众脑同步与连续参与相关，且现场共同观看时更高 | A1／iScience 2025 | 论文同时指出，脑同步可反映对共同刺激的相似神经加工／共同注意，不必然是共享情感体验 |
| RES-12B | [Inter-subject correlation of EEG and behavioural responses reflects time-varying engagement with natural music](https://doi.org/10.1111/ejn.16324) | 在自然音乐的单次暴露中，EEG 与连续行为响应的跨被试相关可追踪随时间变化的参与 | A1／European Journal of Neuroscience 2024 | 不同测量捕捉体验的不同方面；不得把某一生理或神经指标升格为完整审美评价 |
| RES-13 | [LongVideoAgent](https://github.com/longvideoagent/LongVideoAgent) | Master Agent 协调 grounding 与 vision Agent，先定位问题相关片段，再提取定向视觉观察 | A2／官方代码；ACL 2026 | 为问答设计，不是连续观众体验；仍需验证具体许可证与模型依赖 |
| RES-14 | [Deep Video Discovery](https://github.com/microsoft/DeepVideoDiscovery) | 用 deep-research 式工具搜索理解超长视频，先做全局浏览，再检索局部证据 | A2／MIT 代码；A3 预印本 | 目标是问答；全局描述仍可能丢失细节 |
| RES-15 | [Active Video Perception](https://openaccess.thecvf.com/content/CVPR2026F/html/Wang_Active_Video_Perception_Iterative_Evidence_Seeking_for_Agentic_Long_Video_CVPRF_2026_paper.html) | plan–observe–reflect 主动取证，在五个长视频基准上以更少推理时间和 token 改善准确率 | A1／CVPR 2026 Findings | Benchmark 增益不能直接外推到影视审美或人群预测 |
| RES-16 | [LensWalk](https://openaccess.thecvf.com/content/CVPR2026/papers/Li_LensWalk_Agentic_Video_Understanding_by_Planning_How_You_See_in_CVPR_2026_paper.pdf) | 推理器动态决定时间范围与采样密度，支持广域扫描、局部精看和跨时刻验证 | A1／CVPR 2026 | 不提供 Persona、群体聚合和真人校准 |
| RES-17 | [VideoHV-Agent](https://github.com/Haorane/VideoHV-Agent)、[VideoMind](https://videomind.github.io/)、[LongVT](https://github.com/agentic-practice/agentic_longvideo) | 当前长视频 Agent 共同采用假设—验证、工具定位和多轮观察，而非一次均匀采样 | A2／官方代码与项目页 | 项目成熟度、许可证和运行成本需逐一固定 Commit 复核 |
| RES-18 | [Qwen2.5-VL](https://qwenlm.github.io/blog/qwen2.5-vl/) 与 [Seed1.8](https://seed.bytedance.com/en/blog/official-release-of-seed1-8-a-generalized-agentic-model) | 两家模型团队均公开长视频理解与时间定位／局部高帧率能力 | B／厂商技术自述 | 官方 Benchmark 不能代替同一公开素材的独立横评 |
| RES-13 | [InfiniBench](https://aclanthology.org/2025.emnlp-main.984/) | 平均 53 分钟电影／剧集；最佳模型 grounding 47.1%，并会利用标题等元数据猜答案 | A1／EMNLP 2025 | 加去片名／去标题对照，防止预训练记忆冒充观看 |

### 5.3 界面系统与组件基础

这些来源只用于界面工程和交互行为，不构成 Audience Mirror 预测有效性的证据。

| ID | 来源 | 可复核事实 | 等级 | 本项目使用方式 |
| --- | --- | --- | --- | --- |
| UI-01 | [Ice Works Showcase](https://github.com/MegD1/Ice-works-showcase) | 公开源码展示粒子凝图、悬停粒子影、编辑式信息编排和液态转场；仓库说明源码 MIT，但 `public/` 资产不随源码许可开放 | A2／代码与仓库说明 | 只吸收“证据从噪声中显影”的交互原则；不复制资产、字体、shader 或品牌表达 |
| UI-02 | [Radix Primitives Accessibility](https://www.radix-ui.com/primitives/docs/overview/accessibility) | 官方说明组件遵循 WAI-ARIA 预期，并处理常见键盘、焦点和标签行为 | A2／官方文档 | 作为 Tabs、Dialog、Tooltip、Select 等复杂控件的行为参考 |
| UI-03 | [Base UI Quick Start](https://base-ui.com/react/overview/quick-start) | 官方提供无样式、单包、可 tree-shake 的 React primitives，覆盖 Drawer、Toast、Field、Tabs 等组件 | A2／官方文档 | 未来 React 化的默认候选之一；当前原生基线不新增依赖 |
| UI-04 | [React Aria Getting Started](https://react-aria.adobe.com/getting-started) | 官方组件暴露交互状态，覆盖 Focus、Press、Selection、Virtualizer 与国际化能力 | A2／官方文档 | 高密度集合、表格和复杂键盘交互的候选基础 |
| UI-05 | [Motion Accessibility](https://motion.dev/docs/react-accessibility) | 官方提供 reduced-motion 全局策略与 hook，并建议减少大幅 transform、自动播放和视差 | A2／官方文档 | 当前原生实现直接遵守系统偏好；未来迁 React 时保持同一契约 |
| UI-06 | [Observable Plot](https://observablehq.com/plot/) 与 [Visx](https://visx.airbnb.tech/) | 两者提供可组合的可视化基础；Plot 用 mark、scale、transform、facet 组织图形，Visx 提供低层 React 视觉组件 | A2／官方项目页 | 仅在时间轴／群体分布超出当前 SVG 基线后评估，不因“图表更多”而引入 |

## 6. Demo 素材

| ID | 来源 | 权利与用途 | 等级 |
| --- | --- | --- | --- |
| DEMO-01 | [Sintel Sharing](https://durian.blender.org/sharing/) | 项目成果 CC BY 3.0；需遵守署名、片尾和商标排除 | A2／官方许可 |
| DEMO-02 | [Sintel About](https://durian.blender.org/about/) | 约 15 分钟、连续叙事、开放制作资产 | A2／官方 |
| DEMO-03 | [Sintel Download](https://durian.blender.org/download/) | 多分辨率影片、音轨和多语言字幕 | A2／官方 |
| DEMO-04 | [LIRIS-ACCEDE](https://liris-accede.ec-lyon.fr/) | 可作为连续情绪方向的第二基准，使用前需遵守数据集 EULA | A2／数据集 |

## 7. 中国市场扫描结论

公开检索已经发现：

- 长短视频主观反应与广告前测：明略 AdEff；
- 企业虚拟受访者与行为研究：火山引擎 DataAgent、Atypica；
- 剧本／内容 AI 分析：多家内容平台和工具；
- 游戏自动化与平衡：腾讯 WeTest／UDT、网易 Athena；
- 传统真人 Panel、眼动和神经科学服务。

截至检索日，未在公开资料中发现同时明确提供“长叙事顺序观看、稳定 Persona Panel、个体可审计 Trace、讨论／传播前后分离、真人校准”的中国成型产品。这只能表述为**公开检索未发现**，不能表述为“中国没有竞品”；大型平台可能有未公开内部系统或定制服务。

## 8. 已知冲突与更新

1. 早期交接材料引用了 154 个实验、主效应约 76%、交互约 47%。论文 2025 年 v3 已更新为 156 个实验和 73%—81%／46%—63%，本仓库采用当前版本。
2. 早期交接将影视虚拟观众视为较新空位。Largo、aiScreeningRoom、明略 AdEff 和通用合成用户产品表明该判断需要收窄。
3. MiroFish 社区数字随时间快速变化；Star／Fork 只在本文件记录检索日快照。
4. 厂商“准确率”使用不同目标、样本和定义，不能横向排行。
5. 用户补充的 MatrAIx 证明“大 Persona 池”和“产品化任务运行时”可直接复用，但其论文与代码同时证明 Persona 数、Trial 数和人口代表性必须分开。本仓库因此新增 Deep Trace、Broad Sweep 与 Population Projection 三层，而不再把 12—18 Persona 写成产品总体规模。
6. MatrAIx 代码 MIT 与 Persona 1M 数据使用边界不是同一结论；在数据卡补充统一许可证或逐来源审计完成前，不把 Persona 1M 直接再分发或默认用于商业项目。
7. 用户提供的 MatrAIx 文章把“83 亿 Persona 记录”传播为“83 亿数字人上线”。本仓库继续采用论文、代码和数据卡口径，不因二级报道改变 Pool／Trial／Projection 的分层。
8. 真实演出 EEG 研究支持“接受情境会改变体验”，不支持“脑同步等于共同喜爱”。生理、自报、访谈编码与实际行为仍分轨验证。
9. 公开文化现象评论提供了社交货币、戏谑与参与式观看等假设；MusicLab 实验则表明社会影响会增加文化市场的不可预测性。产品因此做语境敏感性和机制实验，不从内容单独反应承诺爆款预测。

## 9. 仍需补齐的研究

### P0

- 在不对外联系的前提下继续观察 aiScreeningRoom、Largo 和 AdEff 的公开 Demo／报告颗粒度；
- 与首个授权方确认安全、真人基准和真实决策对象；
- 用同一公开视频问题集实测 Gemini、Seed／方舟、Qwen 本地与 Twelve Labs 的事实、时间定位、成本和数据边界；
- 比较原生整片 one-shot、固定采样和主动局部复核的增量；
- 对固定 MatrAIx Commit 完成 Adapter Spike、Smoke、依赖清单和 Persona 数据来源审计；
- 实测 12 个 Deep Trace、约 100 个 Broad Sweep 与 10k 无 LLM 投影的调用量、耗时和边际成本。

### P1

- 获取 5—8 位内容决策者对 Trace Inspector 的盲评；
- 研究中文叙事与本地人群的公开校准集；
- 评估本地／VPC 多模态模型质量与成本；
- 验证拒绝、放弃和不购买状态是否系统性不足。
- 用一个可设置信息截止时间的公开文化案例，比较盲测内容反应与显式社会语境注入，并检查是否泄漏已知市场结果。

### P2

- 游戏 PV、皮肤、Battle Pass 与商城原型的真人对照；
- 群体讨论中的从众、错误传播和关系校准；
- 完整长片与快节奏 3D 游戏的运行边界。

## 10. 引用规则

后续文档引用本登记册时：

- A1／A2／A3 需分别保留论文、官方实现和预印本的来源性质与任务范围；
- B 级写“厂商公开提供／宣称”，不写“已经证明有效”；
- C 级只写脱敏事实，不带来源身份；
- D 级只用于提出方向、案例线索或可证伪机制；技术数字和因果结论回到一级来源；
- H 级必须配实验或买方访谈；
- 不把两个不同厂商的“准确率”放在同一排名表；
- 不引用私密原文或绝对路径。
