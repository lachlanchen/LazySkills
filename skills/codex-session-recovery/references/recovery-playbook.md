# Codex Session Recovery Playbook

## Contents

1. [Scope](#scope)
2. [Failure layers](#failure-layers)
3. [Evidence order](#evidence-order)
4. [Supported recovery protocol](#supported-recovery-protocol)
5. [Safety and integrity model](#safety-and-integrity-model)
6. [Tool commands](#tool-commands)
7. [Result interpretation](#result-interpretation)
8. [Failure handling](#failure-handling)
9. [Handoff fallback](#handoff-fallback)
10. [Version drift](#version-drift)
11. [Security notes](#security-notes)
12. [Official references](#official-references)

## Scope

Use this playbook for a persisted Codex CLI thread that appears frozen, takes an unusually long time to resume, repeatedly aborts, or carries a very large model-visible context. It covers safe diagnosis, private rollout backup, official app-server compaction, load verification, and fresh-thread handoff.

It does not repair provider outages, account authorization, a full filesystem, or an application bug unrelated to one persisted thread.

## Failure layers

Separate these layers before acting:

| Layer | Typical evidence | Response |
| --- | --- | --- |
| Active owner | Exact rollout file descriptor held by Codex | Do not touch it; ask the user to close or interrupt it |
| Cold-load cost | Large rollout, high CPU/RSS, eventual resume | Wait within a measured timeout; compact model-visible history |
| Context pressure | High last-turn input relative to context window | Compact; optionally lower effort only by explicit choice |
| Inline payload growth | Many `data:image` occurrences or giant tool outputs | Document the cause; compaction will not shrink disk history |
| Provider/auth | 401, 403, 429, quota or rate-limit status | Resolve externally; never auto-retry recovery |
| Damaged tail | Missing newline or invalid final JSON record | Stop; do not synthesize, truncate, or rewrite history |
| Protocol drift | Generated schema lacks required contracts | Stop and update/test the tool for that Codex version |

Silence alone is not corruption. A large thread can spend minutes parsing history or waiting for remote compaction while emitting little output.

## Evidence order

Use this priority:

1. Exact rollout ownership and current process state.
2. Read-only thread metadata and rollout stat/tail evidence.
3. Generated app-server schema from the installed Codex binary.
4. Verified private backup manifest.
5. Matching app-server lifecycle notifications.
6. Append-only postflight evidence.
7. Curated handoff and task files.
8. Targeted raw-history inspection only when the user explicitly needs it.

Do not treat cumulative `tokens_used` as current context size. Prefer the numeric `last_token_usage.input_tokens` and `model_context_window` from the latest token event, while noting that these are still evidence from the latest completed turn.

## Supported recovery protocol

The tool starts a private local stdio child:

```text
CODEX_HOME=<resolved-home> codex app-server --disable hooks --stdio
```

It never opens a TCP listener. It verifies that `initialize.result.codexHome` matches the resolved home, disables configured Codex hooks in the helper-owned process, and verifies that `thread/resume` returns the requested thread ID. The core request flow is:

```json
{"method":"initialize","id":1,"params":{"clientInfo":{"name":"codex-session-recovery","title":"Codex Session Recovery","version":"1.0.0"},"capabilities":{"experimentalApi":true}}}
{"method":"initialized","params":{}}
{"method":"thread/resume","id":2,"params":{"threadId":"THREAD_UUID","excludeTurns":true}}
{"method":"thread/compact/start","id":3,"params":{"threadId":"THREAD_UUID"}}
```

The compaction request response only proves acceptance. Track `turn/started` so a stall before the first item can still be interrupted. Declare success only after correlating all of these to the same `threadId` and compaction `turnId`:

1. `item/started` with `item.type == "contextCompaction"`;
2. `item/completed` for the same context-compaction item;
3. `turn/completed` with `turn.status == "completed"`;
4. the response to the original `thread/compact/start` request.

Buffer event order. Notifications can arrive before the request acknowledgement. Ignore unrelated thread/turn events.

Use `thread/settings/update` only when the user explicitly supplies `--effort`. This method is experimental and version-sensitive.

Use `turn/start` only for the explicit canary. A normal `probe` stops after a successful cold `thread/resume` and adds no model turn. The canary rejects command, file-change, MCP, collaboration-agent, and other tool item types whether they only start or complete. It permits an automatically generated `contextCompaction` item for the same turn.

If a compaction or canary has a known in-flight turn and then times out or encounters a protocol error, the helper sends `turn/interrupt` and briefly drains its acknowledgement and terminal event before shutting down. It never retries the failed operation automatically.

## Safety and integrity model

### Path authority

For mutation, require exactly one rollout that:

- is under resolved `$CODEX_HOME/sessions`;
- ends in `-THREAD_UUID.jsonl`;
- is a regular file owned by the current user;
- has no symlink component and one hard link;
- is not marked archived;
- ends with a newline and a parseable JSON record.

The SQLite row is a read-only discovery hint. Never make SQLite the mutation surface.

### Ownership

Use `lsof` when available, then Linux `/proc/*/fd` inode matching. The shared state database being open is irrelevant because unrelated Codex threads share it.

Before backup, after backup, and immediately before resume, require no rollout owner. After backup, re-attest the source device, inode, size, mtime, and full SHA-256 against the verified archive. After the helper resumes the thread, require that every rollout owner belongs to the helper's private process tree. Never terminate an unexpected owner.

The per-session lock prevents helper/helper races. Codex itself does not honor that lock, so repeated file-descriptor checks remain necessary.

### Backup

Create a fresh private directory outside all Git worktrees. Set restrictive creation mode before writing any byte:

```text
directory: 0700
files:     0600
```

Record:

- source device, inode, size, and modification time;
- source SHA-256;
- compressed archive SHA-256;
- decompressed SHA-256 and byte count;
- Codex version and ownership method.

Reject the backup if the source changes during compression or if decompression differs. A zstd integrity test alone is insufficient because it does not prove equality to the source hash.

The archive is compressed, not encrypted. Treat it as the complete private conversation.

### Postflight

After the tool-owned app-server exits, run postflight whether the primary operation succeeded or failed. Require:

- the same rollout device and inode;
- size after recovery greater than or equal to size before;
- SHA-256 of the first original-size bytes unchanged;
- a complete final newline;
- a parseable final JSON record.

Verify the backup against its manifest. Do not compare the full live file hash to the pre-compaction hash because successful compaction appends records.

Postflight opens one non-symlink file descriptor, hashes and parses through that descriptor, verifies its stat fields did not change during the check, then re-attests the path to the same inode. Failure JSON preserves both the primary error and available backup, effort, interruption, and postflight evidence.

## Tool commands

Assuming:

```bash
RECOVERY="${CODEX_HOME:-$HOME/.codex}/skills/codex-session-recovery/scripts/codex_session_recovery.py"
```

| Command | Mutation | Purpose |
| --- | --- | --- |
| `python3 "$RECOVERY" --json doctor` | No | Generate and check installed app-server schemas |
| `python3 "$RECOVERY" --json inspect UUID` | No | Show safe metadata, owners, size, and tail state |
| `python3 "$RECOVERY" --json inspect UUID --scan` | No | Add streaming aggregate counts |
| `python3 "$RECOVERY" --json backup UUID` | Writes private backup only | Create and verify an exact rollout backup |
| `python3 "$RECOVERY" --json verify-backup MANIFEST` | No | Recompute archive and decompressed hashes |
| `python3 "$RECOVERY" --json probe UUID` | Loads thread, no model turn | Measure cold resume and owner correctness |
| `python3 "$RECOVERY" --json recover UUID --dry-run` | No | Preview guarded recovery |
| `python3 "$RECOVERY" --json recover UUID --yes` | Appends compaction | Back up, compact, and post-verify |
| `python3 "$RECOVERY" --json canary UUID --yes` | Appends model turn | Explicitly test a model response |

Global options such as `--json`, `--codex-home`, and `--codex-bin` must precede the subcommand.

## Result interpretation

Important fields include:

- `ownership.verified` and `ownership.owners`;
- `tail.newlineComplete`, `tail.invalidTailRecords`, and `tail.lastEventType`;
- `backup.sourceSha256`, `backup.backupSha256`, and `backup.manifestPath`;
- `compaction.contextItemStarted`, `contextItemCompleted`, and `status`;
- `postflight.prefixUnchanged`, `bytesAppended`, and `tailJsonValid`;
- failure `partial.backup`, `partial.effortChange`, `partial.operationDetails.interrupt`, and `partial.postflight`;
- `loadProbe.elapsedSeconds` or explicit `canary.elapsedSeconds`.

Current exit codes:

| Code | Meaning |
| ---: | --- |
| 0 | Success |
| 2 | Invalid arguments, missing/ambiguous session, or confirmation absent |
| 3 | Session busy or ownership cannot be proved |
| 4 | Backup, disk-space, or checksum failure |
| 5 | App-server or append-only protocol failure |
| 6 | Timeout |
| 7 | Explicit canary failure |
| 8 | Unsupported Codex binary or schema |
| 130 | User interruption |

## Failure handling

### Active owner

Report PID and short process name only. Do not dump its command line because arguments can contain private paths or tokens. Ask the user to close or interrupt that exact session, then rerun `inspect`.

### Long resume or compaction

Keep a visible heartbeat. Defaults are 600 seconds for resume and 1,800 seconds per compaction/model turn. Increase a timeout only with evidence that the process is still active and the user accepts the wait.

### 401, 403, 429, or quota failure

Stop the helper. Fix login, authorization, account policy, or limits separately. Start a new explicit recovery attempt after the external condition changes. Do not loop.

### Invalid tail or prefix mismatch

Preserve evidence and stop. Do not restore automatically and do not offer a truncation flag. Escalate to a version-specific Codex support/debug workflow with the verified backup intact.

### Still slow after successful compaction

Distinguish model-turn latency from cold-open latency. Compaction may cut model-visible tokens while the historical rollout remains hundreds of megabytes or gigabytes. Use a fresh thread plus curated handoff when startup time is the remaining problem.

## Handoff fallback

Write a handoff without copying raw chat:

```markdown
# Codex Thread Handoff

Updated: YYYY-MM-DD

## Objective

The concrete outcome still required.

## Verified state

Files, branch, processes, artifacts, counts, and validation evidence.

## Unfinished tasks

Ordered next actions with exact paths and stop conditions.

## Safety boundaries

Changes to preserve, private artifacts not to commit, and external actions not authorized.

## Recovery evidence

Original thread UUID, backup manifest path, compaction result, and known cold-load limitation.
```

Store private handoffs in an ignored directory. Put only sanitized reusable operational facts in tracked documentation.

## Version drift

The app-server protocol is version-sensitive. `doctor` runs:

```text
codex app-server generate-json-schema --experimental --out TEMP_DIR
```

It parses a structural projection for resume, compaction, turn start/started, interruption, item lifecycle, and terminal turn fields, then reports a contract fingerprint. Additive schema fields are acceptable. Missing or changed required contracts must stop mutation until the tool and fixture tests are updated.

Run the isolated tests with a temporary HOME, temporary CODEX_HOME, and fake Codex executable. Standard tests must never invoke a real session. Reserve live tests for a disposable thread and explicit opt-in.

## Security notes

- The helper uses the user's current Codex provider, authentication, configuration, and experimental app-server implementation.
- The helper disables configured Codex hooks in its app-server child. Other configuration and provider behavior still apply; an explicit model canary is not a read-only security boundary.
- Never print raw JSON-RPC traffic, prompt previews, reasoning, authorization headers, or unbounded stderr.
- Keep generated backup manifests private because they include the local source path and thread UUID.
- Do not commit the raw backup, manifest, checksum, generated images, `auth.json`, cookies, or SQLite state.
- Do not add archive/delete/rollback/inject/shell-command operations to this recovery tool.

## Official references

- [Codex app-server overview](https://learn.chatgpt.com/docs/app-server#api-overview)
- [Trigger thread compaction](https://learn.chatgpt.com/docs/app-server#trigger-thread-compaction)
- [App-server message schema](https://learn.chatgpt.com/docs/app-server#message-schema)
- [Build Codex skills](https://learn.chatgpt.com/docs/build-skills)
