# 报告来源与 QA 记录

日期：2026-08-19
受众：Product stakeholders
交付模式：Portable HTML

## 报告结构映射

| Executive Report 要求 | 报告区段 |
| --- | --- |
| Title | 虚拟观众规模与开源策略 |
| Executive Summary | Executive Summary |
| Key findings with visual evidence | MatrAIx 规模表、跨模型分组柱图、三层执行表 |
| Recommended next steps | Recommended Next Steps |
| Further questions | Further Questions |
| Caveats and assumptions | Caveats and Assumptions |

## 来源清单

- MatrAIx arXiv v1：规模、实际 Trial、验证设计、跨模型结果、限制；
- MatrAIx 固定 Commit `07bb6a4e07c33b5ab96dc4563cf516d5d15b3dd9`：代码、MIT License、Quickstart、Task／Trial／Cohort 合同；
- MatrAIx Persona 1M 数据卡：记录数、字段、来源、边际校准和使用限制；
- TinyTroupe、genagents、OASIS、Concordia、AgentSociety 官方仓库：开放生态功能与许可证扫描；
- 用户给定约束：不扩招、不采购大规模算力；开源范围由商业价值与社区信号决定。

## Chart Map

| 报告区段 | 问题 | 图形 | 字段 | 支持的结论 | 色彩策略 |
| --- | --- | --- | --- | --- | --- |
| 模型选择偏差 | 相同／完整匹配 Cohort 换底模时，产品结果变化多大？ | 分组横向柱图 `horizontalBar` | task、model、result_pct | 7 个可比任务中多个指标跨模型差异明显；大 Cohort 不消除模型选择偏差 | categorical，由 Artifact Reader 统一主题管理 |

Meal Planning 因论文报告 GPT 5.5 Arm 未运行声明 Cohort，从图中排除；明细表保留该行和限制。News+ 与 Stocks 的 App Cohort 很小，在图中保留但显示 Caveat。

## 计算与数据检查

- 8 个明细任务的 `range_pp` 已独立按 `max(model pct) - min(model pct)` 重算，全部一致；
- 所有比例在 0%—100%范围内；
- 图形数据为 7 个任务 × 3 个模型，共 21 行，排除项与论文 Cohort 完整性说明一致；
- MatrAIx Persona 1M Hugging Face API 的 `cardData.license` 为空，数据卡正文写明底层来源许可证和条款继续适用；
- 新增的 11 个主要公开链接在 2026-08-19 均返回 HTTP 200；
- 隐私扫描未发现私密逐字稿人名、客户／项目名或本地资料库路径。

## 交付验证

- Artifact validation：passed；
- Packaging：passed；
- Structural verification：passed；
- Browser verification：未完成。Portable Builder 未发现其预期的 Chromium headless-shell；尝试复用系统 Chrome 时静态图提取在约 11 秒超时，随后按结构验证回退；
- 自包含 `report.html` 已生成，语义回退包含 15 个 Block、1 张图的数据表和 4 张表；
- Source dialog、交互图和窄屏布局尚未经过浏览器自动化验证。

## 对外分享前仍需检查

1. 在带 Chromium headless-shell 的 CI 或开发机重新运行 Portable Builder 的浏览器验证；
2. 视觉检查中文长标签、横向分组柱图、暗色主题和窄屏布局；
3. 若公开仓库，先确定仓库许可证并生成第三方 Notices；
4. 不把 Persona 1M 数据文件随代码再分发，除非逐来源条款审计完成。
