# 可运行工程基线

版本：Implementation Baseline v0.2.0-alpha.1
日期：2026-08-20
状态：Local vertical slice runnable；remote providers key-gated

## 1. 这一版能完成什么

仓库已经从“合成媒体报告”进入真实视频纵向切片：有权处理的本地视频可以被真正解码、抽帧和提取音轨，转成可校验 Timeline；同一 Timeline 可以导出通用 Environment Contract，交给确定性工程 Runtime 或结构化模型 Runtime 逐事件运行；聚合结果可下钻到具体 Persona、Trace、时间点、原视频和声音；真人锚点可以在严格版本对齐后生成校准诊断。

这仍是实验原型。没有真人数据时，注意、情绪、理解和购买数值均为预测代理量；任何 Agent 数量都不计入真人样本量。

## 2. 能力状态

| 模块 | 已实现 | 本轮实际验证 | 未完成／边界 |
| --- | --- | --- | --- |
| 真实视频 Ingest | PyAV 解码、技术元数据、SHA-256、定时／场景差分帧、JPEG 证据、单声道 16 kHz WAV | 单测真实编码并解码含 AAC 音轨的 MP4；浏览器实际打开 H.264／AAC 视频，原视频与 WAV 均支持 Range，时间片可 seek | 还没有生产级转码、断点续传和病毒扫描 |
| 多模态事实层 | Gemini Files API 原生整片 Adapter；结构化事件／观察；Timeline Fusion；显式远程许可；敏感分级拒绝；删除尝试 | 权限门和缺 Key 错误路径已验证；Provider 合同和融合单测通过 | 本轮没有 Gemini Key，未执行真实远端推理；ASR、OCR、说话人和局部高 FPS 复核器待实现 |
| Environment Contract | Observation、Action、Transition、终止条件、成本和版本化 Schema；Media Timeline Adapter | Schema、语义验证与 Future-blind step 单测通过 | 当前只有 Media 参考 Adapter；Web／App／Game 尚无代码示例 |
| 顺序体验 | 模型无关 `JsonReasoner`；Claude Code CLI Adapter；每 Persona × Event 一次结构化调用；过去记忆；未来泄漏阻断 | Fake Reasoner 完整跑通并校验哈希 Trace；确定性 Runtime 浏览器端跑 6 Persona／18 Trace | Claude Code OAuth 过期，真实模型 Session 未执行；Social Lab 未实现 |
| Trace | 事件哈希链、Timeline／Observation 引用、状态、记忆、动作、模型／Prompt／Persona／Seed／成本指纹 | Trace 语义校验与证据下钻通过 | 还没有数据库级 append-only store 和分布式幂等 |
| 真人校准 | Human Anchor 校验、实验／Timeline／素材哈希强对齐、撤回排除、Top 问题召回、时间点召回、代理量 MAE、A/B 方向一致性 | 合成 Fixture、错版拒绝、撤回排除与 UI 展示通过；A/B 只读取 `ab_choice` 量表 | 只有计算器，没有真人数据、校准参数或现实预测声明 |
| 工作台 | 上传与权利、逐次远程授权与政策确认、能力状态、原视频／声音、时间轴、规模分账、聚合→Persona→Trace、校准视图、移动端布局 | 浏览器真实上传／回放／seek、运行、下钻、远程许可拒绝；主时间片 44px、键盘导航和 378px 无溢出通过 | 无登录、持久数据库、协作和生产部署 |
| Persona 规模 | 10k 本地合成 Pool、Deep Persona、Broad Sweep、Population Projection 分层 | 原有确定性测试通过 | MatrAIx 1M 数据未导入；数据许可证／来源仍需审计 |

## 3. 代码地图

```text
src/audience_mirror/
├── environment.py        # 通用 Environment Contract 与 Media Adapter
├── media/
│   ├── ingest.py         # 真实本地视频解析
│   └── fusion.py         # 原生模型结果 → Timeline
├── models/
│   ├── base.py           # 可替换视频 Provider 合同
│   └── gemini.py         # Gemini Files API 原生视频 Adapter
├── reasoning.py          # JsonReasoner 与 Claude Code CLI Adapter
├── model_runtime.py      # Future-blind 模型顺序体验
├── calibration.py        # Human Anchor 对齐与校准诊断
├── webapp.py             # FastAPI 本地实验工作台
├── runtime.py            # 确定性 Deep／Sweep／Projection 基线
└── validation.py         # Timeline／Trace 语义门禁

web/                      # 证据工作台前端
schemas/environment.schema.json
schemas/timeline.schema.json
schemas/trace.schema.json
schemas/human-anchor.schema.json
```

## 4. 运行

```bash
python3 -m venv .venv
source .venv/bin/activate
python -m pip install -e '.[media,web,dev]'

audience-mirror ingest-video /path/to/authorized.mp4 --output artifacts/my-video
audience-mirror environment-spec \
  --timeline artifacts/my-video/timeline.json \
  --output artifacts/my-video/environment.json
audience-mirror serve --host 127.0.0.1 --port 8765

python -m unittest discover -s tests -v
```

原生远程视频模型和模型顺序体验是可选能力，分别需要 `.[gemini]` + `GEMINI_API_KEY`，以及有效认证的 `claude` CLI。默认不发送素材；每次远程动作必须同时确认实际 Provider／模型和当期数据政策，确认不会跨调用持久生效。

## 5. 成本与规模门

视频事实层按素材／版本解析一次，可被多 Persona 复用；顺序体验成本近似：

```text
model calls = Deep Persona count × visible Event count
```

CLI 和 Web 模型模式默认硬限制 16 次调用，并有美元预算参数。10k Persona Pool 和 10k 本地 Projection 不代表 10k 人完成了整片模型体验；Manifest／界面必须分别报告 Pool、Deep Persona、Trace Event 和 Human Participant。

## 6. 发布前仍需完成

1. 用公开授权视频真实跑至少一个原生 Provider，并保存无敏感信息的模型／成本／时间定位制品；
2. 恢复 Claude Code 认证或接第二个 JsonReasoner，完成至少 2 Persona × 4 Event 的真实模型顺序体验；
3. 完成同一公开问题集的 Gemini、国内模型、开放权重模型横评；
4. 加入 ASR／OCR 和 Agentic 局部复核，以覆盖音频、文字和快动作；
5. 用公开素材招募／获取同任务真人 Anchor，再允许出现任何“校准后”表述；
6. 用户明确授权后再创建远程公共仓库、提交、推送和打 Tag。

## 7. 安全与许可

- Apache-2.0 只覆盖本仓库自有代码；第三方模型、MatrAIx Persona 数据和媒体素材各自审查；
- MiroFish AGPL 代码没有并入本仓库；
- `artifacts/`、媒体、密钥、私密数据和日志默认不进入 Git；
- 公有 Gemini Adapter 默认拒绝 `confidential`／`restricted`；
- 素材权利、远程处理授权和真人同意是三个独立开关。
