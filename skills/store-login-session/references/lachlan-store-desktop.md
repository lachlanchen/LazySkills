# Shared store desktop on the Lachlan workstation

Verified for LazyEdit Studio on 2026-10-04. Read the latest project handoff and
check live ownership before using these values; do not assume they stay fixed.

- Existing browser: local CDP `127.0.0.1:9497`.
- Visible desktop:
  `http://127.0.0.1:6165/vnc.html?autoconnect=1&resize=scale`.
- Persistent Chrome profile:
  `/home/lachlan/.local/share/echomind-oauth-chrome`.
- Existing display `:197`, loopback VNC `5965`, noVNC `6165`.
- LazyEdit CDP adapter: `scripts/studio/cdp.py`, `Tab(port, target_id)`.
  `Page.bringToFront` selects the observed tab; `Tab.close()` closes the
  controller socket, not the Chrome tab or profile.

This desktop/profile also has authorized tabs for other apps. Select only the
current app's ASC or Play page and leave unrelated tabs untouched. Discover
target IDs live; historical IDs are not release selectors. Avoid printing a
full tab inventory because OAuth URLs may contain private state.

The owner explicitly requested keeping Apple/Google login in this existing
desktop. Reuse it across store tasks; no new Xvfb/noVNC stack or recurring
keepalive job was requested. Capture release receipts and stop obsolete test
simulators/emulators without stopping this requested store desktop.

LazyEdit's current formal App Store app ID is `6814061525`, bundle
`art.lazying.lazyedit`. Store instructions and release facts live under
`store/studio/` and `references/studio/` in the lowercase deployed checkout.
Private credentials and receipts stay under the existing protected config and
`/home/lachlan/Nutstore Files/Share/LazyEdit/`; use the scoped credential source
documented for the selected task, never copy its values into a skill.

On this run, the renewed ASC session opened App Privacy normally. The owner
reported that remembered Apple authentication often needs two ordinary
Continue clicks. That shortcut is a recovery strategy, not a guarantee that
every Apple flow is passwordless or that 2FA can be skipped.
