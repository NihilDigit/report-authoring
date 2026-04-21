#!/usr/bin/env bash
# silicon_cli.sh  — 用本 skill 推荐的参数渲染单个源码文件
# 用法: silicon_cli.sh <源码文件> <silicon 语言名> <输出 png>
#   silicon 语言名坑见 docs/code-presentation.md：protobuf→proto、thrift→cpp、text→ini
set -eu
SRC="$1"; LANG="$2"; OUT="$3"
FONT="${SILICON_FONT:-Maple Mono NF CN}"

silicon "$SRC" -o "$OUT" \
    --theme "GitHub" --background "#FFFFFF" \
    --no-window-controls --font "$FONT" \
    --pad-horiz 0 --pad-vert 0 \
    --no-line-number --language "$LANG"
