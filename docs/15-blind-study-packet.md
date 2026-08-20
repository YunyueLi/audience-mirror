# 真人盲测包与 Human Anchor 闭环

日期：2026-08-21
状态：工程合同与公开素材演练已完成；尚未招募或记录真人参与者

## 结论

Audience Mirror 现在可以从一个或两个已冻结 Timeline 生成结果盲法的人体研究包。它解决的是“如何把 Agent 输出与同任务真人反馈放进同一可核查实验”，不负责招募、替代伦理／法务审核，也不会把计划槽位算成真人样本。

当前公开 Sintel Timeline 已生成 12 个匿名参与者槽位的单版本演练包：`study-a4e080dbee1d`。输出只在本机 `artifacts/`，未进入 Git；`human_participants_completed` 为 0。

## 1. 运行方式

单版本探索性盲测：

```bash
audience-mirror prepare-blind-study \
  --timeline-a timeline.json \
  --participants 12 \
  --experiment-id exp-public-sintel \
  --output artifacts/blind-study/sintel
```

A/B 反平衡盲测：

```bash
audience-mirror prepare-blind-study \
  --timeline-a cut-a.timeline.json \
  --timeline-b cut-b.timeline.json \
  --participants 12 \
  --seed 20260821 \
  --output artifacts/blind-study/trailer-ab
```

A/B 模式要求两个 Timeline 指向同一 `asset_id`，但 `content_hash` 不同。系统用不暴露真实版本名的 `cut-x`／`cut-y` 分配，并把 `ab`／`ba` 尽量均衡到匿名槽位；随机种子和 Timeline 哈希共同决定稳定的 Study ID。

## 2. 三份输出

| 文件 | 使用者 | 内容与边界 |
| --- | --- | --- |
| `study-plan.json` | 研究负责人、审计 | 实验目的、独立盲测、结果盲法、计划槽位、Timeline／素材哈希、量表、预注册指标和停止边界 |
| `participant-pack.json` | 现场执行 | 匿名槽位、暴露顺序和操作说明；不含姓名、联系方式、Consent 内容或真实版本映射 |
| `researcher-key.json` | 独立保管者 | `cut-x`／`cut-y` 到具体 Variant／Timeline 哈希的映射；固定 `internal`、`no_export`，应与参与者包分权保存 |

这三份文件都不等于 Human Anchor。只有参与者完成授权、观看与记录后，才能按 [Human Anchor Schema](../schemas/human-anchor.schema.json) 生成观察；撤回后关联数据必须从分析和导出中失效。

## 3. 默认测量

- 观看过程中的困惑、放弃、摩擦和付费异议时间点；
- 观看后的理解、注意代理量、继续／分享／考虑付费；
- 开放问题：最主要问题、最难忘时刻、缺失背景；
- 双版本研究的 A/B 方向与理由。

眼动、脑电或其他生理数据不进入默认包。若私有试点已有此类数据，应作为独立 Human Anchor 类型，并与自报、访谈编码和行为分别报告。

## 4. 盲法与解盲顺序

1. 冻结素材、Timeline、问题、Agent 输出、Prompt／模型指纹和运行次数；
2. 研究执行者按匿名槽位收集真人记录，不查看 Agent 总结和真实市场结果；
3. 锁定真人响应与 Consent 状态；
4. 由独立保管者解盲版本映射；
5. 导入 Human Anchors，计算 A/B 方向一致性、Top 问题召回、时间点召回和同名代理量误差；
6. 校准集与后续封存验收集分开，不在 8—12 人探索样本上拟合生产校正器。

## 5. 当前还缺什么

1. 公开单版本演练还没有真实参与者，只验证包生成和合同；
2. 下一个高价值输入是一对同源、公开可分享、确有剪辑差异的短视频版本；
3. 私有试点必须先获得素材授权、真人研究授权和数据处理边界；
4. 产品界面尚未提供参与者填写页，当前使用研究包与 Human Anchor JSON 导入；
5. C1 方向校准需要新的封存素材或封存人群，不能在同一探索样本上自证。
