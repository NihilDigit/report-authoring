#!/usr/bin/env bash
# preview_docx.sh  — docx → PDF → 每页 JPG，便于阶段 5 快速目检
# 用法: preview_docx.sh <docx 路径>  [page_from] [page_to]
set -eu
DOCX="$1"
FROM="${2:-1}"
TO="${3:-}"

OUTDIR="$(mktemp -d /tmp/preview_docx.XXXX)"
soffice --headless --convert-to pdf "$DOCX" --outdir "$OUTDIR" > /dev/null 2>&1

PDF="$OUTDIR/$(basename "${DOCX%.docx}.pdf")"
ARGS=(-jpeg -r 100)
[[ -n "$FROM" ]] && ARGS+=(-f "$FROM")
[[ -n "$TO" ]]   && ARGS+=(-l "$TO")
pdftoppm "${ARGS[@]}" "$PDF" "$OUTDIR/page"

ls "$OUTDIR"/*.jpg | head -20
echo "---"
echo "预览在 $OUTDIR/"
