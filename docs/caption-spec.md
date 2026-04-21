# Caption 规范（学术报告约定）

## 编号规则

- 格式：`图 X-Y  描述文字`（两个空格分隔）
- X = 章节号（中文章节用阿拉伯数字：一→1，二→2，以此类推）
- Y = 章节内的图序号，从 1 起
- 如果一个大章节下还要区分「图」与「表」，表单独编号为 `表 X-Y`
- 代码图**不需要** caption（代码本身即内容，冗余）

## 样式

- **居中**：`<w:jc w:val="center"/>`
- **字体**：黑色（默认继承正文字体，宋体/等线）
- **字号**：小五号 = 9pt = `<w:sz w:val="18"/>`（正文是五号 10.5pt，caption 小一号）
- **加粗**：`<w:b/><w:bCs/>`
- **位置**：紧跟图片段落下方，一个空行都不加

## XML 模板

```xml
<w:p>
  <w:pPr>
    <w:spacing w:before="60" w:after="180" w:line="276" w:lineRule="auto"/>
    <w:jc w:val="center"/>
    <w:rPr><w:rFonts w:hint="eastAsia"/><w:b/><w:bCs/><w:sz w:val="18"/></w:rPr>
  </w:pPr>
  <w:r>
    <w:rPr><w:rFonts w:hint="eastAsia"/><w:b/><w:bCs/><w:sz w:val="18"/></w:rPr>
    <w:t xml:space="preserve">图 2-1  Python 版 pb_demo.py 运行输出</w:t>
  </w:r>
</w:p>
```

直接调 `scripts/builders.py` 的 `build_caption_paragraph(chapter, idx, desc)` 获取。

## 何时不加

- **代码图**：silicon 渲染的代码 PNG 本身即"正文"，不需要 caption
- **装饰性元素**：logo、分隔线、水印
- **正文中紧邻句子的小图标**：caption 会打破语流

## 章节切换时 Y 归零

每到新章节 Y 从 1 重新开始。Agent 在写多图章节时要维护一个 `chapter_counters` dict，别搞错了。
