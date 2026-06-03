#!/usr/bin/env python3
"""Small Chrome DevTools helper for Xiaoyunque browser automation."""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.request
from pathlib import Path

import websocket


DEFAULT_CDP = "http://127.0.0.1:9222"


class Cdp:
    def __init__(self, page_id: str, cdp_url: str = DEFAULT_CDP) -> None:
        page = json.load(urllib.request.urlopen(f"{cdp_url}/json/list"))
        target = next((p for p in page if p.get("id") == page_id), None)
        if not target:
            raise SystemExit(f"Page id not found: {page_id}")
        self.ws = websocket.create_connection(target["webSocketDebuggerUrl"], timeout=10)
        self.next_id = 0

    def call(self, method: str, params: dict | None = None) -> dict:
        self.next_id += 1
        msg_id = self.next_id
        self.ws.send(json.dumps({"id": msg_id, "method": method, "params": params or {}}))
        while True:
            raw = self.ws.recv()
            msg = json.loads(raw)
            if msg.get("id") == msg_id:
                if "error" in msg:
                    raise RuntimeError(json.dumps(msg["error"], ensure_ascii=False))
                return msg.get("result", {})

    def eval(self, expression: str, *, await_promise: bool = False) -> object:
        result = self.call(
            "Runtime.evaluate",
            {
                "expression": expression,
                "returnByValue": True,
                "awaitPromise": await_promise,
            },
        )
        remote = result.get("result", {})
        if "value" in remote:
            return remote["value"]
        return remote

    def click(self, x: float, y: float) -> None:
        for event_type in ("mouseMoved", "mousePressed", "mouseReleased"):
            params = {
                "type": event_type,
                "x": x,
                "y": y,
                "button": "left",
                "clickCount": 1,
            }
            if event_type == "mousePressed":
                params["buttons"] = 1
            self.call("Input.dispatchMouseEvent", params)

    def screenshot(self, output: Path) -> None:
        data = self.call("Page.captureScreenshot", {"format": "png", "fromSurface": True})["data"]
        output.write_bytes(base64.b64decode(data))

    def navigate(self, url: str) -> None:
        self.call("Page.enable")
        self.call("Page.navigate", {"url": url})

    def bring_to_front(self) -> None:
        self.call("Page.bringToFront")

    def insert_text(self, text: str) -> None:
        self.call("Input.insertText", {"text": text})

    def key(self, event_type: str, key: str, code: str, vk: int, modifiers: int = 0) -> None:
        self.call(
            "Input.dispatchKeyEvent",
            {
                "type": event_type,
                "key": key,
                "code": code,
                "windowsVirtualKeyCode": vk,
                "nativeVirtualKeyCode": vk,
                "modifiers": modifiers,
            },
        )

    def set_file_input_files(self, files: list[Path], selector: str = "input[type=file]", index: int = -1) -> dict:
        root = self.call("DOM.getDocument", {"depth": -1, "pierce": True})["root"]["nodeId"]
        nodes = self.call("DOM.querySelectorAll", {"nodeId": root, "selector": selector})["nodeIds"]
        if not nodes:
            return {"ok": False, "error": f"no nodes for selector: {selector}"}
        node_infos = []
        for position, node in enumerate(nodes):
            described = self.call("DOM.describeNode", {"nodeId": node}).get("node", {})
            attrs_raw = described.get("attributes") or []
            attrs = {attrs_raw[i]: attrs_raw[i + 1] for i in range(0, len(attrs_raw), 2)}
            node_infos.append(
                {
                    "position": position,
                    "nodeId": node,
                    "accept": attrs.get("accept", ""),
                    "multiple": "multiple" in attrs,
                    "class": attrs.get("class", ""),
                }
            )

        def infer_file_kind(paths: list[Path]) -> str:
            image_exts = {".png", ".jpg", ".jpeg", ".webp", ".gif", ".bmp", ".tif", ".tiff"}
            video_exts = {".mp4", ".mov", ".webm", ".mkv", ".avi", ".m4v"}
            suffixes = {path.suffix.lower() for path in paths}
            if suffixes and suffixes <= image_exts:
                return "image"
            if suffixes and suffixes <= video_exts:
                return "video"
            return "generic"

        def smart_score(info: dict, kind: str) -> int:
            accept = str(info.get("accept") or "").lower()
            score = 0
            if ".json" in accept and "image" not in accept and "video" not in accept:
                score -= 1000
            if info.get("multiple"):
                score += 25
            if kind == "image":
                if "image" in accept:
                    score += 200
                if "video" in accept:
                    score += 10
            elif kind == "video":
                if "video" in accept:
                    score += 200
                if "image" in accept:
                    score += 10
            elif accept and ".json" not in accept:
                score += 50
            # Earlier upload inputs are usually the composer/material uploaders;
            # later inputs on Xiaoyunque include JSON preset importers.
            score -= int(info.get("position") or 0)
            return score

        chosen_info = None
        if selector == "input[type=file]" and index == -1:
            kind = infer_file_kind(files)
            chosen_info = max(node_infos, key=lambda item: smart_score(item, kind))
        else:
            chosen_info = node_infos[index]
        node_id = int(chosen_info["nodeId"])
        abs_files = [str(path.resolve()) for path in files]
        self.call("DOM.setFileInputFiles", {"nodeId": node_id, "files": abs_files})
        return {
            "ok": True,
            "selector": selector,
            "index": index,
            "chosenPosition": chosen_info.get("position"),
            "chosenAccept": chosen_info.get("accept"),
            "nodeCount": len(nodes),
            "files": abs_files,
        }


ATTACHMENT_VERIFY_JS = r"""
(() => {
  const text = el => (el && (el.innerText || el.textContent || '')).trim();
  const visible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.display !== 'none' && s.visibility !== 'hidden';
  };
  const rect = el => {
    const r = el.getBoundingClientRect();
    return {x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)};
  };
  const lowerHalf = el => {
    const r = el.getBoundingClientRect();
    return r.bottom > window.innerHeight * 0.35 && r.top < window.innerHeight + 20;
  };
  const editable = [...document.querySelectorAll('textarea,input,[contenteditable=true],[contenteditable=plaintext-only]')]
    .filter(visible)
    .sort((a, b) => b.getBoundingClientRect().bottom - a.getBoundingClientRect().bottom)[0] || null;
  const composerRoot = editable
    ? (editable.closest('[class*="prompt"],[class*="composer"],[class*="input"],[class*="editor"],[class*="content"]') || document.body)
    : document.body;
  const selectors = [
    '[class*="uploadPreview"]',
    '[class*="attachmentItem"]',
    '[class*="assetItem"]',
    '[class*="uploadItem"]',
    '[class*="imageChip"]',
    '[class*="thumbnail"]',
    '[class*="previewItem"]',
    '[class*="reference"] img',
    '[class*="upload"] img',
    '[class*="material"] img',
    '[class*="file"] img'
  ];
  const seen = new Set();
  const candidates = [];
  const add = (el, selector) => {
    if (!el || seen.has(el) || !visible(el) || !lowerHalf(el)) return;
    seen.add(el);
    const img = el.tagName === 'IMG' ? el : el.querySelector('img');
    candidates.push({
      selector,
      tag: el.tagName,
      cls: String(el.className || '').slice(0, 100),
      text: text(el).replace(/\s+/g, ' ').slice(0, 80),
      rect: rect(el),
      imgSrc: img ? String(img.currentSrc || img.src || '').slice(0, 100) : ''
    });
  };
  selectors.forEach(selector => {
    try {
      [...document.querySelectorAll(selector)].forEach(el => add(el, selector));
    } catch (_) {}
  });
  const imageEvidence = [...document.querySelectorAll('img')]
    .filter(el => visible(el) && lowerHalf(el))
    .filter(el => {
      const r = el.getBoundingClientRect();
      const src = String(el.currentSrc || el.src || '');
      return r.width >= 24 && r.height >= 24 && !src.startsWith('data:image/svg+xml');
    })
    .map(el => ({
      cls: String(el.className || '').slice(0, 80),
      alt: String(el.alt || '').slice(0, 80),
      rect: rect(el),
      src: String(el.currentSrc || el.src || '').slice(0, 120)
    }));
  const fileNameEvidence = [...document.querySelectorAll(
    '[class*="materialCard"],[class*="materialTitle"],[class*="materialMeta"],[class*="assetCount"],img[alt]'
  )]
    .filter(visible)
    .map(el => {
      const img = el.tagName === 'IMG' ? el : el.querySelector('img');
      return {
        tag: el.tagName,
        cls: String(el.className || '').slice(0, 80),
        text: text(el).replace(/\s+/g, ' ').slice(0, 160),
        alt: img ? String(img.alt || '').slice(0, 160) : '',
        rect: rect(el)
      };
    })
    .filter(item => item.text || item.alt);
  return {
    href: location.href,
    title: document.title,
    viewport: {w: window.innerWidth, h: window.innerHeight},
    composerRoot: {
      tag: composerRoot.tagName,
      cls: String(composerRoot.className || '').slice(0, 100),
      rect: rect(composerRoot)
    },
    visibleAttachmentCount: candidates.length,
    visibleImageEvidenceCount: imageEvidence.length,
    fileNameEvidence,
    candidates: candidates.slice(0, 20),
    imageEvidence: imageEvidence.slice(0, 20)
  };
})()
"""


def list_pages(args: argparse.Namespace) -> None:
    pages = json.load(urllib.request.urlopen(f"{args.cdp_url}/json/list"))
    for page in pages:
        if page.get("type") == "page":
            print(f"{page.get('id')}\t{page.get('title')}\t{page.get('url')}")


def cmd_eval(args: argparse.Namespace) -> None:
    cdp = Cdp(args.page_id, args.cdp_url)
    result = cdp.eval(args.javascript, await_promise=args.await_promise)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_visible(args: argparse.Namespace) -> None:
    js = r"""
(() => {
  const items = [];
  const nodes = [...document.querySelectorAll('button,[role=button],input,textarea,[contenteditable=true],.uploadMenuItem-GDs2iL,.historyItem-EesJ6i')];
  for (const el of nodes) {
    const r = el.getBoundingClientRect();
    const style = getComputedStyle(el);
    if (r.width < 2 || r.height < 2 || style.visibility === 'hidden' || style.display === 'none') continue;
    items.push({
      tag: el.tagName,
      cls: el.className && String(el.className).slice(0, 120),
      text: (el.innerText || el.getAttribute('title') || el.getAttribute('aria-label') || '').trim().slice(0, 160),
      x: Math.round(r.x), y: Math.round(r.y), w: Math.round(r.width), h: Math.round(r.height)
    });
  }
  return items;
})()
"""
    cdp = Cdp(args.page_id, args.cdp_url)
    print(json.dumps(cdp.eval(js), ensure_ascii=False, indent=2))


def cmd_click(args: argparse.Namespace) -> None:
    cdp = Cdp(args.page_id, args.cdp_url)
    cdp.click(args.x, args.y)


def cmd_click_text(args: argparse.Namespace) -> None:
    contains = json.dumps(args.text, ensure_ascii=False)
    js = f"""
(() => {{
  const needle = {contains};
  const nodes = [...document.querySelectorAll('button,[role=button],.uploadMenuItem-GDs2iL,.historyItem-EesJ6i,div,span')];
  const visible = (el) => {{
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.display !== 'none' && s.visibility !== 'hidden';
  }};
  const candidates = nodes
    .filter(n => visible(n) && ((n.innerText || '').trim().includes(needle) || (n.getAttribute('title') || '').includes(needle)))
    .map(n => {{
      const text = ((n.innerText || n.getAttribute('title') || '').trim()).replace(/\\s+/g, ' ');
      const r = n.getBoundingClientRect();
      const area = r.width * r.height;
      const isButton = n.tagName === 'BUTTON' || n.getAttribute('role') === 'button';
      const cls = String(n.className || '');
      const inDropdown = !!n.closest('[class*="dropdownPanel"],[class*="lv-trigger"],[class*="dropdown"]');
      const dropdownItem = /dropdownItem|uploadMenuItem/.test(cls) || !!n.closest('[class*="dropdownItem"],[class*="uploadMenuItem"]');
      const historyItem = /history|History/.test(cls) || !!n.closest('[class*="history"],[class*="History"]');
      const editorItem = /editor|ProseMirror|content/.test(cls) || !!n.closest('.ProseMirror,[class*="editor"]');
      const exact = text === needle;
      const starts = text.startsWith(needle);
      return {{
        node:n,
        text,
        r,
        area,
        score:
          (dropdownItem ? 30000 : 0) +
          (inDropdown ? 12000 : 0) +
          (isButton ? 10000 : 0) +
          (exact ? 5000 : 0) +
          (starts ? 1000 : 0) -
          (historyItem ? 8000 : 0) -
          (editorItem ? 5000 : 0) -
          Math.min(area, 2000000) / 1000
      }};
    }})
    .sort((a, b) => b.score - a.score);
  const el = candidates[0] && candidates[0].node;
  if (!el) return {{ok:false, error:'not found'}};
  const r = el.getBoundingClientRect();
  el.click();
  return {{ok:true, text:(el.innerText || el.getAttribute('title') || '').trim(), x:r.x+r.width/2, y:r.y+r.height/2, cls:String(el.className).slice(0,120), candidateCount:candidates.length}};
}})()
"""
    cdp = Cdp(args.page_id, args.cdp_url)
    print(json.dumps(cdp.eval(js), ensure_ascii=False, indent=2))


def cmd_navigate(args: argparse.Namespace) -> None:
    cdp = Cdp(args.page_id, args.cdp_url)
    cdp.navigate(args.url)


def cmd_screenshot(args: argparse.Namespace) -> None:
    cdp = Cdp(args.page_id, args.cdp_url)
    cdp.screenshot(Path(args.output))
    print(args.output)


def cmd_bring_to_front(args: argparse.Namespace) -> None:
    cdp = Cdp(args.page_id, args.cdp_url)
    cdp.bring_to_front()
    print(json.dumps({"ok": True, "pageId": args.page_id}, ensure_ascii=False, indent=2))


def cmd_set_file_input(args: argparse.Namespace) -> None:
    files = [Path(path) for path in args.files]
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise SystemExit(f"Missing files: {', '.join(missing)}")
    cdp = Cdp(args.page_id, args.cdp_url)
    print(json.dumps(cdp.set_file_input_files(files, args.selector, args.index), ensure_ascii=False, indent=2))


def cmd_verify_attachments(args: argparse.Namespace) -> None:
    cdp = Cdp(args.page_id, args.cdp_url)
    result = cdp.eval(ATTACHMENT_VERIFY_JS)
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_upload_images_verify(args: argparse.Namespace) -> None:
    files = [Path(path) for path in args.files]
    missing = [str(path) for path in files if not path.exists()]
    if missing:
        raise SystemExit(f"Missing files: {', '.join(missing)}")
    output = Path(args.screenshot)
    output.parent.mkdir(parents=True, exist_ok=True)
    cdp = Cdp(args.page_id, args.cdp_url)
    upload = cdp.set_file_input_files(files, args.selector, args.index)
    last_verify: object = {}
    deadline = time.time() + args.timeout
    while time.time() < deadline:
        time.sleep(args.interval)
        last_verify = cdp.eval(ATTACHMENT_VERIFY_JS)
        if isinstance(last_verify, dict):
            visible_count = max(
                int(last_verify.get("visibleAttachmentCount") or 0),
                int(last_verify.get("visibleImageEvidenceCount") or 0),
            )
            evidence_blob = json.dumps(last_verify, ensure_ascii=False)
            matched_names = [path.name for path in files if path.name in evidence_blob]
            if visible_count >= len(files) or len(matched_names) == len(files):
                break
    cdp.screenshot(output)
    visible_count = 0
    if isinstance(last_verify, dict):
        visible_count = max(
            int(last_verify.get("visibleAttachmentCount") or 0),
            int(last_verify.get("visibleImageEvidenceCount") or 0),
        )
    evidence_blob = json.dumps(last_verify, ensure_ascii=False)
    matched_names = [path.name for path in files if path.name in evidence_blob]
    result = {
        "ok": bool(upload.get("ok")) and (visible_count >= len(files) or len(matched_names) == len(files)),
        "expectedFiles": len(files),
        "matchedFileNames": matched_names,
        "visibleEvidenceCount": visible_count,
        "upload": upload,
        "verify": last_verify,
        "screenshot": str(output),
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))


def cmd_set_prompt(args: argparse.Namespace) -> None:
    content = Path(args.markdown_file).read_text(encoding="utf-8")
    # Tiptap accepts HTML. Preserve line breaks as paragraphs.
    html_parts = []
    for block in content.split("\n\n"):
        escaped = (
            block.replace("&", "&amp;")
            .replace("<", "&lt;")
            .replace(">", "&gt;")
            .replace("\n", "<br>")
        )
        if escaped.strip():
            html_parts.append(f"<p>{escaped}</p>")
    html = "".join(html_parts)
    js = f"""
(() => {{
  const html = {json.dumps(html, ensure_ascii=False)};
  const el = document.querySelector('.editor-HT1dqv') || document.querySelector('.ProseMirror') || document.querySelector('[contenteditable=true]');
  if (!el) return {{ok:false, error:'editor not found'}};
  if (el.editor && el.editor.commands) {{
    el.editor.commands.setContent(html, true);
    el.editor.commands.focus('end');
    return {{ok:true, method:'tiptap', length:(el.innerText || '').length}};
  }}
  el.focus();
  document.execCommand('selectAll', false, null);
  document.execCommand('insertText', false, {json.dumps(content, ensure_ascii=False)});
  return {{ok:true, method:'execCommand', length:(el.innerText || '').length}};
}})()
"""
    cdp = Cdp(args.page_id, args.cdp_url)
    print(json.dumps(cdp.eval(js), ensure_ascii=False, indent=2))


def cmd_type_prompt(args: argparse.Namespace) -> None:
    content = Path(args.markdown_file).read_text(encoding="utf-8")
    js = r"""
(() => {
  const visible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.display !== 'none' && s.visibility !== 'hidden';
  };
  const candidates = [...document.querySelectorAll('.editor-HT1dqv,.ProseMirror,[contenteditable=true],[contenteditable=plaintext-only],textarea,input')]
    .filter(visible)
    .sort((a,b) => b.getBoundingClientRect().bottom - a.getBoundingClientRect().bottom);
  const el = candidates[0];
  if (!el) return {ok:false, error:'editor not found'};
  el.focus();
  return {ok:true, tag:el.tagName, cls:String(el.className).slice(0,120), beforeLength:(el.innerText || el.value || '').length};
})()
"""
    cdp = Cdp(args.page_id, args.cdp_url)
    focus = cdp.eval(js)
    if not isinstance(focus, dict) or not focus.get("ok"):
        print(json.dumps(focus, ensure_ascii=False, indent=2))
        return
    # Use real key events and insertText so React/Tiptap sees user-like edits.
    cdp.key("keyDown", "a", "KeyA", 65, modifiers=2)
    cdp.key("keyUp", "a", "KeyA", 65, modifiers=2)
    cdp.key("keyDown", "Backspace", "Backspace", 8)
    cdp.key("keyUp", "Backspace", "Backspace", 8)
    cdp.insert_text(content)
    time.sleep(args.wait)
    state = cdp.eval(
        r"""
(() => {
  const text = el => (el && (el.innerText || el.textContent || el.value || '')).trim();
  const visible = el => {
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.display !== 'none' && s.visibility !== 'hidden';
  };
  const editor = [...document.querySelectorAll('.editor-HT1dqv,.ProseMirror,[contenteditable=true],textarea,input')].filter(visible)[0] || null;
  const create = [...document.querySelectorAll('button')].filter(visible).find(b => /createButton|arrow-up/.test(String(b.className))) || null;
  return {
    ok:true,
    editorLength: editor ? text(editor).length : 0,
    createDisabled: create ? (create.disabled || /disabled/.test(String(create.className))) : null,
    createClass: create ? String(create.className).slice(0,160) : '',
  };
})()
"""
    )
    print(json.dumps({"ok": True, "focus": focus, "state": state}, ensure_ascii=False, indent=2))


def cmd_select_mode(args: argparse.Namespace) -> None:
    label = args.label
    js = f"""
(async () => {{
  const label = {json.dumps(label, ensure_ascii=False)};
  const sleep = ms => new Promise(resolve => setTimeout(resolve, ms));
  const text = el => (el && (el.innerText || el.textContent || '')).trim();
  const visible = el => {{
    const r = el.getBoundingClientRect();
    const s = getComputedStyle(el);
    return r.width > 2 && r.height > 2 && s.display !== 'none' && s.visibility !== 'hidden';
  }};
  const rect = el => {{
    const r = el.getBoundingClientRect();
    return {{x:Math.round(r.x), y:Math.round(r.y), w:Math.round(r.width), h:Math.round(r.height)}};
  }};
  const items = () => [...document.querySelectorAll('[class*="dropdownItem"]')]
    .filter(visible)
    .filter(el => text(el).includes(label));
  let item = items()[0] || null;
  let opened = false;
  if (!item) {{
    const modeWords = ['Agent 模式', '短剧 Agent', '沉浸式短片', '智能长视频 2.0', '生成图片', '智能长视频', '短片'];
    const triggers = [...document.querySelectorAll('[class*="selectedTag"],[class*="configButtons"],[class*="toolbarLeft"],button,[role=button],div')]
      .filter(visible)
      .filter(el => {{
        const t = text(el);
        const r = el.getBoundingClientRect();
        return r.y > window.innerHeight * 0.45 && r.y < window.innerHeight + 20 && t.length < 180 && modeWords.some(word => t.includes(word));
      }})
      .sort((a,b) => {{
        const ar = a.getBoundingClientRect(), br = b.getBoundingClientRect();
        const aTag = /selectedTag/.test(String(a.className)) ? 0 : 100000;
        const bTag = /selectedTag/.test(String(b.className)) ? 0 : 100000;
        return aTag - bTag || (ar.width * ar.height) - (br.width * br.height);
      }});
    if (!triggers.length) return {{ok:false, error:'mode trigger not found'}};
    triggers[0].click();
    opened = true;
    await sleep(350);
    item = items()[0] || null;
  }}
  if (!item) {{
    return {{
      ok:false,
      error:'mode item not found after opening dropdown',
      visibleDropdownText:[...document.querySelectorAll('[class*="dropdownItem"]')].filter(visible).map(el => text(el)).slice(0,20)
    }};
  }}
  const clicked = {{text:text(item), rect:rect(item), cls:String(item.className).slice(0,120)}};
  item.click();
  await sleep(600);
  const toolbar = [...document.querySelectorAll('[class*="toolbar"],[class*="configButtons"],[class*="selectedTag"]')]
    .filter(visible)
    .map(el => text(el).replace(/\\s+/g, ' ').slice(0,160))
    .filter(Boolean)
    .slice(0,20);
  return {{ok:true, label, opened, clicked, toolbar, href:location.href}};
}})()
"""
    cdp = Cdp(args.page_id, args.cdp_url)
    print(json.dumps(cdp.eval(js, await_promise=True), ensure_ascii=False, indent=2))


def cmd_wait(args: argparse.Namespace) -> None:
    seconds = None
    for value in reversed(args.values):
        try:
            seconds = float(value)
            break
        except ValueError:
            continue
    if seconds is None:
        seconds = 1.0
    time.sleep(seconds)
    print(json.dumps({"ok": True, "seconds": seconds, "values": args.values}, ensure_ascii=False, indent=2))


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp-url", default=DEFAULT_CDP)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("list-pages").set_defaults(func=list_pages)

    p = sub.add_parser("eval")
    p.add_argument("page_id")
    p.add_argument("javascript")
    p.add_argument("--await-promise", action="store_true")
    p.set_defaults(func=cmd_eval)

    p = sub.add_parser("visible")
    p.add_argument("page_id")
    p.set_defaults(func=cmd_visible)

    p = sub.add_parser("click")
    p.add_argument("page_id")
    p.add_argument("x", type=float)
    p.add_argument("y", type=float)
    p.set_defaults(func=cmd_click)

    p = sub.add_parser("click-text")
    p.add_argument("page_id")
    p.add_argument("text")
    p.set_defaults(func=cmd_click_text)

    p = sub.add_parser("navigate")
    p.add_argument("page_id")
    p.add_argument("url")
    p.set_defaults(func=cmd_navigate)

    p = sub.add_parser("screenshot")
    p.add_argument("page_id")
    p.add_argument("output")
    p.set_defaults(func=cmd_screenshot)

    p = sub.add_parser("bring-to-front")
    p.add_argument("page_id")
    p.set_defaults(func=cmd_bring_to_front)

    p = sub.add_parser("set-file-input")
    p.add_argument("page_id")
    p.add_argument("files", nargs="+")
    p.add_argument("--selector", default="input[type=file]")
    p.add_argument("--index", type=int, default=-1)
    p.set_defaults(func=cmd_set_file_input)

    p = sub.add_parser("verify-attachments")
    p.add_argument("page_id")
    p.set_defaults(func=cmd_verify_attachments)

    p = sub.add_parser("upload-images-verify")
    p.add_argument("page_id")
    p.add_argument("files", nargs="+")
    p.add_argument("--selector", default="input[type=file]")
    p.add_argument("--index", type=int, default=-1)
    p.add_argument("--timeout", type=float, default=20.0)
    p.add_argument("--interval", type=float, default=1.0)
    p.add_argument("--screenshot", default="outputs/xyq-upload-training/upload-verification.png")
    p.set_defaults(func=cmd_upload_images_verify)

    p = sub.add_parser("set-prompt")
    p.add_argument("page_id")
    p.add_argument("markdown_file")
    p.set_defaults(func=cmd_set_prompt)

    p = sub.add_parser("type-prompt")
    p.add_argument("page_id")
    p.add_argument("markdown_file")
    p.add_argument("--wait", type=float, default=0.5)
    p.set_defaults(func=cmd_type_prompt)

    p = sub.add_parser("select-mode")
    p.add_argument("page_id")
    p.add_argument("label")
    p.set_defaults(func=cmd_select_mode)

    p = sub.add_parser("wait")
    p.add_argument("values", nargs="+", help="seconds, or page_id seconds; page_id-only defaults to 1s")
    p.set_defaults(func=cmd_wait)

    args = parser.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
