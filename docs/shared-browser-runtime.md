# Shared Browser Runtime

Lachlan's persistent automation browser uses one Chrome identity for
Xiaoyunque, JLC/JLCEDA web pages, and normal downloads.

| Component | Value |
| --- | --- |
| Chrome profile | `$HOME/.cache/xyq-chrome` |
| Display | `:98` |
| VNC | `127.0.0.1:5908` |
| noVNC | `127.0.0.1:6099` |
| AgInTi Browser | `http://127.0.0.1:8794` |
| CDP | `http://127.0.0.1:9344` |

Viewer URL:

```text
http://127.0.0.1:6099/vnc_lite.html?host=127.0.0.1&port=6099&autoconnect=1&resize=remote
```

Reuse the profile; never create a replacement when the browser is merely
stopped. Keep its cookies, login state, history, downloads, and other private
state out of git. LCEDA Pro's Electron state is separate from this Chrome
profile.
