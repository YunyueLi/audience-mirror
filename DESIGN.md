---
name: Audience Mirror Interface System
version: 0.3
status: implemented-baseline
defaultTheme: light
sourceOfTruth:
  - web/styles.css
  - web/index.html
  - web/app.js
---

# Audience Mirror Interface System

## 1. 产品界面的职责

Audience Mirror 的界面是一间“可校准的放映与实验工作台”。它同时服务三件事：

1. 让素材成为视觉中心，用户先看见正在被体验的对象；
2. 让每个聚合结论都能回到时间点、素材证据和个体记录；
3. 明确区分素材事实、模型推断、预测代理量和真人校准，避免用视觉权威掩盖不确定性。

设计北极星是 **Evidence develops from noise / 证据从噪声中显影**。浅色模式是温暖、克制的编辑室与档案纸；深色模式是同一空间的夜间放映状态。两种主题中，视频孔径始终是最深、最重的视觉面。

这套系统吸收了专业编辑软件的时间坐标、顶级 SaaS 的状态清晰度和 [Ice Works Showcase](https://github.com/MegD1/Ice-works-showcase) 的粒子显影／编辑式信息启发，但不复制其素材、字体、shader 或品牌形式。参考仓库的 `public/` 素材不在其源码许可范围内；Audience Mirror 只实现自己的 Canvas 2D 动效与信息语法。

## 2. 不可破坏的体验原则

- **视频第一。** 桌面工作台固定为约 65% 舞台、35% Inspector；Inspector 不得决定视频高度。真实视频按固有比例 `contain`，不裁切，不用封面图冒充视频。
- **证据优先于总结。** 当前事件、时间码、观察、命中证据、分歧、反例和 Trace 必须在同一实验中可达。
- **时间比例不造假。** 标尺、事件卡、曲线、选中游标和真实播放游标共用毫秒坐标。短事件仍保留至少 48px 命中宽度，必要时整条轨道横向滚动。
- **代理量不伪装成人。** 困惑、注意、继续等默认写为未校准预测代理量；AI 观众数与真人数分开显示。
- **编辑式层级。** 时间码、事件名、来源和证据状态采用非对称锁定排版；减少“卡片套卡片”，用留白、发丝线和对齐表达层级。
- **动效只报告状态。** 没有氛围性循环、自动视差或无意义发光。`prefers-reduced-motion` 下信息仍完整，运动立即完成或完全取消。
- **移动端是任务切换，不是桌面缩小。** 899px 以下一次只呈现设置、画面、证据或进度中的一个面板；页面不得横向溢出。

## 3. Token 系统

运行时 token 的唯一事实源是 `web/styles.css`。以下是稳定语义，具体数值可迭代但不可改变含义。

### 3.1 颜色

| Token 族 | 浅色含义 | 深色含义 | 使用限制 |
| --- | --- | --- | --- |
| `--page` / `--panel*` | 暖纸与白色工作面 | 冷黑与石墨工作面 | 构成空间，不表达状态 |
| `--aperture` | 近黑视频孔径 | 更深的放映黑 | 所有主题中最重的面 |
| `--ink*` / `--muted` / `--faint` | 四级文本层次 | 单独调校的夜间层次 | 不能用低对比文本承载唯一事实 |
| `--accent*` | 深青色 | 高亮青色 | 只表示证据、选中或可执行动作 |
| `--limit*` | 琥珀色 | 提亮琥珀色 | 只表示限制、授权和待校准边界 |
| `--mint` | 已完成 | 已完成 | 必须配合文字或图标 |
| `--coral` | 失败或错误 | 失败或错误 | 不用于普通提醒 |
| `--slate-series` | 第二预测序列 | 第二预测序列 | 不与语义色竞争 |

默认浅色值为暖纸 `#f5f3ee`、面板 `#ffffff`、孔径 `#0c1013`、正文 `#14171a`、证据青 `#0c7a89`。深色不是机械反相，使用页面 `#0a0d11`、面板 `#12181f`、孔径 `#04070a`、证据青 `#4fd0e0`。

### 3.2 字体与数据

- 正文使用系统无衬线栈，优先匹配 Apple／Windows／中文系统字体，不引入受限商业字体。
- 时间码、比例、哈希、Agent ID 和版本使用系统等宽栈，并启用 tabular numbers。
- UI 正文字号 12–14px，事件与 Inspector 标题 15–21px；11px 仅用于仍有上下文的元数据。
- 时间码是信息锚点，不是装饰标签。它应与事件名错位排列，形成可快速扫描的编辑式节奏。

### 3.3 空间、形状与触控

- 4px 基础网格；间距 token 为 4、6、8、10、12、16、20、28px。
- 圆角只使用 4、8、10px 和状态胶囊；新增半径必须先解释新层级。
- 鼠标与键盘可见控件最小触控区域为 44 × 44px；编辑时间轴事件为 48px 最小宽度。
- 阴影只用于真正浮动的 Drawer、Popover、Toast、分段选择滑块和视频孔径。页面内证据块用发丝线归组。

### 3.4 Motion

| Token | 时长 | 含义 |
| --- | ---: | --- |
| `--dur-1` | 120ms | 颜色、边框和简单状态读取 |
| `--dur-2` | 180ms | 小范围 disclosure 与颗粒淡入 |
| `--dur-3` | 260ms | Drawer、Pane、Toast 等表面变化 |
| `--dur-4` | 460ms | 证据光路交接 |
| `--dur-5` | 700ms | 单次画面显影 |

所有 motion 使用 `--ease`、`--ease-out` 或 `--ease-grain`。只有真正的未定进度可以循环；其他动画必须由用户动作或新证据到达触发，并自行终止。

## 4. 布局系统

### 4.1 桌面（1180px 及以上）

- 顶栏粘性停靠，包含品牌、画面／证据／进度跳转、本机状态、主题与设置。
- 第二行是单行 Command Bar：链接／文件、输入、授权、参数和主动作共享一个平面。
- 主工作台是 `minmax(0, 65fr) minmax(360px, 35fr)`。左侧包含视频、运输栏和同坐标时间轴；右侧 Inspector 粘性停靠并内部滚动。
- 视频舞台高度为 `clamp(380px, 48vh, 620px)`，不为“首屏塞满信息”而压缩。
- 流程、量表账本与校准状态位于主工作台之后，属于第三信息层。

### 4.2 中窄屏（899–1179px）

按页面宽度保留单列阅读；画面仍优先，Inspector 进入自然文档流。不得重新生成横向页面滚动。

### 4.3 移动端（899px 以下）

- 粘性 Pane Switch 提供“设置／画面／证据／进度”，一次显示一个任务面板。
- 560px 以下品牌收敛为 AM，设置收敛为图标；系统状态继续可读，379px 以下才只保留状态点。
- 视频按固有比例显示。9:16、1:1、4:3、16:9 和 2.39:1 均使用 `contain`。
- 时间轴可独立横向滚动；页面本身保持零横向溢出。

## 5. 组件目录

### 5.1 Foundation

| 组件 | 必需状态 | 契约 |
| --- | --- | --- |
| Button | default / hover / focus-visible / active / disabled / busy | busy 保留原标签并设置 `aria-busy`；主动作每个视图只保留一个 |
| Icon Button | 同上 | 必须有可访问名称；触控区至少 44px |
| Input / Select | empty / ready / focus / invalid / disabled | 错误必须有文字；不只变色 |
| Segmented Control | idle / checked / focus | 使用原生 radio 或等价 ARIA；滑块阴影只解释选中层 |
| Tabs | active / hover / focus / disabled | 支持方向键、Home、End；`aria-selected` 与面板同步 |
| Disclosure | closed / open / focus | summary 可键盘触发，展开后焦点顺序自然 |
| Toast | info / success / error | 不抢焦点；错误内容说明数据是否写入 |
| Loading / Empty / Error | pending / none / failed / retry | Empty 教用户下一步；Error 保留安全重试路径 |

### 5.2 Product components

| 组件 | 用途 | 核心状态与规则 |
| --- | --- | --- |
| `CommandBar` | 链接或文件导入 | 支持 `⌘/Ctrl K`、授权门、参数和进度；窄屏文案主动缩短 |
| `MediaStage` | 原视频或证据帧主舞台 | 真实媒体 `contain`；Canvas 不接收指针；控件始终可操作 |
| `ApertureMetadata` | 时间码、素材分类、来源 | 时间与状态非对称编排；机密状态切换为限制色 |
| `StageTransport` | 当前事件、前后事件、运行顺序体验 | 禁用边界明确；不会自动播放视频 |
| `EvidenceTimeline` | 标尺、事件、代理曲线和游标 | 毫秒坐标统一；事件至少 48px；支持滚动、缩放、Home/End |
| `Inspector` | 当前证据、逐段反应、个体记录、真人校准 | 方法限制常驻；每个结论可下钻；内部滚动不改变视频高度 |
| `EvidenceClaim` | 命中证据与引用 | 展示 epistemic status、review status、时间点与来源哈希 |
| `TraceSession` | Persona 的连续经历 | 展开后保持事件顺序、先前记忆、反例和动作，不把 Agent 发言伪装成人话 |
| `ExperimentDeck` | 素材、事实层、顺序体验、校准进度 | 第三层信息；不与视频争夺首屏注意力 |
| `MethodBoundary` | 模型、授权和校准限制 | 琥珀色只承担边界，内容必须可展开并可读 |

### 5.3 状态属性

现有原生前端用 `data-state`、`aria-current`、`aria-selected`、`aria-pressed`、`aria-busy` 和 `hidden` 作为公共状态接口。样式不得依据按钮文字推断状态。将来组件化时也保持这套外部语义，以便视觉测试、辅助技术和自动化脚本复用。

## 6. 品牌动效语法

### 6.1 Emulsion / 证据显影

`MediaStage` 内的 Canvas 2D 粒子只在初次实验、真实素材切换或证据画面切换后运行一次。点场向画面边界与视线轴凝聚，560–760ms 后完全透明并取消 `requestAnimationFrame`。

性能边界：

- 单次最多 136 粒子；
- DPR 上限 1.5；
- 页面隐藏立即停止；
- resize 只重测现有归一化坐标；
- `pointer-events: none`；
- `prefers-reduced-motion` 下 Canvas 不显示，JS 不启动帧循环；
- 合成空态每个实验最多显影一次，不能在每个 cue 炫技。

### 6.2 Grain Shadow / 悬停颗粒影

事件卡、命中证据与可下钻 Trace 只在 hover 或 focus-visible 时出现克制的点阵牵引。颗粒位于内容下层，不能降低文字对比；选中态不常驻发光。

### 6.3 Evidence Light Path / 证据光路

桌面端用一条点状路径把当前事件连接到 Inspector 中的精确证据。选择或悬停时，单个 spark 沿线通过后静止。单面板模式、缺少两端证据或 reduced motion 下隐藏运动，证据关系仍由时间码和引用表达。

## 7. 无障碍与质量门槛

- 所有交互使用语义元素；不以 `div` 模拟按钮。
- 键盘焦点统一为 2px 可见轮廓；focus-visible 与 hover 提供等价信息。
- Tabs、Drawer、Disclosure、Select 和 Toast 对照 WAI-ARIA 预期行为。
- `hidden` 元素的计算样式必须为 `display: none`；加载层不允许残留遮挡。
- 390px、512px、1242px、1440px、1584px、1920px 都必须无页面级横向溢出。
- 16:9、9:16、1:1、4:3、2.39:1 视频比例都必须验证不裁切。
- 浅色、深色、reduced motion、真实视频、合成空态和错误态都要进入截图回归。
- 控制台零错误；`node --check web/app.js`、`git diff --check` 和全量测试通过后才可发布。

## 8. 组件库与未来实现选择

当前原型没有构建链，为了快速发布和可审计性使用原生 HTML/CSS/JS，不从 CDN 引入 UI 依赖。可运行的组件目录位于 `web/components.html`，与工作台共享 `web/styles.css` 的 Token 和基础组件；它覆盖 Button、Field、Tabs、Segmented Control、Media Stage、Evidence Claim、Timeline Cue、Trace Session、Toast 以及空／忙／失败／成功状态。未来进入多环境、多用户产品阶段时，建议迁移为“Audience Mirror 视觉层 + 无样式可访问 primitive”，而不是采购一套带强品牌皮肤的组件库。

- [Radix Primitives](https://www.radix-ui.com/primitives/docs/overview/accessibility)：优先参考 Dialog、Tabs、Tooltip、Scroll Area 的键盘、焦点与 WAI-ARIA 行为。
- [Base UI](https://base-ui.com/react/overview/quick-start)：候选默认基础；单包、可 tree-shake、无样式，覆盖 Drawer、Toast、Field、Tabs 等主要 primitive。
- [React Aria](https://react-aria.adobe.com/getting-started)：复杂集合、Selection、Press、Focus、虚拟化和国际化的行为参考；如果产品进入高密度表格／集合编辑，可优先选择。
- [Motion](https://motion.dev/docs/react-accessibility)：若迁 React，只用于状态编排，并启用 reduced-motion 策略；Canvas 显影仍保持独立、可替换。
- [Visx](https://visx.airbnb.tech/) 或 [Observable Plot](https://observablehq.com/plot/)：当时间轴和群体分布超出当前 SVG 基线时再评估。选择标准是可下钻、可访问与性能，不是图表数量。

迁移前提：交互复杂度确实超过原生基线，且能够建立 Storybook／视觉回归、类型化 token 和组件测试。第一选择是 Base UI 承担通用 primitive，React Aria 补充复杂集合与国际化，业务组件保持自主实现；Radix 作为行为对照，不同时叠加多套 primitive。不得为了“看起来像 SaaS”而先迁框架。

## 9. 禁止项

- 不把页面做成 KPI 卡片墙、营销落地页或通用深色 Dashboard。
- 不让粒子、发光、玻璃、渐变承担无语义装饰。
- 不用超小字号和压缩视频换取“一屏展示全部”。
- 不用 Agent 数、模型分数或漂亮曲线制造真人代表性。
- 不隐藏未校准、无真人、推断来源、反例或模型未覆盖区间。
- 不复制参考产品的资产、商业字体、具体 shader 或商标性表达。

## 10. 当前实现状态

界面系统 0.3 基线已实现：默认浅色、独立深色、65/35 视频工作台、响应式单面板、真实比例视频、编辑式时间轴、最小事件命中宽度、Inspector 下钻、Canvas 显影、颗粒 hover、证据光路、Drawer、Toast、空态／错误态／忙碌态和 reduced-motion；组件目录可通过本机 `/components.html` 或公开静态路径独立审查。公开部署与本机工作台共享组件，但用 `static_public_demo` 明确只读状态。该状态说明组件与交互合同已运行，不代表所有未来 Environment 已经完成，也不代表用户研究或真人校准已经完成。
