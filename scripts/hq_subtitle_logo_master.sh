#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'USAGE'
Usage:
  scripts/hq_subtitle_logo_master.sh INPUT.mp4 SUBTITLES.srt OUTPUT.mp4 [options]

Create a high-quality publish master by burning an SRT subtitle file and
optionally overlaying a logo in a single ffmpeg encode pass. This is useful
when a standard publish pipeline re-encodes too aggressively.

Options:
  --logo PATH            Optional PNG/WebP logo to overlay.
  --logo-height N        Logo height in pixels. Default: 288 for 1080x1920.
  --logo-x N             Logo x position. Default: 38.
  --logo-y N             Logo y position. Default: 38.
  --font-size N          Subtitle font size. Default: 44.
  --font-file PATH       Subtitle font file. Default: fc-match Noto Sans CJK JP.
  --margin-v N           Subtitle bottom margin. Default: 280.
  --crf N                x264 CRF. Default: 10.
  --preset NAME          x264 preset. Default: slow.
  --audio-mode MODE      copy or aac. Default: copy.
  -h, --help             Show help.

Example:
  scripts/hq_subtitle_logo_master.sh input.mp4 lyrics.srt output.mp4 \
    --logo /path/to/logo.png --crf 10 --margin-v 280
USAGE
}

if [[ $# -lt 3 ]]; then
  usage >&2
  exit 2
fi

input=$1
subtitles=$2
output=$3
shift 3

logo=""
logo_height=288
logo_x=38
logo_y=38
font_size=44
font_file=""
margin_v=280
crf=10
preset=slow
audio_mode=copy

while [[ $# -gt 0 ]]; do
  case "$1" in
    --logo)
      logo="${2:?missing --logo value}"
      shift 2
      ;;
    --logo-height)
      logo_height="${2:?missing --logo-height value}"
      shift 2
      ;;
    --logo-x)
      logo_x="${2:?missing --logo-x value}"
      shift 2
      ;;
    --logo-y)
      logo_y="${2:?missing --logo-y value}"
      shift 2
      ;;
    --font-size)
      font_size="${2:?missing --font-size value}"
      shift 2
      ;;
    --font-file)
      font_file="${2:?missing --font-file value}"
      shift 2
      ;;
    --margin-v)
      margin_v="${2:?missing --margin-v value}"
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

for required in "$input" "$subtitles"; do
  if [[ ! -f "$required" ]]; then
    echo "file not found: $required" >&2
    exit 1
  fi
done

if [[ -n "$logo" && ! -f "$logo" ]]; then
  echo "logo not found: $logo" >&2
  exit 1
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
tmpdir=$(mktemp -d)
cleanup() {
  rm -rf "$tmpdir"
}
trap cleanup EXIT

cp "$subtitles" "$tmpdir/subtitles.srt"

if [[ -z "$font_file" ]]; then
  font_file=$(fc-match -f '%{file}\n' 'Noto Sans CJK JP' | head -1 || true)
fi
if [[ -z "$font_file" || ! -f "$font_file" ]]; then
  echo "could not resolve a subtitle font; pass --font-file" >&2
  exit 1
fi

if ffmpeg -hide_banner -filters 2>/dev/null | grep -qE ' subtitles +V->V'; then
  subtitle_style="FontName=Noto Sans CJK JP,Fontsize=${font_size},PrimaryColour=&H00FFFFFF,OutlineColour=&H00000000,BorderStyle=1,Outline=3,Shadow=0,Bold=1,Alignment=2,MarginV=${margin_v}"
  subtitle_filter="subtitles=${tmpdir}/subtitles.srt:force_style='${subtitle_style}'"
else
  awk -v outdir="$tmpdir" '
    function seconds(t, parts) {
      gsub(",", ".", t)
      split(t, parts, ":")
      return (parts[1] * 3600) + (parts[2] * 60) + parts[3]
    }
    /^[0-9]+$/ { next }
    /-->/ {
      idx += 1
      split($0, range, " --> ")
      starts[idx] = seconds(range[1])
      ends[idx] = seconds(range[2])
      files[idx] = sprintf("%s/cue_%03d.txt", outdir, idx)
      next
    }
    NF == 0 { next }
    idx > 0 {
      print $0 >> files[idx]
    }
    END {
      manifest = outdir "/cue_manifest.tsv"
      for (i = 1; i <= idx; i++) {
        printf "%s\t%s\t%s\n", starts[i], ends[i], files[i] >> manifest
      }
    }
  ' "$tmpdir/subtitles.srt"

  subtitle_filter=""
  while IFS=$'\t' read -r cue_start cue_end cue_file; do
    [[ -n "$cue_start" && -n "$cue_end" && -f "$cue_file" ]] || continue
    subtitle_filter+="drawtext=fontfile=${font_file}:"
    subtitle_filter+="textfile=${cue_file}:fontcolor=white:fontsize=${font_size}:"
    subtitle_filter+="borderw=3:bordercolor=black:line_spacing=8:"
    subtitle_filter+="x=(w-text_w)/2:y=h-${margin_v}-text_h:"
    subtitle_filter+="enable='between(t,${cue_start},${cue_end})',"
  done < "$tmpdir/cue_manifest.tsv"
  subtitle_filter="${subtitle_filter%,}"
fi

if [[ -n "$logo" ]]; then
  filter_complex="[0:v]${subtitle_filter}[base];[1:v]scale=-1:${logo_height}[logo];[base][logo]overlay=${logo_x}:${logo_y},setsar=1[v]"
  ffmpeg -hide_banner -loglevel error -y \
    -i "$input" -i "$logo" \
    -filter_complex "$filter_complex" \
    -map "[v]" -map 0:a? \
    -c:v libx264 -preset "$preset" -crf "$crf" -pix_fmt yuv420p \
    "${audio_args[@]}" \
    -movflags +faststart \
    "$output"
else
  ffmpeg -hide_banner -loglevel error -y \
    -i "$input" \
    -vf "$subtitle_filter" \
    -map 0:v:0 -map 0:a? \
    -c:v libx264 -preset "$preset" -crf "$crf" -pix_fmt yuv420p \
    "${audio_args[@]}" \
    -movflags +faststart \
    "$output"
fi

ffprobe -v error \
  -show_entries format=duration,size,bit_rate:stream=index,codec_type,codec_name,width,height,bit_rate,sample_rate,channels \
  -of default=noprint_wrappers=1 \
  "$output"

echo "created: $output"
