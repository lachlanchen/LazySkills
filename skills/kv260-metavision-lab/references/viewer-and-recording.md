# KV260 Viewer And Recording

Use this reference for the custom viewer, native viewer, and recording API.

## Ownership Rule

Only one process can own `/dev/video0`.

Typical owners:

```text
custom GTK viewer
native metavision_viewer
headless event API
validation/scanner commands
```

Before switching targets:

```sh
cd /home/petalinux/Projects/kria-kv260-starter
./scripts/kv260-event-camera-switch.sh --stop-all
fuser -v /dev/video0 2>/dev/null || true
```

## Custom Viewer

Main files:

```text
scripts/kv260-event-camera-app.py
scripts/kv260-event-camera-app.sh
scripts/kv260-event-camera-switch.sh
scripts/kv260-event-camera-x11.sh
scripts/kv260-validate-event-camera.py
references/kv260-event-camera-app.md
references/kv260-event-camera-validation.md
references/kv260-recording-robustness.md
```

User-facing behavior:

- open the event camera preview;
- choose output folder and file prefix;
- record `.pse2.raw` plus JSON metadata;
- load/open previous recordings;
- tune common preview parameters;
- close cleanly and release `/dev/video0`.

Design priority:

```text
recording correctness > preview smoothness > decorative GUI
```

When recording is active, preview may be decimated so writer/capture work stays ahead.

## Headless Recording API

Main files:

```text
scripts/kv260-event-camera-api.py
scripts/kv260-event-camera-api.sh
references/kv260-remote-recording-api.md
```

Start/status/tail:

```sh
./scripts/kv260-event-camera-api.sh start
./scripts/kv260-event-camera-api.sh status
./scripts/kv260-event-camera-api.sh tail
```

API base:

```text
http://192.168.1.250:8765
```

Core endpoints:

```text
GET  /api/v1/status
POST /api/v1/record/start
POST /api/v1/record/stop
GET  /api/v1/recordings
GET  /api/v1/recordings/download
```

Recommended for experiments:

```json
{
  "takeover": true,
  "count_events": false,
  "metadata": {
    "source": "experiment"
  }
}
```

## Native Metavision Viewer

Main files:

```text
scripts/kv260-metavision-viewer-toggle.sh
scripts/kv260-open-prophesee-viewer.sh
scripts/kv260-fix-metavision-launcher.sh
references/kv260-native-metavision-viewer-close-behavior.md
```

Known behavior:

- native viewer can be useful for SDK smoke tests;
- close may need multiple clicks because the native viewer/spawn wrapper can relaunch or redraw while the camera stream is active;
- use the toggle/recovery wrapper instead of creating duplicate desktop launchers.

## Recording Files

Default recording location:

```text
/home/petalinux/event_recordings
```

Repo `.gitignore` should exclude raw recordings:

```text
*.raw
*.pse2.raw
recordings/
event-visual/
```

