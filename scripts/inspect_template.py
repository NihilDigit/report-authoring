#!/usr/bin/env python3
"""
inspect_template.py — 阶段 1：摘要 docx 模板的结构与样式。

输出三部分：
  1) 顶层段落 + 表格（递归展开嵌套 cell/table）
  2) sectPr 页面几何
  3) ★ 样式 diff 表：「模板实际样式 vs skill 硬编码默认」——Agent 看到 diff 就知道要不要
     给 builders.py 的函数传 override 参数

用法：
    uvx --with python-docx python inspect_template.py <docx>

依赖：python-docx。临时用 `uvx --with python-docx`；常用则 `uv tool install python-docx`。
"""
from __future__ import annotations

import sys
from pathlib import Path
from zipfile import ZipFile
import xml.etree.ElementTree as ET


# -------------- skill 硬编码默认（来自 builders.py，同步更新）--------------
# 注意：这些是「常见约定」而非权威值。见 docs/typography.md 的「诚实」段。
SKILL_DEFAULTS = {
    "body.size":       {"val": 21,  "note": "五号 10.5pt"},
    "body.line":       {"val": 360, "note": "1.5 倍行距"},
    "body.lineRule":   {"val": "auto", "note": ""},
    "body.firstLine":  {"val": 200, "note": "首行缩进 2 字符（firstLineChars）"},
    "body.jc":         {"val": "left", "note": "左对齐（含两端对齐亦可）"},
    "heading1.size":   {"val": 24,  "note": "小三"},
    "heading2.size":   {"val": 22,  "note": "四号"},
    "heading3.size":   {"val": 21,  "note": "小四"},
    "caption.size":    {"val": 18,  "note": "小五 + 加粗 + 居中"},
    "code.size":       {"val": 20,  "note": "稍小于正文（10pt）"},
    "code.font":       {"val": "Consolas", "note": ""},
}

W_NS = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
W = f"{{{W_NS}}}"


# -------------- python-docx 遍历（段落 + 递归表格） --------------

def dump_paragraphs(paragraphs, indent: str = ""):
    for i, p in enumerate(paragraphs):
        text = p.text.strip()
        marker = "（空）" if not text else text[:80] + ("…" if len(text) > 80 else "")
        print(f"{indent}[P {i:3d}] {marker}")


def dump_table(tbl, tid: str, indent: str = ""):
    rows, cols = len(tbl.rows), len(tbl.columns)
    print(f"\n{indent}[T {tid}] {rows} rows × {cols} cols")
    for r, row in enumerate(tbl.rows):
        for c, cell in enumerate(row.cells):
            text = cell.text.strip()
            marker = "（空）" if not text else text[:80] + ("…" if len(text) > 80 else "")
            print(f"{indent}  [T {tid} {r},{c}] {marker}")
            # 递归：cell 里可能还有嵌套表格
            if cell.tables:
                for ntid, ntbl in enumerate(cell.tables):
                    dump_table(ntbl, f"{tid}.{r}.{c}.{ntid}", indent + "    ")


# -------------- 直接解析 XML 提取样式 --------------

def _read_xml(zf: ZipFile, name: str) -> ET.Element | None:
    try:
        with zf.open(name) as f:
            return ET.fromstring(f.read())
    except KeyError:
        return None


def _get(elem, tag: str):
    """返回第一个子元素的指定属性值，或 None"""
    return elem.find(f"{W}{tag}") if elem is not None else None


def _attr(node, attr: str) -> str | None:
    if node is None:
        return None
    return node.get(f"{W}{attr}")


def extract_default_styles(styles_root: ET.Element | None) -> dict:
    """从 styles.xml 的 w:docDefaults + w:style[type=paragraph default] 提取默认值"""
    out = {}
    if styles_root is None:
        return out

    # w:docDefaults > w:rPrDefault/w:rPr 里有默认字号/字体
    rpr_default = styles_root.find(f"{W}docDefaults/{W}rPrDefault/{W}rPr")
    if rpr_default is not None:
        sz = _get(rpr_default, "sz")
        out["docDefault.size"] = _attr(sz, "val")
        fonts = _get(rpr_default, "rFonts")
        if fonts is not None:
            out["docDefault.ascii"] = fonts.get(f"{W}ascii")
            out["docDefault.eastAsia"] = fonts.get(f"{W}eastAsia")

    # w:docDefaults > w:pPrDefault/w:pPr 里有默认段落属性
    ppr_default = styles_root.find(f"{W}docDefaults/{W}pPrDefault/{W}pPr")
    if ppr_default is not None:
        spacing = _get(ppr_default, "spacing")
        if spacing is not None:
            out["docDefault.line"] = spacing.get(f"{W}line")
            out["docDefault.lineRule"] = spacing.get(f"{W}lineRule")
        ind = _get(ppr_default, "ind")
        if ind is not None:
            out["docDefault.firstLineChars"] = ind.get(f"{W}firstLineChars")

    # default="1" 的段落样式（通常 styleId="Normal" / "正文"）
    for style in styles_root.findall(f"{W}style"):
        if style.get(f"{W}type") == "paragraph" and style.get(f"{W}default") == "1":
            sid = style.get(f"{W}styleId", "?")
            out["normal.styleId"] = sid
            rpr = _get(style, "rPr")
            if rpr is not None:
                sz = _get(rpr, "sz")
                if sz is not None:
                    out["normal.size"] = sz.get(f"{W}val")
                fonts = _get(rpr, "rFonts")
                if fonts is not None:
                    out["normal.ascii"] = fonts.get(f"{W}ascii")
                    out["normal.eastAsia"] = fonts.get(f"{W}eastAsia")
            ppr = _get(style, "pPr")
            if ppr is not None:
                spacing = _get(ppr, "spacing")
                if spacing is not None:
                    out["normal.line"] = spacing.get(f"{W}line")
                    out["normal.lineRule"] = spacing.get(f"{W}lineRule")
                ind = _get(ppr, "ind")
                if ind is not None:
                    out["normal.firstLineChars"] = ind.get(f"{W}firstLineChars")
                jc = _get(ppr, "jc")
                if jc is not None:
                    out["normal.jc"] = jc.get(f"{W}val")
            break
    return out


def extract_first_body_paragraph(doc_root: ET.Element | None) -> dict:
    """从 document.xml 取第一个有文字、看起来像正文（非标题）的 <w:p>"""
    out = {}
    if doc_root is None:
        return out
    body = doc_root.find(f"{W}body")
    if body is None:
        return out
    for p in body.findall(f"{W}p"):
        # 是否有文字
        texts = [t.text or "" for t in p.iter(f"{W}t")]
        if not any(t.strip() for t in texts):
            continue
        # 先不跳过标题样式——取最早的有文字段，agent 自己判断
        out["text_preview"] = "".join(texts)[:60]
        ppr = _get(p, "pPr")
        if ppr is not None:
            pstyle = _get(ppr, "pStyle")
            out["p.pStyle"] = _attr(pstyle, "val")
            spacing = _get(ppr, "spacing")
            if spacing is not None:
                out["p.line"] = spacing.get(f"{W}line")
                out["p.lineRule"] = spacing.get(f"{W}lineRule")
            ind = _get(ppr, "ind")
            if ind is not None:
                out["p.firstLineChars"] = ind.get(f"{W}firstLineChars")
            jc = _get(ppr, "jc")
            if jc is not None:
                out["p.jc"] = jc.get(f"{W}val")
            rpr_in_ppr = _get(ppr, "rPr")
            if rpr_in_ppr is not None:
                sz = _get(rpr_in_ppr, "sz")
                if sz is not None:
                    out["p.size"] = sz.get(f"{W}val")
        # 第一个 run 的 rPr
        r = _get(p, "r")
        if r is not None:
            rpr = _get(r, "rPr")
            if rpr is not None:
                sz = _get(rpr, "sz")
                if sz is not None:
                    out["r.size"] = sz.get(f"{W}val")
                fonts = _get(rpr, "rFonts")
                if fonts is not None:
                    out["r.ascii"] = fonts.get(f"{W}ascii")
                    out["r.eastAsia"] = fonts.get(f"{W}eastAsia")
        break
    return out


# -------------- diff 打印 --------------

def _coalesce(*vals):
    """返回第一个非 None / 非空的值"""
    for v in vals:
        if v not in (None, ""):
            return v
    return None


def print_style_diff(styles_data: dict, body_data: dict):
    """把实际样式和 SKILL_DEFAULTS 做 diff，以表格形式打印"""
    # 正文字号：优先首段 run rPr > 首段 pPr rPr > normal 样式 > docDefault
    actual_body_size = _coalesce(
        body_data.get("r.size"),
        body_data.get("p.size"),
        styles_data.get("normal.size"),
        styles_data.get("docDefault.size"),
    )
    actual_body_line = _coalesce(
        body_data.get("p.line"),
        styles_data.get("normal.line"),
        styles_data.get("docDefault.line"),
    )
    actual_body_line_rule = _coalesce(
        body_data.get("p.lineRule"),
        styles_data.get("normal.lineRule"),
        styles_data.get("docDefault.lineRule"),
    )
    actual_body_first = _coalesce(
        body_data.get("p.firstLineChars"),
        styles_data.get("normal.firstLineChars"),
        styles_data.get("docDefault.firstLineChars"),
    )
    actual_body_jc = _coalesce(
        body_data.get("p.jc"),
        styles_data.get("normal.jc"),
    )
    actual_east_asia = _coalesce(
        body_data.get("r.eastAsia"),
        styles_data.get("normal.eastAsia"),
        styles_data.get("docDefault.eastAsia"),
    )
    actual_ascii = _coalesce(
        body_data.get("r.ascii"),
        styles_data.get("normal.ascii"),
        styles_data.get("docDefault.ascii"),
    )

    rows = [
        ("body.size", actual_body_size, SKILL_DEFAULTS["body.size"]),
        ("body.line", actual_body_line, SKILL_DEFAULTS["body.line"]),
        ("body.lineRule", actual_body_line_rule, SKILL_DEFAULTS["body.lineRule"]),
        ("body.firstLine", actual_body_first, SKILL_DEFAULTS["body.firstLine"]),
        ("body.jc", actual_body_jc, SKILL_DEFAULTS["body.jc"]),
        ("body.fontEastAsia", actual_east_asia, {"val": "继承模板", "note": "宋体/等线等"}),
        ("body.fontAscii",    actual_ascii,     {"val": "继承模板", "note": "Times/Calibri 等"}),
    ]

    # 表头
    print(f"  {'维度':<20} {'模板实际':<20} {'skill 默认':<20} {'是否一致':<10} 备注")
    print(f"  {'-'*20} {'-'*20} {'-'*20} {'-'*10} {'-'*30}")

    diffs = 0
    for name, actual, default in rows:
        # 对比：字号/行距用字符串比较（XML 里都是 str），对齐和字体也比较
        default_val = default["val"]
        def_str = str(default_val)
        actual_str = str(actual) if actual is not None else "（未显式）"

        # "继承模板" 特殊处理：模板没 diff 就算一致
        if def_str == "继承模板":
            same = True
        else:
            same = (actual_str == def_str)

        if same:
            mark = "✓"
        else:
            mark = "❌ DIFF"
            diffs += 1

        note = default["note"]
        print(f"  {name:<20} {actual_str:<20} {def_str:<20} {mark:<10} {note}")

    print()
    if diffs == 0:
        print("  ✅ 没有 diff，可直接用 builders.py 默认参数")
    else:
        print(f"  ⚠️  共 {diffs} 处 diff。写正文时给 build_body_paragraph() 传 override，例如：")
        if actual_body_size and str(actual_body_size) != "21":
            print(f"         build_body_paragraph(text, size={actual_body_size}, ...)")
        if actual_body_line and str(actual_body_line) != "360":
            print(f"         build_body_paragraph(text, line={actual_body_line}, ...)")


# -------------- main --------------

def main():
    if len(sys.argv) != 2:
        sys.exit("用法: inspect_template.py <docx 路径>")
    path = Path(sys.argv[1])
    if not path.exists():
        sys.exit(f"不存在: {path}")

    from docx import Document
    doc = Document(str(path))

    print(f"=== {path.name} ===\n")

    print("--- 顶层段落 ---")
    dump_paragraphs(doc.paragraphs)

    print("\n--- 表格（递归展开嵌套）---")
    for ti, tbl in enumerate(doc.tables):
        dump_table(tbl, str(ti))

    print("\n--- sectPr 页面 ---")
    for section in doc.sections:
        print(f"  页面大小: {section.page_width} x {section.page_height}")
        print(f"  页边距:   上 {section.top_margin}  下 {section.bottom_margin}  "
              f"左 {section.left_margin}  右 {section.right_margin}")

    # 样式 diff
    print("\n--- 样式 diff（模板实际 vs skill 硬编码默认）---")
    with ZipFile(str(path)) as zf:
        styles_root = _read_xml(zf, "word/styles.xml")
        doc_root = _read_xml(zf, "word/document.xml")

    styles_data = extract_default_styles(styles_root)
    body_data = extract_first_body_paragraph(doc_root)

    if body_data.get("text_preview"):
        print(f"  首段预览：{body_data['text_preview']!r}")
    print()

    print_style_diff(styles_data, body_data)

    # 提示：若想看原始字典值
    if "--verbose" in sys.argv:
        print("\n--- raw styles.xml 提取值 ---")
        for k, v in styles_data.items():
            print(f"  {k}: {v}")
        print("\n--- raw first paragraph 提取值 ---")
        for k, v in body_data.items():
            print(f"  {k}: {v}")


if __name__ == "__main__":
    main()
