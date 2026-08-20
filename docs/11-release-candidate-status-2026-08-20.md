# Audience Mirror v0.2 开发者预览发布状态

日期：2026-08-20
建议：**可以立即做公开代码预览；不应把远程模型效果或真人预测能力写入发布承诺。**

## 已达到的发布面

- Apache-2.0 独立仓库结构、README、贡献、安全、第三方边界、CI 和 Issue 模板；
- 零 Key 可复现 Demo；
- 真实本地视频 Ingest 与可验证 Timeline；
- 通用 Environment Contract；
- 确定性顺序体验与模型顺序体验 Adapter；
- Gemini 原生整片视频 Adapter；
- Codex 最多 12 张时间戳证据帧的视觉基线；
- Human Anchor 校准指标；
- 可运行的本地证据工作台；
- 48 项测试全部通过，包括真实 MP4 音画编码／解码、磁盘实验恢复、证据帧调用上限与长片时间分层、人工字幕选择／解析／融合、语义 Timeline 压缩、远程授权门、模型终止语义、错版 Human Anchor 拒绝和 Environment／Trace 合同；
- 桌面／移动浏览器完成真实上传、H.264／AAC 原视频回放、WAV 证据、时间片 seek、顺序运行、证据下钻和逐次远程授权检查；
- Persona Pool 未建立时显示“—”，运行后与 Deep Persona 分开报告；
- 发布审查发现的时间轴键盘语义、44px 目标、深色主按钮对比度和非颜色流程状态已修复；
- Schema、公开 Fixture 和工作台资源已进入 wheel；从源码目录外安装后，CLI 校验与零成本 Demo 通过，CI 已加入独立 wheel Smoke；
- 视频模型、Agent、产品和开源技术版图已经补入证据登记册。

## 发布时必须写清楚

1. `v0.2.0-alpha.2` 是本地 MVP／开发者预览，不是人群预测服务；
2. 仓库不包含媒体、Persona 1M、模型权重、密钥或真人数据；
3. 默认 Demo 不调用外部模型；
4. Gemini Adapter 是可运行代码路径，但本轮没有 Key，因此没有发布可声称的 Gemini 原生整片结果；Codex 证据帧基线已经产生真实视觉结果，但它没有接收视频或音轨，不能冒充原生完整视频理解；
5. Codex CLI Adapter 已用 GPT-5.6 Sol／xhigh 在公开合成 Timeline 完成 1 Persona × 4 Event，在 2 张真实解码帧生成的语义 Timeline 上完成 1×2，并在《Sintel》全片的 12 事件 Timeline 上完成 1×12；它验证工程闭环，不验证真人预测；
6. 10k Persona Pool／Projection 不等于 10k 次完整体验，更不等于 10k 真人；
7. 所有注意、情绪、理解和购买输出在真人校准前均为预测代理量。

合成 Human Anchor Fixture 只用于演示合同、撤回排除和界面，不属于真人数据或校准效果证据；不同 Experiment／Timeline／素材哈希会被拒绝。

## 公开发布后的第一个迭代

不是继续加产品页功能，而是发布一个可复核的公开视频 Benchmark：

- 一段 8—15 分钟公开叙事视频；
- 25—40 个人工标注的音画、OCR、时间定位和长程问题；
- 至少两种视频 Provider；
- 原生整片、固定采样与 Agentic 局部复核三种策略；
- 2—6 个 Deep Persona 顺序体验；
- 完整的调用数、耗时、成本、失败、证据与不确定性。

完成它以后再开始公开真人 Anchor 招募或授权私有试点。

## alpha.2 发布更新

`v0.2.0-alpha.2` 已补齐 URL-first 来源层：公共视频直链、YouTube／Bilibili／抖音页面 Adapter、本地文件兜底、公共直链 DNS 固定与逐跳重定向检查、共享下载／合并预算、失败 staging 清理和路径／参数脱敏 Source Receipt。真实联网验证覆盖 Qwen 公共 MP4 直链和 Blender Foundation YouTube 页面；后者在没有系统级 FFmpeg CLI 的环境中通过 PyAV 合并分离音视频。平台 Adapter 仍经由 `yt-dlp` 联网，不宣称与固定 IP 的公共直链具有同等级别的出站隔离；当前版本只面向默认回环地址上的单用户原型。单机实验现在能从脱敏磁盘制品恢复，最近实验、视频、Timeline、Trace、校准与深链接已通过真实重启。完整本地测试及桌面／移动端检查通过。

同一 working tree 进一步补齐稠密镜头证据到最多 16 个语义体验事件的重建、覆盖缺口披露、Codex／Claude 双 CLI Reasoner、逐次远程授权、`abandon` 终止和 Run Manifest。Codex 证据帧基线首次跑通真实解码画面到 2 个语义事件，再由 1 个模型 Persona 形成 2 条可验证 Trace；随后从官方 YouTube 页面导入 888 秒《Sintel》全片，本地保留 148 张证据帧，按时间分层选择 12 张并生成 12 个语义事件，再由 1 个模型 Persona 完成 12 次顺序体验调用。事实层耗时 127,779 ms，顺序体验聚合模型时延 252,507 ms，所有 Trace 通过合同校验。平台字幕路径另以同一官方页面真实验证：选中 1,556-byte 简中人工 WebVTT，解析 26 个 cue，并能按时间作为独立证据附加到事件；未调用自动翻译，也不把字幕写成已核验 ASR。当前长片 Session 仍是固定帧、无原生音轨理解、单 Persona、未校准的工程基线。Gemini 原生视频分析仍因缺 Key 未执行。

## 发布执行记录

2026-08-20，项目发起人明确授权在 GitHub 账号 `YunyueLi` 下创建公开仓库 `audience-mirror`，并执行初始提交、推送、`v0.2.0-alpha.1` Tag 与 Pre-release 发布。公开授权只覆盖本仓库中的脱敏文档、合成 Fixture 和代码，不覆盖私密逐字稿、未公开客户素材、真人数据或受限媒体。
