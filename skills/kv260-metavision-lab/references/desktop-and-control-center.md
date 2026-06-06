# KV260 Desktop And Control Center

Use this reference for local desktop launchers, Windows SSH X11, and the control center.

## Board Desktop Launchers

Main installer/fixer scripts:

```text
scripts/kv260-install-prophesee-desktop.sh
scripts/kv260-fix-metavision-launcher.sh
scripts/kv260-launch-desktop-viewer.sh
scripts/kv260-metavision-viewer-toggle.sh
```

Target behavior:

- one custom viewer launcher;
- one native Metavision viewer launcher/toggle;
- one file-transfer/control utility launcher when needed;
- no duplicate stale desktop launchers.

If duplicate launchers appear, inspect:

```text
/usr/share/applications
/home/petalinux/.local/share/applications
/home/root/.local/share/applications
/home/petalinux/Desktop
/home/root/Desktop
```

## Windows Control Center

Main files:

```text
scripts/kv260-metavision-control-panel.py
scripts/kv260-metavision-control-panel.sh
scripts/windows/Install-KV260WindowsShortcuts.ps1
scripts/windows/Open-KV260EventCamera.ps1
scripts/windows/Start-KV260EventCamera-BoardDesktop.ps1
scripts/windows/Start-KV260EventCamera-X11.ps1
```

The Windows control center was designed as one user entry point for:

- open custom event viewer on Windows via SSH X11;
- open custom event viewer on KV260 display;
- stop all viewers before switching target;
- open common KV260 GUI apps via SSH X11;
- open Jupyter through tunnel/browser;
- run board power actions;
- browse and transfer files.

## File Transfer GUI

Main files:

```text
scripts/kv260-file-transfer-gui.py
scripts/kv260-file-transfer-gui.sh
scripts/kv260-list-files-json.py
references/kv260-file-transfer.md
```

Design:

- left panel for board files;
- right panel for remote/host files;
- bidirectional copy buttons;
- drag/drop when the GUI toolkit/session supports it;
- avoid relying on PetaLinux SFTP.

Important PetaLinux transfer detail:

```text
This image lacks /usr/libexec/sftp-server.
```

From Windows, use legacy SCP mode when pulling from KV260:

```powershell
scp.exe -O petalinux-kv260:/home/petalinux/file.txt C:\Users\Administrator\Downloads\
```

From KV260 to Windows, the SSH key used in this lab is:

```text
/home/petalinux/.ssh/id_dropbear_rsa
```

## X11 Versus Local Display

The custom viewer can run either:

```text
KV260 local HDMI desktop
Windows SSH X11 display
```

Only one process can own `/dev/video0`, so switching targets should stop the other side first.

The control center should implement target switching as:

```text
stop all viewers -> start requested target -> confirm process/device owner
```

