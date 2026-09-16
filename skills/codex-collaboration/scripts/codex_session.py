#!/usr/bin/env python3
"""Read-only helpers for taking over, handing off to, or collaborating with Codex CLI sessions.

Everything here treats ``$CODEX_HOME/sessions/**/rollout-*.jsonl`` as private,
append-only evidence. The script never opens a rollout for writing, never touches
the shared ``state_*.sqlite`` databases, and never kills a Codex process.

Subcommands:
  list        Recent named sessions from session_index.jsonl plus rollout path/size/owner.
  find        Resolve a thread name or UUID (prefix) to its rollout file.
  tail        Print the last N user/assistant messages of a session (scans only the tail bytes by default).
  extract     Dump user, assistant, tool-call, and compaction events into plain-text files for study.
  handoff     Write a Markdown handoff packet skeleton from a session (last requests, last reply, git state).
  quota       Report Codex account quota using the repository quota probe (cached, no tokens spent).
  delegate    Run a bounded ``codex exec`` task and capture its last message as JSON (spends quota; gated).
  queue       Queue a message into a live interactive Codex session (``codex queue``).
"""
from __future__ import annotations

import argparse
import datetime as _dt
import json
import os
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterator

CODEX_HOME = Path(os.environ.get("CODEX_HOME", Path.home() / ".codex"))
SESSIONS = CODEX_HOME / "sessions"
INDEX = CODEX_HOME / "session_index.jsonl"
UUID_RE = re.compile(r"[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}")
QUOTA_PROBE_CANDIDATES = [
    Path("/home/lachlan/ProjectsLFS/AgenticApp/agentic_tools/wechat_gui_agent/scripts/codex_quota_status.py"),
]
NOISE_PREFIXES = ("<environment_context>", "# AGENTS.md", "<permissions", "<codex_internal_context")


# ----------------------------------------------------------------------------- discovery

def read_index() -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    if not INDEX.exists():
        return rows
    for line in INDEX.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return rows


def rollout_for(uuid: str) -> Path | None:
    hits = sorted(SESSIONS.rglob(f"rollout-*-{uuid}.jsonl"))
    return hits[-1] if hits else None


def resolve(query: str) -> tuple[str, Path]:
    """Resolve a name, UUID, or UUID prefix to (uuid, rollout path)."""
    rows = read_index()
    # exact uuid
    if UUID_RE.fullmatch(query):
        path = rollout_for(query)
        if path is None:
            raise SystemExit(f"no rollout found for {query}")
        return query, path
    # exact / case-insensitive thread name, newest first
    by_name = [r for r in reversed(rows) if str(r.get("thread_name", "")).lower() == query.lower()]
    if by_name:
        uuid = by_name[0]["id"]
        path = rollout_for(uuid)
        if path is None:
            raise SystemExit(f"index names {uuid} but no rollout file exists")
        return uuid, path
    # uuid prefix on disk
    hits = sorted(SESSIONS.rglob(f"rollout-*-{query}*.jsonl"))
    if len(hits) == 1:
        return UUID_RE.search(hits[0].name).group(0), hits[0]
    if len(hits) > 1:
        raise SystemExit("ambiguous prefix:\n" + "\n".join(str(h) for h in hits))
    # substring of thread name
    subs = [r for r in reversed(rows) if query.lower() in str(r.get("thread_name", "")).lower()]
    if len(subs) == 1:
        uuid = subs[0]["id"]
        return uuid, rollout_for(uuid)
    if subs:
        raise SystemExit("ambiguous name:\n" + "\n".join(f"{r['id']}  {r.get('thread_name')}" for r in subs))
    raise SystemExit(f"no session matches {query!r}")


def owners(path: Path) -> list[str]:
    """PIDs holding the rollout open (via lsof when available, else /proc scan)."""
    if shutil.which("lsof"):
        try:
            out = subprocess.run(["lsof", "-t", str(path)], capture_output=True, text=True, timeout=20).stdout
            return [p for p in out.split() if p]
        except Exception:
            pass
    pids: list[str] = []
    target = str(path)
    for proc in Path("/proc").iterdir():
        if not proc.name.isdigit():
            continue
        fd_dir = proc / "fd"
        try:
            for fd in fd_dir.iterdir():
                try:
                    if os.readlink(fd) == target:
                        pids.append(proc.name)
                        break
                except OSError:
                    continue
        except OSError:
            continue
    return pids


# ----------------------------------------------------------------------------- streaming

def iter_events(path: Path, *, tail_bytes: int | None = None) -> Iterator[tuple[int, dict[str, Any]]]:
    """Yield (approx_line_no, event). With tail_bytes, only the file tail is scanned."""
    with path.open("rb") as fh:
        if tail_bytes:
            size = path.stat().st_size
            if size > tail_bytes:
                fh.seek(size - tail_bytes)
                fh.readline()  # drop the partial line
        n = 0
        for raw in fh:
            n += 1
            try:
                yield n, json.loads(raw)
            except json.JSONDecodeError:
                continue


def message_text(payload: dict[str, Any]) -> str:
    parts = []
    for chunk in payload.get("content", []) or []:
        if isinstance(chunk, dict):
            parts.append(chunk.get("text", ""))
    return "".join(parts)


def classify(event: dict[str, Any]) -> tuple[str, str] | None:
    """Return (kind, text) for interesting events."""
    t = event.get("type")
    p = event.get("payload") or {}
    if t == "response_item":
        pt = p.get("type")
        if pt == "message":
            txt = message_text(p)
            role = p.get("role", "?")
            if role == "user" and txt.startswith(NOISE_PREFIXES):
                return None
            return role.upper(), txt
        if pt == "function_call":
            return f"CALL {p.get('name')}", str(p.get("arguments", ""))
        if pt == "custom_tool_call":
            return f"CALL {p.get('name')}", str(p.get("input", ""))
        if pt in ("function_call_output", "custom_tool_call_output"):
            out = p.get("output", "")
            return "OUTPUT", json.dumps(out) if isinstance(out, (dict, list)) else str(out)
        if pt == "reasoning":
            summ = " ".join(x.get("text", "") for x in p.get("summary", []) if isinstance(x, dict))
            return ("REASONING", summ) if summ else None
        return None
    if t == "compacted":
        return "COMPACTED", json.dumps(p)
    if t == "session_meta":
        keep = {k: p.get(k) for k in ("id", "forked_from_id", "cwd", "timestamp", "cli_version")}
        return "SESSION_META", json.dumps(keep)
    if t == "event_msg" and p.get("type") == "thread_goal_updated":
        return "GOAL", json.dumps(p.get("goal"))
    return None


# ----------------------------------------------------------------------------- commands

def cmd_list(args: argparse.Namespace) -> int:
    rows = read_index()
    seen: dict[str, dict[str, Any]] = {}
    for r in rows:  # later rows win (newest name)
        seen[r["id"]] = r
    items = sorted(seen.values(), key=lambda r: r.get("updated_at", ""), reverse=True)[: args.limit]
    report = []
    for r in items:
        path = rollout_for(r["id"])
        entry = {
            "id": r["id"],
            "thread_name": r.get("thread_name"),
            "updated_at": r.get("updated_at"),
            "rollout": str(path) if path else None,
            "size_mb": round(path.stat().st_size / 1e6, 1) if path else None,
            "owners": owners(path) if (path and args.owners) else None,
        }
        report.append(entry)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for e in report:
            own = f" owners={e['owners']}" if e["owners"] else ""
            print(f"{e['updated_at']}  {e['id']}  {e['thread_name']!s:<28} {e['size_mb']} MB{own}")
    return 0


def cmd_find(args: argparse.Namespace) -> int:
    uuid, path = resolve(args.query)
    meta: dict[str, Any] = {}
    for _, ev in iter_events(path, tail_bytes=None):
        if ev.get("type") == "session_meta":
            p = ev.get("payload") or {}
            meta = {k: p.get(k) for k in ("forked_from_id", "cwd", "timestamp", "cli_version", "originator")}
        break
    info = {
        "uuid": uuid,
        "rollout": str(path),
        "size_mb": round(path.stat().st_size / 1e6, 1),
        "owners": owners(path),
        "session_meta": meta,
    }
    print(json.dumps(info, indent=2))
    return 0


def cmd_tail(args: argparse.Namespace) -> int:
    uuid, path = resolve(args.query)
    kinds = {"USER", "ASSISTANT"} if not args.all else None
    buf: list[tuple[str, str, str]] = []
    for _, ev in iter_events(path, tail_bytes=args.tail_bytes):
        c = classify(ev)
        if not c:
            continue
        kind, txt = c
        if kinds and kind not in kinds:
            continue
        buf.append((ev.get("timestamp", ""), kind, txt))
    for ts, kind, txt in buf[-args.count :]:
        print(f"\n===== {ts} [{kind}] =====\n{txt[: args.max_chars]}")
    if not buf:
        print("no messages found in scanned tail; raise --tail-bytes", file=sys.stderr)
    return 0


def cmd_extract(args: argparse.Namespace) -> int:
    uuid, path = resolve(args.query)
    out = Path(args.out)
    out.mkdir(parents=True, exist_ok=True)
    files = {
        "user": (out / "user_messages.txt").open("w"),
        "assistant": (out / "assistant_messages.txt").open("w"),
        "tools": (out / "tool_calls.txt").open("w"),
        "compacted": (out / "compaction_summaries.txt").open("w"),
        "meta": (out / "session_meta_and_goals.txt").open("w"),
        "all": (out / "transcript.txt").open("w") if args.transcript else None,
    }
    counts: dict[str, int] = {}
    started = args.since_line is None
    for n, ev in iter_events(path):
        if not started:
            if n < args.since_line:
                continue
            started = True
        c = classify(ev)
        if not c:
            continue
        kind, txt = c
        ts = ev.get("timestamp", "")
        counts[kind] = counts.get(kind, 0) + 1
        block = f"\n##### L{n} {ts} [{kind}]\n{txt[: args.max_chars]}\n"
        if kind == "USER":
            files["user"].write(block)
        elif kind == "ASSISTANT":
            files["assistant"].write(block)
        elif kind.startswith("CALL") or kind == "OUTPUT":
            files["tools"].write(block)
        elif kind == "COMPACTED":
            files["compacted"].write(block)
        elif kind in ("SESSION_META", "GOAL"):
            files["meta"].write(block)
        if files["all"] is not None and kind != "OUTPUT" or (files["all"] is not None and args.transcript_outputs):
            files["all"].write(block)
    for fh in files.values():
        if fh:
            fh.close()
    summary = {"uuid": uuid, "rollout": str(path), "out": str(out), "counts": counts}
    (out / "extract_summary.json").write_text(json.dumps(summary, indent=2))
    print(json.dumps(summary, indent=2))
    return 0


def git_state(cwd: Path | None) -> dict[str, Any]:
    if not cwd or not cwd.exists() or not shutil.which("git"):
        return {}
    probe = subprocess.run(["git", "-C", str(cwd), "rev-parse", "--is-inside-work-tree"], capture_output=True, text=True)
    if probe.stdout.strip() != "true":
        return {}
    def run(*cmd: str) -> str:
        try:
            return subprocess.run(["git", "-C", str(cwd), *cmd], capture_output=True, text=True, timeout=30).stdout.strip()
        except Exception as exc:  # pragma: no cover
            return f"error: {exc}"
    return {
        "branch": run("rev-parse", "--abbrev-ref", "HEAD"),
        "head": run("log", "-1", "--format=%h %ad %s", "--date=short"),
        "status_short": run("status", "--short")[:4000],
        "recent": run("log", "-8", "--format=%h %ad %s", "--date=short"),
    }


def cmd_handoff(args: argparse.Namespace) -> int:
    uuid, path = resolve(args.query)
    users: list[tuple[str, str]] = []
    assistants: list[tuple[str, str]] = []
    compacted: list[tuple[str, str]] = []
    meta: dict[str, Any] = {}
    goal: str | None = None
    for _, ev in iter_events(path, tail_bytes=args.tail_bytes):
        c = classify(ev)
        if not c:
            continue
        kind, txt = c
        ts = ev.get("timestamp", "")
        if kind == "USER":
            users.append((ts, txt))
        elif kind == "ASSISTANT":
            assistants.append((ts, txt))
        elif kind == "COMPACTED":
            compacted.append((ts, txt))
        elif kind == "SESSION_META":
            meta = json.loads(txt)
        elif kind == "GOAL":
            goal = txt
    cwd = Path(meta.get("cwd")) if meta.get("cwd") else (Path(args.cwd) if args.cwd else None)
    name = next((r.get("thread_name") for r in reversed(read_index()) if r.get("id") == uuid), None)
    now = _dt.datetime.now(_dt.timezone.utc).strftime("%Y-%m-%d %H:%M UTC")
    lines = [
        f"# Codex Session Handoff: {name or uuid}",
        "",
        f"Generated: {now}",
        f"Thread: `{uuid}`" + (f" (forked from `{meta.get('forked_from_id')}`)" if meta.get("forked_from_id") else ""),
        f"Rollout: `{path}` ({path.stat().st_size / 1e6:.1f} MB)",
        f"Owners at generation time: `{owners(path) or 'none'}`",
        f"Workspace: `{cwd}`" if cwd else "Workspace: unknown",
        "",
        "## Objective",
        "",
        (goal or "_fill in: what this session is for_"),
        "",
        "## Last user requests (newest last)",
        "",
    ]
    for ts, txt in users[-args.user_count :]:
        lines.append(f"- `{ts}` {txt.strip()[: args.max_chars].replace(chr(10), ' ')}")
    lines += ["", "## Last assistant report", ""]
    if assistants:
        ts, txt = assistants[-1]
        lines += [f"`{ts}`", "", txt.strip()[: args.max_chars * 4]]
    else:
        lines.append("_none in scanned tail_")
    if compacted and args.include_compaction:
        ts, txt = compacted[-1]
        lines += ["", "## Last compaction summary (raw, private)", "", "```", txt[: args.max_chars * 6], "```"]
    gs = git_state(cwd)
    if gs:
        lines += ["", "## Repository state", "", f"- branch: `{gs['branch']}`", f"- HEAD: `{gs['head']}`", "", "Recent commits:", "", "```", gs["recent"], "```", "", "Uncommitted:", "", "```", gs["status_short"] or "(clean)", "```"]
    lines += [
        "",
        "## Verified facts",
        "",
        "_fill in: only what you re-checked on disk or by running commands_",
        "",
        "## Open work / next actions",
        "",
        "_fill in_",
        "",
        "## Ownership and stop conditions",
        "",
        "- The original Codex thread stays the archive; do not write to its rollout.",
        "- Record which agent (Codex thread, Claude Code session) owns each next action.",
        "",
        "## Private context",
        "",
        "- Raw rollout and extracted transcripts are private; keep them out of Git.",
    ]
    text = "\n".join(lines) + "\n"
    if args.out:
        Path(args.out).parent.mkdir(parents=True, exist_ok=True)
        Path(args.out).write_text(text)
        print(args.out)
    else:
        print(text)
    return 0


def quota_probe_path() -> Path | None:
    env = os.environ.get("CODEX_QUOTA_PROBE")
    if env and Path(env).exists():
        return Path(env)
    for cand in QUOTA_PROBE_CANDIDATES:
        if cand.exists():
            return cand
    return None


def read_quota(mode: str = "status") -> dict[str, Any]:
    probe = quota_probe_path()
    if probe is None:
        return {"ok": False, "error": "quota probe script not found; set CODEX_QUOTA_PROBE"}
    try:
        out = subprocess.run([sys.executable, str(probe), mode, "--json"], capture_output=True, text=True, timeout=90)
        return json.loads(out.stdout)
    except Exception as exc:
        return {"ok": False, "error": str(exc)}


def cmd_quota(args: argparse.Namespace) -> int:
    data = read_quota("probe" if args.probe else "status")
    print(json.dumps(data, indent=2))
    return 0 if data.get("ok") else 1


def quota_gate(min_percent: float, *, skip: bool) -> None:
    if skip:
        return
    q = read_quota("status")
    rem = q.get("remaining_percent")
    if not q.get("ok"):
        raise SystemExit(f"refusing to spend Codex quota: probe failed: {q.get('error')} (use --skip-quota-check to override)")
    if rem is not None and rem < min_percent:
        raise SystemExit(
            f"refusing to launch Codex: remaining quota {rem}% < {min_percent}% "
            f"(resets_at={q.get('window', {}).get('resets_at')}). Use --skip-quota-check to override."
        )


def cmd_delegate(args: argparse.Namespace) -> int:
    quota_gate(args.min_quota_percent, skip=args.skip_quota_check)
    if not shutil.which("codex"):
        raise SystemExit("codex CLI not on PATH")
    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    stamp = _dt.datetime.now(_dt.timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    last_msg = out_dir / f"codex-last-message-{stamp}.md"
    events = out_dir / f"codex-events-{stamp}.jsonl"
    cmd = ["codex", "exec"]
    if args.resume:
        cmd += ["resume", args.resume]
    cmd += ["--json", "-o", str(last_msg), "-C", args.cwd, "-s", args.sandbox]
    if args.model:
        cmd += ["-m", args.model]
    if args.effort:
        cmd += ["-c", f'model_reasoning_effort="{args.effort}"']
    if args.full_auto:
        cmd += ["--dangerously-bypass-approvals-and-sandbox"]
    for img in args.image or []:
        cmd += ["-i", img]
    prompt = args.prompt
    if prompt == "-":
        prompt = sys.stdin.read()
    if args.prompt_file:
        prompt = Path(args.prompt_file).read_text()
    cmd.append(prompt)
    if args.dry_run:
        print(json.dumps({"dry_run": True, "cmd": cmd, "last_message": str(last_msg), "events": str(events)}, indent=2))
        return 0
    with events.open("w") as fh:
        proc = subprocess.run(cmd, stdout=fh, stderr=subprocess.PIPE, text=True, timeout=args.timeout)
    result = {
        "returncode": proc.returncode,
        "last_message_file": str(last_msg),
        "last_message": last_msg.read_text() if last_msg.exists() else None,
        "events_file": str(events),
        "stderr_tail": proc.stderr[-2000:],
    }
    print(json.dumps(result, indent=2))
    return proc.returncode


def cmd_queue(args: argparse.Namespace) -> int:
    quota_gate(args.min_quota_percent, skip=args.skip_quota_check)
    cmd = ["codex", "queue", "--thread", args.thread, "--message", args.message]
    for img in args.image or []:
        cmd += ["-i", img]
    if args.dry_run:
        print(json.dumps({"dry_run": True, "cmd": cmd}))
        return 0
    return subprocess.run(cmd).returncode


# ----------------------------------------------------------------------------- main

def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)

    p = sub.add_parser("list", help="recent named sessions")
    p.add_argument("--limit", type=int, default=20)
    p.add_argument("--owners", action="store_true", help="also report PIDs holding each rollout open (slower)")
    p.add_argument("--json", action="store_true")
    p.set_defaults(fn=cmd_list)

    p = sub.add_parser("find", help="resolve name/UUID to rollout path and metadata")
    p.add_argument("query")
    p.set_defaults(fn=cmd_find)

    p = sub.add_parser("tail", help="last N messages of a session")
    p.add_argument("query")
    p.add_argument("-n", "--count", type=int, default=12)
    p.add_argument("--tail-bytes", type=int, default=64 * 1024 * 1024, help="scan only the last N bytes (default 64 MB); 0 = whole file")
    p.add_argument("--all", action="store_true", help="include tool calls, outputs, reasoning summaries")
    p.add_argument("--max-chars", type=int, default=3000)
    p.set_defaults(fn=cmd_tail)

    p = sub.add_parser("extract", help="dump session events to text files (whole file)")
    p.add_argument("query")
    p.add_argument("--out", required=True)
    p.add_argument("--since-line", type=int, default=None, help="start at this rollout line number (e.g. the fork point)")
    p.add_argument("--max-chars", type=int, default=6000)
    p.add_argument("--transcript", action="store_true", help="also write one merged transcript.txt")
    p.add_argument("--transcript-outputs", action="store_true", help="include tool outputs in transcript.txt")
    p.set_defaults(fn=cmd_extract)

    p = sub.add_parser("handoff", help="write a handoff packet skeleton")
    p.add_argument("query")
    p.add_argument("--out")
    p.add_argument("--cwd", help="workspace override when session_meta is outside the scanned tail")
    p.add_argument("--tail-bytes", type=int, default=256 * 1024 * 1024)
    p.add_argument("--user-count", type=int, default=15)
    p.add_argument("--max-chars", type=int, default=1200)
    p.add_argument("--include-compaction", action="store_true")
    p.set_defaults(fn=cmd_handoff)

    p = sub.add_parser("quota", help="Codex quota (cached by default; --probe queries the app server)")
    p.add_argument("--probe", action="store_true")
    p.set_defaults(fn=cmd_quota)

    p = sub.add_parser("delegate", help="run a bounded codex exec task (spends quota)")
    p.add_argument("prompt", help="prompt text, or '-' for stdin")
    p.add_argument("--prompt-file")
    p.add_argument("--cwd", default=os.getcwd())
    p.add_argument("--resume", help="session UUID or thread name to continue instead of starting fresh")
    p.add_argument("--model")
    p.add_argument("--effort", choices=["minimal", "low", "medium", "high", "xhigh"])
    p.add_argument("--sandbox", default="workspace-write", choices=["read-only", "workspace-write", "danger-full-access"])
    p.add_argument("--full-auto", action="store_true", help="pass --dangerously-bypass-approvals-and-sandbox")
    p.add_argument("--image", action="append")
    p.add_argument("--out-dir", default=str(Path.home() / ".codex" / "handoffs" / "delegations"))
    p.add_argument("--timeout", type=int, default=3600)
    p.add_argument("--min-quota-percent", type=float, default=5.0)
    p.add_argument("--skip-quota-check", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_delegate)

    p = sub.add_parser("queue", help="queue a message into a live interactive session")
    p.add_argument("--thread", required=True)
    p.add_argument("--message", required=True)
    p.add_argument("--image", action="append")
    p.add_argument("--min-quota-percent", type=float, default=5.0)
    p.add_argument("--skip-quota-check", action="store_true")
    p.add_argument("--dry-run", action="store_true")
    p.set_defaults(fn=cmd_queue)

    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
