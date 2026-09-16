# Handoff Packet Template

Copy this into `~/.codex/handoffs/<thread>-<purpose>.md` (private) and, when the
project tracks dated handoff notes, a curated copy under its `references/`.

```markdown
# <Thread name>: <purpose> handoff

Updated: YYYY-MM-DD
From: <agent and session id>  To: <agent>
Source thread: `<UUID>` (`~/.codex/sessions/...`), forked from `<UUID>` if any

## Objective

One paragraph. What "done" means. What must not change.

## Verified state

Only facts re-checked on disk or by running a command. Cite paths, commit
hashes, run folder names, manifest fields.

## Design or task parameters

Every number that drives the work, with provenance (user statement, datasheet,
measurement, prior accepted run).

## Files and commands

- source of truth files
- build / verify / render commands, exact
- sync / publish conventions

## User corrections to respect

Verbatim short quotes. These are the mistakes the receiving agent must not
repeat.

## Open work

Numbered, smallest verifiable step first.

## Ownership boundaries

Who owns which repo, folder, device, service, tmux session, run folder.

## Stop conditions

When to stop and ask: irreversible actions, paid submissions, quota exhaustion,
ambiguous measurements.

## Evidence

Commits, test output, render paths, screenshots.

## Private context

Paths to raw rollouts or extracts. Never commit them.
```
