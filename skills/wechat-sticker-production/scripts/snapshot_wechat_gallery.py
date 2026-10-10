#!/usr/bin/env python3
"""Capture the existing CDP sticker gallery and sync its public artwork only."""
import argparse
import base64
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import time
import urllib.request

import websocket


class Cdp:
    """Small read/capture client, standalone for installed skill use."""
    def __init__(self, page_id, endpoint):
        with urllib.request.urlopen(endpoint.rstrip("/") + "/json/list", timeout=10) as response:
            pages = json.load(response)
        target = next(page for page in pages if page.get("id") == page_id)
        self.ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=30)
        self.serial = 0

    def call(self, method, params=None):
        self.serial += 1
        self.ws.send(json.dumps({"id": self.serial, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == self.serial:
                if "error" in message:
                    raise RuntimeError(message["error"])
                return message.get("result", {})

    def eval(self, expression, await_promise=False):
        result = self.call("Runtime.evaluate", {"expression": expression,
                           "returnByValue": True, "awaitPromise": await_promise})
        if "exceptionDetails" in result:
            raise RuntimeError(result["exceptionDetails"])
        return result.get("result", {}).get("value")

    def navigate(self, url):
        self.call("Page.navigate", {"url": url})

    def bring_to_front(self):
        self.call("Page.bringToFront")


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def sync_file(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    if not destination.exists() or sha256(source) != sha256(destination):
        temporary = destination.with_name(destination.name + ".part")
        shutil.copy2(source, temporary)
        temporary.replace(destination)
    if sha256(source) != sha256(destination):
        raise ValueError(f"Copy verification failed: {source.name}")


def artwork_files(album):
    """Explicit allowlist: never export account receipts or browser screenshots."""
    names = ["index.html", "cover.png", "icon.png", "banner.jpg", "audit.json",
             "reward-guide.png", "reward-thanks.png"]
    return [album / name for name in names if (album / name).is_file()] + sorted(
        (album / "gifs").glob("*.gif"))


def capture(cdp, path, clip):
    data = cdp.call("Page.captureScreenshot", {
        "format": "png", "fromSurface": True, "captureBeyondViewport": True,
        "clip": {**clip, "scale": 1},
    })["data"]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(base64.b64decode(data))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("album", type=Path)
    parser.add_argument("destination", type=Path)
    parser.add_argument("--cdp-url", required=True)
    parser.add_argument("--page-id", required=True, help="Existing local gallery tab, not an account tab")
    parser.add_argument("--all-editions", action="store_true",
                        help="Show the library's All tab before capturing current and archived GIFs")
    args = parser.parse_args()
    album = args.album.resolve()
    destination = args.destination.resolve()
    expected = sorted(path.name for path in (album / "gifs").glob("*.gif"))
    if not expected or not (album / "index.html").is_file():
        parser.error("an existing populated local gallery is required")
    if destination == album or album in destination.parents or destination in album.parents:
        parser.error("source and destination must be independent directories")
    cdp = Cdp(args.page_id, args.cdp_url)
    try:
        if not str(cdp.eval("location.href")).startswith("file:"):
            parser.error("refusing to navigate a non-local-gallery tab")
        url = (album / "index.html").as_uri()
        cdp.navigate(url)
        cdp.bring_to_front()
        deadline = time.monotonic() + 30
        editions_selected = not args.all_editions
        while time.monotonic() < deadline:
            if not editions_selected:
                editions_selected = cdp.eval("location.href === " + json.dumps(url) +
                    " && document.readyState === 'complete' && (() => {"
                    "const all=document.querySelector('[data-edition=all]');"
                    "if(!all)return false; all.click();"
                    "document.querySelectorAll('img').forEach(i=>i.loading='eager');"
                    "return true;})()") is True
            ready = cdp.eval("location.href === " + json.dumps(url) + " && document.readyState === 'complete' && document.querySelectorAll('main figure img').length > 0 && [...document.querySelectorAll('header img, main figure img')].every(i => i.complete && i.naturalWidth > 0)")
            if ready is True and editions_selected:
                break
            time.sleep(.25)
        else:
            raise TimeoutError("Gallery images did not finish loading")
        cdp.eval("document.fonts.ready.then(() => true)", await_promise=True)
        items = cdp.eval("[...document.querySelectorAll('main figure img')].map(i => {const r=i.getBoundingClientRect();return {src:i.getAttribute('src'),x:r.x+scrollX,y:r.y+scrollY,width:r.width,height:r.height};})")
        if sorted(item["src"] for item in items) != ["gifs/" + name for name in expected]:
            raise ValueError("Gallery and GIF folder differ; rebuild the gallery first")
        stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
        folder = album / "captures" / stamp
        size = cdp.call("Page.getLayoutMetrics")["cssContentSize"]
        capture(cdp, folder / "gallery-full-page.png", {key: size[key] for key in ("x", "y", "width", "height")})
        for item in items:
            capture(cdp, folder / "stickers" / (Path(item["src"]).stem + ".png"),
                    {key: item[key] for key in ("x", "y", "width", "height")})
        manifest = {"captured_utc": stamp, "gif_count": len(expected),
                    "gallery_size": {key: size[key] for key in ("width", "height")},
                    "preview_kind": "CDP screenshot of each animated GIF at its current frame",
                    "files": [{"file": str(path.relative_to(folder)), "sha256": sha256(path)}
                              for path in sorted(folder.rglob("*.png"))]}
        (folder / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n")
        files = artwork_files(album) + [path for path in folder.rglob("*") if path.is_file()]
        for source in files:
            sync_file(source, destination / source.relative_to(album))
        print(json.dumps({"count": len(expected), "copied_files": len(files),
                          "hashes_verified": True, "capture": str(folder.relative_to(album)),
                          "destination": str(destination), "cloud_acknowledged": False}, ensure_ascii=False, indent=2))
    finally:
        cdp.ws.close()


if __name__ == "__main__":
    main()
