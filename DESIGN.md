---
name: Audience Mirror Media Environment
description: Calibrated Projection Room：固定视口、可回放、可校准的多模态证据工作台。
colors:
  canvas-black: "#080a0d"
  room-graphite: "#0d1116"
  panel-graphite: "#11171d"
  panel-raised: "#151c23"
  panel-soft: "#0f141a"
  aperture-black: "#050709"
  tungsten-white: "#f1eee6"
  tungsten-dim: "#c5c1b8"
  muted-steel: "#a0a8b1"
  faint-steel: "#838c97"
  hairline: "#252d36"
  hairline-strong: "#35404b"
  signal-cyan: "#59d8e6"
  signal-cyan-bright: "#80eaf2"
  signal-cyan-deep: "#1b8494"
  signal-cyan-wash: "rgb(89 216 230 / 10%)"
  limit-amber: "#e2ad4f"
  limit-amber-wash: "rgb(226 173 79 / 10%)"
  danger-coral: "#e9746b"
  success-mint: "#77d6b0"
  ink-on-cyan: "#061114"
typography:
  brand:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "13px"
    fontWeight: 720
    lineHeight: 1.2
    letterSpacing: "-.015em"
  headline:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "12px"
    fontWeight: 680
    lineHeight: 1.2
  body:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "12px"
    fontWeight: 400
    lineHeight: 1.48
  operator:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "11px"
    fontWeight: 650
    lineHeight: 1.2
  label:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "10px"
    fontWeight: 680
    lineHeight: 1.2
    letterSpacing: ".105em"
  metadata:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "9px"
    fontWeight: 400
    lineHeight: 1.48
  mono:
    fontFamily: '"SFMono-Regular", "Cascadia Code", Consolas, "Liberation Mono", monospace'
    fontSize: "11px"
    fontWeight: 650
    lineHeight: 1
  action:
    fontFamily: 'Inter, ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", "Noto Sans CJK SC", "Microsoft YaHei", sans-serif'
    fontSize: "12px"
    fontWeight: 760
    lineHeight: 1
rounded:
  micro: "4px"
  cue: "5px"
  control: "6px"
  surface: "9px"
  pill: "999px"
spacing:
  micro: "3px"
  xs: "5px"
  sm: "7px"
  md: "9px"
  lg: "12px"
  shell: "14px"
components:
  primary-button:
    backgroundColor: "{colors.signal-cyan}"
    textColor: "{colors.ink-on-cyan}"
    typography: "{typography.action}"
    rounded: "{rounded.control}"
    padding: "0 15px"
    height: "40px"
  secondary-button:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.tungsten-dim}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 11px"
    height: "34px"
  command-input:
    backgroundColor: "{colors.aperture-black}"
    textColor: "{colors.tungsten-white}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "0 11px"
    height: "40px"
  source-mode-selected:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.tungsten-white}"
    typography: "{typography.label}"
    rounded: "{rounded.micro}"
    padding: "0 12px"
    height: "34px"
  status-tag:
    backgroundColor: "{colors.panel-soft}"
    textColor: "{colors.muted-steel}"
    typography: "{typography.metadata}"
    rounded: "{rounded.pill}"
    padding: "3px 6px"
  timeline-cue:
    backgroundColor: "{colors.panel-soft}"
    textColor: "{colors.tungsten-dim}"
    typography: "{typography.label}"
    rounded: "{rounded.cue}"
    padding: "16px 8px 7px"
    height: "78px"
  timeline-cue-selected:
    backgroundColor: "{colors.signal-cyan-wash}"
    textColor: "{colors.tungsten-white}"
    typography: "{typography.label}"
    rounded: "{rounded.cue}"
    padding: "16px 8px 7px"
    height: "78px"
  limitation-strip:
    backgroundColor: "{colors.limit-amber-wash}"
    textColor: "{colors.limit-amber}"
    typography: "{typography.metadata}"
    padding: "8px 11px"
  pane-switch-active:
    backgroundColor: "{colors.panel-raised}"
    textColor: "{colors.signal-cyan-bright}"
    typography: "{typography.label}"
    rounded: "{rounded.micro}"
    height: "34px"
  trace-session:
    backgroundColor: "{colors.panel-soft}"
    textColor: "{colors.tungsten-dim}"
    typography: "{typography.metadata}"
    rounded: "{rounded.control}"
    padding: "7px 9px"
    height: "43px"
  evidence-light-path:
    textColor: "{colors.signal-cyan}"
    width: "100%"
---

# Design System: Audience Mirror Media Environment

## Overview

**Creative North Star: "Calibrated Projection Room"**

Calibrated Projection Room（direction seed `6ade60aa`）把 Audience Mirror 的 Media Environment 塑造成一间精密、克制的校准放映机房：近黑环境压低界面噪声，深石墨面板承载仪器结构，钨丝白保证证据可读，Signal Cyan 只点亮可操作的证据链。界面不是结果陈列墙，而是从素材、cue、观察到个体 Trace 与真人校准状态的可回放研究空间。

桌面端以固定视口组织完整实验现场，三栏工作台与底部流程带同时保持上下文；局部面板自行滚动，页面不离开当前实验。窄屏切换为单面板操作，保留实验、放映台、证据和流程四个明确入口。整体密度来自专业仪器而非缩小后的营销页面，关键限制永远与当前证据并置。

**Key Characteristics:**

- 近黑、石墨与钨丝白构成稳定的放映机房材质。
- 桌面固定视口三栏工作台，底部流程带持续呈现实验阶段与代理量。
- Signal Cyan 证据光路是连接 cue 与精确 Claim 的签名组件。
- 移动端一次只呈现一个工作面板，避免横向页面溢出。
- 9–13px 的仪器级字号配合清晰明度分层，密度高但不牺牲证据可辨性。

## Colors

色板以低亮度冷黑与深石墨建立“机房”，以钨丝白形成阅读层；两种有彩色都承担严格语义，不作为氛围装饰。

### Primary

- **Signal Cyan** (#59d8e6 / #80eaf2 / #1b8494 / rgb(89 216 230 / 10%)): 标记主操作、键盘焦点、选中 cue、证据引用、代理量证据条与动态证据光路。亮色用于 hover 和选中标签，深色用于结构边界，低透明洗色只用于当前证据状态。

### Secondary

- **Limit Amber** (#e2ad4f / rgb(226 173 79 / 10%)): 只承载方法限制、远程处理边界、受限素材与尚待确认的能力状态；必须同时出现清楚文字，不能依赖色相独立传意。

### Tertiary

- **Outcome Mint** (#77d6b0): 仅用于成功或已完成状态点与细窄进度标记。
- **Failure Coral** (#e9746b): 仅用于失败状态与错误反馈，不用于普通警示。

### Neutral

- **Calibration Black** (#080a0d): 页面与整个房间的最深基底。
- **Room Graphite** (#0d1116): 三栏工作台的统一机身。
- **Panel Graphite** (#11171d / #151c23 / #0f141a): 命令条、可操作面板、选项浮层和局部状态的明度层级。
- **Aperture Black** (#050709): 视频孔径、命令输入槽和需要最大聚焦的内容窗口。
- **Tungsten White** (#f1eee6 / #c5c1b8): 标题、关键数值与主要证据文本；dim 版本用于常规说明，完整白只保留给最重要读数。
- **Instrument Steel** (#a0a8b1 / #838c97): 控件标签与元数据；faint 只用于上下文仍可由位置恢复的次级信息。
- **Machine Hairlines** (#252d36 / #35404b): 用 1px 结构线划分面板、表格、cue 与控件，strong 版本定义外框和交互边界。

**The Signal Circuit Rule.** Signal Cyan 只表示证据或操作；任何不具备证据关系或操作含义的装饰都不得使用它。

**The Amber Boundary Rule.** Limit Amber 只表示限制、风险和授权边界，不与成功、选中或模型得分混用。

## Typography

**Brand / Heading Font:** Inter 优先的系统无衬线栈（`brand`／`headline`）
**Body Font:** Inter 优先的系统无衬线栈（`body`／`operator`）
**Label / Mono Font:** 同一无衬线栈与 SFMono-Regular 优先的等宽栈（`label`／`metadata`／`mono`）

**Character:** 所有文字都像放映设备上的标注与研究记录：小、稳、直接。字重和明度承担层级，时间码、哈希、Agent ID 与精确比例才切换为等宽字体。

### Hierarchy

- **Brand** (weight 720, 13px, line-height 1.2): 品牌名与孔径占位的最高层级，不扩张成超大展示字。
- **Headline** (weight 680, 12px, line-height 1.2): Inspector 标题、实验身份与局部内容标题。
- **Body** (weight 400, 12px, line-height 1.48): 全局默认说明文本；关键工作区正文以 10–11px 的已实现上下文变体保持同一明度秩序。
- **Operator** (weight 650, 11px, line-height 1.2): 关键读数、当前事件和紧凑操作信息。
- **Label** (weight 680, 10px, line-height 1.2, letter-spacing .105em): 大写 rail label、区段标题和高密度表头。
- **Metadata** (weight 400, 9px, line-height 1.48): 来源、分群、状态和辅助说明；仅装饰性刻度可降至 7px，不能承载独立事实。
- **Mono** (weight 650, 11px, line-height 1): 时间码、数量、百分比、哈希、Environment／Timeline 版本与 Agent 标识。

**The Instrument Type Rule.** 不以大字号制造权威；层级来自字重、明度、对齐和等宽数据节奏，所有可决策证据保持在 9px 以上的已实现可读层。

## Layout

桌面外壳占满 `100dvh`，最小高度为 640px，以 48px 顶栏、64px 命令条、弹性工作台和 108px 底部流程带组成四行，行间距为 9px，左右安全边距为 14px。工作台使用左 204px 实验轨、中部至少 420px 的弹性放映台、右侧 350–410px Inspector；宽度在 1260px 和 1040px 两级收紧。短桌面视口在 679px 高度以下将顶栏、命令条和流程带分别压缩为 42px、54px 和 84px。

桌面页面本身锁定滚动。实验轨、Inspector 视图和 Trace 表在自己的面板内纵向滚动；cue 轨按事件时长横向滚动，并在溢出时隐藏无法正确对齐的装饰刻度。底部流程带在同一视口持续展示素材与权利、多模态事实层、顺序体验和真人校准四阶段。

899px 及以下进入单面板模式：粘性 pane switch 固定展示“实验／放映台／证据／流程”，一次只显示一个面板；页面恢复必要的纵向滚动，内部视图继续管理证据与表格溢出。560px 及以下缩短放映台、隐藏运输辅助信息并让主运行按钮占满一行，页面不得产生横向滚动。

**The Fixed Room Rule.** 桌面必须在一个视口内同时保留实验轨、放映台、Inspector 和流程带；新增内容进入面板滚动或现有 tab，不得推高整页。

**The Single-Pane Rule.** 窄屏只呈现当前任务面板，并用持久的四入口切换器保留全流程可达性。

## Elevation & Depth

深度主要来自相邻黑阶、1px 结构线和孔径明暗，不用重复卡片阴影。整块工作台使用一次结构性深影与背景分离；命令条使用更轻的环境影，主操作只带低强度青色投影。选项浮层、方法详情与 toast 可使用深影，因为它们确实离开当前平面。模糊仅用于移动 pane switch 和孔径 chip 的可读性保护，不形成大面积玻璃材质。

### Shadow Vocabulary

- **Room Isolation** (`0 18px 48px rgb(0 0 0 / 28%)`): 仅用于完整三栏工作台和真实浮层。
- **Command Lift** (`0 8px 28px rgb(0 0 0 / 18%)`): 用于链接优先命令条，建立输入层与工作台的先后关系。
- **Cyan Action Lift** (`0 6px 18px rgb(35 171 187 / 17%)`): 只用于主要青色操作按钮。
- **Evidence Glow** (`0 0 9px rgb(89 216 230 / 55%)`): 只用于当前 cue 标记和短暂证据扫描反馈。

**The Structural Depth Rule.** 阴影只解释层级或瞬时状态；静态证据容器依靠色调和结构线归组，不悬浮成卡片墙。

## Shapes

机房结构以小圆角、薄边框和正交路径为主。全局面板使用 9px 圆角，控件与 Trace Session 使用 6px，cue 使用 5px，极小标签与 pane switch 项使用 4px；胶囊仅保留给系统状态和复核标签。视频孔径内部仍是硬朗矩形，通过四角 15px 校准框建立“可测量窗口”的轮廓。证据光路使用 1px 正交线与 9px 转角，不使用自由曲线或装饰性波形。

## Components

### Buttons

- **Shape:** 主要与次要操作都使用紧凑控制圆角（6px），不使用超大胶囊。
- **Primary:** Signal Cyan 底、深色文字、40px 高、水平 padding 15px；放映台内的运行操作压缩到 28–30px 以适配运输条。
- **Hover / Focus:** hover 切换为 bright cyan，active 下移 1px；键盘焦点统一使用 2px Signal Cyan 轮廓和低强度外晕。
- **Secondary:** raised graphite 底、strong hairline 边框、34px 高；hover 仅将边框与文字转为 cyan，不产生额外抬升。
- **Text / Evidence:** 无底色，Signal Cyan 文本；证据按钮保留细下划线，必须指向时间片、Observation 或 Trace。

### Chips

- **Status:** 小型等宽胶囊，透明或 soft graphite 背景、hairline 边框，用于复核状态和系统状态。
- **Aperture:** 4px 圆角、半透明近黑底，时间码用 bright cyan；机密／受限分类切换为 Limit Amber。
- **State:** chip 不承担主要操作，也不显示未经校准的强结论。

### Cards / Containers

- **Corner Style:** 工作台、命令条和流程带使用 9px；内部 cue、流程步骤和 Trace Session 使用 5–6px。
- **Background:** 通过 aperture、room、panel、raised 和 soft 五级黑阶建立层次。
- **Shadow Strategy:** 只有完整工作台、命令条与真实浮层使用阴影；内部证据块保持平面。
- **Border:** 所有可交互边界使用 1px hairline；外框与 hover 使用 strong hairline。
- **Internal Padding:** 高频面板以 9–14px 为主，避免宽松卡片节奏破坏同屏证据量。

### Inputs / Fields

- **Style:** 命令输入位于 40px 高的 Aperture Black 槽内；普通 select、number 与 search 使用 soft graphite 底、strong hairline 边框和 6px 圆角。
- **Focus:** 2px Signal Cyan 内轮廓，外加 3px 低透明青色 halo；不通过背景大幅变色表达焦点。
- **Error / Disabled:** disabled 保留结构但降至 `.42` opacity；错误通过 Coral 边框与明确文字同时说明。

### Navigation

- **Desktop:** 顶栏只包含品牌、产品命题和系统能力状态；工作区不引入站点式导航。
- **Inspector:** 四个等宽 tab 以 2px cyan 下划线表示当前视图，并支持方向键、Home 与 End。
- **Mobile:** 四入口 pane switch 在 899px 以下出现并保持 sticky；active 项使用 raised graphite 与 bright cyan，同时更新 `aria-pressed`。

### Timeline Cue

cue 以时长决定横向宽度，最小宽度 84px。默认使用 soft graphite、hairline 边框和 5px 圆角；选中态使用 cyan 深边、低透明 cyan 渐变、顶部 2px 发光标记和 `aria-current`。键盘与上一／下一运输控件都能改变当前 cue，并将其保持在可见轨道内。

### Methods & Limitations Strip

Inspector 顶部始终用低透明 amber 洗色与 amber 分隔线说明“预测代理量，不是现实人群预测”。详情浮层继续使用 amber 边界与深色背景；任何模型能力、素材外发和真人校准限制都必须在操作附近用文字展开。

### Evidence Light Path

证据光路是本系统的签名组件：桌面端从当前选中 cue 的底部出发，经一个观察 waypoint 沿正交路径到达 Inspector 中的精确 Claim anchor。线宽 1px、端点 3.5–4.5px，颜色固定为 Signal Cyan；选择 cue 时用 500ms 的单次描线反馈，静止后保留路径。`prefers-reduced-motion` 下立即呈现，不播放动画；单面板模式关闭光路，因为源与目标不同时可见。

**The Evidence Light Path Rule.** 光路必须连接一个真实的当前 cue 与一个可核查 Claim；没有两端证据、在窄屏面板分离或 forced-colors 模式下都必须隐藏。

### Trace Session

每个 Persona 使用 43px 高的紧凑 disclosure：左侧是等宽 Agent ID 与分群，中部是按事件顺序的 channel strip，右侧是理解、困惑与继续代理量。展开体内部滚动并保留表头；来自反例或高反应链接的跳转会清空筛选、展开目标 Session、定位具体 Trace 并转移焦点。

## Do's and Don'ts

### Do:

- **Do** 在桌面同一视口内保持实验轨、放映台、证据 Inspector 与流程带，并把溢出交给内部面板。
- **Do** 让每个聚合值都能回到 cue、Observation、Persona Trace、来源状态和反例。
- **Do** 把 Signal Cyan 限定为证据和操作，把 Limit Amber 限定为限制与授权边界。
- **Do** 使用钨丝白、dim white、muted steel 与 faint steel 的明度层级维持 9–13px 密集排版的可读性。
- **Do** 为所有键盘操作保留 2px 可见焦点，并在 reduced-motion 与 forced-colors 下提供等价状态。
- **Do** 在 899px 以下切换为单面板，不隐藏实验、放映台、证据或流程中的任何一个入口。

### Don't:

- **Don't** 把工作台改成通用 KPI 卡片墙、营销落地页或以粒子和炫目曲线制造 AI 权威感。
- **Don't** 让 Signal Cyan 或 Limit Amber 承担无语义装饰，也不要只靠颜色表达状态。
- **Don't** 在桌面让 body 滚动，或把四个工作区顺序堆叠到视口之外。
- **Don't** 用摘要遮蔽个体 Trace、反例、模型推断状态、零真人或无法判断项。
- **Don't** 对每个内部容器添加阴影、玻璃模糊或大圆角；结构线和黑阶已经承担层级。
- **Don't** 把 Agent 数、预测代理量或模型复核状态写成真人样本、真实注意或确定性业务预测。
