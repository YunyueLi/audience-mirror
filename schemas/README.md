# Schema 状态

本目录的可执行合同：

- environment.schema.json：模型无关的环境能力、Observation／Action／Transition 与安全边界；
- timeline.schema.json：单一素材版本的分层多模态时间轴；
- trace.schema.json：单一模拟 Agent Session 的不可变事件；
- human-anchor.schema.json：与模拟 Trace 分离的匿名真人观察。

`environment.schema.json` 已有 Media Timeline 参考实现和语义校验；Web／App／Game Environment Adapter 仍待实现。Asset／Rights、Audience／Persona、Experiment Manifest、Claim Ledger 和 Calibration Profile 目前仍是领域设计，不是完整可执行合同。进入私有试点前必须补成 Schema、正例 fixture、反例 fixture 和迁移规则。

## JSON Schema 以外的语义校验

实现必须另写校验器检查：

1. ID 唯一、外键存在、父子时间包含和 Timeline 无环；
2. t_end 大于 t_start，Evidence 落在 Asset 时长内；
3. Frozen Timeline 必须有 Rights Manifest；
4. Alignment 指向精确的对方 Timeline ID、版本与哈希；
5. 同一 Session 的 sequence 唯一、只追加、哈希链连续；
6. event_hash 与规范化载荷一致，idempotency_key 不产生重复业务事件；
7. review.override 的前值与被覆盖事件一致；
8. Object Ref 只能是内部 opaque ID，不能是 URL、本地路径或凭据；
9. 导出操作遵守 data_classification、export_policy、retention_class 和 redaction_status；
10. 真人撤回后立即从分析和报告排除，关联 Claim、缓存和导出制品失效，并记录删除 receipt 或保留的法律依据；
11. Human Session 的 assignment、exposure_order 和 counterbalance_cell 与随机分配／反平衡方案一致；
12. 早期 Trace 不引用未来 Timeline 事件。

JSON Schema 验证通过不等于上述语义成立。
