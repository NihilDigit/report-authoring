# scripts/migration/ — 扫描式工具（应急用）

这里的脚本**不是**写新报告的主路径。请先看 SKILL.md 的五阶段流程：新报告都应该走
`scripts/builders.py` 的**构建**模式，每张图/每段正文在写的时候就规范好，不走扫描。

本目录存在的意义是：**接手别人的半成品 docx** 或 **自己早期写歪了的文档**，要批量回填。

## In scope（适用场景）

✅ 用户拿到一份已经写了正文的 docx，需要：
- 把里面所有 Consolas 文字代码段**批量**渲染成 silicon 图
- 把零散插入的截图**批量**裁空白、编号 caption、居中
- 把并排放的图**批量**拆成独立段 + caption

✅ 从 Markdown 或旧版模板导入的 docx，需要一次性规范化

✅ **本 skill 诞生的场景**：之前手工写了正文、逐一加图，想回头统一格式

## Out of scope（不适用场景）

❌ 写全新报告 —— 用 `scripts/builders.py`（`build_body_paragraph` / `build_heading` /
`build_screenshot_block` 等），边写边规范，不要先写脏再清

❌ 只修改一两张图 —— 直接手动 Edit XML 或让用户在 Word 里调，不值得上脚本

❌ 跨 cell / 跨表格的复杂位置调整 —— 扫描正则难保证不跨块，手工 XML 更稳

❌ 保留模板已有的特殊样式（老师自定义的 pPr）—— migration 脚本会覆盖样式为 skill 默认，这不是你要的

## 脚本清单

### `scan_and_render_codes.py`
扫描 `document.xml` 里所有连续的 Consolas 段落（本 skill 约定代码段用 Consolas 字体），聚合成代码块，
调 silicon 渲染成 PNG，然后用图片段替换原文字段落。同时维护 `_rels/document.xml.rels`。

**用法**：
```bash
python scripts/migration/scan_and_render_codes.py <unpacked_dir> \
    [--theme GitHub] [--font "Maple Mono NF CN"] [--rid-start 200]
```

**坑**：
- 若文档里有 Consolas 但非代码（比如技术术语行内），会被误伤 → 先在 Word 里用不同字体
- 替换后文字不可复制 → 和用户确认过再跑
- 语言推断基于内容启发式，不准时脚本会 fallback 到 `ini`

### `crop_screenshots.py`
批量裁切 `word/media/` 下所有 `image*.png` 的背景空白（magick `-trim`），就地覆盖。

**用法**：
```bash
python scripts/migration/crop_screenshots.py <unpacked_dir>/word/media [--fuzz 15%] [--border 12]
```

**坑**：
- 跳过 `image1.png` / `image2.png`（模板 logo 用）—— 若你的模板不是这样，调 `--skip-prefix`
- 裁切后图片像素尺寸变了，但 `document.xml` 里的 cx/cy 还是旧值。要再跑一次 `builders.py` 里的
  `image_emu()` 重算、或者用 XML 替换脚本同步 —— 历史上漏掉这步导致图被拉伸

## 和 builders 的关系

扫描脚本产出的最终 XML 片段和 `builders.py` 一致（居中、3000 EMU/px、编号 caption 等约定）。
一份 docx 可以**先跑 migration 救回来**，之后新增的内容再走 builders 构建模式，不冲突。

## 不要做什么

- 不要把 migration 脚本放进阶段 4 的主流程（SKILL.md 的「拼接」步骤）。主流程应是 builders。
- 不要在同一个 docx 上反复跑 migration —— 它没做幂等保护，重复跑会导致图片文件名、rId 冲突
  （见 pitfalls.md 里"image_code_00 被后续运行覆盖"那一条）
- 不要迷信扫描正则。处理复杂模板时**读用户的模板 XML** 优先于机械替换
