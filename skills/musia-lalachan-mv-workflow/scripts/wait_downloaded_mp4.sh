#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  wait_downloaded_mp4.sh [--downloads DIR] [--since-epoch SECONDS] [--min-bytes BYTES] [--timeout SECONDS]

Wait for a Chrome/browser MP4 download to finish and print the completed path.

Options:
  --downloads    Download directory. Default: ~/Downloads
  --since-epoch  Only consider files newer than this Unix epoch.
  --min-bytes    Minimum completed MP4 size. Default: 1000000
  --timeout      Maximum wait time in seconds. Default: 240
  -h, --help     Show this help.
USAGE
}

downloads="$HOME/Downloads"
since_epoch="$(date +%s)"
min_bytes=1000000
timeout=240

while [[ $# -gt 0 ]]; do
  case "$1" in
    --downloads)
      downloads="${2:?missing --downloads value}"
      shift 2
      ;;
    --since-epoch)
      since_epoch="${2:?missing --since-epoch value}"
      shift 2
      ;;
    --min-bytes)
      min_bytes="${2:?missing --min-bytes value}"
      shift 2
      ;;
    --timeout)
      timeout="${2:?missing --timeout value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    *)
      echo "unknown argument: $1" >&2
      usage >&2
      exit 2
      ;;
  esac
done

if [[ ! -d "$downloads" ]]; then
  echo "downloads directory not found: $downloads" >&2
  exit 1
fi

deadline=$(( $(date +%s) + timeout ))

while (( $(date +%s) <= deadline )); do
  newest="$(
    find "$downloads" -maxdepth 1 -type f \( -iname '*.mp4' -o -iname '*.crdownload' \) \
      -newermt "@$since_epoch" \
      -printf '%T@ %s %p\n' 2>/dev/null |
      sort -nr |
      head -n 1
  )"

  if [[ -n "$newest" ]]; then
    path="${newest#* * }"
    case "$path" in
      *.crdownload)
        sleep 2
        continue
        ;;
    esac

    size="$(stat -c%s "$path" 2>/dev/null || echo 0)"
    if (( size >= min_bytes )); then
      printf '%s\n' "$path"
      exit 0
    fi
  fi

  sleep 2
done

echo "timeout waiting for completed MP4 in $downloads" >&2
exit 1
