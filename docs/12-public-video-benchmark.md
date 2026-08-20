# Audience Mirror 公开视频 Benchmark

日期：2026-08-20

当前题集：`sintel-public-dev-v0.1`
状态：**可用于开发，不可用于发布稳定模型排名**

## 1. 为什么先建 Benchmark

Audience Mirror 的高层 Persona 反应依赖视频事实层。如果事实、时间定位或证据回查不可靠，后续的注意、困惑、理解、分享和购买代理量都会继承错误。因此第一套公开验证先回答一个更基础的问题：不同视频理解策略能否在同一开放影片上给出正确答案，并指回正确时间证据。

这套 Benchmark 不测真人偏好，也不把答题准确率外推为票房、收入或传播预测。

## 2. 资产与权利

- 影片：Blender Foundation《Sintel》；
- 公开页面：https://www.youtube.com/watch?v=eRsGyueVLvQ；
- 官方许可：CC BY 3.0；
- 署名：© Blender Foundation | durian.blender.org；
- 仓库只保存题目、时间窗、公开页面、内容哈希和署名，不提交影片、音轨、字幕文件或证据帧。

题集固定到 888,041 ms、SHA-256 `8d42f955c7a46f5ce117ac3493b3355d074b04c3f5dce7e009951ba07567817f` 的本地导入版本。Provider 使用其他编码版本时，必须先确认时间轴对齐。

## 3. 题目结构

共 31 道公开开发题：

| 类别 | 数量 | 主要能力 |
| --- | ---: | --- |
| 视觉事实 | 10 | 场景、物体、角色姿态、局部细节和不确定性 |
| 片尾 OCR | 5 | 标题、机构、城市和名单成员 |
| 人工字幕 | 5 | 物体、动机、寻找对象、名字和地点 |
| 时间定位 | 5 | 首次／末次出现、对白、场景转换和片尾区间 |
| 时间顺序 | 3 | 跨段场景与细粒度对白顺序 |
| 跨事件理解 | 3 | 任务对象、环境迁移和片尾视觉母题 |

每题包含：稳定 ID、问题、答案类型、参考答案、一个或多个证据时间窗、证据模态、来源、评分策略、难度和标签。

## 4. 标注成熟度

当前 `annotation_status` 为 `single_maintainer_draft`：

- 一位维护者依据公开影片逐段观看、YouTube 人工中英字幕和本地时间戳帧建立答案；
- 没有第二位独立标注者；
- 没有计算跨标注者一致性；
- 对话没有逐字复核说话人、口型和翻译一致性；
- 所有题目公开，存在训练污染和标题泄漏风险。

只有在第二位人工标注者独立回答、冲突裁决、时间窗对齐和变更冻结完成后，才能把状态升级为 `double_checked` 或 `frozen`。模型或 Agent 复核不能替代这里的第二位真人。

## 5. 评分

`audience-mirror benchmark score` 分开计算：

1. **Answer accuracy**：每题 0／1，宏平均，并按类别拆分；未回答计 0。
2. **Temporal localization**：时间题的预测区间与参考区间 IoU；命中还允许题目显式登记的中心点容差。
3. **Evidence grounding**：Provider 提交的证据区间与任一参考证据的最佳 IoU 和命中率。

Predictions 文件最小结构：

```json
{
  "schema_version": "audience-mirror.video-benchmark-predictions/v0.1",
  "benchmark_id": "sintel-public-dev-v0.1",
  "run": {
    "provider": "example",
    "model_id": "example-model",
    "strategy": "native_full_video"
  },
  "predictions": [
    {
      "question_id": "visual-01-setting",
      "answer": "雪山山谷",
      "evidence": [{"t_start_ms": 45000, "t_end_ms": 70000}]
    }
  ]
}
```

运行：

```bash
audience-mirror benchmark validate fixtures/benchmarks/sintel-public-dev-v0.1.json
audience-mirror benchmark score \
  --benchmark fixtures/benchmarks/sintel-public-dev-v0.1.json \
  --predictions /path/to/provider-predictions.json \
  --output artifacts/benchmark/report.json
```

## 6. 第一轮对比矩阵

| 策略 | 目的 | 必须记录 |
| --- | --- | --- |
| 原生整片 | 检验模型端到端视频、音频和长上下文能力 | Provider、模型、采样说明、调用数、时延、token、成本、失败 |
| 固定采样 | 建立低成本可复现下限 | 帧数、时间选择算法、是否含字幕／音频、未覆盖窗口 |
| 主动局部复核 | 检验 plan–observe–reflect 的增量 | 初扫成本、复核次数、局部帧率、证据选择轨迹 |

每种策略还要做去片名／去标题对照，避免模型用训练记忆或页面元数据代替观看。公开开发题用于迭代；最终比较另留隐藏题，不在模型运行前暴露答案。

## 7. 下一步验收门

1. 第二位真人独立标注并完成冲突裁决；
2. 接至少两个视频 Provider；
3. 每种策略至少重复三次，报告答案稳定性和证据漂移；
4. 发布完整 Predictions、Report、成本、耗时、错误和模型指纹；
5. 在事实层达到预注册门槛后，才将同一 Timeline 交给 2—6 个 Deep Persona 做顺序体验。

## 8. 首轮工程基线

2026-08-20，GPT-5.6 Sol／xhigh 完成一次 `semantic_timeline_text` 运行。输入只有 12 个语义事件及其视觉／OCR 观察和 31 道公开问题；原视频、音轨、证据帧、题目参考答案和片名均未提供。一次模型调用耗时 50,306 ms，返回 31 条 prediction，其中 10 条为明确弃答。

宏平均为 64.5%：视觉事实 100%、片尾 OCR 100%、对白 0%、时间定位 40%、时间顺序 33.3%、跨事件 66.7%。21 条非弃答预测都提交了时间证据，证据命中率为 100%，最佳区间 IoU 均值为 0.9747；该高值主要反映输入事件已经带时间边界，不能当作原始视频定位能力。

完整解释见[首轮基线记录](13-sintel-timeline-baseline-2026-08-20.md)。

2026-08-21 又完成无字幕和人工字幕两个条件各三次重复。无字幕宏平均为 62.4%，范围 58.1%—64.5%；人工字幕宏平均为 81.7%，范围 80.6%—83.9%。对白均值由 0% 升到 86.7%，时间顺序由 33.3% 升到 100%，但视觉事实由 96.7% 降到 80%；这证明字幕对当前语义 Timeline 的对白与顺序信息有明确增量，也说明融合输入会改变非目标类别，仍需分模态消融。详见[稳定性与字幕增量记录](14-sintel-stability-and-caption-baseline-2026-08-21.md)。
