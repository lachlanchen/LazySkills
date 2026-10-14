# Comparison helper and private state

The helper plans and verifies; it does **not** copy into the active manuscript, upload, resolve meaning, or advance a baseline automatically. Review its output, apply the requested changes with normal file/editor tools, and verify again.

## State layout

Keep a project-specific directory outside the repository, or explicitly ignored and excluded from submission packages:

```text
private-sync-state/
  mapping.json
  baseline.zip              # last verified common source, unchanged during a run
  previous-baseline.zip
  runs/<unique-run>/
    before.zip
    plan/                   # generated report.json + optional candidates/
    before-push.zip
    staged/                 # only intended remote files, exact remote names
    after.zip
    compiled.pdf
    verification.json
```

Record the project URL/browser session separately in private state. Record baseline timestamp/hash, local commit, mapping hash, pending differences, and compiler settings in the handoff. Do not commit manuscripts, project identifiers, share-link tokens, cookies, or browser profiles into the skill repository.

## Explicit filename mapping

`files` maps **remote path → local path relative to --local**. The planner covers every file present in baseline or remote snapshots plus explicitly mapped paths. Files existing only in the local tree are excluded unless explicitly mapped, preventing experiments and build artifacts from becoming accidental uploads.

Example `mapping.json`:

```json
{
  "files": {
    "main.tex": "main.tex",
    "reference.bib": "reference.bib",
    "figures/fig1.pdf": "figures/fig1_reviewed.pdf"
  },
  "local_to_remote_text": {
    "main.tex": [
      {"local": "{fig1_reviewed.pdf}", "remote": "{fig1.pdf}"}
    ]
  }
}
```

Unmapped remote files use identical local paths. Replacements apply to the named local text file for comparison only; they never change the input. Use exact path tokens, including braces or path context. Do not normalize wording, whitespace, bibliography fields, or arbitrary substrings to hide differences. Merge candidates use remote names/tokens; translate them back deliberately when importing locally. A mapping change can invalidate the old baseline's interpretation; review it explicitly.

## Plan a sync

```bash
python /path/to/overleaf-local-sync/scripts/overleaf_sync.py plan \
  --base "$SYNC_STATE/baseline.zip" \
  --local "$MANUSCRIPT_ROOT" --remote "$SYNC_RUN/before.zip" \
  --map "$SYNC_STATE/mapping.json" --out "$SYNC_RUN/plan"
```

Without `--base`, differing files are `bootstrap_review`, never automatic pull/push. Matching bytes are `converged`. Establish the first baseline only after reconciling both sides and verifying equality.

Reports include canonical remote paths, mapped local paths, and SHA-256 hashes. Statuses:

| Status | Meaning |
| --- | --- |
| `unchanged` / `converged` | Equal files; the latter differs from B or has no B. |
| `pull` / `push` | One side changed, including an unambiguous new file when B exists. |
| `merge_review` | Both edited; Git produced a nonoverlapping text merge candidate. Review its meaning. |
| `conflict` | Overlapping text edits or binary divergence. Text candidate includes conflict markers. |
| `review_missing` | A tracked file is missing on at least one side. Check deletion/rename intent. |
| `bootstrap_review` | Different files without an established B. |

Candidates are proposed for UTF-8 text formats such as `.tex`, `.bib`, `.sty`, and `.cls`. They use `git merge-file` with explicit local/base/remote labels; a clean exit is not proof of scientific correctness. If Git is unavailable, install/reuse the normal system Git or resolve the diff manually. The helper does not fall back to two-way overwrites.

ZIPs are read without extraction. Unsafe paths, duplicate members, archive symlinks, and local paths escaping the manuscript root are rejected. Directory snapshots must contain project-relative files without symlinks. Archives with a wrapping directory are not automatically flattened: inspect and prepare an explicit clean snapshot if necessary. Each snapshot is limited to 512 MiB uncompressed; use a deliberate source-only snapshot for oversized projects.

## Verify a remote update

Put the exact expected final bytes of changed files under `staged/`, in remote layout. Use a repeated `--allow` for each intended changed path:

```bash
python /path/to/overleaf-local-sync/scripts/overleaf_sync.py verify \
  --before "$SYNC_RUN/before-push.zip" --after "$SYNC_RUN/after.zip" \
  --allow main.tex --allow figures/fig1.pdf \
  --expected "$SYNC_RUN/staged" > "$SYNC_RUN/verification.json"
```

Exit codes: `0` for a generated plan or passing verification, `1` for a verification mismatch, `2` for invalid inputs/tool failure. A generated plan can still contain conflicts; inspect its statuses. Verification checks unexpected changed paths and all supplied expected files. Omitting `--expected` checks change scope only, **not** whether intended content landed. Deletions require separate reviewed intent and a missing-file check; an allowlist alone does not authorize them.

If collaborators changed another file, verification reports that difference. Preserve and reconcile it; do not revert it to obtain a passing report. After reconciling local and remote, rerun `plan` against the final source. Promote that snapshot to the common baseline only when all relevant files are equal and the compiled result is verified. A partial sync needs a record of outstanding paths and per-file common versions; keep the older baseline for unresolved files.
