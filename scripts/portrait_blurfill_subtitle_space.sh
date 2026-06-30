#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/portrait_blurfill_subtitle_space.sh INPUT.mp4 OUTPUT.mp4 [options]

Create a 9:16 portrait short from a 4:3 or horizontal video:
- full-height portrait background is built from the current frame;
- background is zoomed, center-cropped, blurred, and slightly dimmed;
- original foreground frame is kept intact and lifted upward;
- bottom blur area is intentionally left open for burned subtitles.

Options:
  --width N              Output width. Default: 1080
  --height N             Output height. Default: 1920
  --fg-width N           Foreground width. Default: output width
  --fg-y N               Foreground top y position. Default: 240
  --blur N               Background gblur sigma. Default: 36
  --background-dim N     Background brightness adjustment. Default: -0.08
  --background-sat N     Background saturation multiplier. Default: 1.08
  --crf N                x264 CRF. Default: 12
  --preset NAME          x264 preset. Default: slow
  --scale-flags NAME     ffmpeg scale flags. Default: lanczos
  --audio-mode MODE      copy or aac. Default: copy
  -h, --help             Show help.

Example:
  scripts/portrait_blurfill_subtitle_space.sh input.mp4 output.mp4 --fg-y 240
USAGE
}

if [[ $# -lt 2 ]]; then
  usage >&2
  exit 2
fi

input=$1
output=$2
shift 2

width=1080
height=1920
fg_width=""
fg_y=240
blur=36
background_dim="-0.08"
background_sat="1.08"
crf=12
preset=slow
scale_flags="lanczos"
audio_mode="copy"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --width)
      width="${2:?missing --width value}"
      shift 2
      ;;
    --height)
      height="${2:?missing --height value}"
      shift 2
      ;;
    --fg-width)
      fg_width="${2:?missing --fg-width value}"
      shift 2
      ;;
    --fg-y)
      fg_y="${2:?missing --fg-y value}"
      shift 2
      ;;
    --blur)
      blur="${2:?missing --blur value}"
      shift 2
      ;;
    --background-dim)
      background_dim="${2:?missing --background-dim value}"
      shift 2
      ;;
    --background-sat)
      background_sat="${2:?missing --background-sat value}"
      shift 2
      ;;
    --crf)
      crf="${2:?missing --crf value}"
      shift 2
      ;;
    --preset)
      preset="${2:?missing --preset value}"
      shift 2
      ;;
    --scale-flags)
      scale_flags="${2:?missing --scale-flags value}"
      shift 2
      ;;
    --audio-mode)
      audio_mode="${2:?missing --audio-mode value}"
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

if [[ ! -f "$input" ]]; then
  echo "input not found: $input" >&2
  exit 1
fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  echo "ffmpeg is required" >&2
  exit 1
fi

if [[ -z "$fg_width" ]]; then
  fg_width="$width"
fi

case "$audio_mode" in
  copy)
    audio_args=(-c:a copy)
    ;;
  aac)
    audio_args=(-c:a aac -b:a 192k)
    ;;
  *)
    echo "--audio-mode must be copy or aac" >&2
    exit 2
    ;;
esac

mkdir -p "$(dirname "$output")"

filter_complex="[0:v]split=2[fgsrc][bgsrc];"
filter_complex+="[bgsrc]scale=${width}:${height}:force_original_aspect_ratio=increase:flags=${scale_flags},"
filter_complex+="crop=${width}:${height},gblur=sigma=${blur},"
filter_complex+="eq=brightness=${background_dim}:saturation=${background_sat}[bg];"
filter_complex+="[fgsrc]scale=${fg_width}:-2:flags=${scale_flags}[fg];"
filter_complex+="[bg][fg]overlay=(W-w)/2:${fg_y},setsar=1[v]"

ffmpeg -hide_banner -loglevel error -y \
  -i "$input" \
  -filter_complex "$filter_complex" \
  -map "[v]" -map 0:a? \
  -c:v libx264 -preset "$preset" -crf "$crf" \
  -pix_fmt yuv420p \
  "${audio_args[@]}" \
  -movflags +faststart \
  "$output"

ffprobe -v error \
  -show_entries format=duration,size:stream=index,codec_type,codec_name,width,height,sample_rate,channels \
  -of default=noprint_wrappers=1 \
  "$output"

echo "created: $output"
