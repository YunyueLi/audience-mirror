# 可运行工程基线

版本：Implementation Baseline v0.2.0-alpha.2 working tree
日期：2026-08-20
状态：Local vertical slice runnable；remote providers key-gated

## 1. 这一版能完成什么

仓库已经从“合成媒体报告”进入真实视频纵向切片：有权处理的公开视频链接或本地文件可以被真正下载／读取、解码、抽帧和提取音轨，转成可校验 Timeline；同一 Timeline 可以导出通用 Environment Contract，交给确定性工程 Runtime 或结构化模型 Runtime 逐事件运行；聚合结果可下钻到具体 Persona、Trace、时间点、原视频和声音；真人锚点可以在严格版本对齐后生成校准诊断。

这仍是实验原型。没有真人数据时，注意、情绪、理解和购买数值均为预测代理量；任何 Agent 数量都不计入真人样本量。

## 2. 能力状态

| 模块 | 已实现 | 本轮实际验证 | 未完成／边界 |
| --- | --- | --- | --- |
| 视频来源 Resolver | URL-first；公共直链逐跳解析并固定到已验证公共 IP；YouTube／Bilibili／抖音 allowlist Adapter；平台选定媒体端点公共地址检查；共享下载／合并工作区预算与 30 分钟时限；直播和无法确认时长的视频拒绝导入；已声明时长上限 4 小时；路径与参数脱敏 Source Receipt；PyAV 本地音视频合并 | Qwen 公共直链 36,698,404 bytes／177.96 秒／12 个事件；Blender Foundation YouTube 页生成 161,192,038-byte MP4，含 1 个视频与 1 个音频流 | `yt-dlp` 元数据解析不受完整任务硬超时保护，且其本身仍是外部网络信任边界，只适用于默认回环地址上的单用户原型；登录、Cookie、付费、地区和平台访问控制不绕过；尚无断点续传、任务队列、容器级出站策略或生产域名策略 |
| 真实视频 Ingest | PyAV 解码、技术元数据、SHA-256、定时／场景差分帧、JPEG 证据、单声道 16 kHz WAV | 单测真实编码并解码含 AAC 音轨的 MP4；浏览器实际打开 H.264／AAC 视频，原视频与 WAV 均支持 Range，时间片可 seek；《Sintel》全片解码 21,313 帧，保留 148 张证据帧与 16 kHz 单声道音频 | 还没有生产级转码、断点续传和病毒扫描 |
| 多模态事实层 | Gemini Files API 原生整片 Adapter；Codex 最多 12 张带时间戳证据帧的视觉基线；长片按时间分层选取邻近证据帧；平台人工 WebVTT 单轨下载、解析与事件时间重叠；结构化事件／观察；稠密镜头证据重建为最多 16 个语义体验事件；Provider 覆盖缺口显式保留；远程许可与敏感分级拒绝 | Codex 在公开合成 H.264 视频的 2 张真实解码帧上用 26,693 ms 生成 2 个画面／文字事件；《Sintel》用按时间分层的 12 张证据帧在 127,779 ms 内生成 12 个语义事件；同一官方页面真实获取 1,556-byte 简中人工字幕并解析 26 个时间 cue；完整覆盖、缺口、20→≤16 事件压缩与字幕融合单测通过 | Codex 路径是固定抽帧基线，不是原生完整视频理解；平台字幕不保证逐字、说话人与完备性；本轮没有 Gemini Key；ASR、说话人和主动局部高 FPS 复核器待实现 |
| Environment Contract | Observation、Action、Transition、终止条件、成本和版本化 Schema；Media Timeline Adapter | Schema、语义验证与 Future-blind step 单测通过 | 当前只有 Media 参考 Adapter；Web／App／Game 尚无代码示例 |
| 顺序体验 | 模型无关 `JsonReasoner`；Codex CLI／Claude Code CLI Adapter；每 Persona × Event 一次结构化调用；过去记忆；未来泄漏阻断；`abandon` 后终止 | GPT-5.6 Sol／xhigh 已完成公开合成 Timeline 的 1×4 Session；另在 2 帧语义 Timeline 上完成 1×2／34,571 ms，在《Sintel》12 事件 Timeline 上完成 1×12／252,507 ms；全部 Trace 均通过哈希与合同校验 | 模型反应仍是未校准代理量，不证明真人预测；Claude 交叉运行、重复稳定性与 Social Lab 未实现 |
| Trace | 事件哈希链、Timeline／Observation 引用、状态、记忆、动作、模型／Prompt／Persona／Seed／成本指纹；计划／实际调用、会话结局和预算 Run Manifest | 真实 Codex Session、提前放弃和 Run Manifest 单测通过 | 还没有数据库级 append-only store 和分布式幂等 |
| 真人校准 | Human Anchor 校验、实验／Timeline／素材哈希强对齐、撤回排除、Top 问题召回、时间点召回、代理量 MAE、A/B 方向一致性 | 合成 Fixture、错版拒绝、撤回排除与 UI 展示通过；A/B 只读取 `ab_choice` 量表 | 只有计算器，没有真人数据、校准参数或现实预测声明 |
| 工作台 | 粘贴链接优先、上传兜底、权利确认、逐次远程授权与政策确认、Source Receipt、最近实验与本地深链接、原视频／声音、时间轴、规模分账、聚合→Persona→Trace、校准视图、固定视口三栏与移动端单面板 | 真实服务重启后恢复 8 个本地实验；414.2 秒实验恢复 155 个事件、6 个 Persona 与 657 条 Trace；《Sintel》恢复 12 个语义事件与 12 条模型 Trace；已校准实验恢复 2 位真人口径；桌面／移动端无水平溢出 | 当前是单机文件持久化；无登录、多用户数据库、协作、异步任务进度和生产部署 |
| Persona 规模 | 10k 本地合成 Pool、Deep Persona、Broad Sweep、Population Projection 分层 | 原有确定性测试通过 | MatrAIx 1M 数据未导入；数据许可证／来源仍需审计 |
| 安装与资源 | Wheel 携带 Schema、公开 Fixture 与工作台静态资源；只读资源与可写 Workspace 分离；支持 `AUDIENCE_MIRROR_WORKSPACE` | 在源码目录外安装 wheel 后，Timeline／Trace 校验与零成本 Demo 均通过；CI 新增独立 wheel Smoke | 还没有正式 PyPI 发布、签名制品或 SBOM |

2026-08-20 联网验证源包括 [Qwen2-VL 公开视频文件](https://qianwen-res.oss-cn-beijing.aliyuncs.com/Qwen2-VL/space_woaudio.mp4)、[Blender Foundation 的 Big Buck Bunny YouTube 页面](https://www.youtube.com/watch?v=aqz-KE-bpKQ)与 [Sintel 官方 YouTube 页面](https://www.youtube.com/watch?v=eRsGyueVLvQ)。《Sintel》的复用边界另见[官方许可说明](https://durian.blender.org/sharing/)；本仓库没有提交影片。数值是当次工程运行记录，不代表平台可用性 SLA，也不授予对其他素材的再分发权。

## 3. 代码地图

```text
src/audience_mirror/
├── environment.py        # 通用 Environment Contract 与 Media Adapter
├── media/
│   ├── ingest.py         # 真实本地视频解析
│   ├── source.py         # 安全视频链接 Resolver 与平台 Adapter
│   ├── subtitles.py      # 有上限的平台字幕解析与时间对齐
│   └── fusion.py         # 原生模型结果 → 证据保持的稀疏语义 Timeline
├── models/
│   ├── base.py           # 可替换视频 Provider 合同
│   ├── gemini.py         # Gemini Files API 原生视频 Adapter
│   └── codex_frames.py   # 有上限的证据帧视觉基线
├── reasoning.py          # JsonReasoner、Codex CLI 与 Claude Code CLI Adapter
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
python -m pip install '.[media,web,dev]'

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

1. 用公开授权视频真实跑至少一个原生整片 Provider，并保存无敏感信息的模型／成本／时间定位制品；
2. 在《Sintel》公开语义 Timeline 上完成至少 2 Persona × 4 Event 的 Codex／Claude 交叉稳定性运行，并报告重复运行差异；
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
