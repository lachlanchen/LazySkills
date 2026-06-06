#!/usr/bin/env sh
set -eu

PROJECT_DIR="${KV260_PROJECT_DIR:-/home/petalinux/Projects/kria-kv260-starter}"

section() {
  printf '\n== %s ==\n' "$1"
}

section "identity"
hostname || true
ip -4 addr show scope global || true

section "project"
if [ -d "${PROJECT_DIR}/.git" ]; then
  git -C "${PROJECT_DIR}" status --short --branch || true
  git -C "${PROJECT_DIR}" log --oneline -n 3 || true
else
  echo "missing project: ${PROJECT_DIR}"
fi

section "camera nodes"
ls -l /dev/video* /dev/media* /dev/v4l-subdev* 2>/dev/null || true
fuser -v /dev/video0 2>/dev/null || true

section "viewer/api status"
if [ -x "${PROJECT_DIR}/scripts/kv260-event-camera-switch.sh" ]; then
  (cd "${PROJECT_DIR}" && ./scripts/kv260-event-camera-switch.sh --status) || true
else
  echo "missing kv260-event-camera-switch.sh"
fi
if [ -x "${PROJECT_DIR}/scripts/kv260-event-camera-api.sh" ]; then
  (cd "${PROJECT_DIR}" && ./scripts/kv260-event-camera-api.sh status) || true
else
  echo "missing kv260-event-camera-api.sh"
fi

section "display"
printf 'DISPLAY=%s\n' "${DISPLAY:-}"
ps -ef | grep -Ei 'matchbox|Xorg|xserver|metavision|kv260-event' | grep -v grep || true

section "storage"
df -h / /home/petalinux 2>/dev/null || df -h || true
