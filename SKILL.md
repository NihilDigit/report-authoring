---
name: report-authoring
description: >
  撰写中文学术/工程类 docx 报告（实验报告、课程设计、项目总结、毕业设计等）。当用户给出一个 docx
  模板并希望系统性地填入正文、代码、截图、图表、caption 时触发。本 skill 提供一套五阶段工作流：
  需求对齐 → 理解模板 → md 成稿 → 资产处理 → 拼接 → QA，每个 HITL 检查点都回到用户确认。覆盖：
  模板解析（python-docx / XML）、代码片段展示（silicon 语法高亮图 / 文字代码块）、终端截图
  自动化、图片裁切居中、caption 章节编号、中文排版约定、OOXML 常见坑。
  Triggers: "写实验报告"、"课程设计报告"、"报告排版"、"把截图放进报告"、"给代码加高亮图"、
  "给图加编号 caption"、"docx 模板填充"、"实验报告格式"。
user-invocable: true
allowed-tools: Bash, Read, Write, Edit, Grep, Glob
---

# report-authoring

把一份 docx 模板 + 用户的原始素材（代码、运行结果、图表数据）变成规范的中文学术/工程报告。

## 何时使用

用户的情境通常是：
- 老师/学校提供了 docx 模板（含章节表格、占位符或空白 cell），要填入一次实验/设计的完整内容
- 需要把程序代码、运行截图、图表说明嵌入正文，并保持统一排版
- 最终产出是 docx（可能再转 PDF 提交）

## 核心工作流（五阶段 + HITL）

```
┌─────────┐   ┌──────────┐   ┌──────────┐   ┌──────────┐   ┌────────┐
│0. 需求  │-> │1. 理解   │-> │2. md     │-> │3. 资产   │-> │4. 拼接 │-> QA
│   对齐  │   │   模板   │   │   成稿   │   │   处理   │   │        │
└─────────┘   └──────────┘   └──────────┘   └──────────┘   └────────┘
    HITL          HITL           HITL           HITL         HITL
```

**每个阶段结束前回到用户确认**。这不是可选 polite，而是硬性要求——报告是用户自己的作品，不是
Agent 的一次性生成物。

### 阶段 0 · 需求对齐（必须先做，不可跳）

**目的**：建立用户的心智模型，锚定整个流程。**这一步能挽救所有后续的返工**。

在动手前与用户确认清楚：

1. **报告类型**：实验报告？课程设计？毕设中期？毕设终稿？项目总结？
   → 决定用哪份 `report-formats/*.md` 作结构参考
2. **模板位置**：docx 模板绝对路径
3. **项目位置**：要展示的代码/运行在哪个目录
4. **交付目标**：最终是 docx 还是 docx + PDF？是否有页数限制？
5. **排版偏好**（给出默认值让用户确认）：
   - 代码展示：silicon 浅色主题语法高亮图（推荐）/ 文字代码块 / 纯等宽文字
   - Caption 样式：黑色加粗小五号居中 + 章节编号（推荐）
   - 图片是否居中、是否禁止并排
6. **行文风格**：见 `docs/writing-style.md`。硬性 6 条（口语 / 黑话 / 过度工程化 / 欧化 /
   翻译腔 / overclaim）必守。风格松紧度三选一：严肃学术 / 平实书面（默认）/ 技术文档——
   给用户看三段样例再选
7. **篇幅策略**：哪些章节详写哪些简写？哪些代码/截图必须有哪些可省？
8. **时间盒**：用户今天需要的是完整交付还是第一版草稿？

把回答整理成一个小清单，让用户最后 confirm 一次再进下一阶段。

### 阶段 1 · 理解模板格式

把 docx 模板解析清楚，告诉用户"你的模板长这样"，让他知道后续填写会落在哪里。

**两种解析方式，互补使用**：

| 方式 | 适用场景 | 工具 |
|---|---|---|
| `python-docx` | 快速列出所有段落/表格/cell 的文字，看章节结构 | `scripts/inspect_template.py` |
| 直接 XML | 需要精确把握 pPr/rPr 样式、占位符位置、cell 边界 | `document-skills:docx` 的 `unpack.py` |

**产出物**：一份模板结构说明（章节、要填内容的 cell 列表、是否有占位符"（此处删除）"之类），回给用户
确认。

详见 `docs/template-inspection.md`。

### 阶段 2 · md 成稿（HITL 重灾区）

用户和 Agent **在 Markdown 里共同撰写**报告正文。这一步绝不跳过。

**为什么用 md 中转**：
- 用户能直接读/改/diff，不需要打开 Word
- 纯文本协作，Agent 输出效率最高
- 代码/图片只写**占位**（`{{IMG:xxx.png}}`、` ```python ... ``` `），不做实际处理

**md 文件结构约定**（避免后续拼接时混乱）：
```markdown
# 实验名
## 一、开发环境与项目结构
正文…
```bash
uv add protobuf avro thrift
```
{{IMG: part1_env_tree}}

## 二、Protocol Buffers 序列化
```

HITL 要点：每写完一大节就停下来让用户读一遍、改/补/删，**再写下一节**。一次性写完再让用户全文审
阅是最差策略。详见 `docs/md-authoring.md`。

**行文风格在第一段之前就要对齐**。硬性 6 条（口语 / 大厂黑话 / 过度工程化 / 汉语欧化 / 英语翻译腔
/ overclaim 或堆限制条件）必守。风格松紧度让用户从三段样例里选（严肃学术 / 平实书面 / 技术文档）。
详见 `docs/writing-style.md`。

### 阶段 3 · 资产处理

这时 md 里的占位符已经明确了"要什么图、要什么代码块"。开始把占位符变成真资产。

**资产 = 图片（截图、代码图、图表）+ 最终代码片段**。

```
对 md 里每一处 {{IMG:label}}：
  - 若是终端截图：scripts/capture.sh <label> "<命令>"
  - 若是代码图（silicon 渲染）：scripts/silicon_cli.sh <src> <lang> <out>
  - 若是已有截图：用户提供路径，调 scripts/trim_png.sh 裁切
  → 产出 PNG 放在 assets/<label>.png
  → 让用户看一下截图是否合意（HITL）
```

**HITL 点**：每张图生成后 qimgv 弹给用户看，不满意就重跑。不要一次生成 20 张让用户事后挑。详见
`docs/terminal-capture.md`、`docs/code-presentation.md`、`docs/image-embedding.md`。

### 阶段 4 · 拼接

md + 资产 → 填入 docx 模板。

**构建优先**：按 md 的顺序，每遇到一段文字/代码/占位符，调 `scripts/builders.py` 里的 builder 函数
生成对应 `<w:p>` XML，一次性写入目标 cell。不要先写纯文字再扫描替换——那是 `scripts/migration/`
提供的"救已有半成品"能力，写新报告时不需要。

关键 builder（见 `scripts/builders.py`）：
- `build_body_paragraph(text)` — 正文段（宋体五号 1.5 倍行距）
- `build_heading(text, level)` — 章节标题
- `build_code_image_paragraph(png_path, media_dir, rels)` — silicon 代码图嵌入
- `build_screenshot_paragraph(png_path, chapter, idx, caption, media_dir, rels)` — 终端截图 + 编号 caption
- `build_caption_paragraph(chapter, idx, text)` — 独立 caption 段

详见 `docs/docx-fundamentals.md`、`docs/image-embedding.md`、`docs/caption-spec.md`。

### 阶段 5 · QA

**必做**：生成 PDF 预览 + 目测每一页 + 让用户过目。

```bash
soffice --headless --convert-to pdf output.docx --outdir /tmp
pdftoppm -jpeg -r 100 /tmp/output.pdf /tmp/preview
```

检查清单（`docs/qa-checklist.md`）：
- [ ] 所有章节标题在正确位置
- [ ] 所有 `{{IMG:xxx}}` 占位都被真实图片替换，没有残留
- [ ] 图片居中、未跨页撕裂
- [ ] Caption 编号连续（图 2-1、2-2… 无跳号）
- [ ] 代码图字号统一（同一 EMU/px 密度）
- [ ] 页眉页脚、页码正确
- [ ] 字体中英混排无错字、无字体丢失

**HITL 收尾**：让用户打开 docx（不是 PDF）做最后校对。Agent 不能代替用户的终审。

## 目录

```
report-authoring/
├── SKILL.md              本文件
├── docs/                 专题文档（按需读）
│   ├── template-inspection.md  阶段 1：解析模板
│   ├── md-authoring.md         阶段 2：md 成稿 HITL 模式
│   ├── writing-style.md        阶段 2：行文风格（硬性避免 + 风格对齐）
│   ├── terminal-capture.md     阶段 3：Niri + Alacritty 截图
│   ├── code-presentation.md    阶段 3：silicon 渲染 / 文字代码块
│   ├── image-embedding.md      阶段 4：图片嵌入 XML / EMU / cx-cy
│   ├── caption-spec.md         阶段 4：caption 样式 / 编号
│   ├── typography.md           阶段 4：中文排版约定
│   ├── docx-fundamentals.md    阶段 4：OOXML 基础 / unpack-pack / schema 坑
│   ├── qa-checklist.md         阶段 5：QA 清单
│   └── pitfalls.md             跨阶段坑合集
├── report-formats/       不同类型报告的结构参考
│   ├── lab-report.md           实验报告（目的/过程/结果分析）
│   └── README.md               新增格式的 contributing
├── scripts/              可执行工具
│   ├── builders.py             ★ 阶段 4 主力：XML 段落构建器
│   ├── inspect_template.py     阶段 1：python-docx 摘要模板
│   ├── capture.sh              阶段 3：Niri + Alacritty 自动截图
│   ├── silicon_cli.sh          阶段 3：源码 → 语法高亮 PNG
│   ├── trim_png.sh             阶段 3：magick 裁黑色空白
│   ├── preview_docx.sh         阶段 5：docx → PDF → JPG 快速预览
│   └── migration/              救已有半成品 docx 的扫描工具
│       ├── scan_and_render_codes.py
│       └── finalize_existing.py
└── templates/            可复用 XML 片段
    ├── image_block.xml
    ├── code_block_text.xml
    └── section_heading.xml
```

## 对 Agent 的元指导

- **HITL 不是装饰**：每个阶段边界都必须回到用户。一次性跑完五阶段是危险做法
- **先对齐，再执行**：阶段 0 的需求对齐清单必须让用户 confirm，哪怕用户说"你自己定"也要给默认值让用户点头
- **增量交付**：20 张图不要一次生成。先 2 张给用户看风格，确认后再批量
- **md 是中转站**：正文内容永远先在 md 稿定稿再填 docx，不要直接写 docx
- **构建优先，扫描备用**：新报告用 `scripts/builders.py`；接手别人的半成品才用 `scripts/migration/`
- **沉淀坑**：做完一份报告若遇到新坑，更新 `docs/pitfalls.md` 或对应专题
- **保留用户的判断权**：排版风格、详略取舍、章节组织，用户的偏好优先于 skill 的默认值
