# 公开 Demo 与部署边界

状态：`v0.2.0-alpha.3` 发布候选，2026-08-21。

## 两种运行面

Audience Mirror 使用同一套界面系统提供两个边界明确的运行面。

| 运行面 | 数据来源 | 可执行能力 | 明确不做 |
| --- | --- | --- | --- |
| GitHub Pages 公开体验 | 仓库内合成 Timeline、合成 Persona、确定性 Trace | 浏览时间轴、证据、个体 Trace、分歧、口径、主题和组件目录 | 不上传、不解析视频、不调用模型、不保存输入、不导入真人数据 |
| 本机 FastAPI 工作台 | 用户明确授权的链接／文件与本机制品 | 链接或文件导入、本机解码、可选远程多模态分析、顺序体验、Human Anchor 校准 | 默认不监听公网；机密／受限素材不走公有模型路由 |

公开体验不是伪造后端。`audience-mirror export-static-demo` 从公开合成 Fixture 生成 `web/static-demo.js`，页面只有在 `/api/*` 不可用时才进入 `static_public_demo`。状态栏、限制清单和所有写操作都会显示只读边界；输入不会被发送。

## 可复现静态包

```bash
audience-mirror export-static-demo --output web/static-demo.js
python -m http.server 4173 --directory web
```

生成内容固定包含：

- `schema_version = audience-mirror.static-demo/v0.1`；
- 10,000 条 Persona Pool 口径、6 个 Deep Persona 和对应确定性 Trace；
- `human_participants = 0`；
- 空媒体 URL 与空证据帧 URL；
- 上传、链接解析、视频模型、Agent 模型和真人校准能力均为 `false`。

静态包不枚举 `artifacts/`，不读取本机工作台实验，不包含媒体、字幕、Cookie、密钥、私人路径或真人记录。CI 会重新生成并验证静态包；Pages 只发布 `web/`。

## 界面与组件库

`web/components.html` 是随产品发布的 Component Lab，不是独立品牌稿。它与工作台共享 `web/styles.css` 的颜色、排版、空间、焦点、动效与状态 Token，并覆盖：

- Button、Icon Button、Field、Select、Segmented Control、Tabs、Disclosure；
- Media Stage、Evidence Claim、Timeline Cue、Trace Session、Method Boundary；
- loading、empty、error、success、disabled、focus-visible 与 reduced-motion。

当前无构建链的原型继续使用原生 HTML／CSS／JavaScript，以减少首发依赖和保持可审计。进入多环境、多用户产品阶段后，优先采用 Base UI 承担无样式可访问 Primitive，React Aria 补充复杂集合与国际化；Audience Mirror 的证据业务组件、视觉 Token 和品牌动效保持自主实现。组件迁移须同时建立 Storybook、视觉回归和键盘行为测试，不能只替换外观。

## 发布与验收

`.github/workflows/pages.yml` 按 GitHub 官方自定义 Pages 流程使用 `configure-pages`、`upload-pages-artifact` 与 `deploy-pages`。发布前必须通过：

1. 全量 Python 测试与 JavaScript 语法检查；
2. 390px 与桌面宽度无页面级横向溢出；
3. 默认浅色、深色和 reduced-motion；
4. 静态模式控制台零错误，所有写操作均产生边界清楚的反馈；
5. 公开包隐私扫描为零，仓库不包含受限媒体或真人数据。

GitHub Pages 的数据与日志处理仍受 GitHub 当期服务与隐私条款约束；本项目的公开静态页面本身不设置账户、分析 SDK 或表单提交端点。
