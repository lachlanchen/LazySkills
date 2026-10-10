#!/usr/bin/env python3
"""Replace GIFs on one explicitly selected existing draft; save, never submit."""
import argparse
import json
from pathlib import Path
from urllib.parse import parse_qs, urlparse

from audit_wechat_album import audit
from stage_wechat_album import (
    Cdp, attach, fill, wait, wait_save_result, upload_packaging,
    verify_packaging, validate_packaging,
)


def protected_details(cdp):
    return cdp.eval("""({
      fields:[...document.querySelectorAll('input[type=text],textarea')]
        .filter(e=>e.placeholder!=='输入含义词').map(e=>[e.placeholder,e.value]),
      checked:[...document.querySelectorAll('input:checked')]
        .map(e=>[e.type,e.value,e.parentElement.innerText.trim()]),
      packaging:[...document.querySelectorAll('input[type=file]')].slice(1,6)
        .map(e=>e.parentElement.querySelector('img')?.src),
      classification:document.querySelector('dt.weui-desktop-form__dropdowncascade__dt')?.innerText
    })""")


def assert_preserved(before, after):
    if before != after:
        raise ValueError('Non-GIF details changed; inspect the SAME work before submission')


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('album', type=Path)
    parser.add_argument('metadata', type=Path)
    parser.add_argument('--cdp-url', required=True)
    parser.add_argument('--page-id', required=True)
    parser.add_argument('--work-id', required=True)
    parser.add_argument('--expected-title', required=True)
    parser.add_argument('--expected-count', type=int, required=True)
    parser.add_argument('--receipt', type=Path, required=True)
    parser.add_argument('--preserve-details', action='store_true',
                        help='Replace only GIFs/meaning words; verify all other fields and artwork unchanged')
    args = parser.parse_args()
    if args.receipt.exists():
        parser.error('Receipt already exists: inspect the same work before resuming')
    meta = json.loads(args.metadata.read_text())
    files = sorted((args.album / 'gifs').glob('*.gif'))
    if not 8 <= len(files) <= 24 or len(files) != len(meta['words']):
        parser.error('Replacement and meaning-word counts differ')
    for path in files:
        audit(path)
    if not args.preserve_details:
        validate_packaging(args.album)
    cdp = Cdp(args.page_id, args.cdp_url)
    try:
        url = urlparse(cdp.eval('location.href'))
        if url.hostname != 'sticker.weixin.qq.com' or not url.path.endswith('/stickerPage/detail') or parse_qs(url.query).get('stikerid') != [args.work_id]:
            raise ValueError('Wrong existing draft')
        title = cdp.eval("document.querySelector('input[placeholder=填写表情专辑名称]')?.value")
        count_expr = "document.querySelectorAll('input[placeholder=输入含义词]').length"
        if title != args.expected_title or cdp.eval(count_expr) != args.expected_count:
            raise ValueError('Remote draft changed; inspect before replacing')
        cdp.bring_to_front()
        protected = protected_details(cdp) if args.preserve_details else None
        record = {'id': args.work_id, 'status': 'replacement_started_not_saved',
                  'previous_title': title, 'previous_count': args.expected_count,
                  'replacement_files': [p.name for p in files],
                  'protected_details': protected}
        args.receipt.parent.mkdir(parents=True, exist_ok=True)
        args.receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        for remaining in range(args.expected_count, 0, -1):
            cdp.eval("""(()=>{const e=document.querySelector('input[placeholder=输入含义词]')
              .closest('[isfirstcrop]');e.scrollIntoView({block:'center'});
              e.dispatchEvent(new MouseEvent('mouseenter',{bubbles:true}));})()""")
            wait(cdp, "document.querySelector('[ml-key=delete_emoji]')!==null")
            cdp.eval("document.querySelector('[ml-key=delete_emoji]').click()")
            wait(cdp, count_expr + '===' + str(remaining - 1))
        attach(cdp, 0, files)
        wait(cdp, count_expr + '===' + str(len(files)), 180)
        for index, word in enumerate(meta['words']):
            cdp.eval("""(()=>{const e=[...document.querySelectorAll('input[placeholder=输入含义词]')][INDEX];
              Object.getOwnPropertyDescriptor(HTMLInputElement.prototype,'value').set.call(e,WORD);
              e.dispatchEvent(new Event('input',{bubbles:true}));e.dispatchEvent(new Event('change',{bubbles:true}));})()"""
              .replace('INDEX', str(index)).replace('WORD', json.dumps(word)))
        for selector, value in ([] if args.preserve_details else [('input[placeholder=填写表情专辑名称]', meta['title']),
                                ('textarea', meta['description']),
                                ('input[placeholder=最少填写5个字]', meta['thanks'])]):
            fill(cdp, selector, value)
        # GIF thumbnails remain local blobs until Save; packaging uploads immediately.
        wait(cdp, "document.querySelectorAll('img.h-16').length===" + str(len(files)) +
             " && [...document.querySelectorAll('img.h-16')].every(i=>i.complete&&i.naturalWidth>0)", 180)
        if args.preserve_details:
            assert_preserved(protected, protected_details(cdp))
        else:
            upload_packaging(cdp, args.album)
        cdp.eval("[...document.querySelectorAll('button')].find(x=>x.innerText.trim()==='保存').click()")
        wait_save_result(cdp)
        old_origin = cdp.eval('performance.timeOrigin')
        cdp.call('Page.reload')
        wait(cdp, f"performance.timeOrigin!=={old_origin} && document.querySelector('input[placeholder=填写表情专辑名称]')?.value==={json.dumps(meta['title'])} && {count_expr}==={len(files)}")
        current = cdp.eval("""({title:document.querySelector('input[placeholder=填写表情专辑名称]').value,
          words:[...document.querySelectorAll('input[placeholder=输入含义词]')].map(e=>e.value),
          checked:[...document.querySelectorAll('input:checked')].map(e=>e.parentElement.innerText.trim())})""")
        if current['words'] != meta['words']:
            raise ValueError('Reloaded words differ; inspect same work')
        wait(cdp, "document.querySelectorAll('img.h-16').length===" + str(len(files)) +
             " && [...document.querySelectorAll('img.h-16')].every(i=>i.complete&&i.naturalWidth>0&&i.src.includes('/getmedia?fileid='))")
        record['saved_previews'] = cdp.eval("[...document.querySelectorAll('img.h-16')].map(i=>i.src)")
        verify_packaging(cdp)
        if args.preserve_details:
            assert_preserved(protected, protected_details(cdp))
        if not {'10 微信豆','接受赞赏'}.issubset(current['checked']):
            raise ValueError('Paid/appreciation settings changed')
        record.update(current, status='saved_draft_not_submitted')
        args.receipt.write_text(json.dumps(record, ensure_ascii=False, indent=2) + '\n')
        print(json.dumps({'status':record['status'],'title':current['title'],'count':len(files)},ensure_ascii=False))
    finally:
        cdp.ws.close()


if __name__ == '__main__':
    main()
