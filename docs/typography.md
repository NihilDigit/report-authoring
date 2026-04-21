# 中文排版约定

## 字号映射（docx `<w:sz w:val="N"/>` 的 N = pt × 2）

| 中文字号名 | pt | sz val | 用途 |
|---|---|---|---|
| 小三 | 15 | 30 | 章节大标题 |
| 四号 | 14 | 28 | 二级标题 |
| 小四 | 12 | 24 | 三级标题 / 加粗强调 |
| 五号 | 10.5 | **21** | ★ **正文** |
| 小五 | 9 | **18** | ★ **caption / 脚注** |
| 六号 | 7.5 | 15 | 说明备注 |

## 正文常见约定（默认假设，**阶段 1 必须核对**）

以下是中文学术/工程报告里最常见的正文约定，也是 `scripts/builders.py` 里 `build_body_paragraph()`
的硬编码默认值。**不等于所有模板都这样**——各校/各课程/各单位的要求不同。阶段 1 用
`scripts/inspect_template.py` 会产出"模板实际 vs skill 默认"的 diff 表，若出现 diff 就要给 builder
传 `override` 参数（如 `build_body_paragraph(text, size=24, line=480, ...)`）。

| 维度 | skill 默认 | 含义 | 常见替代 |
|---|---|---|---|
| 字体（中文） | 宋体（模板 `<w:rFonts>` 决定） | 正文标准 | 仿宋、黑体（部分学校） |
| 字体（英文） | Times New Roman / Arial | 英文字符 | Calibri / Source Han |
| 字号 | 五号（sz=21） | 10.5 pt | 小四（sz=24）也常见 |
| 行距 | 1.5 倍（line="360" lineRule="auto"） | — | 单倍（240）、1.25 倍（300）、多倍（480=2 倍）|
| 首行缩进 | 两个汉字（ind firstLineChars="200"） | 中文书写习惯 | 无缩进（部分工程报告） |
| 段前段后 | before/after 120 | 中等间距 | 0（紧凑）、240（宽松）|

**决策规则**：
1. inspect_template 读到的模板**第一个正文段的实际样式**是 ground truth
2. 若该样式和 skill 默认一致，直接用 builder 默认值
3. 若不一致，把模板值作为 override 传给 builder，全文统一跟随模板

## 代码字体常见约定

- 首选 Consolas（模板可能已有），fallback：JetBrains Mono / Fira Code / Maple Mono NF CN
- 字号：小五（sz=20 ≈ 10pt）稍小于正文，保持紧凑
- 中英文混排时必须显式声明 `w:rFonts w:ascii=... w:hAnsi=... w:eastAsia=...`，否则英文和中文的字体
  不一致导致等宽失效

## 关于"诚实"

学术报告排版在中文学界有惯例但无单一标准。本 skill 的硬编码默认是**一个合理起点**，不是权威值。
读到这里的 Agent 应当：
- 把这些数字当"假设"而非"真理"
- **每次新报告都跑一次 `inspect_template.py` 对齐真实样式**
- 发现模板的惯例不同时主动告知用户，由用户确认跟随模板还是改模板
- 不要默默用 skill 默认值覆盖模板里老师设定的样式

## 中英混排小贴士

- 中文和英文之间习惯加半角空格（如 `Python 语言`），视觉更清爽
- 单位、数字、括号优先用半角：`126 字节`、`(展示用)`
- 专有名词保留原文大小写：protoc、Maven、Thrift（不要翻译成「节俭」）
