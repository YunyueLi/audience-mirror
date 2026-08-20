# Audience Mirror｜观众镜

> 在现实发生前，先让一万种人走一遍。

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache--2.0-blue.svg)](LICENSE)
[![CI](https://github.com/YunyueLi/audience-mirror/actions/workflows/ci.yml/badge.svg)](https://github.com/YunyueLi/audience-mirror/actions/workflows/ci.yml)

**Developer Preview `v0.2.0-alpha.1`** — 真实视频纵向切片与开放合同预览；以 GitHub Pre-release 形式发布，但不是经过真人验证的预测产品。

Audience Mirror 是一个开放的“现实之前人群实验层”：让异质 Persona 按顺序进入内容、软件、游戏或社会情境，形成体验、判断、选择并相互影响；每条结论都能回到环境状态、个体 Trace、实验条件和真人校准。这里的 Audience 指面对某项内容、产品、规则或世界的目标人群，不只指影视观众。

Audience Mirror is an open, pre-reality population experimentation platform.
It simulates how heterogeneous people experience, judge, choose, and influence
each other across multimodal environments, while keeping every result linked
to inspectable traces, conditions, and human calibration status.

**影视／IP 是 Audience Mirror 的首个验证环境，不是项目总边界。** 它先用内容体验验证多模态顺序体验与证据链；平台内核保持 Environment、Population、Experience、Decision、Interaction、Trace 和 Calibration 的通用抽象。当前状态为 **Conditional Go（有条件推进）**：值得用 2—4 周完成首个可运行且能与真人结果盲测的参考环境，尚不足以承诺准确预测票房、收入或现实人群比例。

基线日期：2026-08-20。

## 当前可运行基线

仓库现在有两条可运行路径。

零 Key 工程基线使用合成 Timeline 和 Persona Fixture，跑通：

```text
10k Persona Pool
  → 12 个 Deep Persona / 48 条可哈希校验 Trace
  → 100 个 Broad Sweep
  → 10k 条零逐人 LLM Projection
  → 自包含证据报告
```

真实视频路径已跑通：本地 MP4 解码与音轨抽取、关键帧／场景差分、Timeline、Environment Contract、Future-blind 顺序体验、个体 Trace、校准指标和交互式证据工作台。Gemini 原生整片视频 Adapter 与 Claude Code 结构化顺序推理 Adapter 已实现，但实际远程调用分别需要显式素材授权与有效的本地认证。本轮没有可用 Gemini Key，Claude Code OAuth 已过期，所以不能把 Provider 代码写成“真实模型结果已验证”。

两条路径都只证明工程合同和下钻链路可以工作，不证明虚拟用户能预测真人。

工作台中的校准入口可先加载 `fixtures/public-demo/human-anchors.synthetic.json` 检查合同、撤回排除、A/B 方向和指标展示。该文件全部为合成记录，只是界面 Fixture，不是“真人校准已经完成”的证据。

### 直接运行

要求 Python 3.11 或更高版本。零 Key Demo 无运行时依赖：

```bash
git clone https://github.com/YunyueLi/audience-mirror.git
cd audience-mirror
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e .
audience-mirror demo
```

安装真实媒体解析和本地工作台：

```bash
python -m pip install -e '.[media,web]'

# 把有权处理的本地视频转成可校验 Timeline
audience-mirror ingest-video /path/to/public-or-authorized.mp4 \
  --output artifacts/my-video

# 输出与媒体无关的 Environment Contract
audience-mirror environment-spec \
  --timeline artifacts/my-video/timeline.json \
  --output artifacts/my-video/environment.json

# 打开交互工作台；默认只监听本机
audience-mirror serve --host 127.0.0.1 --port 8765
```

可选的原生视频模型路径必须显式授权远程处理：

```bash
python -m pip install -e '.[gemini]'
export GEMINI_API_KEY='...'
audience-mirror analyze-video /path/to/authorized.mp4 \
  --timeline artifacts/my-video/timeline.json \
  --allow-remote-processing
```

模型驱动的 Persona 顺序体验使用本机已认证的 Claude Code CLI，并默认限制 16 次逐事件调用：

```bash
audience-mirror run-agent \
  --timeline artifacts/my-video/timeline.json \
  --persona-count 2 \
  --max-model-calls 16 \
  --max-budget-usd 0.25
```

机密／受限素材默认拒绝发送到公有 Gemini Adapter；任何远程模型使用前仍须确认授权、保留、训练使用、地域和删除策略。

输出位于 `artifacts/public-demo/`：

- `report.html`：可筛选、可下钻的本地报告；
- `run-manifest.json`：数量口径、运行指纹、成本和限制；
- `deep-traces.json`：符合 Trace v0.1 的不可变事件流；
- `broad-sweep.json` 与 `population-projection.json`：分别标记非完整观看与零 LLM 投影；
- `matraix-media-contract.json`：合同级 Adapter 输出，不执行或下载 MatrAIx。

验证与测试：

```bash
audience-mirror validate timeline fixtures/public-demo/timeline.json
python -m unittest discover -s tests -v
```

如果已有外部 MatrAIx Checkout，可检查固定版本和许可边界：

```bash
audience-mirror matraix-doctor --repo /path/to/MatrAIx
```

代码使用 [Apache License 2.0](LICENSE)。本仓库不捆绑第三方代码、模型权重、Persona 数据集或媒体素材；具体边界见 [THIRD_PARTY.md](THIRD_PARTY.md)。

## 一页结论

| 决策 | 当前建议 |
| --- | --- |
| 项目命题 | 在现实发生前，对不同人群如何体验、评价、选择和相互影响进行可回放、可校准的模拟实验 |
| 平台边界 | 通用 Experiment Core + 可插拔 Media／Web／App／Game／Social Environment；不同时开发全部环境 |
| 首个环境 | Media：影视／剧集／IP 内容及营销素材的发布前观看体验测试 |
| 首个客户 | 有目标人群数据、多个素材版本和既有真人研究记录的内容平台或 IP 商业化团队 |
| 通用差异 | 顺序经历、长期记忆、个体 Trace、环境版本对齐、条件语境、群体互动与真人校准 |
| 第一个 Demo | Blender 开放短片《Sintel》全片体验 Trace，加同源两版预告片 A/B |
| 工程形态 | 逐步抽象通用实验合同；先实现 Media Environment，并适配 MatrAIx、Foreworld／GAIA 等开放运行时 |
| 规模方式 | 大 Persona 池用于检索；12—32 个 Deep Trace、100—1,000 个 Broad Sweep、10k+ 低成本投影分别报告 |
| 产品形态 | 暂按“开放内核倾向”设计；用社区复用与私有试点两类信号决定全开源、open-core 或闭源 |
| 游戏方向 | 第二阶段先测 PV、皮肤、Battle Pass、商城 UI、玩法录像和可点击原型；完整 Build 试玩后置 |
| 明确禁区 | 不用 Agent 数量伪造统计显著性，不把模型分数写成真实注意力或确定性营收预测 |

Audience Mirror 所在的影视垂直已经有强竞品：[aiScreeningRoom](https://aiscreeningroom.com/) 在 2026 年 Beta 中宣传完整影片、多次观看、逐分钟反馈、时间戳证据和真人 Panel 校准；[Largo Content Insights](https://home.largo.io/largo-content-insights/) 也已支持脚本／视频、数字孪生焦点组、情绪分析和影视预测。这个事实说明首个垂直存在采购类别，也说明“虚拟观众”本身不能承担整个平台的差异与叙事。

[MiroFish](https://github.com/666ghj/MiroFish) 的宽叙事和 [MatrAIx](https://github.com/MatrAIx-ai/MatrAIx-Persona-8B) 的多环境结构提供了另一层启示：平台可以面向广泛人群实验，同时用一个具体环境先证明技术与有效性。详见[平台命题](docs/00-platform-thesis.md)。

## 文档地图

0. [平台命题](docs/00-platform-thesis.md)：通用愿景、三层结构、环境边界、开源／商业结构与本轮纠偏。
1. [机会判断](docs/01-opportunity-assessment.md)：平台机会、首个垂直、买方、竞争格局、证据与假设。
2. [产品需求文档](docs/02-prd.md)：定位、首客、工作流、输出、下钻体验、边界与非目标。
3. [技术架构与 MVP](docs/03-architecture-and-mvp.md)：模型无关管线、时间轴、状态机、Trace、校准、安全和 2—4 周范围。
4. [验证计划](docs/04-validation-plan.md)：公开 Demo、私有试点、盲测指标、成功门槛和停止条件。
5. [证据登记册](docs/05-evidence-register.md)：公开来源、证据等级、私密资料脱敏方式与未决研究。
6. [决策与下一步](docs/06-recommendation.md)：仓库选择、品牌表达、阶段路线与应立即制作的 Demo。
7. [开源生态与规模策略](docs/07-open-ecosystem-and-scale-strategy.md)：MatrAIx 核验、开源复用、三层执行成本和产品形态门槛。
8. [规模与开源策略决策报告](docs/reports/2026-08-19-scale-open-strategy/report.html)与 [QA 记录](docs/reports/2026-08-19-scale-open-strategy/source-notes.md)：可独立阅读的自包含 HTML 与验证说明。
9. [可运行工程基线](docs/08-implementation-baseline.md)：CLI、三层运行时、MatrAIx 合同、输出制品和下一步实现顺序。
10. [产品上下文](PRODUCT.md) 与 [设计系统](DESIGN.md)：固化用户、定位、无障碍要求、视觉 token 和证据交互规则。
11. [2026-08-20 新增外部输入复核](docs/09-external-input-review-2026-08-20.md)：记录脱敏一手信号、数字分身交叉检查、三篇公开文章及对接受语境与产品边界的净修正。
12. [视频理解与视频 Agent 技术版图](docs/10-video-understanding-landscape-2026-08-20.md)：复核抖音 AI 解析、火山 Aideo、LibTV、MiniMax Design、原生模型、长视频 Agent 论文与开源项目，并给出 build／buy 决策。
13. [v0.2 本地发布候选状态](docs/11-release-candidate-status-2026-08-20.md)：精确列出可发布面、不可声称项、首个 Benchmark 与仍需授权的对外动作。
14. [Schema 状态](schemas/README.md)、[Environment](schemas/environment.schema.json)、[Trace](schemas/trace.schema.json)、[Timeline](schemas/timeline.schema.json) 与 [Human Anchor](schemas/human-anchor.schema.json)：供原型直接实现和验收。

## 研究口径

- **A1 级**：同行评审论文或正式录用的会议论文。
- **A2 级**：官方技术文档、许可证或可复核代码。
- **A3 级**：方法清楚但尚未同行评审的预印本。
- **B 级**：厂商官方功能、定价与客户范围，只证明“它公开这样销售”，不自动证明效果。
- **C 级**：经脱敏的一手访谈、业务经历与体验记录，用于发现需求和设计场景，不外推市场规模。
- **D 级**：公开访谈、二级报道或行业评论，用于发现方向与可证伪机制，技术数字和因果结论必须回到一级来源。
- **H 级**：需要实验验证的产品或技术假设。

仓库没有复制任何私密逐字稿、真实人名、未公开客户信息或本地资料路径。

## Audience Mirror 首个验证需要确认的三个高价值问题

1. 私有试点的第一个真实决策对象，能否优先选“预告片／营销短视频 A/B”？它比完整粗剪更容易在四周内形成版本差异与真人盲测闭环。
2. 授权方能否提供同一素材的既有真人问卷／访谈编码，或支持按预注册指标制定真人样本计划？10—20 人只适合探索性问题发现，不能同时承担三分群、双版本、校准和封存验收。
3. 未来试点是否要求境内私有化／VPC 和素材不出域？这会直接决定模型路由、媒体存储和成本方案。

在这三个问题确认前，最合理的投入是完成 Audience Mirror 公开 Demo、通用 Environment Contract、MatrAIx Adapter Spike 与验证工具链。大规模 Persona 由开放数据与索引提供，完整体验按信息价值分层运行；不扩招，也不采购大规模算力。
