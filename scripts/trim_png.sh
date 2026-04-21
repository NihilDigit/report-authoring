#!/usr/bin/env bash
# trim_png.sh  — 用 magick -trim 去除终端截图的背景空白（就地覆盖原文件）
# 用法: trim_png.sh <png>  [fuzz%] [border_px] [bg_color]
set -eu
PNG="$1"
FUZZ="${2:-15%}"
BORDER="${3:-12}"
BG="${4:-#282828}"

TMP="${PNG%.png}.tmp.png"
magick "$PNG" -fuzz "$FUZZ" -trim +repage \
    -bordercolor "$BG" -border "$BORDER" "$TMP"
mv "$TMP" "$PNG"
identify -format "%w x %h\n" "$PNG"
