#!/usr/bin/env python3
"""
inspect_template.py — 阶段 1 用 python-docx 摘要模板结构。

输出所有段落、表格、cell 的文字，建立模板心智图。

用法：
    uvx --with python-docx python inspect_template.py <docx>

需要：python-docx。若未装：`uv tool install python-docx` 或用 uvx 一次性。
"""
import sys
from pathlib import Path


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
    for i, p in enumerate(doc.paragraphs):
        text = p.text.strip()
        marker = "（空）" if not text else text[:80] + ("…" if len(text) > 80 else "")
        print(f"[P {i:3d}] {marker}")

    print("\n--- 表格 ---")
    for ti, tbl in enumerate(doc.tables):
        print(f"\n[T {ti}] {len(tbl.rows)} rows × {len(tbl.columns)} cols")
        for r, row in enumerate(tbl.rows):
            for c, cell in enumerate(row.cells):
                text = cell.text.strip()
                marker = "（空）" if not text else text[:80] + ("…" if len(text) > 80 else "")
                print(f"  [T {ti}, {r},{c}] {marker}")

    print("\n--- sectPr 页面 ---")
    for section in doc.sections:
        print(f"  页面大小: {section.page_width} x {section.page_height}")
        print(f"  页边距:   上 {section.top_margin}  下 {section.bottom_margin}  "
              f"左 {section.left_margin}  右 {section.right_margin}")


if __name__ == "__main__":
    main()
