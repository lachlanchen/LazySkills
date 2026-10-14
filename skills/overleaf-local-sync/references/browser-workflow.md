# Browser workflow

Use the already authorized project and browser profile. If a dedicated desktop is needed, follow the workstation's resource policy and maintain one stack per project. Record its ownership privately. Do not start a new profile merely because a tab is difficult to find.

## Source snapshots

Locate the exact project URL; reject ambiguous duplicate tabs until the correct tab is selected. Do not choose the first Overleaf tab or a similarly titled paper. Bring the chosen tab to the front.

In the English editor UI observed in October 2026:

1. **File** is a button, not a menuitem.
2. Open **File → Download → Download as source (.zip)**.
3. Reopen **File → Download → Download as PDF** after compilation when needed.

Inspect the current UI because controls may change. Execute each complete menu/download sequence in one browser connection. Menus may close between separate tool sessions. In Playwright, wrap the download click in `expect_download`; `click(no_wait_after=True)` avoids waiting for navigation when the action downloads a file instead. Wait for the download event and validate the saved artifact.

Example using environment values from the project's private handoff:

```bash
python /path/to/overleaf-local-sync/scripts/browser_download.py \
  --cdp "$OVERLEAF_CDP" --project-url "$OVERLEAF_PROJECT_URL" \
  --source-zip "$SYNC_RUN/before.zip"
```

Use a fresh filename each time. The helper refuses overwrite and ambiguous tabs, and stops on visible offline/out-of-sync states. It does not compile; the optional `--pdf` downloads the current compiled PDF, which must already have been verified as current. Its JSON output contains file paths and hashes, not account details. If the UI is localized or redesigned, use inspected controls rather than guessing identifiers.

## Offline / out-of-sync recovery

Before reload, preserve any unsaved local editor text in private state. An observed **Out of sync** dialog offered **Show Local File Contents** and **Reload editor**. Save the exposed text first, then reload and download fresh source. If copying from the editor, focus the actual source editor, select/copy via normal keyboard controls, and verify that the copy contains the intended complete document rather than only a virtualized visible section. Do not assume DOM text from CodeMirror contains the full file.

Compare the saved browser copy with both the fresh server file and local work. It can contain a third independent edit. Do not dismiss that copy as stale merely because the server source differs. If recovery is ambiguous, preserve all versions and ask about the affected passage rather than discarding one.

## Incremental source edits

- Select the exact source file and retain the active Reviewing/Editing mode. Leave existing suggestions, comments, and unresolved reviews intact.
- Open the editor's ordinary Find/Replace controls. Search exact old text, with regex disabled for literal searches. For multiline regex searches, escape the entire old passage and verify the selected text before replacement.
- Check the expected occurrence count and context. For one intended hunk, require one matching passage; use ordinary Replace or selected-text insertion. `Replace All` is suitable only for an explicitly intended repeated literal change with a verified count.
- Re-read the changed region and wait for save state. Record each applied hunk so a timeout cannot cause the same insertion twice.
- Use normal keyboard/locator operations. Do not invoke internal editor dispatch APIs, set hidden application state, or POST source mutations behind the browser to simulate “human edits.”

If a match fails or a write times out, inspect/re-download first and determine whether the change already landed. Stop blind retries after the first unexplained failure. Never force-click through an unexpected overlay. A remote reread before each logical batch reduces concurrency risk; it does not replace final verification.

## Figures and other binary assets

1. Stage the exported asset under the exact intended remote basename. Keep the author-edited PPT/source untouched.
2. Inspect the file tree. Click a folder once to expand if necessary; double-click can toggle it closed again.
3. Select the intended folder/file and use the ordinary **Upload** action. An observed flow was a file's context menu → **Upload** → **Add files** dialog → **Select files**.
4. Supply only the staged file through the file chooser. Verify its destination and choose **Overwrite** only for the intended collision.
5. Wait for the dialog to close and saving to complete. Download source to check the exact path and content hash. A root-level duplicate is not a successful replacement of a nested figure.

For multiple assets, apply a reviewed explicit list. Do not replace the entire source archive. Retain the previous asset locally for recovery; never roll it back automatically over newer remote edits.

## Compilation evidence

Run **Recompile** and wait for completion. Inspect errors, warnings, unresolved references/citations, and relevant rendered pages. The **View logs** button may disappear or change when the log panel is already open; inspect state before clicking it again. Successful compilation can still use a misplaced old figure, so verify source hashes and the rendered figure together.

Source ZIPs do not preserve the full Overleaf comment/review history. Keeping incremental edits in the original project is part of preserving that history; the ZIP is a source baseline, not a complete collaboration backup.
