#!/bin/sh

set -eu

SCRIPT_DIR=$(CDPATH= cd -- "$(dirname -- "$0")" && pwd)

if [ -f "$SCRIPT_DIR/.env" ]; then
  set -a
  # Load the repo defaults into the shell before expanding variables below.
  . "$SCRIPT_DIR/.env"
  set +a
fi

INPUT_PATH="${PDF_PATH:-./pdf}"
OUTPUT_PATH="${OUTPUT_PATH:-./output}"
WATERMARK_IMAGE="${WATERMARK_FILE:-./watermarks/watermark.png}"
WATERMARK_ANGLE="${WATERMARK_ANGLE:-45}"
WATERMARK_OPACITY="${WATERMARK_OPACITY:-0.25}"
WATERMARK_SCALE="${WATERMARK_SCALE:-1}"
docker compose run --rm watermark-pdf \
  "$INPUT_PATH" \
  "$OUTPUT_PATH" \
  --image "$WATERMARK_IMAGE" \
  --angle "$WATERMARK_ANGLE" \
  --opacity "$WATERMARK_OPACITY" \
  --image-scale "$WATERMARK_SCALE"
