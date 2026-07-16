---
name: remote-gui-virtual-desktop
description: Use when launching, controlling, documenting, debugging, or cleaning up remote Linux GUI apps through a clean Xvfb desktop, x11vnc, noVNC/websockify, browser app windows, SSH-local ports, or camera/GUI process isolation. Applies to LabVIEW, KiCad, JLCEDA, FreeCAD, Blender GUI, vendor camera tools, license activation flows, and other agent-controlled desktop apps.
---

# Remote GUI Virtual Desktop

Use this skill when a GUI app should run in a clean remote desktop that the user
and agent can both view or control without disturbing the main desktop.

## Default Pattern

1. Pick a dedicated display and local ports, for example `:98`, VNC `5908`, noVNC `6099`.
2. Start Xvfb with explicit 24-bit depth:

```bash
Xvfb :98 -screen 0 1920x1080x24 -ac
```

3. Launch the app with clean X auth:

```bash
DISPLAY=:98 XAUTHORITY= /path/to/gui-app
```

4. Expose only localhost VNC:

```bash
x11vnc -display :98 -localhost -nopw -forever -shared -rfbport 5908
```

5. Bridge to noVNC:

```bash
websockify -D --web=/usr/share/novnc 127.0.0.1:6099 127.0.0.1:5908
```

6. Give the user:

```text
http://127.0.0.1:6099/vnc_lite.html?host=127.0.0.1&port=6099&autoconnect=1&scale=1
```

Keep VNC/noVNC bound to `127.0.0.1`. Use SSH tunneling or another authenticated
layer for remote viewing from a different machine.

## Canonical Shared Browser

On Lachlan's workstation, preserve the established Chrome browser identity:

```text
X display: :98
VNC: 127.0.0.1:5908
noVNC: http://127.0.0.1:6099/vnc_lite.html?host=127.0.0.1&port=6099&autoconnect=1&scale=1
AgInTi Browser: http://127.0.0.1:8794
Chrome CDP: http://127.0.0.1:9344
Chrome profile: $HOME/.cache/xyq-chrome
```

Xiaoyunque, JLC/JLCEDA web work, and ordinary downloads share this Chrome
profile. Reuse it when the user asks for the familiar browser or its download
history. Do not substitute `embedded-agentic-browser-chrome`,
`agentic-browser-vdesktop-chrome`, or a temporary profile. Do not delete,
overwrite, inspect secrets from, or commit the profile. LCEDA Pro's Electron
application state remains separate.

For `vnc_lite.html`, use `scale=1` to fit the entire remote desktop inside the
viewer. The lite client ignores `resize=remote`, which otherwise leaves a large
remote canvas clipped on smaller screens.

## AgenticApp Launcher

When working in AgenticApp, prefer:

```bash
agentic_tools/virtual_desktop/launch_virtual_desktop.sh \
  --name labview \
  --display :98 \
  --screen 1920x1080x24 \
  --vnc-port 5908 \
  --novnc-port 6099 \
  --open-browser \
  -- /path/to/gui-app
```

For LabVIEW Community:

```bash
agentic_tools/virtual_desktop/launch_virtual_desktop.sh \
  --name labview \
  --display :98 \
  --screen 1920x1080x24 \
  --vnc-port 5908 \
  --novnc-port 6099 \
  --app-match /usr/local/natinst/LabVIEW-2026-64/labview \
  --open-browser \
  -- /usr/local/natinst/LabVIEW-2026-64/labview
```

## Verification

```bash
DISPLAY=:98 XAUTHORITY= xdpyinfo | rg 'dimensions|depth of root window'
DISPLAY=:98 XAUTHORITY= xwininfo -root -tree | head -n 80
ss -ltnp | rg ':5908|:6099'
ps -eo pid,ppid,stat,cmd | rg -i 'Xvfb|x11vnc|websockify|labview|kicad|freecad|blender'
```

For LabVIEW, also check `:23520` for activation callback, `:3363` for VI
Server, and `:36987` for a LabVIEW MCP VI HTTP endpoint.

## Camera Cleanup

Stop camera tasks without closing the desktop:

```bash
ps -eo pid,ppid,stat,cmd | rg -i 'labview|ffplay|camera|v4l|/dev/video|MVCamCtrlDemo'
fuser -v /dev/video* 2>/dev/null || true
kill -TERM <camera-viewer-pid>
fuser -v /dev/video* 2>/dev/null || true
```

Do not kill the main IDE, Xvfb, x11vnc, or websockify unless the user asks to
close the whole GUI session.

## Troubleshooting

- If the browser opens without the expected Xiaoyunque, JLC, and download
  history, stop and verify `--user-data-dir=$HOME/.cache/xyq-chrome`; changing
  noVNC ports or displays does not select the browser identity.
- If `xdpyinfo` fails but the X socket exists, remove stale `/tmp/.X11-unix/XN`
  and `/tmp/.XN-lock` only after confirming no matching Xvfb process is alive.
- If a GUI reports X11 `BadMatch`, retry on a fresh `1920x1080x24` Xvfb display.
- If noVNC is blank, reconnect the browser and inspect `x11vnc` and `websockify`
  logs.
- If camera capture fails, find who owns `/dev/video*` with `fuser`.
- Record display, ports, process IDs, URLs, and stop commands in the repo or
  shared documentation after a successful setup.
