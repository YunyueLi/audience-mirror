---
name: Audience Mirror
description: Audience Mirror 首个 Media Environment 的证据工作台设计系统。
colors:
  canvas: "oklch(1 0 0)"
  surface: "oklch(.975 .004 250)"
  surface-strong: "oklch(.945 .006 250)"
  ink: "oklch(.18 .012 250)"
  muted: "oklch(.48 .018 250)"
  tertiary: "oklch(.41 .016 250)"
  line: "oklch(.9 .008 250)"
  control-line: "oklch(.54 .022 250)"
  accent: "oklch(.5 .19 251)"
  accent-ink: "oklch(1 0 0)"
  warning: "oklch(.92 .045 83)"
  warning-ink: "oklch(.35 .07 72)"
  focus: "oklch(.68 .17 251)"
  dark-canvas: "oklch(.19 .008 250)"
  dark-surface: "oklch(.24 .01 250)"
  dark-surface-strong: "oklch(.29 .012 250)"
  dark-ink: "oklch(.92 .006 250)"
  dark-muted: "oklch(.76 .012 250)"
  dark-tertiary: "oklch(.75 .012 250)"
  dark-line: "oklch(.34 .012 250)"
  dark-control-line: "oklch(.68 .018 250)"
  dark-accent: "oklch(.77 .13 247)"
  dark-accent-ink: "oklch(.18 .012 250)"
  dark-warning: "oklch(.3 .04 75)"
  dark-warning-ink: "oklch(.88 .07 83)"
  dark-focus: "oklch(.78 .13 247)"
typography:
  display:
    fontFamily: '"Songti SC", "Noto Serif CJK SC", "Source Han Serif SC", serif'
    fontSize: "clamp(2.25rem, 6vw, 4.8rem)"
    fontWeight: 700
    lineHeight: 1.2
    letterSpacing: "-.035em"
  headline:
    fontFamily: 'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif'
    fontSize: "clamp(1.45rem, 2.5vw, 2.05rem)"
    fontWeight: 620
    lineHeight: 1.2
    letterSpacing: "-.02em"
  body:
    fontFamily: 'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif'
    fontSize: "15px"
    fontWeight: 400
    lineHeight: 1.55
  label:
    fontFamily: 'ui-sans-serif, -apple-system, BlinkMacSystemFont, "Segoe UI", "PingFang SC", sans-serif'
    fontSize: "12px"
    fontWeight: 600
    lineHeight: 1.55
  mono:
    fontFamily: "ui-monospace, SFMono-Regular, Menlo, monospace"
    fontSize: ".86em"
    fontWeight: 400
    lineHeight: 1.55
rounded:
  control: "10px"
  surface: "14px"
  pill: "999px"
spacing:
  xs: "8px"
  sm: "12px"
  md: "18px"
  lg: "24px"
  section: "72px"
components:
  status-tag:
    backgroundColor: "{colors.surface}"
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    rounded: "{rounded.pill}"
    padding: "3px 10px"
    height: "28px"
  warning-notice:
    backgroundColor: "{colors.warning}"
    textColor: "{colors.warning-ink}"
    rounded: "{rounded.surface}"
    padding: "16px 18px"
  input:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    rounded: "{rounded.control}"
    padding: "8px 11px"
    height: "44px"
  nav-link:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.muted}"
    typography: "{typography.label}"
    height: "44px"
  session-disclosure:
    backgroundColor: "{colors.canvas}"
    textColor: "{colors.ink}"
    typography: "{typography.body}"
    padding: "12px 0"
    height: "56px"
---

# Design System: Audience Mirror Media Environment

## Overview

**Creative North Star: "审片证据台"**

本设计系统服务 Audience Mirror 的首个 Media Environment，不定义整个平台的视觉边界。当前界面像一张编辑部与研究室共用的审片桌：大片留白让内容保持安静，紧凑表格承载可核查事实，极少的蓝色只指向可操作的证据链。它不渲染“AI 神谕”，也不用规模数字制造确定感。未来 Web／App、Game 或 Social Environment 应继承证据关系与无障碍原则，再根据各自任务形成工作台。

默认密度为专业研究工具级：首屏先说明证据边界，其后通过一致的分隔线、排版层级和语义色彩区分“数据”、“限制”与“操作”。深色主题保持同一信息层级，不把专业工具变成赛博风控制台。

**Key Characteristics:**

- 编辑式大标题与研究仪器式表格并存。
- 先呈现限制与证据口径，再展开结果。
- 蓝色稀缺，专用于链接、聚焦和交互状态。
- 亮色与深色主题均以 WCAG 2.2 AA 为下限。

## Colors

色板以冷中性灰建立事实层，用单一高辨识度蓝色建立行为层，用低饱和黄色标记限制和风险。

### Primary

- **证据蓝**（`accent`／`dark-accent`）：只用于可下钻链接、表单悬停和披露箭头，不用于大面积背景。
- **聚焦蓝**（`focus`／`dark-focus`）：提供统一的键盘焦点环，与普通链接状态分开。

### Secondary

- **限制黄**（`warning`／`dark-warning`）：承载“不可用于业务预测”等方法边界，需始终搭配对应的 `warning-ink`。

### Neutral

- **白纸画布**（`canvas`／`dark-canvas`）：页面基底和表单背景。
- **冷灰表面**（`surface`／`dark-surface`）：状态标签、运行指纹和次级区块。
- **研究墨色**（`ink`／`dark-ink`）：标题、表格关键字段和主要结论。
- **注释灰**（`muted`／`dark-muted`）：正文辅助信息；`tertiary` 只用于更次要的元数据。
- **仪器分隔线**（`line`／`dark-line`）：表格与 Session 行的结构边界；表单控件使用对比更高的 `control-line`。

**The One Blue Voice Rule.** 一屏中的蓝色只能回答“这里可以操作或下钻”，不得同时担任装饰或模型得分高低。

## Typography

**Display Font:** 中文宋体栈（`display`）
**Body Font:** 平台无衬线栈（`body`）
**Label/Mono Font:** 平台无衬线与等宽数据栈（`label`／`mono`）

**Character:** 宋体只为页面命题提供编辑感；主体工作区使用高可读无衬线，时间码、哈希与标识符才进入等宽字体。

### Hierarchy

- **Display**（`display`）：每个页面只出现一次，承载最重要的方法态度。
- **Headline**（`headline`）：区分口径、时间轴、Trace 和运行指纹等主要工作区。
- **Body**（`body`）：段落控制在 65–75 个英文字符宽度，长中文保持可扫读的行长。
- **Label**（`label`）：表头、标签、筛选器标题和运行元数据。
- **Mono**（`mono`）：只用于时间码、Hash、Run ID 和 Observation ID。

**The Editorial Threshold Rule.** 宋体不进入表格、控件或指标；研究仪器区始终优先清晰度。

## Layout

主容器限定为 1180px，桌面端保留 40px 横向安全边距，窄屏收紧为 28px。页面使用单列长卷轴，重要数据用全宽表格，长表在局部容器内横向滚动，不允许整页溢出。

章节以 `section` 间距建立宏观节奏；标题与说明紧密成组，表格、筛选器与 Session 列表保持更高密度。760px 以下，顶部导航与区块标题改为纵向排布，筛选控件保持至少 44px 高度。粘性导航与所有证据锚点使用匹配的滚动偏移。

**The Evidence Corridor Rule.** 任何聚合结论到个体 Trace 的路径都必须在同一长卷轴内连续可达，不使用打断证据上下文的模态框。

## Elevation & Depth

系统默认完全扁平，不使用卡片阴影。深度由色调层、细分隔线、粘性导航和局部背景区分；顶栏的轻微背景模糊是为了保持滚动后的文字可读性，不是装饰性玻璃拟态。

**The Flat Evidence Rule.** 静态证据不浮起；状态变化通过聚焦环、色彩和披露层级呈现。

## Shapes

表单控件使用温和的 `control` 圆角，限制提示与指纹容器使用稍大的 `surface` 圆角，只有小型状态标签使用 `pill`。表格和 Session 列表不包进通用卡片，它们依靠分隔线和对齐关系成组。披露箭头使用 CSS 线条绘制，不使用 Unicode 符号或 emoji。

## Components

### Status Tags

- **Shape:** 小型胶囊（`pill`），不承担主操作。
- **Color:** 默认使用冷灰表面；未校准或合成限制可使用限制黄。

### Warning Notice

- **Shape:** 整体稳定、边界清晰的提示面（`surface`）。
- **Content:** 首行直接说明不可用途，其后解释原因，不使用警告图标制造情绪。

### Inputs / Fields

- **Style:** 画布背景、高对比控件线、`control` 圆角，触控高度不低于 `input` token。
- **Hover / Focus:** 悬停时边线转为证据蓝；键盘聚焦使用统一外轮廓。
- **Empty:** Persona 筛选没有结果时，在列表上方的 `aria-live` 状态直接说明结果为空。

### Navigation

- **Style:** 粘性单层顶栏，品牌名使用主墨色，章节链接默认为注释灰。
- **Mobile:** 品牌名与章节链接分两行，保留所有核心入口，不折叠成隐藏菜单。

### Session Disclosure

- **Style:** 每个 Persona 占一条无卡片的披露行，左侧是身份与分群，右侧是结果摘要与一致箭头。
- **Behavior:** 来自时间轴的 Trace 链接会清空筛选、展开对应 Session、将目标行置于视口中部并转移键盘焦点。
- **Evidence Return:** Trace 内的 Timeline 节点与 Observation 链接需能返回上游证据。

## Do's and Don'ts

### Do:

- **Do** 让每条聚合结论能下钻到时间点、Persona、Trace 与 Observation。
- **Do** 始终分开 Persona Pool、Deep Trace、Broad Sweep、Projection 和真人数量。
- **Do** 使所有可操作控件具有明确的 hover、focus-visible 和窄屏状态。
- **Do** 使表格数字、时间码和运行指纹保持稳定对齐。

### Don't:

- **Don't** 用蓝色、大数字或动画装饰模型能力和 Agent 规模。
- **Don't** 把表格、Session 或每个指标装进同等重量的圆角卡片。
- **Don't** 使用系统黑体、等宽字体或赛博效果伪装专业感。
- **Don't** 以颜色作为唯一状态信号，也不隐藏“未校准”、“零真人”或“无法判断”。
