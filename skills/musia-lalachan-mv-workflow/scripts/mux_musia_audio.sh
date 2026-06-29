#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  mux_musia_audio.sh --video VISUAL.mp4 --audio MUSIA_MASTER.mp3 --output FINAL.mp4 [--copy-to DIR]

Replace or add audio on a generated MV using the reviewed Musia master track.

Options:
  --video     Generated visual/video file.
  --audio     Reviewed Musia song master, usually .mp3 or .wav.
  --output    Final song-locked MP4.
  --copy-to   Optional directory to copy the final MP4 into.
  -h, --help  Show this help.
USAGE
}

video=""
audio=""
output=""
copy_to=""

while [[ $# -gt 0 ]]; do
  case "$1" in
    --video)
      video="${2:?missing --video value}"
      shift 2
      ;;
    --audio)
      audio="${2:?missing --audio value}"
      shift 2
      ;;
    --output)
      output="${2:?missing --output value}"
      shift 2
      ;;
    --copy-to)
      copy_to="${2:?missing --copy-to value}"
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

if [[ -z "$video" || -z "$audio" || -z "$output" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -f "$video" ]]; then
  echo "video not found: $video" >&2
  exit 1
fi

if [[ ! -f "$audio" ]]; then
  echo "audio not found: $audio" >&2
  exit 1
fi

mkdir -p "$(dirname "$output")"

ffmpeg -y \
  -i "$video" \
  -i "$audio" \
  -map 0:v:0 -map 1:a:0 \
  -c:v copy -c:a aac -b:a 192k \
  -shortest \
  "$output"

ffprobe -v error \
  -show_entries format=duration:stream=index,codec_type,codec_name,width,height \
  -of default=noprint_wrappers=1 \
  "$output"

if [[ -n "$copy_to" ]]; then
  mkdir -p "$copy_to"
  cp -f "$output" "$copy_to/"
  echo "copied to: $copy_to/$(basename "$output")"
fi

echo "finalized: $output"

