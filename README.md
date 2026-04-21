# report-authoring

一个 **agent skill**，用于撰写中文学术/工程类 docx 报告——实验报告、课程设计、项目总结、毕业设计等。

**核心工作流**：需求对齐 → 理解模板 → md 成稿 → 资产处理 → 拼接 → QA，每阶段都 HITL 回到用户。

## 为什么需要这个 skill

中文高校/公司的 docx 报告有很多**重复的体力活**：

- 正文章节按老师给的模板表格 cell 填写
- 代码片段要有语法高亮、格式规整
- 程序运行截图要裁切、居中、有编号 caption
- 字号字体行距符合「宋体五号 1.5 倍行距」之类的惯例

这些活**机械但容易出错**：代码缩进被 Word 吃掉、caption 编号跳号、图片格式被拉伸、OOXML 样式写错
导致文件打不开…… 本 skill 把这套流程沉淀成可复现的工具 + 文档，让 Agent 跟用户协作高效产出。

## 能力一览

| 阶段 | 能力 |
|---|---|
| 理解模板 | python-docx 摘要 + OOXML XML 解析 |
| md 成稿 | 与用户协作的 markdown 中转稿模式，占位符约定 |
| 代码展示 | silicon 语法高亮图（推荐）/ 文字代码块（左竖线 + 灰底） |
| 终端截图 | Niri + Alacritty 无鼠标全自动 / 其他平台指导手动 |
| 图片处理 | ImageMagick 裁空白、按原始分辨率居中、禁止并排、编号 caption |
| 排版规范 | 中文字号字体行距、caption 样式、章节内编号规则 |
| 打包 QA | docx → PDF 预览 → 清单式核查 |

## 安装

本仓库符合 [Agent Skills 开放标准](https://agentskills.io)（Anthropic 2025 年 10 月发布，12 月开放，
已有 40+ 平台采纳：Claude Code / Cursor / OpenAI Codex / GitHub Copilot / Gemini CLI / JetBrains Junie / OpenHands 等）。

**最简单**：直接跟你的 Agent 说：
> 安装 report-authoring skill  
> （或：帮我把 https://github.com/NihilDigit/report-authoring 装成一个 skill）

Agent 应能理解并把仓库 clone 到正确位置。

**手动安装**（各平台 skill 目录）：
```bash
# Claude Code
git clone https://github.com/NihilDigit/report-authoring.git ~/.claude/skills/report-authoring

# Cursor / VS Code Copilot / Gemini CLI 等多数平台
git clone https://github.com/NihilDigit/report-authoring.git <平台的 skills 目录>
```

`SKILL.md` 的 YAML frontmatter 遵守标准字段（`name` / `description` / `allowed-tools`），
各平台都能识别。Claude Code 专有扩展字段（`context: fork` 之类）本 skill 未使用，确保最大兼容性。

## 依赖

运行时需要：

| 工具 | 必需度 | 用途 |
|---|---|---|
| Python 3.10+ | ★ 必需 | builders / scripts |
| `python-docx` | ★ 必需 | 模板摘要 |
| `silicon`     | ★ 必需 | 代码图片渲染 |
| `ImageMagick` | ★ 必需 | 图片裁切 |
| `LibreOffice` / `soffice` | 必需 | docx → PDF 预览 |
| `poppler`（`pdftoppm`） | 必需 | PDF → JPG 预览 |
| Niri 25+ / Hyprland / Sway | 可选 | Wayland 合成器下终端截图全自动 |
| Alacritty | 可选 | 搭配上面自动截图 |
| `jq` | 可选 | 配合 Niri JSON 输出 |

Arch / CachyOS 一键装：
```bash
sudo pacman -S python-docx silicon imagemagick libreoffice-fresh poppler alacritty jq
# Niri 按自己窗口管理器选择
```

## 快速开始

用户给 Agent：「帮我写实验报告，模板是 `~/实验一模板.docx`，项目在 `~/code/exp1`。」

Agent 自动按 SKILL.md 里的**五阶段流程**推进：
1. 阶段 0：问清楚报告类型、交付目标、排版偏好
2. 阶段 1：`inspect_template.py` 摘要模板
3. 阶段 2：与用户一起在 `report.md` 写正文，边写边 HITL
4. 阶段 3：`capture.sh` / `silicon_cli.sh` / `trim_png.sh` 批量生成图
5. 阶段 4：`builders.py` 拼接进 docx
6. 阶段 5：`preview_docx.sh` QA → 交付

## 扩展机制

本 skill 设计成**渐进式积累**，做完一份新报告后发现坑/技巧就往对应文件里加：

- 新工具链坑 → `docs/pitfalls.md`
- 新样式约定 → `docs/typography.md` / `docs/caption-spec.md`
- 新类型报告 → `report-formats/<kind>.md`
- 新自动化工具 → `scripts/`

## 路线图

- [ ] 其他 Agent 平台适配（Gemini、Codex、自建 Agent）
- [ ] Windows 上手动截图的 helper（目前是 Agent 指导）
- [ ] `report-formats/` 扩充：课程设计、毕设、技术方案
- [ ] 表格（`<w:tbl>`）builder
- [ ] 自动编号的公式（非代码类 caption）

## 贡献

**欢迎踩坑 → 提 Issue / PR**。本 skill 设计成渐进式积累：

- 发现新的工具链坑 / OOXML schema 坑 → 往 `docs/pitfalls.md` 里加条目
- 新类型报告的结构约定 → 在 `report-formats/` 加 `<kind>.md`
- 新的排版技巧 / 字体组合 → 更新 `docs/typography.md` 或 `docs/caption-spec.md`
- 新的自动化工具（其他窗口管理器的截图、新的代码渲染器等）→ `scripts/` 加小工具 + 更新 SKILL.md 导航

Issue 模板建议说清楚：触发条件、期望行为、实际表现、最好附上最小复现。PR 欢迎所有合理改进。

## License

MIT（见 LICENSE）
