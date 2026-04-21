# 阶段 1 · 理解模板格式

## 两种手段

### A. python-docx 快速摘要

用 `scripts/inspect_template.py` 输出所有段落文字 + 表格 cell 内容，帮你迅速建立"这份模板有哪些
章节、哪些空 cell 需要填"的心智图。

```bash
python scripts/inspect_template.py 模板.docx
```

**输出格式**（示例）：
```
[P 0] 《大数据计算与可视化》实验报告
[P 1] （空）
[T 0] table 5 rows × 2 cols
  [T 0, 0,0] 实验名称
  [T 0, 0,1] 实验二 数据采集与网络传输
  [T 0, 1,0] 实验目的与要求
  [T 0, 1,1] （长文本…）
  [T 0, 2,0] 实验过程
  [T 0, 2,1] （空 — 待填）
  [T 0, 3,0] 结果分析
  [T 0, 3,1] （空 — 待填）
```

### B. unpack + 看 XML

当 python-docx 看不清楚（比如表格里嵌套段落样式、占位符带彩色提示）时，解压看 XML：

```bash
python ${DOCX_SKILL}/scripts/office/unpack.py 模板.docx /tmp/unpacked
# 用 Grep / Read 查看 /tmp/unpacked/word/document.xml
```

## 产出物（给用户确认）

一份模板 summary，内容包括：
1. 有哪些章节 / 表格
2. 每个要填的 cell 是什么
3. 有没有占位符文字（比如「（写实验报告时删除说明内容）」这类，后续要删掉）
4. 表格 cell 内部的 pPr 样式（是否已预设字体、行距——决定是否要在插入时覆盖）

## 什么时候要改模板本身的样式？

一般**不改**。模板由老师/学校定，保持原格式用户才方便提交。只在以下情况改：
- 用户明确授权"随便调"
- 模板里的样式明显错（比如正文字号是小六号这类显然超出规范的）
