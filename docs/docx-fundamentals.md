# OOXML / docx 基础

## docx 本质 = zip + XML

```
报告.docx (ZIP)
├── [Content_Types].xml     # 每个文件的 MIME 声明
├── _rels/.rels             # 顶层关系
├── docProps/{app,core,custom}.xml
└── word/
    ├── document.xml        # ★ 正文所在
    ├── styles.xml          # 样式定义
    ├── numbering.xml       # 编号列表
    ├── settings.xml
    ├── fontTable.xml
    ├── _rels/document.xml.rels  # 图片、子文档等关系
    └── media/              # 所有嵌入的图片
```

## unpack / pack 流程

借助 `document-skills:docx` 里的 helper：

```bash
# 解压
python ${DOCX_SKILL}/scripts/office/unpack.py 输入.docx /tmp/unpacked
# 编辑 /tmp/unpacked/word/document.xml 等
# 打包回 docx
python ${DOCX_SKILL}/scripts/office/pack.py /tmp/unpacked 输出.docx \
    --original 输入.docx --validate false
```

`--original` 让 pack 继承模板的 meta / 字体 / 样式等；`--validate false` 绕过 WPS 模板常见的
broken reference 报错（见 pitfalls.md）。

## XML 层级速查

```
<w:document>
  <w:body>
    <w:p>        ← 段落
      <w:pPr>…</w:pPr>    ← 段落属性（居中、间距、缩进、段落级底色边框）
      <w:r>      ← run（同属性的一段字）
        <w:rPr>…</w:rPr>  ← 字符属性（字体、字号、颜色、加粗）
        <w:t>文字</w:t>   ← 实际文字
      </w:r>
    </w:p>
    <w:tbl>      ← 表格
      <w:tr>     ← 行
        <w:tc>   ← 单元格（内部又是 <w:p> 序列）
          <w:p>…</w:p>
        </w:tc>
      </w:tr>
    </w:tbl>
    <w:sectPr>…</w:sectPr>  ← 分节属性（页面大小、页边距、栏）
  </w:body>
</w:document>
```

## python-docx vs 直接 XML

| 维度 | python-docx | 直接 XML |
|---|---|---|
| 提取文字、遍历段落 | ✓ 方便 | 繁琐 |
| 改字号/加粗/颜色 | ✓ 方便 | 代码冗长 |
| 处理表格 cell | ✓ 方便 | 繁琐 |
| 插入图片 | ✓ 有 API | 要手写 `<w:drawing>` |
| 精确控制 pPr 子元素顺序 | ✗ 黑盒 | ✓ 必须 |
| 处理 WPS 特殊字段 | ✗ 不认识 | ✓ 可保留 |
| 精确样式调整（pBdr + shd） | 部分 | ✓ 完全控制 |

**推荐混用**：
- 阶段 1 用 python-docx 快速摘要模板结构（`scripts/inspect_template.py`）
- 阶段 4 拼接时用直接 XML（`scripts/builders.py`），避免 python-docx 吃掉样式

## 常见属性单位

- **字号 `<w:sz w:val="N"/>`**：半点。五号=10.5pt → `N=21`；小五=9pt → `N=18`
- **行距 `<w:spacing w:line="N" w:lineRule="auto"/>`**：二十分之一磅。1.5 倍 → `N=360`；单倍 → `N=240`
- **缩进 `<w:ind w:firstLineChars="200"/>`**：百分之一字符。200 = 首行缩进 2 个汉字宽
- **段前段后 `<w:spacing w:before="N" w:after="N"/>`**：二十分之一磅。常用 120~240
- **EMU**（图片用）：914400 EMU = 1 inch，见 image-embedding.md

## 字体 hint

中英文混排时：
```xml
<w:rFonts w:hint="eastAsia" w:ascii="Consolas" w:hAnsi="Consolas" w:eastAsia="宋体"/>
```
- `hint="eastAsia"`：优先按东亚字体渲染（中文）
- `ascii / hAnsi`：ASCII 和高位字符用的字体（英文/数字）
- `eastAsia`：中日韩字体
- `cs`：复杂脚本（阿拉伯等）
