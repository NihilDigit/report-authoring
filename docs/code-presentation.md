# 代码展示：图片化 vs 文字代码块

两种风格，各有适用场景。**风格选择让用户决定，不要预设**。

## 风格 A · silicon 渲染成图片（推荐）

**优点**：
- 带语法高亮，视觉专业
- 不受 Word 排版影响（不会被中英文字体切换搞乱缩进）
- 整段作为一张图，版面干净

**缺点**：
- 文字不可复制
- 修改代码要重新渲染

**标准命令**：
```bash
silicon input.py -o output.png \
    --theme "GitHub" --background "#FFFFFF" \
    --no-window-controls \
    --font "Maple Mono NF CN" \
    --pad-horiz 0 --pad-vert 0 \
    --no-line-number \
    --language python
```

**关键参数理由**：
- `--theme GitHub`：浅色主题，和中文正文色调协调（深色终端截图已经提供了"对比色"）
- `--font "Maple Mono NF CN"`：支持 CJK 的等宽字体，否则中文注释渲染成方块
- `--pad-horiz/vert 0`：去外层白边，紧凑
- `--no-window-controls / --no-line-number`：学术报告不需要 Mac 风圆点/行号

**silicon 语言映射坑**（见 pitfalls.md）：
- `protobuf` → `proto`
- `thrift` → `cpp`
- 纯文本/目录树 → `ini`

## 风格 B · 文字代码块（pBdr + shd）

**优点**：
- 文字可复制
- 修改只改正文、不用重渲染
- 无需额外工具

**缺点**：
- 无语法高亮（或需要手工着色，成本大）
- 中英文字体切换可能打乱等宽对齐

**样式**：左侧粗竖线 + 浅灰背景。每一行代码独立成 `<w:p>`，用 `<w:pBdr>`（左竖线）+ `<w:shd>`
（浅灰填充）。相邻代码段自然形成块效果。

调 `scripts/builders.py::build_text_code_paragraph(line)` 获取。

**⚠️ pPr 元素顺序**：`pBdr → shd → spacing → ind → rPr`。放错顺序 OOXML 验证失败。

## 何时用哪种

| 场景 | 推荐 |
|---|---|
| 关键算法、会反复读的代码 | silicon 图（高亮有助理解） |
| 配置文件、命令、一两行简短示例 | silicon 图 或 文字块均可 |
| 需要用户直接复制运行的命令 | 文字块（可复制） |
| 长篇代码（> 30 行） | silicon 图 + 同时附完整源文件链接 |
| 混合中英文字体的代码 | silicon 图（避免 Word 字体切换破对齐） |

## 混用策略

同一份报告可以两种风格混用：**短命令行用文字块，核心算法/结构体用 silicon 图**。但整体以一种为主，
避免半段文字半段图看起来杂乱。
