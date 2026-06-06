# KV260 Metavision Troubleshooting

Use this reference when the desktop, viewer, recording, or remote control gets stuck.

## Quick Status

```sh
cd /home/petalinux/Projects/kria-kv260-starter
./scripts/kv260-event-camera-switch.sh --status
./scripts/kv260-event-camera-api.sh status
fuser -v /dev/video0 2>/dev/null || true
ps -ef | grep -Ei 'metavision|kv260-event|x11|matchbox' | grep -v grep || true
```

## Stale Viewer Or Busy Cursor

Use:

```sh
./scripts/kv260-event-camera-switch.sh --stop-all
./scripts/kv260-recover-event-viewer.sh
```

Then reopen exactly one target:

```sh
./scripts/kv260-event-camera-switch.sh --board
```

or:

```sh
./scripts/kv260-event-camera-switch.sh --windows
```

## Preview Turns Black Or Stalls

Known observed problem:

```text
custom preview can become static/black after event bursts or lighting/cap changes;
native viewer may continue to show events because it uses Prophesee/OpenEB rendering paths.
```

Debug order:

1. Confirm `/dev/video0` is not shared.
2. Run the validator and stream test.
3. Check whether recording still writes bytes even if preview stalls.
4. Prefer recording robustness over preview experiments.
5. Compare with native `metavision_viewer` only as a smoke test.

Useful files:

```text
references/kv260-event-camera-validation.md
references/kv260-openeb-custom-viewer-research.md
references/kv260-recording-robustness.md
```

## Duplicate Launchers

If extra desktop menu items appear, check both `root` and `petalinux` application locations. The board desktop may run under a user different from the SSH shell.

Common locations:

```text
/usr/share/applications
/home/petalinux/.local/share/applications
/home/root/.local/share/applications
/home/petalinux/Desktop
/home/root/Desktop
```

Use the installer/fixer:

```sh
./scripts/kv260-install-prophesee-desktop.sh
./scripts/kv260-fix-metavision-launcher.sh
```

## RDP/VNC Limits

The observed Prophesee PetaLinux image did not provide `xrdp`/`xorgxrdp` packages in its feeds. Practical remote GUI choices:

```text
Windows SSH X11 for apps
local HDMI/Matchbox desktop
custom control center that starts local or X11 viewer
```

Treat full RDP as requiring a PetaLinux image/rootfs rebuild or custom package feed unless proven otherwise on the target image.

## PetaLinux SCP/SFTP Limit

PetaLinux Dropbear image may not provide SFTP server:

```text
/usr/libexec/sftp-server: No such file or directory
```

Use `scp -O` from Windows where needed, or use SSH/base64 fallback for private history mirrors.

