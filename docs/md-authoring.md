# 阶段 2 · md 成稿 HITL 模式

## 为什么先写 md 再填 docx

- md 纯文本，diff / 搜索 / 粘贴超好用
- 用户能直接读懂、直接改、直接说「这段删掉」
- Agent 输出文本效率最高
- 图片/代码只占位不实做，改结构无成本

## 目录布局

```
project/
├── 模板.docx                原始模板
├── report.md                ← md 正文稿（与用户协作的主战场）
├── assets/                  ← 阶段 3 产出的 PNG
│   ├── fig-2-1-pb-python.png
│   └── …
└── output.docx              ← 阶段 4 产出
```

## md 段落约定

- `# 章节一级标题` 对应 docx 里的大章节
- `## 小节二级标题`
- 正文用普通 markdown 段落；Agent 写每段后问用户是否继续
- 代码：` ```python ... ``` ` 或 ` ```bash ... ```（阶段 4 转为 silicon 图或文字代码块）
- 图片：`{{IMG: label-name}}`（阶段 3 在 assets/label-name.png 生成）
- 表格：标准 markdown 表格

## 占位符命名

**约定**：`{{IMG: partN_context_description}}`，label 用小写 + 下划线/短横线。例如：
- `{{IMG: part1_tree}}` 项目目录 tree
- `{{IMG: tcp-server-log}}` TCP 服务端日志
- `{{IMG: split-files-list}}` avro_files 文件列表

**文件名与 label 一致**：`assets/part1_tree.png`

## HITL 节奏

**错**：一次写完全文 1500 字再让用户审 → 改动成本高，用户易疲劳
**对**：每章（或每两节）一个 checkpoint
```
Agent: 我写完了「二、Protobuf」的 1/2/3 节（基础 + Python），你看看？
User:  第 3 节的 Book 结构例子太长，简化成 5 个字段。第 2 节 OK。
Agent: 好，改完了：[...]。继续第 4 节 Java 吗？
User:  继续。
```

## md 里不做什么

- **不做排版样式**（字号、行距、缩进）——留给阶段 4 的 builders
- **不插真图片**——只占位
- **不生成最终代码** silicon 图——先写 markdown code fence

## 成稿检查

定稿的 md 应满足：
- [ ] 每个 `{{IMG:xxx}}` 的 xxx 都能在阶段 3 落实成真图
- [ ] 每个 code block 用户都同意现在的内容
- [ ] 章节编号连贯，与模板结构对上
