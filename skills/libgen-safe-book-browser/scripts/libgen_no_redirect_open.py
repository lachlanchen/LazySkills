#!/usr/bin/env python3
"""Open LibGen detail pages while blocking ad redirects through Chrome CDP.

The script attaches to an existing Chrome remote-debugging endpoint, opens each
URL from an about:blank tab, enables Fetch interception before navigation, and
aborts requests whose host is not explicitly allowed. It is intended for
bibliographic/detail-page inspection, not mirror/download-page automation.
"""

from __future__ import annotations

import argparse
import json
import queue
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any


DEFAULT_AD_WORDS = [
    "trip.com",
    "tripcdn",
    "ctrip",
    "pipaffiliates",
    "realizationnewestfangs",
    "evaluatestormypawn",
    "preferencenail",
    "storageimagedisplay",
    "googlesyndication",
    "doubleclick",
    "googleadservices",
    "pagead2",
    "taboola",
    "outbrain",
    "popads",
    "propeller",
]

INIT_SCRIPT = r"""
(() => {
  const bad = /trip\.com|tripcdn|ctrip|pipaffiliates|realizationnewestfangs|evaluatestormypawn|preferencenail|storageimagedisplay|googlesyndication|doubleclick|googleadservices|pagead2|taboola|outbrain|popads|propeller/i;
  const block = (url) => bad.test(String(url || ""));
  const allowed = (url) => {
    const value = String(url || "");
    if (!value || value.startsWith("/") || value.startsWith("#")) return true;
    if (value.startsWith("about:") || value.startsWith("data:") || value.startsWith("blob:")) return true;
    try {
      const host = new URL(value, location.href).hostname;
      return host === "libgen.pw" || host.endsWith(".libgen.pw") || host === "libgen.li" || host.endsWith(".libgen.li");
    } catch (_) {
      return false;
    }
  };
  const originalOpen = window.open;
  window.open = function(url, target, features) {
    if (block(url) || !allowed(url)) return null;
    return originalOpen.call(window, url, target, features);
  };
  for (const method of ["assign", "replace"]) {
    try {
      const original = Location.prototype[method];
      Location.prototype[method] = function(url) {
        if (block(url) || !allowed(url)) return undefined;
        return original.call(this, url);
      };
    } catch (_) {}
  }
  for (const method of ["pushState", "replaceState"]) {
    try {
      const original = history[method];
      history[method] = function(state, title, url) {
        if (url && (block(url) || !allowed(url))) return undefined;
        return original.call(this, state, title, url);
      };
    } catch (_) {}
  }
  document.addEventListener("click", (event) => {
    const a = event.target && event.target.closest ? event.target.closest("a[href]") : null;
    if (a && (block(a.href) || !allowed(a.href))) {
      event.preventDefault();
      event.stopImmediatePropagation();
    }
  }, true);
})();
"""


@dataclass(frozen=True)
class OpenResult:
    label: str
    status: str
    url: str
    title: str = ""
    final_url: str = ""
    text_sample: str = ""
    error: str = ""


LOAD_CHECK_SCRIPT = r"""
(() => {
  const text = document.body ? document.body.innerText : "";
  const resources = performance.getEntriesByType("resource").map((entry) => entry.name);
  const hasBootstrapCss = !!document.querySelector('link[href*="bootstrap"][href$=".css"], link[href*="bootstrap.min.css"]');
  const hasJquery = !!document.querySelector('script[src*="jquery"]');
  const hasBootstrapJs = !!document.querySelector('script[src*="bootstrap"][src$=".js"], script[src*="bootstrap.min.js"], script[src*="bootstrap.bundle.min.js"]');
  const bootstrapCssLoaded = resources.some((url) => url.includes("bootstrap") && url.includes(".css"));
  const jqueryLoaded = resources.some((url) => url.includes("jquery"));
  const bootstrapJsLoaded = resources.some((url) => url.includes("bootstrap") && url.includes(".js"));
  return {
    title: document.title,
    url: location.href,
    readyState: document.readyState,
    text: text.slice(0, 240),
    textLength: text.length,
    bootstrapCssLinked: hasBootstrapCss,
    bootstrapCssLoaded,
    jqueryLinked: hasJquery,
    jqueryLoaded,
    bootstrapJsLinked: hasBootstrapJs,
    bootstrapJsLoaded,
    useful: document.readyState === "complete" &&
      document.title &&
      text.length > 500 &&
      (!hasBootstrapCss || bootstrapCssLoaded) &&
      (!hasJquery || jqueryLoaded) &&
      (!hasBootstrapJs || bootstrapJsLoaded) &&
      !/bad internet|checking your browser|loading/i.test(text.slice(0, 1200))
  };
})()
"""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("urls", nargs="+", help="LibGen detail/search URLs to open")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222", help="Chrome CDP HTTP endpoint")
    parser.add_argument("--guard-seconds", type=int, default=600, help="Seconds to keep redirect guard attached")
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=["libgen.pw", "libgen.li"],
        help="Allowed top-level LibGen host. Repeat to allow additional hosts.",
    )
    parser.add_argument(
        "--allowed-resource-host",
        action="append",
        default=["cdn.jsdelivr.net", "code.jquery.com"],
        help="Allowed static subresource host. Repeat to allow additional CSS/JS hosts.",
    )
    parser.add_argument("--label", action="append", default=[], help="Optional labels matching positional URLs")
    parser.add_argument("--no-close-ad-targets", action="store_true", help="Do not close existing ad targets first")
    parser.add_argument("--json", action="store_true", help="Emit JSON lines for machine reading")
    return parser.parse_args()


def http_json(cdp_url: str, path: str, *, method: str = "GET") -> Any:
    request = urllib.request.Request(cdp_url.rstrip("/") + path, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def http_text(cdp_url: str, path: str, *, method: str = "GET") -> str:
    request = urllib.request.Request(cdp_url.rstrip("/") + path, method=method)
    with urllib.request.urlopen(request, timeout=10) as response:
        return response.read().decode("utf-8", "replace")


def new_tab(cdp_url: str, url: str) -> dict[str, Any]:
    path = "/json/new?" + urllib.parse.quote(url, safe=":/?&=%")
    try:
        return http_json(cdp_url, path, method="PUT")
    except urllib.error.HTTPError:
        return http_json(cdp_url, path, method="GET")


def host_allowed(url: str, allowed_hosts: set[str]) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme in {"about", "data", "blob"}:
        return True
    if host in allowed_hosts:
        return True
    return any(host.endswith("." + allowed) for allowed in allowed_hosts)


def is_ad_target(tab: dict[str, Any], ad_words: list[str]) -> bool:
    text = f"{tab.get('type', '')} {tab.get('title', '')} {tab.get('url', '')}".lower()
    return any(word in text for word in ad_words)


def close_ad_targets(cdp_url: str, ad_words: list[str]) -> list[dict[str, str]]:
    closed: list[dict[str, str]] = []
    for tab in http_json(cdp_url, "/json"):
        if not is_ad_target(tab, ad_words):
            continue
        try:
            http_text(cdp_url, "/json/close/" + tab["id"])
            closed.append({"type": tab.get("type", ""), "title": tab.get("title", ""), "url": tab.get("url", "")})
        except Exception:
            continue
    return closed


def cdp_call(
    ws: Any,
    counter: list[int],
    method: str,
    params: dict[str, Any] | None = None,
    *,
    allowed_hosts: set[str],
) -> dict[str, Any]:
    counter[0] += 1
    message_id = counter[0]
    ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
    while True:
        message = json.loads(ws.recv())
        if message.get("id") == message_id:
            return message
        if message.get("method") == "Fetch.requestPaused":
            handle_paused_request(ws, counter, message, allowed_hosts=allowed_hosts)


def handle_paused_request(ws: Any, counter: list[int], message: dict[str, Any], *, allowed_hosts: set[str]) -> None:
    params = message["params"]
    request_id = params["requestId"]
    request_url = params["request"]["url"]
    if host_allowed(request_url, allowed_hosts):
        method = "Fetch.continueRequest"
        payload = {"requestId": request_id}
    else:
        method = "Fetch.failRequest"
        payload = {"requestId": request_id, "errorReason": "Aborted"}
    counter[0] += 1
    ws.send(json.dumps({"id": counter[0], "method": method, "params": payload}))


def handle_frame_navigation(
    ws: Any,
    counter: list[int],
    message: dict[str, Any],
    *,
    target_url: str,
    allowed_navigation_hosts: set[str],
) -> None:
    frame = message.get("params", {}).get("frame", {})
    if frame.get("parentId"):
        return
    current_url = frame.get("url", "")
    if host_allowed(current_url, allowed_navigation_hosts):
        return
    counter[0] += 1
    ws.send(json.dumps({"id": counter[0], "method": "Page.navigate", "params": {"url": target_url}}))


def wait_for_useful_page(
    ws: Any,
    counter: list[int],
    *,
    allowed_hosts: set[str],
    timeout: float = 20.0,
) -> dict[str, Any]:
    deadline = time.time() + timeout
    last_value: dict[str, Any] = {}
    while time.time() < deadline:
        sample = cdp_call(
            ws,
            counter,
            "Runtime.evaluate",
            {"expression": LOAD_CHECK_SCRIPT, "returnByValue": True},
            allowed_hosts=allowed_hosts,
        )
        last_value = sample.get("result", {}).get("result", {}).get("value", {}) or {}
        if last_value.get("useful"):
            return last_value
        time.sleep(0.5)
    return last_value


def watch_ad_targets(cdp_url: str, ad_words: list[str], stop_event: threading.Event, interval: float = 0.5) -> None:
    while not stop_event.wait(interval):
        try:
            close_ad_targets(cdp_url, ad_words)
        except Exception:
            continue


def guard_tab(
    cdp_url: str,
    label: str,
    target_url: str,
    allowed_navigation_hosts: set[str],
    allowed_request_hosts: set[str],
    guard_seconds: int,
    result_queue: queue.Queue[OpenResult],
) -> None:
    try:
        import websocket  # type: ignore
    except Exception as exc:
        result_queue.put(OpenResult(label, "error", target_url, error=f"websocket-client missing: {exc}"))
        return

    try:
        tab = new_tab(cdp_url, "about:blank")
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)
        ws.settimeout(1)
        counter = [0]
        cdp_call(
            ws,
            counter,
            "Fetch.enable",
            {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]},
            allowed_hosts=allowed_request_hosts,
        )
        cdp_call(ws, counter, "Page.enable", allowed_hosts=allowed_request_hosts)
        cdp_call(
            ws,
            counter,
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": INIT_SCRIPT},
            allowed_hosts=allowed_request_hosts,
        )
        cdp_call(ws, counter, "Page.navigate", {"url": target_url}, allowed_hosts=allowed_request_hosts)
        value = wait_for_useful_page(ws, counter, allowed_hosts=allowed_request_hosts)
        result_queue.put(
            OpenResult(
                label=label,
                status="opened",
                url=target_url,
                title=value.get("title", ""),
                final_url=value.get("url", ""),
                text_sample=(value.get("text", "") or "").replace("\n", " | "),
            )
        )

        deadline = time.time() + max(0, guard_seconds)
        while time.time() < deadline:
            try:
                message = json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:  # type: ignore[attr-defined]
                continue
            except Exception:
                break
            if message.get("method") == "Fetch.requestPaused":
                handle_paused_request(ws, counter, message, allowed_hosts=allowed_request_hosts)
            elif message.get("method") == "Page.frameNavigated":
                handle_frame_navigation(
                    ws,
                    counter,
                    message,
                    target_url=target_url,
                    allowed_navigation_hosts=allowed_navigation_hosts,
                )
        ws.close()
    except Exception as exc:
        result_queue.put(OpenResult(label, "error", target_url, error=f"{type(exc).__name__}: {exc}"))


def main() -> int:
    args = parse_args()
    labels = args.label or [f"url-{index + 1}" for index in range(len(args.urls))]
    if len(labels) != len(args.urls):
        raise SystemExit("--label count must match URL count")

    if not args.no_close_ad_targets:
        closed = close_ad_targets(args.cdp_url, DEFAULT_AD_WORDS)
        if args.json:
            print(json.dumps({"event": "closed_ad_targets", "count": len(closed), "targets": closed}, ensure_ascii=False))
        else:
            print(f"closed_ad_targets={len(closed)}")

    allowed_navigation_hosts = {host.lower() for host in args.allowed_host}
    allowed_request_hosts = allowed_navigation_hosts | {host.lower() for host in args.allowed_resource_host}
    result_queue: queue.Queue[OpenResult] = queue.Queue()
    stop_watcher = threading.Event()
    watcher = threading.Thread(
        target=watch_ad_targets,
        args=(args.cdp_url, DEFAULT_AD_WORDS, stop_watcher),
        daemon=True,
    )
    watcher.start()
    threads: list[threading.Thread] = []

    for label, url in zip(labels, args.urls):
        thread = threading.Thread(
            target=guard_tab,
            args=(
                args.cdp_url,
                label,
                url,
                allowed_navigation_hosts,
                allowed_request_hosts,
                args.guard_seconds,
                result_queue,
            ),
            daemon=False,
        )
        thread.start()
        threads.append(thread)
        time.sleep(0.15)

    for _ in threads:
        result = result_queue.get(timeout=30)
        payload = result.__dict__
        if args.json:
            print(json.dumps(payload, ensure_ascii=False))
        else:
            print(f"{result.label}\t{result.status}\t{result.title}\t{result.final_url or result.url}")
            if result.error:
                print(f"  error: {result.error}")

    if not args.json:
        print(f"redirect_guard_seconds={args.guard_seconds}")
    for thread in threads:
        thread.join()
    stop_watcher.set()
    watcher.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
