#!/usr/bin/env python3
"""Watch a submitted Xiaoyunque browser thread and copy the finished MP4.

This is browser/CDP-only. It does not submit a new job and does not call the
Xiaoyunque open API. It reads the logged-in page DOM/resources, waits for a
finished video URL, downloads it, verifies it with ffprobe when available, and
copies it to requested folders.
"""

from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.parse
import urllib.request
from pathlib import Path
from typing import Any

import websocket


STATUS_RE = (
    r"(排队等待中|优先处理中|生成中|大约还需\s*\d+\s*分钟|还需\s*\d+\s*分钟|"
    r"下载|完成|失败|内部错误|"
    r"积分不足|余额不足|审核|合规|开会员加速|重新生成)"
)

PROBE_JS = rf"""
(() => {{
  const text = document.body ? (document.body.innerText || '') : '';
  const status = (text.match(/{STATUS_RE}/g) || []).slice(-100);
  const videos = [...document.querySelectorAll('video')].map((v, i) => ({{
    i,
    src: v.currentSrc || v.src || '',
    poster: v.poster || '',
    ready: v.readyState,
    duration: Number.isFinite(v.duration) ? v.duration : null,
    w: v.videoWidth,
    h: v.videoHeight,
    rect: (() => {{
      const r = v.getBoundingClientRect();
      return {{x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)}};
    }})()
  }}));
  const anchors = [...document.querySelectorAll('a[href]')]
    .map(a => a.href)
    .filter(h => /mp4|download|media|video|everphoto|tos/i.test(h))
    .slice(-100);
  const resources = performance.getEntriesByType('resource')
    .map(e => e.name)
    .filter(h => /mp4|m3u8|media|video|everphoto|tos/i.test(h))
    .filter(h => !/\.webp|\.png|\.jpg|\.jpeg|sdk|\.js|\.css|sync_asset|common\/upload|pippit_cms/i.test(h))
    .slice(-200);
  return {{
    time: new Date().toISOString(),
    href: location.href,
    points: (document.querySelector('[class*=pointsBadgeButton]')?.innerText || '').trim(),
    status,
    videos,
    anchors,
    resources,
    tail: text.slice(-1200)
  }};
}})()
"""


class CdpPage:
    def __init__(self, page_id: str, cdp_url: str) -> None:
        pages = json.load(urllib.request.urlopen(f"{cdp_url}/json/list", timeout=10))
        target = next((page for page in pages if page.get("id") == page_id), None)
        if not target:
            raise RuntimeError(f"CDP page not found: {page_id}")
        self.ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=20)
        self.next_id = 0

    def call(self, method: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        self.next_id += 1
        msg_id = self.next_id
        self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            message = json.loads(self.ws.recv())
            if message.get("id") == msg_id:
                if "error" in message:
                    raise RuntimeError(json.dumps(message["error"], ensure_ascii=False))
                return message.get("result", {})

    def eval(self, expression: str) -> Any:
        result = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": True},
        )
        remote = result.get("result", {})
        if remote.get("subtype") == "error":
            raise RuntimeError(remote.get("description", "Runtime.evaluate failed"))
        return remote.get("value")

    def navigate(self, url: str) -> None:
        self.call("Page.enable")
        self.call("Page.navigate", {"url": url})


def page_exists(page_id: str, cdp_url: str) -> bool:
    pages = json.load(urllib.request.urlopen(f"{cdp_url}/json/list", timeout=10))
    return any(page.get("id") == page_id for page in pages)


def open_thread_page(thread_url: str, cdp_url: str) -> str:
    encoded = urllib.parse.quote(thread_url, safe="")
    request = urllib.request.Request(f"{cdp_url}/json/new?{encoded}", method="PUT")
    page = json.load(urllib.request.urlopen(request, timeout=10))
    return str(page["id"])


def head_type(url: str) -> tuple[str, str]:
    if url.startswith("blob:"):
        return "blob", ""
    try:
        request = urllib.request.Request(
            url,
            method="HEAD",
            headers={"User-Agent": "Mozilla/5.0", "Referer": "https://xyq.jianying.com/"},
        )
        with urllib.request.urlopen(request, timeout=15) as response:
            return response.headers.get("content-type", ""), response.headers.get("content-length", "")
    except Exception as exc:  # noqa: BLE001 - record and keep trying other candidates.
        return f"ERR:{type(exc).__name__}", ""


def download(url: str, output: Path) -> None:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0", "Referer": "https://xyq.jianying.com/"},
    )
    output.parent.mkdir(parents=True, exist_ok=True)
    with urllib.request.urlopen(request, timeout=600) as response, output.open("wb") as handle:
        while True:
            chunk = response.read(1024 * 1024)
            if not chunk:
                break
            handle.write(chunk)


def ffprobe(path: Path) -> str:
    if not shutil.which("ffprobe"):
        return ""
    result = subprocess.run(
        [
            "ffprobe",
            "-v",
            "error",
            "-show_entries",
            "format=duration,size",
            "-show_entries",
            "stream=width,height,codec_name",
            "-of",
            "json",
            str(path),
        ],
        check=False,
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    return result.stdout.strip()


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222")
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--thread-url", required=True)
    parser.add_argument("--output-dir", type=Path, required=True)
    parser.add_argument("--filename", required=True)
    parser.add_argument("--copy-to", type=Path, action="append", default=[])
    parser.add_argument("--interval", type=float, default=30)
    parser.add_argument("--max-polls", type=int, default=240)
    parser.add_argument("--min-bytes", type=int, default=200_000)
    parser.add_argument("--reload-every", type=float, default=600)
    return parser


def main() -> int:
    args = build_parser().parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)
    output = args.output_dir / args.filename
    page_id = args.page_id
    seen: set[str] = set()
    start = time.time()
    last_reload = start

    for poll in range(1, args.max_polls + 1):
        if not page_exists(page_id, args.cdp_url):
            print(f"poll {poll:03d}: page id missing; reopening thread", flush=True)
            try:
                page_id = open_thread_page(args.thread_url, args.cdp_url)
                (args.output_dir / "watch_page_id.txt").write_text(page_id + "\n", encoding="utf-8")
                time.sleep(8)
            except Exception as exc:  # noqa: BLE001 - keep the watcher alive.
                print(f"poll {poll:03d}: reopen failed {type(exc).__name__}: {exc}", flush=True)
                time.sleep(args.interval)
                continue

        try:
            page = CdpPage(page_id, args.cdp_url)
        except Exception as exc:  # noqa: BLE001 - keep the watcher alive.
            print(f"poll {poll:03d}: attach failed {type(exc).__name__}: {exc}", flush=True)
            time.sleep(args.interval)
            continue

        try:
            if time.time() - last_reload > args.reload_every:
                page.navigate(args.thread_url)
                last_reload = time.time()
                time.sleep(8)
            data = page.eval(PROBE_JS)
        except Exception as exc:  # noqa: BLE001 - keep the watcher alive.
            print(f"poll {poll:03d}: cdp error {type(exc).__name__}: {exc}", flush=True)
            time.sleep(args.interval)
            continue

        (args.output_dir / f"watch_{poll:03d}.json").write_text(
            json.dumps(data, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        status = ",".join(data.get("status") or []) or "no explicit status"
        videos = data.get("videos") or []
        print(
            f"poll {poll:03d}: points={data.get('points')} status={status} "
            f"videos={len(videos)} elapsed={int(time.time() - start)}s",
            flush=True,
        )

        if any(token in status for token in ("失败", "内部错误", "积分不足", "余额不足", "审核", "合规")):
            print("blocking status seen; not retrying automatically", flush=True)
            return 43

        urls = [
            video.get("src") or ""
            for video in videos
            if video.get("src") and not str(video.get("src")).startswith("blob:")
        ]
        if urls or "下载" in status:
            urls.extend(data.get("anchors") or [])
            urls.extend(data.get("resources") or [])

        for url in urls:
            if not url or url in seen or url.startswith("blob:"):
                continue
            seen.add(url)
            content_type, content_length = head_type(url)
            print(f"candidate: {content_type} {content_length} {url[:180]}", flush=True)
            if content_type.startswith("ERR:") or content_type.startswith("text/html"):
                continue
            if "video" not in content_type.lower() and ".mp4" not in url.lower():
                continue

            try:
                download(url, output)
            except Exception as exc:  # noqa: BLE001 - protected URLs can expire or require page-only access.
                print(f"download failed: {type(exc).__name__}: {exc}", flush=True)
                continue
            if output.stat().st_size < args.min_bytes:
                print(f"download too small: {output.stat().st_size}", flush=True)
                continue

            probe = ffprobe(output)
            if probe:
                print(probe, flush=True)
            for folder in args.copy_to:
                folder.mkdir(parents=True, exist_ok=True)
                target = folder / output.name
                shutil.copy2(output, target)
                print(f"copied: {target}", flush=True)
            print(f"DONE output={output}", flush=True)
            return 0

        time.sleep(args.interval)

    print("timed out waiting for Xiaoyunque result", flush=True)
    return 124


if __name__ == "__main__":
    raise SystemExit(main())
