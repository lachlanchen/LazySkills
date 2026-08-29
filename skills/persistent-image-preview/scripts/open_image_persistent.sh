#!/usr/bin/env bash
set -euo pipefail

usage() {
  cat <<'EOF'
Usage: open_image_persistent.sh [--display DISPLAY] [--viewer APP] [--state-dir DIR] IMAGE

Open IMAGE in a detached desktop viewer and record the last-opened state.
EOF
}

display="${DISPLAY:-}"
display_explicit=false
xauthority="${XAUTHORITY:-}"
viewer=""
state_dir="${XDG_STATE_HOME:-$HOME/.local/state}/persistent-image-preview"
image=""

while (($#)); do
  case "$1" in
    --display)
      display="${2:?--display requires a value}"
      display_explicit=true
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

display_is_xvfb() {
  local candidate="${1%%.*}"
  pgrep -a Xvfb 2>/dev/null | awk -v display="$candidate" '
    $0 ~ ("Xvfb " display "([[:space:]]|$)") { found = 1 }
    END { exit(found ? 0 : 1) }
  '
}

display_works() {
  local candidate="$1" candidate_xauthority="${2:-}"
  if command -v xdpyinfo >/dev/null 2>&1; then
    if [[ -n "$candidate_xauthority" ]]; then
      env DISPLAY="$candidate" XAUTHORITY="$candidate_xauthority" xdpyinfo >/dev/null 2>&1
    else
      env DISPLAY="$candidate" xdpyinfo >/dev/null 2>&1
    fi
  elif command -v xset >/dev/null 2>&1; then
    if [[ -n "$candidate_xauthority" ]]; then
      env DISPLAY="$candidate" XAUTHORITY="$candidate_xauthority" xset q >/dev/null 2>&1
    else
      env DISPLAY="$candidate" xset q >/dev/null 2>&1
    fi
  else
    [[ -n "$candidate" ]]
  fi
}

if [[ "$display_explicit" != true ]] && [[ -n "$display" ]] && display_is_xvfb "$display"; then
  display=""
  xauthority=""
fi

if [[ -n "$display" ]] && ! display_works "$display" "$xauthority"; then
  display=""
  xauthority=""
fi

if [[ -z "$display" ]]; then
  current_bus="${DBUS_SESSION_BUS_ADDRESS:-}"
  while read -r shell_pid; do
    [[ -r "/proc/$shell_pid/environ" ]] || continue
    shell_env="$(tr '\0' '\n' <"/proc/$shell_pid/environ")"
    candidate="$(printf '%s\n' "$shell_env" | sed -n 's/^DISPLAY=//p' | head -n 1)"
    candidate_xauthority="$(printf '%s\n' "$shell_env" | sed -n 's/^XAUTHORITY=//p' | head -n 1)"
    candidate_bus="$(printf '%s\n' "$shell_env" | sed -n 's/^DBUS_SESSION_BUS_ADDRESS=//p' | head -n 1)"
    [[ -n "$candidate" ]] || continue
    display_is_xvfb "$candidate" && continue
    if [[ -n "$current_bus" && "$candidate_bus" != "$current_bus" ]]; then
      continue
    fi
    if display_works "$candidate" "$candidate_xauthority"; then
      display="$candidate"
      xauthority="$candidate_xauthority"
      break
    fi
  done < <(pgrep -u "$(id -u)" -x gnome-shell || true)
fi

if [[ -z "$display" ]]; then
  for candidate in :0 :1; do
    display_is_xvfb "$candidate" && continue
    if display_works "$candidate" "$xauthority"; then
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
      if [[ "$candidate" == "eog" ]]; then
        launch=("$candidate" --new-instance "$image")
      else
        launch=("$candidate" "$image")
      fi
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
launch_env=(env DISPLAY="$display")
if [[ -n "$xauthority" ]]; then
  launch_env+=(XAUTHORITY="$xauthority")
fi
nohup setsid "${launch_env[@]}" "${launch[@]}" >>"$log_file" 2>&1 </dev/null &
launcher_pid=$!

printf '%s\n' "$image" >"$state_dir/last-image"
printf '%s\n' "$display" >"$state_dir/last-display"
printf '%s\n' "$xauthority" >"$state_dir/last-xauthority"
printf '%s\n' "$launcher_pid" >"$state_dir/last-launcher.pid"

printf 'opened=%s\ndisplay=%s\nlauncher_pid=%s\nlog=%s\n' \
  "$image" "$display" "$launcher_pid" "$log_file"
