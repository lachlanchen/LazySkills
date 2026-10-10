#!/usr/bin/env python3
"""Fill an observed empty WeChat album form; optionally save, never submit review."""
import argparse
import json
from pathlib import Path
import time
from urllib.parse import urlparse, parse_qs

from PIL import Image

from audit_wechat_album import audit
from snapshot_wechat_gallery import Cdp

PACKAGING = [('banner.jpg', (750, 400)), ('cover.png', (240, 240)),
             ('icon.png', (50, 50)), ('reward-guide.png', (750, 560)),
             ('reward-thanks.png', (750, 750))]


def price_label(meta):
    mode = meta.get('price_mode', 'paid')
    if mode not in {'free', 'paid'}:
        raise ValueError('price_mode must be free or paid')
    return '免费' if mode == 'free' else '10 微信豆'


def validate_packaging(album):
    """Check every local asset before changing an existing remote draft."""
    for name, size in PACKAGING:
        path = album / name
        with Image.open(path) as image:
            image.load()
            if image.size != size or path.stat().st_size > (100_000 if name == 'icon.png' else 500_000):
                raise ValueError(f'Invalid packaging: {name}')
            if name in {'cover.png', 'icon.png'} and (
                    'A' not in image.getbands() or image.getchannel('A').getextrema()[0] != 0):
                raise ValueError(f'Transparent packaging required: {name}')


def wait(cdp, expression, timeout=120):
    end = time.monotonic() + timeout
    while time.monotonic() < end:
        value = cdp.eval(expression)
        if value:
            return value
        time.sleep(.4)
    raise TimeoutError(expression)


def choose(cdp, text):
    cdp.eval("""(()=>{const e=[...document.querySelectorAll('input[type=radio],input[type=checkbox]')]
      .find(x=>x.parentElement.innerText.trim()===TEXT);if(!e)throw Error('Missing choice');
      if(!e.checked)e.click();})()""".replace("TEXT", json.dumps(text)))
    wait(cdp, "[...document.querySelectorAll('input:checked')].some(x=>x.parentElement.innerText.trim()===" + json.dumps(text) + ")")


def fill(cdp, selector, value):
    cdp.eval("""(()=>{const e=document.querySelector(SELECTOR);if(!e)throw Error('Missing field');
      Object.getOwnPropertyDescriptor(Object.getPrototypeOf(e),'value').set.call(e,VALUE);
      e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})()"""
      .replace("SELECTOR", json.dumps(selector)).replace("VALUE", json.dumps(value)))
    wait(cdp, "document.querySelector(" + json.dumps(selector) + ").value===" + json.dumps(value))


def attach(cdp, index, files):
    root = cdp.call("DOM.getDocument", {"depth": 0})["root"]["nodeId"]
    nodes = cdp.call("DOM.querySelectorAll", {"nodeId": root, "selector": "input[type=file]"})["nodeIds"]
    cdp.call("DOM.setFileInputFiles", {"nodeId": nodes[index], "files": [str(p.resolve()) for p in files]})


def wait_save_result(cdp, timeout=120):
    """A created work id is not a persisted draft; stop on explicit UI errors."""
    result = wait(cdp, """(()=>{const text=document.body.innerText;
      if(location.pathname.includes('/timeout/login') || text.includes('登录超时'))return 'login_expired';
      if(text.includes('参数错误'))return 'parameter_error';
      if(text.includes('保存成功'))return 'saved';return null;})()""", timeout)
    if result == "login_expired":
        raise RuntimeError("Login expired. Sign in and inspect the SAME work before retrying.")
    if result != "saved":
        raise RuntimeError("Platform rejected save. Inspect and repair the SAME work; do not create a duplicate.")


def verify_packaging(cdp, timeout=120):
    for index, (_, (width, height)) in enumerate(PACKAGING, 1):
        wait(cdp, f"(()=>{{let i=document.querySelectorAll('input[type=file]')[{index}].parentElement.querySelector('img');return i&&i.complete&&i.naturalWidth==={width}&&i.naturalHeight==={height}&&i.src.includes('/getmedia?fileid=');}})()", timeout)


def upload_packaging(cdp, album):
    for index, (name, (width, height)) in enumerate(PACKAGING, 1):
        attach(cdp, index, [album / name])
        wait(cdp, f"(()=>{{let i=document.querySelectorAll('input[type=file]')[{index}].parentElement.querySelector('img');return i&&i.complete&&i.naturalWidth==={width}&&i.naturalHeight==={height}&&i.src.includes('/getmedia?fileid=');}})()")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("album", type=Path)
    parser.add_argument("metadata", type=Path)
    parser.add_argument("--cdp-url", required=True)
    parser.add_argument("--page-id", required=True)
    parser.add_argument("--receipt", type=Path, required=True)
    parser.add_argument("--save-draft", action="store_true")
    parser.add_argument("--repair-empty-draft-id", help="Explicit known draft id, only if its form is empty")
    args = parser.parse_args()
    if args.receipt.exists():
        raise SystemExit("Receipt exists: resume the saved work instead of creating a duplicate")
    meta = json.loads(args.metadata.read_text())
    price = price_label(meta)
    files = sorted((args.album / "gifs").glob("*.gif"))
    if not 8 <= len(files) <= 24 or len(meta["words"]) != len(files):
        raise ValueError("Count mismatch")
    for path in files:
        audit(path)
    validate_packaging(args.album)
    cdp = Cdp(args.page_id, args.cdp_url)
    try:
        url = urlparse(cdp.eval("location.href"))
        existing_id = parse_qs(url.query).get("stikerid", [None])[0]
        if url.hostname != "sticker.weixin.qq.com" or not url.path.endswith("/stickerPage/detail") or existing_id != args.repair_empty_draft_id:
            raise ValueError("Use an observed empty new-album form; never edit an existing work here")
        if cdp.eval("document.querySelectorAll('input[placeholder=输入含义词]').length"):
            raise ValueError("Form is not empty")
        cdp.bring_to_front()
        wait(cdp, "document.querySelector('input[placeholder=填写表情专辑名称]')!==null")
        choose(cdp, "动态表情")
        wait(cdp, "document.querySelector('input[type=file]').accept==='image/gif'")
        time.sleep(.6)
        attach(cdp, 0, files)
        wait(cdp, "document.querySelectorAll('input[placeholder=输入含义词]').length===" + str(len(files)), 180)
        for index, word in enumerate(meta["words"]):
            cdp.eval("""(()=>{let e=[...document.querySelectorAll('input[placeholder=输入含义词]')][INDEX];
              Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,WORD);
              e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})()"""
              .replace("INDEX", str(index)).replace("WORD", json.dumps(word)))
        for selector, value in [("input[placeholder=填写表情专辑名称]", meta["title"]),
                                ("textarea", meta["description"]),
                                ("input[placeholder=填写版权信息]", meta["copyright"])]:
            fill(cdp, selector, value)
        for text in ["卡通表情/其他", "日常", "软萌可爱", meta.get("theme", "万能通用"), "全球", price, "接受赞赏"]:
            choose(cdp, text)
        fill(cdp, "input[placeholder=最少填写5个字]", meta["thanks"])
        cdp.eval("document.querySelector('dt.weui-desktop-form__dropdowncascade__dt').click()")
        cdp.eval("document.querySelector('[title=拟人角色]').click()")
        wait(cdp, "document.querySelector('[title=其他拟人角色]')!==null")
        cdp.eval("document.querySelector('[title=其他拟人角色]').click()")
        wait(cdp, "document.querySelector('dt.weui-desktop-form__dropdowncascade__dt').innerText.includes('其他拟人角色')")
        upload_packaging(cdp, args.album)
        current = cdp.eval("[...document.querySelectorAll('input[placeholder=输入含义词]')].map(x=>x.value)")
        if current != meta["words"]:
            raise ValueError("Remote order/meaning words differ")
        if not args.save_draft:
            print("Staged only. Inspect the visible previews before saving.")
            return
        cdp.eval("[...document.querySelectorAll('button')].find(x=>x.innerText.trim()==='保存').click()")
        saved = wait(cdp, "new URL(location.href).searchParams.get('stikerid')")
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps({"id": saved, "url": cdp.eval("location.href"),
                                          "status": "saved_awaiting_reload_verification"}, indent=2) + "\n")
        wait_save_result(cdp)
        old_origin = cdp.eval("performance.timeOrigin")
        cdp.call("Page.reload")
        wait(cdp, f"performance.timeOrigin!=={old_origin} && document.querySelector('input[placeholder=填写表情专辑名称]')?.value==={json.dumps(meta['title'])} && document.querySelectorAll('input[placeholder=输入含义词]').length==={len(files)}")
        record = cdp.eval("""({url:location.href,title:document.querySelector('input[placeholder=填写表情专辑名称]').value,
          words:[...document.querySelectorAll('input[placeholder=输入含义词]')].map(x=>x.value),
          checked:[...document.querySelectorAll('input:checked')].map(x=>x.parentElement.innerText.trim())})""")
        if record["words"] != meta["words"] or record["title"] != meta["title"] or not {price, "接受赞赏"}.issubset(record["checked"]):
            raise ValueError("Saved settings do not match; preserve this work and inspect")
        verify_packaging(cdp)
        record.update(status="saved_draft_not_submitted", id=saved)
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + "\n")
        print(json.dumps({"status": record["status"], "title": record["title"], "count": len(files)}, ensure_ascii=False))
    finally:
        cdp.ws.close()


if __name__ == "__main__":
    main()
