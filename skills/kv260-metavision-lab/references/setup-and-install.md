# KV260 Metavision Setup And Install

Use this reference for board bring-up and repeatable setup.

## Primary Repo

```text
/home/petalinux/Projects/kria-kv260-starter
git@github.com:lachlanchen/kria-metavision-lab.git
```

## Setup Script

Main setup entrypoint:

```sh
cd /home/petalinux/Projects/kria-kv260-starter
KV260_SUDO_PASSWORD=<password> ./scripts/kv260-full-setup.sh
```

Dry run:

```sh
./scripts/kv260-full-setup.sh --dry-run
```

The setup script is designed to prepare:

- board packages available from the current PetaLinux feeds;
- X11/Matchbox desktop launchers;
- custom event viewer dependencies;
- native Metavision launcher/toggle wrappers;
- recording API scripts;
- file-transfer and control-center launchers;
- optional Windows shortcut/control-center installation over LAN SSH.

## Prophesee / Metavision Baseline

Known working runtime state from the lab:

```text
load-prophesee-kv260-imx636.sh reports loaded
/dev/video0 exists
/dev/media0 exists
/dev/v4l-subdev0..3 exist
v4l2 stream test can produce non-zero raw data
```

Useful checks:

```sh
media-ctl -p 2>/dev/null || true
v4l2-ctl --list-devices 2>/dev/null || true
v4l2-ctl -d /dev/video0 --all 2>/dev/null || true
```

## Desktop

The practical local desktop is X11 + Matchbox. Full RDP is not reliable on this PetaLinux image because `xrdp`/`xorgxrdp` packages are not available from the observed on-device feeds.

Useful local packages previously installed when available:

```text
matchbox-desktop
matchbox-terminal
matchbox-wm
matchbox-session-sato
xserver-nodm
```

## Rootfs Space

Rootfs expansion tooling lives in:

```text
SystemMaintenance/
scripts/kv260-expand-rootfs-sd.sh
```

The expansion helper was designed to be idempotent and to support absolute or percent-of-full-card targets.

