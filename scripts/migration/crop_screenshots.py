#!/usr/bin/env python3
"""
批量裁切终端截图的周围空白。

用法：
    python crop_screenshots.py <media_dir> [--fuzz 15%] [--border 12] [--bg '#282828']

只处理 image*.png，跳过非 png 与 image1/image2 这类模板原生图（通常是 logo）。
用 ImageMagick 就地覆盖；如需保留原图自行 cp 再运行。

注意：此脚本只改 PNG 文件；XML 里引用这些图的 <wp:extent> / <a:ext> 的 cx/cy 由
finalize_images.py 统一根据新像素尺寸重算。
"""
import argparse
import re
import subprocess
import sys
from pathlib import Path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("media_dir", help="word/media 目录")
    ap.add_argument("--fuzz", default="15%",
                    help="ImageMagick trim fuzz 阈值，终端背景非纯黑时需要调大")
    ap.add_argument("--border", type=int, default=12,
                    help="裁切后加的边距像素")
    ap.add_argument("--bg", default="#282828",
                    help="边距颜色（Alacritty 默认背景 #282828）")
    ap.add_argument("--skip-prefix", default="image1|image2",
                    help="正则：跳过文件名以此开头的图（模板 logo）")
    args = ap.parse_args()

    media = Path(args.media_dir)
    if not media.is_dir():
        sys.exit(f"不是目录: {media}")

    skip_re = re.compile(f"^({args.skip_prefix})\\.")
    for src in sorted(media.glob("*.png")):
        if skip_re.match(src.name):
            print(f"  跳过 {src.name}")
            continue
        tmp = src.with_suffix(".tmp.png")
        subprocess.run([
            "magick", str(src),
            "-fuzz", args.fuzz,
            "-trim", "+repage",
            "-bordercolor", args.bg,
            "-border", str(args.border),
            str(tmp),
        ], check=True)
        tmp.replace(src)

        w, h = _png_size(src)
        print(f"  {src.name}: {w}x{h}")


def _png_size(path: Path) -> tuple[int, int]:
    import struct
    with open(path, "rb") as f:
        head = f.read(24)
    return struct.unpack(">II", head[16:24])


if __name__ == "__main__":
    main()
