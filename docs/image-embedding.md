# 图片嵌入

## EMU 换算

- 1 inch = **914400 EMU**
- A4/US Letter 正文宽（1 inch 页边距）≈ **5 inch = 4572000 EMU**
- 推荐像素密度：`3000 EMU/px`（1200 px → 3.6M EMU ≈ 3.94 inch，合适的代码/截图尺寸）
- 上限：超过 `MAX_CX = 4572000` 时 cx 截断、cy 按比例缩

## 三处必须同时维护

一张图嵌入 docx 涉及三个文件的协同：

1. **`word/media/xxx.png`** — 图片文件本身
2. **`word/_rels/document.xml.rels`** — 关系：`<Relationship Id="rIdXXX" Type=".../image" Target="media/xxx.png"/>`
3. **`word/document.xml`** — drawing 引用：`<a:blip r:embed="rIdXXX"/>`

漏一个都会打不开文档。`scripts/builders.py::embed_image()` 一次性处理这三者。

## cx / cy 出现两次

同一 drawing 内：
- `<wp:extent cx="X" cy="Y"/>` —— 行内布局尺寸
- `<a:ext cx="X" cy="Y"/>` —— spPr 内部尺寸

**两处必须相同**，否则图会被拉伸/截断。更新尺寸时两处都要改。

## Content_Types

绝大多数模板里 `[Content_Types].xml` 已经有：
```xml
<Default Extension="png" ContentType="image/png"/>
<Default Extension="jpeg" ContentType="image/jpeg"/>
```
如果没有，加一条。jpg 要加 `<Default Extension="jpg" ContentType="image/jpeg"/>`。

## 完整段落 XML

见 `templates/image_block.xml`，或用 `scripts/builders.py::build_image_paragraph()`。

## 居中 + 禁止并排

学术规范里每张图独立成段。调 `build_image_paragraph()` 就是段落级居中。不要把两个 `<w:drawing>`
放在同一个 `<w:p>` 的不同 `<w:r>` 里——Word 宽度不足时会换行成上下堆叠，caption 又写「左…右…」就错位了。
