"""
report-authoring · 阶段 4 构建器。

所有 build_* 函数返回 **合法的 OOXML 字符串片段**，直接拼接到 document.xml 的
`<w:body>` 或某个 `<w:tc>` 内部即可。

设计原则
--------
- 每个 builder 是**纯函数**（除了 add_image_relationship 读入/返回 rels 字符串）
- **不扫描已有 XML**，由调用方决定插入位置
- 所有样式默认值来自 `docs/typography.md` 和 `docs/caption-spec.md`
  （中文正文五号宋体 1.5 行距；caption 小五加粗居中；图片居中、原始像素密度 3000 EMU/px）
- 如果默认值不合适，大多接受 keyword-only 覆盖参数
"""

from __future__ import annotations

import re
import struct
from pathlib import Path
from typing import Tuple

# ---------------- 单位换算 ----------------

EMU_PER_INCH = 914400
EMU_PER_PX = 3000          # PNG 像素 × 3000 EMU/px，兼顾字号和页宽
MAX_CX = 4572000           # 5 inch，正文宽度上限
CONTENT_WIDTH_DXA = 9360   # US Letter / A4 1 inch margin 下的表格 cell 宽


# ---------------- 通用辅助 ----------------

def xml_escape(s: str) -> str:
    return (s.replace("&", "&amp;")
             .replace("<", "&lt;")
             .replace(">", "&gt;"))


def png_size(path: Path | str) -> Tuple[int, int]:
    """读取 PNG 像素宽高（不依赖 PIL）"""
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def image_emu(w_px: int, h_px: int, *,
              emu_per_px: int = EMU_PER_PX, max_cx: int = MAX_CX) -> Tuple[int, int]:
    """按像素密度换算 cx/cy，超宽则截断 cx 并按比例缩 cy"""
    cx = min(w_px * emu_per_px, max_cx)
    cy = int(cx * h_px / w_px)
    return cx, cy


# ---------------- 段落级 builder ----------------

def build_body_paragraph(text: str, *,
                          size: int = 21,           # 五号 = 10.5pt × 2
                          first_line_chars: int = 200,
                          line: int = 360,
                          jc: str = "left") -> str:
    """正文段：默认宋体五号 1.5 行距 + 首行缩进两个字符 + 左对齐

    中文学术报告正文惯例是左对齐（`jc="left"`），行末自然收尾不强制拉齐，阅读体验更顺。
    若模板实际要求两端对齐可传 jc="both"。
    """
    r_pr = f'<w:rPr><w:rFonts w:hint="eastAsia"/><w:sz w:val="{size}"/></w:rPr>'
    return (
        '<w:p><w:pPr>'
        f'<w:spacing w:line="{line}" w:lineRule="auto"/>'
        f'<w:ind w:firstLineChars="{first_line_chars}"/>'
        f'<w:jc w:val="{jc}"/>'
        f'{r_pr}</w:pPr>'
        f'<w:r>{r_pr}'
        f'<w:t xml:space="preserve">{xml_escape(text)}</w:t>'
        '</w:r></w:p>'
    )


def build_heading(text: str, *, level: int = 1) -> str:
    """章节标题：加粗，level 1→24（小三）；level 2→22（四号）；level 3→21（小四）"""
    size = {1: 24, 2: 22, 3: 21}.get(level, 21)
    before = {1: 240, 2: 180, 3: 120}.get(level, 120)
    after = {1: 120, 2: 120, 3: 60}.get(level, 60)
    r_pr = f'<w:rPr><w:rFonts w:hint="eastAsia"/><w:b/><w:bCs/><w:sz w:val="{size}"/></w:rPr>'
    return (
        '<w:p><w:pPr>'
        f'<w:spacing w:before="{before}" w:after="{after}" w:line="360" w:lineRule="auto"/>'
        f'{r_pr}</w:pPr>'
        f'<w:r>{r_pr}'
        f'<w:t xml:space="preserve">{xml_escape(text)}</w:t>'
        '</w:r></w:p>'
    )


def build_caption_paragraph(chapter: int, index: int, description: str, *,
                             kind: str = "图",
                             sep: str = "  ") -> str:
    """学术规范 caption：居中、黑色正文字体、加粗、小五号 (sz=18)

    生成形如「图 2-1  Python 版 pb_demo.py 运行输出」。
    代码图不需要 caption，所以本函数只用于截图/图表/示意图。
    """
    text = f"{kind} {chapter}-{index}{sep}{description}"
    r_pr = '<w:rPr><w:rFonts w:hint="eastAsia"/><w:b/><w:bCs/><w:sz w:val="18"/><w:szCs w:val="18"/></w:rPr>'
    return (
        '<w:p><w:pPr>'
        '<w:spacing w:before="60" w:after="180" w:line="276" w:lineRule="auto"/>'
        '<w:jc w:val="center"/>'
        f'{r_pr}</w:pPr>'
        f'<w:r>{r_pr}'
        f'<w:t xml:space="preserve">{xml_escape(text)}</w:t>'
        '</w:r></w:p>'
    )


def build_text_code_paragraph(line: str, *,
                               size: int = 20,
                               left_border_color: str = "5A9FD4",
                               fill: str = "F5F5F5") -> str:
    """文字代码段（一行一段），带左侧竖线 + 浅灰背景，作为 silicon 图的替代风格。

    多行代码请为每行调用一次并按顺序拼接。
    OOXML pPr 子元素严格顺序：pBdr → shd → spacing → ind → rPr
    """
    r_pr = (
        f'<w:rPr><w:rFonts w:hint="eastAsia" w:ascii="Consolas" w:hAnsi="Consolas" w:cs="Consolas"/>'
        f'<w:sz w:val="{size}"/></w:rPr>'
    )
    return (
        '<w:p><w:pPr>'
        f'<w:pBdr><w:left w:val="single" w:sz="18" w:space="8" w:color="{left_border_color}"/></w:pBdr>'
        f'<w:shd w:val="clear" w:color="auto" w:fill="{fill}"/>'
        '<w:spacing w:line="300" w:lineRule="auto"/>'
        '<w:ind w:left="420"/>'
        f'{r_pr}</w:pPr>'
        f'<w:r>{r_pr}'
        f'<w:t xml:space="preserve">{xml_escape(line) if line else ""}</w:t>'
        '</w:r></w:p>'
    )


# ---------------- 图片 drawing 与完整图片段 ----------------

def build_image_drawing(rid: str, docpr_id: int, name: str, cx: int, cy: int) -> str:
    """仅返回 `<w:drawing>...</w:drawing>`，用于嵌在 <w:r> 内"""
    safe_name = xml_escape(name)
    return (
        '<w:drawing>'
        '<wp:inline distT="0" distB="0" distL="0" distR="0">'
        f'<wp:extent cx="{cx}" cy="{cy}"/>'
        f'<wp:docPr id="{docpr_id}" name="{safe_name}"/>'
        '<wp:cNvGraphicFramePr>'
        '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
        '</wp:cNvGraphicFramePr>'
        '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
        '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        f'<pic:nvPicPr><pic:cNvPr id="{docpr_id}" name="{safe_name}"/><pic:cNvPicPr/></pic:nvPicPr>'
        f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr>'
        f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
        '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
        '</pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic>'
        '</wp:inline>'
        '</w:drawing>'
    )


def build_image_paragraph(rid: str, docpr_id: int, name: str, cx: int, cy: int) -> str:
    """居中图片段（不带 caption）"""
    return (
        '<w:p><w:pPr>'
        '<w:spacing w:before="120" w:after="60" w:line="360" w:lineRule="auto"/>'
        '<w:jc w:val="center"/>'
        '</w:pPr>'
        f'<w:r>{build_image_drawing(rid, docpr_id, name, cx, cy)}</w:r>'
        '</w:p>'
    )


def build_screenshot_block(*, rid: str, docpr_id: int, name: str,
                            cx: int, cy: int,
                            chapter: int, index: int, caption: str,
                            kind: str = "图") -> str:
    """截图完整块 = 居中图片段 + 编号 caption 段（学术规范）"""
    return (
        build_image_paragraph(rid, docpr_id, name, cx, cy)
        + build_caption_paragraph(chapter, index, caption, kind=kind)
    )


# ---------------- rels / media 工具 ----------------

def next_rid(rels_xml: str, *, start: int = 200) -> Tuple[str, int]:
    """返回下一个未使用的 rId（从 start 起）"""
    used = set()
    for m in re.finditer(r'<Relationship Id="rId(\d+)"', rels_xml):
        used.add(int(m.group(1)))
    n = start
    while n in used:
        n += 1
    return f"rId{n}", n


def add_image_relationship(rels_xml: str, rid: str, media_filename: str) -> str:
    """在 rels XML 里追加一条 image 关系，返回新 XML"""
    insertion = (
        f'  <Relationship Id="{rid}" '
        'Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" '
        f'Target="media/{media_filename}"/>\n'
    )
    return rels_xml.replace('</Relationships>', insertion + '</Relationships>')


def copy_png_to_media(png_path: Path | str, media_dir: Path | str,
                      *, new_name: str | None = None) -> str:
    """把 PNG 复制到 word/media/，返回 media 下的文件名（不含路径）"""
    src = Path(png_path)
    dst_name = new_name or src.name
    dst = Path(media_dir) / dst_name
    dst.parent.mkdir(parents=True, exist_ok=True)
    dst.write_bytes(src.read_bytes())
    return dst_name


def embed_image(png_path: Path | str, *,
                media_dir: Path | str, rels_xml: str,
                rid_start: int = 200,
                docpr_id: int | None = None,
                emu_per_px: int = EMU_PER_PX,
                max_cx: int = MAX_CX) -> dict:
    """一次性完成：拷 PNG 到 media + 追加 rels + 返回可直接用于 build_image_*/build_screenshot_block 的参数

    返回 dict:
        rid, docpr_id, name, cx, cy, new_rels_xml, media_filename
    """
    src = Path(png_path)
    media_name = copy_png_to_media(src, media_dir)
    w, h = png_size(Path(media_dir) / media_name)
    cx, cy = image_emu(w, h, emu_per_px=emu_per_px, max_cx=max_cx)

    rid, n = next_rid(rels_xml, start=rid_start)
    new_rels = add_image_relationship(rels_xml, rid, media_name)

    return {
        "rid": rid,
        "docpr_id": docpr_id or (n + 100),
        "name": src.stem,
        "cx": cx,
        "cy": cy,
        "new_rels_xml": new_rels,
        "media_filename": media_name,
    }
