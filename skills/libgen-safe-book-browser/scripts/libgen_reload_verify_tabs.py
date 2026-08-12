#!/usr/bin/env python3
"""Reload existing LibGen tabs through Chrome CDP and verify useful page content."""

from __future__ import annotations

import argparse
import json
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any

from libgen_no_redirect_open import DEFAULT_NAVIGATION_HOSTS, build_init_script, handle_paused_request, host_allowed


@dataclass(frozen=True)
class ReloadResult:
    tab_id: str
    status: str
    title: str
    url: str
    ready_state: str = ""
    text_length: int = 0
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222", help="Chrome CDP HTTP endpoint")
    parser.add_argument("--url", action="append", default=[], help="Reload tabs matching this exact URL")
    parser.add_argument("--contains", action="append", default=[], help="Reload tabs whose URL contains this text")
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
        help="Allowed static subresource host",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Seconds to wait for each tab")
    parser.add_argument("--verify-only", action="store_true", help="Inspect current DOM state without reloading")
    parser.add_argument("--json", action="store_true", help="Emit JSON lines")
    return parser.parse_args()


def http_json(cdp_url: str, path: str) -> Any:
    with urllib.request.urlopen(cdp_url.rstrip("/") + path, timeout=10) as response:
        return json.loads(response.read().decode("utf-8"))


def cdp_send(ws: Any, counter: list[int], method: str, params: dict[str, Any] | None = None) -> int:
    counter[0] += 1
    message_id = counter[0]
    ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
    return message_id


def wait_response(ws: Any, counter: list[int], message_id: int, *, allowed_hosts: set[str], timeout: float) -> dict[str, Any]:
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
    raise TimeoutError(f"CDP response timed out for message {message_id}")


def cdp_call(
    ws: Any,
    counter: list[int],
    method: str,
    params: dict[str, Any] | None = None,
    *,
    allowed_hosts: set[str],
    timeout: float = 10.0,
) -> dict[str, Any]:
    return wait_response(ws, counter, cdp_send(ws, counter, method, params), allowed_hosts=allowed_hosts, timeout=timeout)


def tab_matches(tab: dict[str, Any], urls: list[str], contains: list[str]) -> bool:
    current = tab.get("url", "")
    if urls and current in urls:
        return True
    if contains and any(part in current for part in contains):
        return True
    return not urls and not contains and (
        "libgen.li/edition.php" in current
        or re.match(r"https?://(?:[^/]+\.)?libgen\.pw/(?:book|links)/\d+", current) is not None
    )


def evaluate_state(ws: Any, counter: list[int], *, allowed_hosts: set[str], timeout: float) -> dict[str, Any]:
    expression = r"""
(() => {
  const text = document.body ? document.body.innerText : "";
  const resources = performance.getEntriesByType("resource").map((entry) => entry.name);
  const hasBootstrapCss = !!document.querySelector('link[href*="bootstrap"][href$=".css"], link[href*="bootstrap.min.css"]');
  const hasJquery = !!document.querySelector('script[src*="jquery"]');
  const hasBootstrapJs = !!document.querySelector('script[src*="bootstrap"][src$=".js"], script[src*="bootstrap.min.js"], script[src*="bootstrap.bundle.min.js"]');
  const bootstrapCssLoaded = resources.some((url) => url.includes("bootstrap") && url.includes(".css"));
  const jqueryLoaded = resources.some((url) => url.includes("jquery"));
  const bootstrapJsLoaded = resources.some((url) => url.includes("bootstrap") && url.includes(".js"));
  const supportedHost =
    location.hostname.endsWith("libgen.li") ||
    location.hostname.endsWith("libgen.pw");
  const needsClassicAssets = location.hostname.endsWith("libgen.li");
  const classicAssetsReady =
    (!hasBootstrapCss || bootstrapCssLoaded) &&
    (!hasJquery || jqueryLoaded) &&
    (!hasBootstrapJs || bootstrapJsLoaded);
  const detailRecord =
    /^\/book\/\d+\/?$/.test(location.pathname) &&
    /\b(?:pdf|epub|mobi|azw3?|djvu)\b/i.test(text);
  const linksRecord =
    /^\/links\/\d+\/?$/.test(location.pathname) &&
    /\bGet\b/i.test(text) &&
    /Libgen/i.test(text);
  const conciseRecord =
    location.hostname.endsWith("libgen.pw") &&
    (detailRecord || linksRecord) &&
    document.title &&
    text.includes(document.title.trim());
  const enoughText = text.length > 500 || (conciseRecord && text.length > 120);
  const useful =
    supportedHost &&
    document.readyState === "complete" &&
    document.title &&
    enoughText &&
    (!needsClassicAssets || classicAssetsReady) &&
    !/bad internet|checking your browser|loading/i.test(text.slice(0, 1200));
  return {
    title: document.title,
    url: location.href,
    readyState: document.readyState,
    textLength: text.length,
    bootstrapCssLinked: hasBootstrapCss,
    bootstrapCssLoaded,
    jqueryLinked: hasJquery,
    jqueryLoaded,
    bootstrapJsLinked: hasBootstrapJs,
    bootstrapJsLoaded,
    useful
  };
})()
"""
    response = cdp_call(
        ws,
        counter,
        "Runtime.evaluate",
        {"expression": expression, "returnByValue": True},
        allowed_hosts=allowed_hosts,
        timeout=timeout,
    )
    return response.get("result", {}).get("result", {}).get("value", {}) or {}


def verify_tab(tab: dict[str, Any], *, allowed_hosts: set[str], timeout: float) -> ReloadResult:
    try:
        import websocket  # type: ignore
    except Exception as exc:
        return ReloadResult(tab.get("id", ""), "error", tab.get("title", ""), tab.get("url", ""), error=str(exc))

    ws = None
    script_identifier: str | None = None
    try:
        ws = websocket.create_connection(tab["webSocketDebuggerUrl"], timeout=10)
        ws.settimeout(1)
        counter = [0]
        cdp_call(ws, counter, "Runtime.enable", allowed_hosts=allowed_hosts)
        state = evaluate_state(ws, counter, allowed_hosts=allowed_hosts, timeout=timeout)
        return ReloadResult(
            tab.get("id", ""),
            "loaded" if state.get("useful") else "not_verified",
            str(state.get("title", tab.get("title", ""))),
            str(state.get("url", tab.get("url", ""))),
            ready_state=str(state.get("readyState", "")),
            text_length=int(state.get("textLength") or 0),
            error="" if state.get("useful") else "current DOM did not pass the useful-page checks",
        )
    except Exception as exc:
        return ReloadResult(tab.get("id", ""), "error", tab.get("title", ""), tab.get("url", ""), error=f"{type(exc).__name__}: {exc}")
    finally:
        try:
            if ws is not None:
                ws.close()
        except Exception:
            pass


def reload_tab(
    tab: dict[str, Any],
    *,
    allowed_navigation_hosts: set[str],
    allowed_request_hosts: set[str],
    timeout: float,
) -> ReloadResult:
    try:
        import websocket  # type: ignore
    except Exception as exc:
        return ReloadResult(tab.get("id", ""), "error", tab.get("title", ""), tab.get("url", ""), error=str(exc))

    ws = None
    try:
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
        cdp_call(ws, counter, "Runtime.enable", allowed_hosts=allowed_request_hosts)
        init_script = build_init_script(allowed_navigation_hosts)
        script_response = cdp_call(
            ws,
            counter,
            "Page.addScriptToEvaluateOnNewDocument",
            {"source": init_script},
            allowed_hosts=allowed_request_hosts,
        )
        script_identifier = script_response.get("result", {}).get("identifier")
        if not host_allowed(tab.get("url", ""), allowed_navigation_hosts):
            return ReloadResult(tab.get("id", ""), "skipped", tab.get("title", ""), tab.get("url", ""), error="host not allowed")
        cdp_call(ws, counter, "Page.reload", {"ignoreCache": True}, allowed_hosts=allowed_request_hosts)

        deadline = time.time() + timeout
        last_state: dict[str, Any] = {}
        while time.time() < deadline:
            try:
                last_state = evaluate_state(ws, counter, allowed_hosts=allowed_request_hosts, timeout=2)
                if last_state.get("useful"):
                    return ReloadResult(
                        tab.get("id", ""),
                        "loaded",
                        str(last_state.get("title", "")),
                        str(last_state.get("url", "")),
                        ready_state=str(last_state.get("readyState", "")),
                        text_length=int(last_state.get("textLength") or 0),
                    )
            except Exception:
                pass
            time.sleep(0.5)
        return ReloadResult(
            tab.get("id", ""),
            "not_verified",
            str(last_state.get("title", tab.get("title", ""))),
            str(last_state.get("url", tab.get("url", ""))),
            ready_state=str(last_state.get("readyState", "")),
            text_length=int(last_state.get("textLength") or 0),
            error="timed out waiting for useful loaded body",
        )
    except Exception as exc:
        return ReloadResult(tab.get("id", ""), "error", tab.get("title", ""), tab.get("url", ""), error=f"{type(exc).__name__}: {exc}")
    finally:
        if ws is not None:
            if script_identifier:
                try:
                    cdp_call(
                        ws,
                        counter,
                        "Page.removeScriptToEvaluateOnNewDocument",
                        {"identifier": script_identifier},
                        allowed_hosts=allowed_request_hosts,
                    )
                except Exception:
                    pass
            try:
                ws.close()
            except Exception:
                pass


def main() -> int:
    args = parse_args()
    allowed_navigation_hosts = {host.lower() for host in args.allowed_host}
    allowed_request_hosts = allowed_navigation_hosts | {host.lower() for host in args.allowed_resource_host}
    tabs = [tab for tab in http_json(args.cdp_url, "/json") if tab.get("type") == "page" and tab_matches(tab, args.url, args.contains)]
    if args.verify_only:
        results = [verify_tab(tab, allowed_hosts=allowed_request_hosts, timeout=args.timeout) for tab in tabs]
    else:
        results = [
            reload_tab(
                tab,
                allowed_navigation_hosts=allowed_navigation_hosts,
                allowed_request_hosts=allowed_request_hosts,
                timeout=args.timeout,
            )
            for tab in tabs
        ]
    for result in results:
        if args.json:
            print(json.dumps(result.__dict__, ensure_ascii=False))
        else:
            print(f"{result.status}\t{result.text_length}\t{result.title}\t{result.url}")
            if result.error:
                print(f"  error: {result.error}")
    return 0 if all(result.status == "loaded" for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
