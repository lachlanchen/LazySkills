#!/usr/bin/env python3
"""Keep a Chrome/CDP LibGen redirect guard running for existing tabs.

`libgen_no_redirect_open.py` protects tabs that it opens. This companion tool
is meant for normal browsing sessions: it watches an existing Chrome CDP
endpoint, attaches to allowed tabs, and blocks off-list navigation without
closing tabs. Destructive ad-target cleanup is available only as an opt-in.
"""

from __future__ import annotations

import argparse
import json
import queue
import threading
import time
import urllib.parse
from dataclasses import dataclass
from typing import Any

from libgen_no_redirect_open import (
    DEFAULT_AD_WORDS,
    DEFAULT_NAVIGATION_HOSTS,
    build_init_script,
    close_ad_targets,
    handle_paused_request,
    host_allowed,
    http_json,
)


@dataclass
class GuardedTarget:
    target_id: str
    title: str
    url: str
    last_allowed_url: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222", help="Chrome CDP HTTP endpoint")
    parser.add_argument(
        "--allowed-host",
        action="append",
        default=list(DEFAULT_NAVIGATION_HOSTS),
        help="Allowed top-level host",
    )
    parser.add_argument(
        "--allowed-resource-host",
        action="append",
        default=["cdn.jsdelivr.net", "code.jquery.com"],
        help="Allowed static resource host; never allowed for top-level navigation",
    )
    parser.add_argument("--scan-interval", type=float, default=1.0, help="Seconds between tab scans")
    parser.add_argument("--close-ads-interval", type=float, default=0.5, help="Seconds between ad-tab cleanup passes")
    parser.add_argument(
        "--close-ad-targets",
        action="store_true",
        help="Explicitly close known ad tabs; disabled by default",
    )
    parser.add_argument("--duration", type=int, default=0, help="Seconds to run; 0 means until interrupted")
    parser.add_argument("--json", action="store_true", help="Emit JSON events")
    return parser.parse_args()


def cdp_send(ws: Any, counter: list[int], method: str, params: dict[str, Any] | None = None) -> int:
    counter[0] += 1
    ws.send(json.dumps({"id": counter[0], "method": method, "params": params or {}}))
    return counter[0]


def wait_for_response(
    ws: Any,
    counter: list[int],
    message_id: int,
    *,
    allowed_hosts: set[str],
    timeout: float = 5.0,
) -> dict[str, Any]:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            message = json.loads(ws.recv())
        except Exception:
            continue
        if message.get("id") == message_id:
            return message
        if message.get("method") == "Fetch.requestPaused":
            handle_paused_request(ws, counter, message, allowed_hosts=allowed_hosts)
    return {}


def is_libgen_target(tab: dict[str, Any], allowed_hosts: set[str]) -> bool:
    if tab.get("type") != "page":
        return False
    host = (urllib.parse.urlparse(tab.get("url", "")).hostname or "").lower()
    return host in allowed_hosts or any(host.endswith("." + allowed) for allowed in allowed_hosts)


def allowed_host_sets(args: argparse.Namespace) -> tuple[set[str], set[str]]:
    navigation = {host.lower() for host in args.allowed_host}
    requests = navigation | {host.lower() for host in args.allowed_resource_host}
    return navigation, requests


def log_event(json_mode: bool, event: str, **payload: Any) -> None:
    if json_mode:
        print(json.dumps({"event": event, **payload}, ensure_ascii=False), flush=True)
    else:
        details = " ".join(f"{key}={value}" for key, value in payload.items() if value not in {None, ""})
        print(f"{event} {details}".rstrip(), flush=True)


def guard_target(
    target: GuardedTarget,
    allowed_navigation_hosts: set[str],
    allowed_request_hosts: set[str],
    stop_event: threading.Event,
    result_queue: queue.Queue[tuple[str, str]],
    json_mode: bool,
) -> None:
    try:
        import websocket  # type: ignore
    except Exception as exc:
        result_queue.put((target.target_id, f"websocket-client missing: {exc}"))
        return

    ws = None
    counter: list[int] | None = None
    script_identifier: str | None = None
    try:
        ws = websocket.create_connection(target.url, timeout=10)
        ws.settimeout(1)
        counter = [0]
        response_id = cdp_send(
            ws,
            counter,
            "Fetch.enable",
            {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]},
        )
        wait_for_response(ws, counter, response_id, allowed_hosts=allowed_request_hosts)
        wait_for_response(ws, counter, cdp_send(ws, counter, "Page.enable"), allowed_hosts=allowed_request_hosts)
        wait_for_response(ws, counter, cdp_send(ws, counter, "Runtime.enable"), allowed_hosts=allowed_request_hosts)
        init_script = build_init_script(allowed_navigation_hosts)
        script_response = wait_for_response(
            ws,
            counter,
            cdp_send(ws, counter, "Page.addScriptToEvaluateOnNewDocument", {"source": init_script}),
            allowed_hosts=allowed_request_hosts,
        )
        script_identifier = script_response.get("result", {}).get("identifier")
        wait_for_response(
            ws,
            counter,
            cdp_send(ws, counter, "Runtime.evaluate", {"expression": init_script}),
            allowed_hosts=allowed_request_hosts,
        )
        log_event(json_mode, "attached", target_id=target.target_id, title=target.title, url=target.last_allowed_url)

        last_allowed_url = target.last_allowed_url
        while not stop_event.is_set():
            try:
                message = json.loads(ws.recv())
            except websocket.WebSocketTimeoutException:  # type: ignore[attr-defined]
                continue
            except Exception:
                break

            method = message.get("method")
            if method == "Fetch.requestPaused":
                handle_paused_request(ws, counter, message, allowed_hosts=allowed_request_hosts)
            elif method == "Page.frameNavigated":
                frame = message.get("params", {}).get("frame", {})
                if frame.get("parentId"):
                    continue
                current_url = frame.get("url", "")
                if host_allowed(current_url, allowed_navigation_hosts):
                    last_allowed_url = current_url
                    continue
                log_event(json_mode, "blocked_navigation", target_id=target.target_id, url=current_url)
                cdp_send(ws, counter, "Page.navigate", {"url": last_allowed_url})
    finally:
        if ws is not None and counter is not None:
            if script_identifier:
                try:
                    response_id = cdp_send(
                        ws,
                        counter,
                        "Page.removeScriptToEvaluateOnNewDocument",
                        {"identifier": script_identifier},
                    )
                    wait_for_response(
                        ws,
                        counter,
                        response_id,
                        allowed_hosts=allowed_request_hosts,
                        timeout=2.0,
                    )
                except Exception:
                    pass
            try:
                response_id = cdp_send(ws, counter, "Fetch.disable")
                wait_for_response(
                    ws,
                    counter,
                    response_id,
                    allowed_hosts=allowed_request_hosts,
                    timeout=2.0,
                )
            except Exception:
                pass
        try:
            if ws is not None:
                ws.close()
        except Exception:
            pass
        result_queue.put((target.target_id, "detached"))


def main() -> int:
    args = parse_args()
    allowed_navigation_hosts, allowed_request_hosts = allowed_host_sets(args)
    stop_event = threading.Event()
    result_queue: queue.Queue[tuple[str, str]] = queue.Queue()
    attached: dict[str, threading.Thread] = {}

    deadline = time.time() + args.duration if args.duration > 0 else None
    last_close = 0.0
    try:
        while deadline is None or time.time() < deadline:
            now = time.time()
            if args.close_ad_targets and now - last_close >= args.close_ads_interval:
                closed = close_ad_targets(args.cdp_url, DEFAULT_AD_WORDS)
                if closed:
                    log_event(args.json, "closed_ad_targets", count=len(closed))
                last_close = now

            for tab in http_json(args.cdp_url, "/json"):
                if tab.get("id") in attached or not is_libgen_target(tab, allowed_navigation_hosts):
                    continue
                target = GuardedTarget(
                    target_id=tab["id"],
                    title=tab.get("title", ""),
                    url=tab["webSocketDebuggerUrl"],
                    last_allowed_url=tab.get("url", ""),
                )
                thread = threading.Thread(
                    target=guard_target,
                    args=(
                        target,
                        allowed_navigation_hosts,
                        allowed_request_hosts,
                        stop_event,
                        result_queue,
                        args.json,
                    ),
                    daemon=True,
                )
                attached[target.target_id] = thread
                thread.start()

            while True:
                try:
                    target_id, reason = result_queue.get_nowait()
                except queue.Empty:
                    break
                attached.pop(target_id, None)
                log_event(args.json, "detached", target_id=target_id, reason=reason)

            time.sleep(args.scan_interval)
    except KeyboardInterrupt:
        log_event(args.json, "stopping")
    finally:
        stop_event.set()
        for thread in list(attached.values()):
            thread.join(timeout=2)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
