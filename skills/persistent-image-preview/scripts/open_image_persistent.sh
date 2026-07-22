#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: open_image_persistent.sh [--display DISPLAY] [--viewer APP] [--state-dir DIR] IMAGE

Open IMAGE in a detached desktop viewer and record the last-opened state.
EOF
}

display="${DISPLAY:-}"
viewer=""
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/persistent-image-preview"
image=""

while (($#)); do
  case "$1" in
    --display)
      display="${2:?--display requires a value}"
      shift 2
      ;;
    --viewer)
      viewer="${2:?--viewer requires a value}"
      shift 2
      ;;
    --state-dir)
      state_dir="${2:?--state-dir requires a value}"
      shift 2
      ;;
    -h|--help)
      usage
      exit 0
      ;;
    --)
      shift
      image="${1:-}"
      shift || true
      break
      ;;
    -*)
      echo "Unknown option: $1" >&2
      usage >&2
      exit 2
      ;;
    *)
      if [[ -n "$image" ]]; then
        echo "Only one image may be opened per invocation." >&2
        exit 2
      fi
      image="$1"
      shift
      ;;
  esac
done

if [[ -z "$image" ]]; then
  usage >&2
  exit 2
fi

if [[ ! -s "$image" ]]; then
  echo "Image does not exist or is empty: $image" >&2
  exit 1
fi

image="$(realpath "$image")"
if command -v file >/dev/null 2>&1; then
  mime_type="$(file --brief --mime-type "$image")"
  if [[ "$mime_type" != image/* ]]; then
    echo "Not an image file ($mime_type): $image" >&2
    exit 1
  fi
fi

display_works() {
  local candidate="$1"
  if command -v xdpyinfo >/dev/null 2>&1; then
    env DISPLAY="$candidate" xdpyinfo >/dev/null 2>&1
  elif command -v xset >/dev/null 2>&1; then
    env DISPLAY="$candidate" xset q >/dev/null 2>&1
  else
    [[ -n "$candidate" ]]
  fi
}

if [[ -n "$display" ]] && ! display_works "$display"; then
  display=""
fi

if [[ -z "$display" ]]; then
  for candidate in :0 :1 :98 :99; do
    if display_works "$candidate"; then
      display="$candidate"
      break
    fi
  done
fi

if [[ -z "$display" ]]; then
  echo "No reachable graphical display. Pass --display explicitly." >&2
  exit 1
fi

if [[ -n "$viewer" ]]; then
  if ! command -v "$viewer" >/dev/null 2>&1; then
    echo "Viewer is not installed: $viewer" >&2
    exit 1
  fi
  launch=("$viewer" "$image")
else
  launch=()
  for candidate in loupe eog ristretto gwenview imv feh; do
    if command -v "$candidate" >/dev/null 2>&1; then
      launch=("$candidate" "$image")
      break
    fi
  done
  if ((${#launch[@]} == 0)) && command -v xdg-open >/dev/null 2>&1; then
    launch=(xdg-open "$image")
  fi
  if ((${#launch[@]} == 0)) && command -v gio >/dev/null 2>&1; then
    launch=(gio open "$image")
  fi
  if ((${#launch[@]} == 0)); then
    echo "No graphical image viewer or desktop opener is installed." >&2
    exit 1
  fi
fi

mkdir -p "$state_dir"
log_file="$state_dir/viewer.log"
nohup setsid env DISPLAY="$display" "${launch[@]}" >>"$log_file" 2>&1 </dev/null &
launcher_pid=$!

printf '%s\n' "$image" >"$state_dir/last-image"
printf '%s\n' "$display" >"$state_dir/last-display"
printf '%s\n' "$launcher_pid" >"$state_dir/last-launcher.pid"

printf 'opened=%s\ndisplay=%s\nlauncher_pid=%s\nlog=%s\n' \
  "$image" "$display" "$launcher_pid" "$log_file"
