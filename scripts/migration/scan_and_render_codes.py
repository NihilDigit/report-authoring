#!/usr/bin/env python3
"""
扫描 document.xml，把连续的 Consolas 代码段聚合为代码块，用 silicon 渲染成 PNG，
再用 <w:drawing> 图片引用替换掉原代码段。同时维护 _rels/document.xml.rels。

用法：
    python render_codes.py <unpacked_dir> [--theme GitHub] [--font "Maple Mono NF CN"] \
        [--rid-start 200] [--render-out <dir>]

假设 <unpacked_dir> 是用 document-skills:docx 的 unpack.py 解包出来的目录。
代码块的识别规则：<w:p> 段落里 <w:rPr> 包含 ascii="Consolas"（报告里约定代码段用
Consolas 等宽字体），连续的代码段聚合为一个代码块。

语言自动推断与 silicon 支持的语言名映射：
    protobuf → proto，thrift → cpp（silicon 不认 thrift 但 cpp 高亮相近），
    纯文本/目录树 → ini（silicon 不认 text/txt/plain）。
"""
import argparse
import re
import struct
import subprocess
import sys
from pathlib import Path


EMU_PER_PX = 3000      # 每像素 3000 EMU 作为图片显示密度
MAX_CX = 4572000       # 正文宽 5 inch


def png_size(p: Path) -> tuple[int, int]:
    with open(p, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


def guess_lang(text: str, default: str = "ini") -> str:
    first = "\n".join(text.splitlines()[:3]).lower()
    if text.startswith("syntax = ") or ("message " in text[:200] and "=" in text):
        return "proto"
    if text.lstrip().startswith("{") and '"type"' in text[:80]:
        return "json"
    if "namespace java" in text or (
        "struct " in text[:200]
        and ("required" in text[:400] or "optional" in text[:400])
    ):
        return "cpp"  # thrift IDL 没有原生支持
    if "public class" in text or ("import " in text and ";" in text[:100]):
        return "java"
    if "<dependency>" in text or "<groupId>" in text or text.lstrip().startswith("<"):
        return "xml"
    if (
        first.startswith("#")
        or any(kw in text for kw in ("python3", "pip ", "apt ", "mvn ",
                                     "protoc ", "thrift ", "sudo ",
                                     "├──", "└──"))
    ):
        return "bash"
    if (
        "import " in text or "def " in text or "self." in text
        or ".py" in text[:80] or "print(" in text
    ):
        return "python"
    return default


def render_with_silicon(text: str, out_png: Path, *, theme: str, font: str, language: str) -> bool:
    src = out_png.with_suffix(".src")
    src.write_text(text, encoding="utf-8")
    res = subprocess.run([
        "silicon", str(src), "-o", str(out_png),
        "--theme", theme, "--background", "#FFFFFF",
        "--no-window-controls", "--font", font,
        "--pad-horiz", "0", "--pad-vert", "0",
        "--no-line-number", "--language", language,
    ], stderr=subprocess.PIPE, stdout=subprocess.PIPE)
    src.unlink(missing_ok=True)
    return out_png.exists()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("unpacked_dir", help="docx unpack 后的目录")
    ap.add_argument("--theme", default="GitHub")
    ap.add_argument("--font", default="Maple Mono NF CN")
    ap.add_argument("--rid-start", type=int, default=200,
                    help="生成的 image 关系 Id 起始值（避开已有 rId）")
    ap.add_argument("--render-out", default=None,
                    help="渲染源图保留位置（默认与 media 同级的 rendered_code/）")
    args = ap.parse_args()

    root = Path(args.unpacked_dir)
    doc = root / "word" / "document.xml"
    rels = root / "word" / "_rels" / "document.xml.rels"
    media = root / "word" / "media"
    media.mkdir(exist_ok=True)

    render_out = Path(args.render_out) if args.render_out else (root.parent / "rendered_code")
    render_out.mkdir(parents=True, exist_ok=True)

    xml = doc.read_text(encoding="utf-8")
    p_iter = list(re.finditer(r"<w:p>.*?</w:p>", xml, re.DOTALL))

    def is_code(block: str) -> bool:
        return 'ascii="Consolas"' in block

    def get_text(block: str) -> str:
        m = re.search(r"<w:t[^>]*>(.*?)</w:t>", block, re.DOTALL)
        if not m:
            return ""
        t = m.group(1)
        return (t.replace("&lt;", "<").replace("&gt;", ">")
                .replace("&amp;", "&").replace("&quot;", '"').replace("&apos;", "'"))

    # 聚合连续代码段
    blocks = []
    cur = None
    for idx, m in enumerate(p_iter):
        blk = m.group(0)
        if is_code(blk):
            line = get_text(blk)
            if cur is None:
                cur = {"first": idx, "last": idx, "paras": [(m, line)]}
            else:
                cur["last"] = idx
                cur["paras"].append((m, line))
        else:
            if cur is not None:
                blocks.append(cur)
                cur = None
    if cur is not None:
        blocks.append(cur)

    print(f"聚合到 {len(blocks)} 个代码块")

    rel_counter = args.rid_start
    rels_additions = []
    image_additions = []

    for i, blk in enumerate(blocks):
        lines = [line for _, line in blk["paras"]]
        text = "\n".join(lines)
        if not text.strip():
            continue

        lang = guess_lang(text)
        img_name = f"code_{i:02d}.png"
        img_path = render_out / img_name
        ok = render_with_silicon(text, img_path,
                                  theme=args.theme, font=args.font, language=lang)
        if not ok:
            print(f"  [{i:02d}] 语言 {lang!r} 失败，fallback ini")
            ok = render_with_silicon(text, img_path,
                                      theme=args.theme, font=args.font, language="ini")
        if not ok:
            print(f"  [{i:02d}] 跳过：silicon 无法渲染")
            continue

        media_name = f"image_code_{i:02d}.png"
        (media / media_name).write_bytes(img_path.read_bytes())
        w, h = png_size(media / media_name)

        cx = min(w * EMU_PER_PX, MAX_CX)
        cy = int(cx * h / w)
        rid = f"rId{rel_counter}"
        docpr_id = rel_counter + 100
        rel_counter += 1
        rels_additions.append((rid, media_name))

        new_p = (
            '<w:p><w:pPr>'
            '<w:spacing w:line="300" w:lineRule="auto"/>'
            '<w:jc w:val="center"/>'
            '</w:pPr>'
            '<w:r><w:drawing>'
            f'<wp:inline distT="0" distB="0" distL="0" distR="0">'
            f'<wp:extent cx="{cx}" cy="{cy}"/>'
            f'<wp:docPr id="{docpr_id}" name="code_{i}"/>'
            '<wp:cNvGraphicFramePr>'
            '<a:graphicFrameLocks xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" noChangeAspect="1"/>'
            '</wp:cNvGraphicFramePr>'
            '<a:graphic xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main">'
            '<a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            f'<pic:nvPicPr><pic:cNvPr id="{docpr_id}" name="code_{i}"/><pic:cNvPicPr/></pic:nvPicPr>'
            f'<pic:blipFill><a:blip r:embed="{rid}"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            '<pic:spPr>'
            f'<a:xfrm><a:off x="0" y="0"/><a:ext cx="{cx}" cy="{cy}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom>'
            '</pic:spPr>'
            '</pic:pic></a:graphicData></a:graphic>'
            '</wp:inline></w:drawing></w:r></w:p>'
        )

        image_additions.append({
            "first": blk["paras"][0][0],
            "last": blk["paras"][-1][0],
            "new_p": new_p,
        })
        print(f"  [{i:02d}] lang={lang:8s} {len(lines):3d} lines -> {media_name} ({w}x{h})")

    for spec in reversed(image_additions):
        start = spec["first"].start()
        end = spec["last"].end()
        xml = xml[:start] + spec["new_p"] + xml[end:]

    doc.write_text(xml, encoding="utf-8")

    # 更新 rels
    rels_xml = rels.read_text(encoding="utf-8")
    insertion = "\n".join(
        f'  <Relationship Id="{rid}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/{name}"/>'
        for rid, name in rels_additions
    )
    rels_xml = rels_xml.replace("</Relationships>", insertion + "\n</Relationships>")
    rels.write_text(rels_xml, encoding="utf-8")

    print(f"替换代码块 {len(image_additions)} 个，追加 rels {len(rels_additions)} 条")


if __name__ == "__main__":
    main()
