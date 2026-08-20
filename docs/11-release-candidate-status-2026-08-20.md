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
- Human Anchor 校准指标；
- 可运行的本地证据工作台；
- 20 项测试全部通过，包括真实 MP4 音画编码／解码、错版 Human Anchor 拒绝和 Environment／Trace 合同；
- 桌面／移动浏览器完成真实上传、H.264／AAC 原视频回放、WAV 证据、时间片 seek、顺序运行、证据下钻和逐次远程授权检查；
- Persona Pool 未建立时显示“—”，运行后与 Deep Persona 分开报告；
- 发布审查发现的时间轴键盘语义、44px 目标、深色主按钮对比度和非颜色流程状态已修复；
- 视频模型、Agent、产品和开源技术版图已经补入证据登记册。

## 发布时必须写清楚

1. `v0.2.0-alpha.1` 是本地 MVP／开发者预览，不是人群预测服务；
2. 仓库不包含媒体、Persona 1M、模型权重、密钥或真人数据；
3. 默认 Demo 不调用外部模型；
4. Gemini Adapter 是可运行代码路径，但本轮没有 Key，因此没有发布可声称的真实 Provider 结果；
5. Claude Code Adapter 已尝试，因本机 OAuth 过期没有完成真实模型 Session；
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

## 发布执行记录

2026-08-20，项目发起人明确授权在 GitHub 账号 `YunyueLi` 下创建公开仓库 `audience-mirror`，并执行初始提交、推送、`v0.2.0-alpha.1` Tag 与 Pre-release 发布。公开授权只覆盖本仓库中的脱敏文档、合成 Fixture 和代码，不覆盖私密逐字稿、未公开客户素材、真人数据或受限媒体。
