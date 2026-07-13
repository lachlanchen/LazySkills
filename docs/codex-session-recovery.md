# Recovering a Stalled Codex Session Safely

This runbook documents a real recovery pattern in sanitized form. Session identifiers, account details, usernames, repository names, task content, and raw conversation data are intentionally omitted.

## Outcome

A Codex thread that appeared fully stalled was recovered in place with the supported app-server compaction API. The original thread remained resumable, its model-visible context was reduced, and a clean model response was verified. No rollout JSONL or SQLite database was manually edited.

The recovery also established an important limitation: compaction repaired turn-level responsiveness but did not shrink the append-only history file, so cold reopening remained slow.

## Incident evidence

The affected thread had accumulated approximately:

| Evidence | Observed value |
| --- | ---: |
| Rollout JSONL | 1.50 GB |
| JSONL records | 215,131 |
| Inline `data:image` occurrences | 300 |
| Generated-image files | 67 files / 177 MB |
| Prior compactions | 281 |
| Aborted turns | 38 |
| Model-visible context before recovery | about 166K / 258K tokens |
| Reasoning setting before recovery | `ultra` |

The rollout ended with complete JSON and a newline. Its final turn was cleanly aborted rather than half-written. The machine had adequate memory. This established that the main problem was expensive history rehydration plus a large active context—not transcript corruption.

Cold loading consumed several gigabytes of RSS and took roughly 45–132 seconds depending on the surface and cache state. Supported compaction took about 7.5 minutes while emitting normal progress lifecycle events.

After recovery:

- latest per-turn input was about 84.6K tokens, leaving roughly 173.8K of a 258.4K context window free;
- the model and thread UUID were preserved;
- sticky reasoning was explicitly changed to `medium` after the user requested a speed fix;
- after history preparation, the final exact-response canary completed in 8.4 seconds;
- the rollout remained about 1.50 GB because compaction appended recovery state instead of rewriting history.

## Why the thread looked frozen

Three costs overlapped:

1. Codex had to parse and rebuild state from a 1.50-GB append-only rollout.
2. Repeated image/tool payloads made the disk history much larger than ordinary text chat.
3. A large active context and `ultra` reasoning increased remote turn and compaction latency.

An exhausted limit for an unrelated model was not the cause. A previously resolved authorization error was a separate layer. Always distinguish thread-state latency from provider authentication and quota failures.

## Recovery decision tree

```text
Session appears stalled
        |
        v
Does another process own the exact rollout?
   yes ----------------> Stop; user closes/interrupts it
   no
        |
        v
Is the tail newline-complete and valid JSON?
   no -----------------> Preserve evidence; no automatic repair
   yes
        |
        v
Does installed app-server schema match the tool contract?
   no -----------------> Update/test tool for this Codex version
   yes
        |
        v
Create private decompressed-SHA-verified backup
        |
        v
Resume with excludeTurns=true, recheck ownership
        |
        v
Run official thread/compact/start and require full lifecycle
        |
        v
Verify unchanged original prefix + valid append-only tail
        |
        v
Cold-load probe; optional explicit model canary
```

## Install the reusable skill

From the LazySkills repository:

```bash
python3 scripts/lazyskills.py validate
python3 scripts/lazyskills.py install --platform codex codex-session-recovery
```

The canonical source remains in:

```text
skills/codex-session-recovery/
```

The installer copies it to:

```text
~/.codex/skills/codex-session-recovery/
```

## Safe command sequence

```bash
RECOVERY="${CODEX_HOME:-$HOME/.codex}/skills/codex-session-recovery/scripts/codex_session_recovery.py"
THREAD_UUID="replace-with-thread-uuid"

python3 "$RECOVERY" --json doctor
python3 "$RECOVERY" --json inspect "$THREAD_UUID" --scan
python3 "$RECOVERY" --json recover "$THREAD_UUID" --dry-run
python3 "$RECOVERY" --json recover "$THREAD_UUID" --yes
python3 "$RECOVERY" --json probe "$THREAD_UUID"
```

Only when the user explicitly wants a model turn appended:

```bash
python3 "$RECOVERY" --json canary "$THREAD_UUID" --yes --expected SESSION_OK
```

Only when the user explicitly chooses a sticky effort change:

```bash
python3 "$RECOVERY" --json recover "$THREAD_UUID" --yes --effort medium
```

The tool refuses recovery while another Codex process holds the exact rollout. It never kills that owner.

## What the tool protects

- It creates backups outside Git with directory mode `0700` and file mode `0600`.
- It records source and compressed SHA-256 values.
- It decompresses the backup and proves the restored SHA-256 and byte count match the source.
- It re-attests source device, inode, size, mtime, and SHA-256 before resume.
- It uses a local `codex app-server --disable hooks --stdio` child for resume, compaction, settings, and the optional canary, and verifies the child reports the intended Codex home and thread ID.
- It requires matching `contextCompaction` item start/completion and a completed turn.
- It tracks `turn/started` and interrupts a known in-flight compaction/canary turn on timeout or protocol failure, including a stall before the first compaction item.
- It always verifies that the original rollout prefix did not change and the final appended tail remains valid JSON, including after a primary recovery failure.
- Failure JSON preserves the verified backup, observed effort change, interruption, and postflight evidence when available.
- It runs fixture tests with isolated temporary HOME/CODEX_HOME and a fake Codex executable.

## Operations deliberately excluded

The recovery tool provides no option to:

- truncate, rewrite, restore, or replace a rollout;
- edit or copy the shared live SQLite state database;
- bypass unknown ownership;
- skip the pre-compaction backup;
- kill another Codex/tmux/IDE process;
- archive, delete, rollback, or inject raw thread items;
- retry authentication, quota, or failed compaction errors automatically.

Manual transcript surgery is not a supported substitute. In the incident above, truncating at the prior compaction would have discarded recent work while removing only a small fraction of the 1.50-GB history.

## When to start a fresh thread

Use a fresh thread with a curated handoff when:

- cold-open latency remains unacceptable after successful compaction;
- the rollout is already hundreds of megabytes or larger;
- separate unfinished projects should not share context;
- the old thread must remain an immutable archive.

The handoff should contain only the current objective, verified files/state, unfinished actions, safety boundaries, and evidence paths. Never commit raw history or a full backup.

## Validation

From the LazySkills repository:

```bash
python3 -m py_compile skills/codex-session-recovery/scripts/*.py
python3 skills/codex-session-recovery/scripts/test_codex_session_recovery.py
python3 scripts/lazyskills.py validate
python3 "${CODEX_HOME:-$HOME/.codex}/skills/.system/skill-creator/scripts/quick_validate.py" \
  skills/codex-session-recovery
```

## References

- [Codex app-server API overview](https://learn.chatgpt.com/docs/app-server#api-overview)
- [Codex thread compaction](https://learn.chatgpt.com/docs/app-server#trigger-thread-compaction)
- [Codex app-server schemas](https://learn.chatgpt.com/docs/app-server#message-schema)
- [Building Codex skills](https://learn.chatgpt.com/docs/build-skills)
- [Skill playbook](../skills/codex-session-recovery/references/recovery-playbook.md)
