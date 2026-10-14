#!/usr/bin/env python3
"""Download source/PDF using an existing English Overleaf editor tab (no edits)."""

import argparse
import asyncio
import hashlib
import json
from pathlib import Path
import re
import sys
import tempfile
from urllib.parse import urlsplit
import zipfile


def project_key(url):
    parsed = urlsplit(url)
    if not re.fullmatch(r"/project/[a-zA-Z0-9]+/?", parsed.path):
        raise ValueError("Use the canonical editor URL ending in /project/PROJECT_ID")
    return parsed.scheme, parsed.netloc, parsed.path.rstrip("/")


async def download(args):
    from playwright.async_api import async_playwright

    outputs = [("Download as source (.zip)", Path(args.source_zip), "zip")]
    if args.pdf:
        outputs.append(("Download as PDF", Path(args.pdf), "pdf"))
    if len({p.resolve() for _, p, _ in outputs}) != len(outputs):
        raise ValueError("Source ZIP and PDF must use different output paths")
    for _, path, _ in outputs:
        if path.exists() or path.is_symlink():
            raise ValueError("Output already exists; choose a fresh private filename")
        if not path.parent.is_dir():
            raise ValueError("Create the private output directory first")
    target = project_key(args.project_url)
    async with async_playwright() as pw:
        browser = await pw.chromium.connect_over_cdp(args.cdp)
        matches = []
        for context in browser.contexts:
            for page in context.pages:
                try:
                    if project_key(page.url) == target:
                        matches.append(page)
                except ValueError:
                    continue
        if len(matches) != 1:
            raise RuntimeError("Need exactly one matching project tab; inspect the browser")
        page = matches[0]
        page.set_default_timeout(8000)
        await page.bring_to_front()
        # Fail before Escape or download when recovery/modals need human inspection.
        body = await page.locator("body").inner_text()
        if re.search(r"out of sync|you[’']re offline|reconnecting", body, re.I):
            raise RuntimeError("Editor is offline/out of sync; preserve local browser text first")
        if await page.get_by_role("dialog").count():
            raise RuntimeError("A dialog is open; inspect and resolve it before downloading")
        results = []
        for item_name, destination, kind in outputs:
            await page.keyboard.press("Escape")
            file_button = page.get_by_role("button", name="File", exact=True)
            if await file_button.get_attribute("aria-expanded") != "true":
                await file_button.click()
            # Observed submenu container; fail rather than force-click if UI differs.
            await page.locator("#toolbar-menu-bar-item-file-file-download-group").click()
            async with page.expect_download(timeout=45000) as event:
                await page.get_by_role("menuitem", name=item_name, exact=True).click(no_wait_after=True)
            artifact = await event.value
            with tempfile.TemporaryDirectory(prefix="overleaf-download-") as directory:
                temp = Path(directory) / "artifact"
                await artifact.save_as(temp)
                if kind == "zip":
                    with zipfile.ZipFile(temp) as archive:
                        if not archive.infolist() or archive.testzip() is not None:
                            raise RuntimeError("Source download is not a valid nonempty ZIP")
                elif not temp.read_bytes().startswith(b"%PDF-"):
                    raise RuntimeError("PDF download has an invalid header")
                content = temp.read_bytes()
                with destination.open("xb") as handle:
                    destination.chmod(0o600)
                    handle.write(content)
            result = {"kind": kind, "path": str(destination), "bytes": len(content),
                      "sha256": hashlib.sha256(content).hexdigest()}
            results.append(result)
            # A later failure must not hide an already completed download.
            print(json.dumps(result), flush=True)
        # Exiting Playwright disconnects this client. Do not close browser/context/tab.
        return results


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cdp", required=True, help="Existing authorized Chrome CDP endpoint")
    parser.add_argument("--project-url", required=True, help="Exact canonical project editor URL")
    parser.add_argument("--source-zip", required=True, help="New private source ZIP path")
    parser.add_argument("--pdf", help="Optional new path for the already-compiled current PDF")
    args = parser.parse_args()
    try:
        asyncio.run(download(args))
    except Exception as error:
        # Playwright call logs can contain project/account details. Keep them private.
        print(f"Download stopped ({type(error).__name__}). Inspect the live UI and preserve any completed files. "
              "Check login, offline/dialog state, exact tab, controls, dependencies, and output paths.", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
