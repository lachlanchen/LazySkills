#!/usr/bin/env python3
"""Search LibGen from inside a Chrome/LibGen page context.

Direct Python HTTP requests to ``libgen.pw/api/search/by-params`` can return
403 while the same request succeeds from an already loaded LibGen tab. This
tool attaches to Chrome DevTools Protocol, runs ``fetch()`` inside the page, and
prints candidate detail URLs without opening mirror/download pages.
"""

from __future__ import annotations

import argparse
import json
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

FORMAT_SCORE = {
    "pdf": 12,
    "epub": 9,
    "azw3": 4,
    "azw": 3,
    "mobi": 3,
    "djvu": 2,
}


@dataclass
class SearchResult:
    query: str
    status: int | None
    books: list[dict[str, Any]]
    error: str = ""


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("queries", nargs="*", help="Search query terms")
    parser.add_argument("--query", action="append", default=[], help="Repeatable search query")
    parser.add_argument("--cdp-url", default="http://127.0.0.1:9222", help="Chrome CDP HTTP endpoint")
    parser.add_argument("--collection", default="libgen", help="LibGen collection")
    parser.add_argument("--from-index", type=int, default=0, help="LibGen result offset")
    parser.add_argument("--limit", type=int, default=20, help="Maximum API results per query")
    parser.add_argument("--top", type=int, default=10, help="Maximum rows printed per query")
    parser.add_argument("--timeout-ms", type=int, default=12000, help="Browser fetch timeout per query")
    parser.add_argument("--language", help="Preferred language code, e.g. jpn, chi, eng")
    parser.add_argument("--title-term", action="append", default=[], help="Expected title substring for scoring")
    parser.add_argument("--author-term", action="append", default=[], help="Expected author substring for scoring")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a table")
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


def close_ad_targets(cdp_url: str) -> int:
    count = 0
    for tab in http_json(cdp_url, "/json"):
        text = f"{tab.get('title', '')} {tab.get('url', '')}".lower()
        if not any(word in text for word in DEFAULT_AD_WORDS):
            continue
        try:
            http_text(cdp_url, "/json/close/" + tab["id"])
            count += 1
        except Exception:
            continue
    return count


def is_libgen_url(url: str) -> bool:
    host = (urllib.parse.urlparse(url).hostname or "").lower()
    return host == "libgen.pw" or host.endswith(".libgen.pw")


def host_allowed(url: str) -> bool:
    parsed = urllib.parse.urlparse(url)
    host = (parsed.hostname or "").lower()
    if parsed.scheme in {"about", "data", "blob"}:
        return True
    return host == "libgen.pw" or host.endswith(".libgen.pw")


class CdpPage:
    def __init__(self, cdp_url: str) -> None:
        try:
            import websocket  # type: ignore
        except Exception as exc:  # pragma: no cover - environment failure
            raise SystemExit(f"websocket-client is required: {exc}") from exc

        self.websocket = websocket
        self.cdp_url = cdp_url.rstrip("/")
        self.counter = 0
        self.tab = self._find_or_create_libgen_tab()
        self.ws = websocket.create_connection(self.tab["webSocketDebuggerUrl"], timeout=10)
        self.ws.settimeout(2)
        self.call("Runtime.enable")
        self.call("Fetch.enable", {"patterns": [{"urlPattern": "*", "requestStage": "Request"}]})
        if not is_libgen_url(self.tab.get("url", "")):
            self.call("Page.enable")
            self.call("Page.navigate", {"url": "https://libgen.pw/"})
            self.wait_for_libgen()

    def _find_or_create_libgen_tab(self) -> dict[str, Any]:
        for tab in http_json(self.cdp_url, "/json"):
            if tab.get("type") == "page" and is_libgen_url(tab.get("url", "")):
                return tab
        return new_tab(self.cdp_url, "about:blank")

    def send(self, method: str, params: dict[str, Any] | None = None) -> int:
        self.counter += 1
        message_id = self.counter
        self.ws.send(json.dumps({"id": message_id, "method": method, "params": params or {}}))
        return message_id

    def handle_paused_request(self, message: dict[str, Any]) -> None:
        params = message["params"]
        request_id = params["requestId"]
        request_url = params["request"]["url"]
        if host_allowed(request_url):
            method = "Fetch.continueRequest"
            payload = {"requestId": request_id}
        else:
            method = "Fetch.failRequest"
            payload = {"requestId": request_id, "errorReason": "Aborted"}
        self.send(method, payload)

    def receive_one(self) -> dict[str, Any] | None:
        try:
            message = json.loads(self.ws.recv())
        except self.websocket.WebSocketTimeoutException:  # type: ignore[attr-defined]
            return None
        if message.get("method") == "Fetch.requestPaused":
            self.handle_paused_request(message)
        return message

    def call(self, method: str, params: dict[str, Any] | None = None, *, timeout: int = 30) -> dict[str, Any]:
        message_id = self.send(method, params)
        deadline = time.time() + timeout
        while time.time() < deadline:
            message = self.receive_one()
            if message and message.get("id") == message_id:
                return message
        raise TimeoutError(method)

    def wait_for_libgen(self) -> None:
        expression = "location.hostname === 'libgen.pw' || location.hostname.endsWith('.libgen.pw')"
        deadline = time.time() + 20
        while time.time() < deadline:
            value = self.evaluate(expression)
            if value is True:
                return
            time.sleep(0.3)
        raise TimeoutError("LibGen page did not load")

    def evaluate(self, expression: str, *, await_promise: bool = False, timeout: int = 30) -> Any:
        message = self.call(
            "Runtime.evaluate",
            {"expression": expression, "returnByValue": True, "awaitPromise": await_promise},
            timeout=timeout,
        )
        result = message.get("result", {}).get("result", {})
        if "exceptionDetails" in message.get("result", {}):
            return {"error": message["result"]["exceptionDetails"]}
        return result.get("value")

    def search(self, query: str, collection: str, from_index: int, limit: int, timeout_ms: int) -> SearchResult:
        expression = f"""
(async () => {{
  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), {int(timeout_ms)});
  try {{
    const params = new URLSearchParams({{
      query: {json.dumps(query, ensure_ascii=False)},
      collection: {json.dumps(collection)},
      from: String({int(from_index)})
    }});
    const response = await fetch('/api/search/by-params?' + params.toString(), {{
      headers: {{accept: 'application/json'}},
      signal: controller.signal
    }});
    const data = await response.json();
    clearTimeout(timer);
    const books = ((data.result && data.result.books) || []).slice(0, {int(limit)}).map((book) => ({{
      id: book.id,
      title: book.title,
      author: book.author,
      year: book.year,
      language: book.language,
      fileExtension: book.fileExtension,
      fileSize: book.fileSize,
      description: book.description
    }}));
    return {{status: response.status, books}};
  }} catch (error) {{
    clearTimeout(timer);
    return {{status: null, error: String(error), books: []}};
  }}
}})()
"""
        payload = self.evaluate(expression, await_promise=True, timeout=max(20, timeout_ms // 1000 + 10))
        if not isinstance(payload, dict):
            return SearchResult(query=query, status=None, books=[], error=f"unexpected payload: {payload!r}")
        return SearchResult(
            query=query,
            status=payload.get("status"),
            books=payload.get("books") or [],
            error=payload.get("error") or "",
        )

    def close(self) -> None:
        try:
            self.ws.close()
        except Exception:
            pass


def normalize(value: Any) -> str:
    if isinstance(value, list):
        value = " ".join(str(item) for item in value)
    return str(value or "").casefold()


def score_book(book: dict[str, Any], args: argparse.Namespace) -> int:
    title = str(book.get("title") or "")
    authors = normalize(book.get("author"))
    haystack = normalize([book.get("title"), book.get("author"), book.get("description")])
    score = 0

    if args.title_term:
        if any(term.casefold() in title.casefold() for term in args.title_term):
            score += 100
        elif any(term.casefold() in haystack for term in args.title_term):
            score += 70
        else:
            score -= 80

    if args.author_term:
        if any(term.casefold() in authors for term in args.author_term):
            score += 35
        else:
            score -= 10

    if args.language:
        language = normalize(book.get("language"))
        if language == args.language.casefold():
            score += 30
        elif not language:
            score += 2
        else:
            score -= 25

    score += FORMAT_SCORE.get(normalize(book.get("fileExtension")), 0)
    return score


def book_url(book: dict[str, Any]) -> str:
    return f"https://libgen.pw/book/{book.get('id')}"


def print_table(results: list[SearchResult], args: argparse.Namespace) -> None:
    for result in results:
        print(f"\n### {result.query}")
        if result.error:
            print(f"error: {result.error}")
            continue
        print(f"status: {result.status}")
        rows = []
        for book in result.books:
            row = dict(book)
            row["score"] = score_book(book, args)
            rows.append(row)
        rows.sort(key=lambda item: item["score"], reverse=True)
        for book in rows[: args.top]:
            authors = ", ".join(book.get("author") or [])
            print(
                f"{book['score']:>4} | {book_url(book)} | {book.get('title') or ''} | "
                f"{authors} | {book.get('year') or ''} | {book.get('language') or ''} | "
                f"{book.get('fileExtension') or ''} | {book.get('fileSize') or ''}"
            )


def main() -> int:
    args = parse_args()
    queries = args.query + args.queries
    if not queries:
        raise SystemExit("provide at least one query")

    closed = close_ad_targets(args.cdp_url)
    page = CdpPage(args.cdp_url)
    try:
        results = [page.search(query, args.collection, args.from_index, args.limit, args.timeout_ms) for query in queries]
    finally:
        page.close()

    if args.json:
        payload = {
            "closed_ad_targets": closed,
            "results": [
                {
                    "query": result.query,
                    "status": result.status,
                    "error": result.error,
                    "books": [
                        {**book, "score": score_book(book, args), "url": book_url(book)}
                        for book in result.books
                    ],
                }
                for result in results
            ],
        }
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"closed_ad_targets={closed}")
        print_table(results, args)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
