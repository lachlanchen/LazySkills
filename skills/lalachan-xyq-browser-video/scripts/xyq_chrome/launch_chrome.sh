#!/usr/bin/env bash
set -euo pipefail

PORT="${PORT:-9222}"
PROFILE_DIR="${PROFILE_DIR:-$HOME/.cache/xyq-chrome}"
URL="${1:-https://xyq.jianying.com/home?tab_name=integrated-agent}"

mkdir -p "$PROFILE_DIR"

exec google-chrome \
  --remote-debugging-port="$PORT" \
  --remote-allow-origins="http://127.0.0.1:$PORT" \
  --user-data-dir="$PROFILE_DIR" \
  --new-window "$URL"
