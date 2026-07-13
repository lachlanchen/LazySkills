#!/usr/bin/env python3
"""Diagnose and recover stalled Codex sessions without editing Codex state.

The mutating paths use ``codex app-server --disable hooks --stdio``.  This
tool never rewrites rollout JSONL or SQLite state.  It intentionally uses only
the Python standard library plus the installed ``codex`` binary; ``zstd`` is
used when available for compact verified backups.
"""

from __future__ import annotations

import argparse
import collections
import contextlib
import datetime as dt
import gzip
import hashlib
import json
import os
import queue
import re
import signal
import shutil
import sqlite3
import stat as stat_module
import subprocess
import sys
import tempfile
import threading
import time
import uuid
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Callable, Iterable


EXIT_OK = 0
EXIT_USAGE_OR_NOT_FOUND = 2
EXIT_BUSY = 3
EXIT_BACKUP = 4
EXIT_PROTOCOL = 5
EXIT_TIMEOUT = 6
EXIT_PROBE = 7
EXIT_UNSUPPORTED = 8

SAFE_THREAD_COLUMNS = (
    "id",
    "rollout_path",
    "cwd",
    "model",
    "reasoning_effort",
    "tokens_used",
    "updated_at",
    "archived",
    "history_mode",
)
MUTATION_CONFIRMATION = "--yes"
EFFORTS = ("none", "minimal", "low", "medium", "high", "xhigh", "ultra")
CANARY_ALLOWED_ITEM_TYPES = {
    "agentMessage",
    "contextCompaction",
    "reasoning",
    "plan",
    "userMessage",
}


class RecoveryError(RuntimeError):
    """Expected operational failure with a stable process exit code."""

    def __init__(
        self,
        message: str,
        exit_code: int = EXIT_PROTOCOL,
        details: dict[str, Any] | None = None,
    ) -> None:
        super().__init__(message)
        self.exit_code = exit_code
        self.details = details or {}


class ProtocolTimeout(RecoveryError):
    def __init__(self, message: str) -> None:
        super().__init__(message, EXIT_TIMEOUT)


@dataclass(frozen=True)
class Owner:
    pid: int
    process: str


@dataclass(frozen=True)
class OwnerCheck:
    verified: bool
    method: str
    owners: tuple[Owner, ...]


@dataclass(frozen=True)
class SessionRecord:
    session_id: str
    rollout_path: Path
    state_db: Path | None
    metadata: dict[str, Any]


def utc_now() -> str:
    return dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()


def validate_session_id(value: str) -> str:
    try:
        return str(uuid.UUID(value))
    except (ValueError, AttributeError) as exc:
        raise argparse.ArgumentTypeError("session id must be a UUID") from exc


def json_safe(value: Any) -> Any:
    if isinstance(value, Path):
        return str(value)
    if isinstance(value, tuple):
        return [json_safe(item) for item in value]
    if isinstance(value, list):
        return [json_safe(item) for item in value]
    if isinstance(value, dict):
        return {str(key): json_safe(item) for key, item in value.items()}
    if hasattr(value, "__dataclass_fields__"):
        return json_safe(asdict(value))
    return value


def emit(payload: dict[str, Any], as_json: bool) -> None:
    safe = json_safe(payload)
    if as_json:
        print(json.dumps(safe, ensure_ascii=False, indent=2, sort_keys=True))
        return
    for key, value in safe.items():
        if isinstance(value, (dict, list)):
            rendered = json.dumps(value, ensure_ascii=False, sort_keys=True)
        else:
            rendered = str(value)
        print(f"{key}: {rendered}")


def progress(message: str, quiet: bool = False) -> None:
    if not quiet:
        print(message, file=sys.stderr, flush=True)


def redact_text(value: str) -> str:
    """Bound diagnostic text and redact common credential-shaped values."""
    text = value[:2000]
    substitutions = (
        (r"(?i)(authorization\s*[:=]\s*bearer\s+)[^\s,;]+", r"\1[REDACTED]"),
        (r"\bsk-[A-Za-z0-9_-]{8,}\b", "[REDACTED_OPENAI_KEY]"),
        (r"(?i)((?:api[_-]?key|token|secret|password)\s*[:=]\s*)[^\s,;]+", r"\1[REDACTED]"),
    )
    for pattern, replacement in substitutions:
        text = re.sub(pattern, replacement, text)
    return text


def state_db_sort_key(path: Path) -> tuple[int, int]:
    match = re.search(r"state_(\d+)\.sqlite$", path.name)
    version = int(match.group(1)) if match else -1
    try:
        modified = path.stat().st_mtime_ns
    except OSError:
        modified = 0
    return version, modified


def state_databases(codex_home: Path) -> list[Path]:
    return sorted(codex_home.glob("state_*.sqlite"), key=state_db_sort_key, reverse=True)


def read_thread_row(db_path: Path, session_id: str) -> dict[str, Any] | None:
    try:
        connection = sqlite3.connect(f"{db_path.as_uri()}?mode=ro", uri=True, timeout=3)
    except (sqlite3.Error, ValueError):
        return None
    connection.row_factory = sqlite3.Row
    try:
        columns = {
            str(row[1])
            for row in connection.execute("PRAGMA table_info(threads)").fetchall()
        }
        selected = [column for column in SAFE_THREAD_COLUMNS if column in columns]
        if "id" not in selected or "rollout_path" not in selected:
            return None
        query = f"SELECT {', '.join(selected)} FROM threads WHERE id = ?"
        row = connection.execute(query, (session_id,)).fetchone()
        return dict(row) if row is not None else None
    except sqlite3.Error:
        return None
    finally:
        connection.close()


def fallback_rollouts(codex_home: Path, session_id: str) -> list[Path]:
    roots = [
        codex_home / "sessions",
        codex_home / "archived_sessions",
        codex_home / "archive",
    ]
    found: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        found.extend(path for path in root.rglob(f"*{session_id}*.jsonl") if path.is_file())
    return sorted(set(path.absolute() for path in found))


def locate_session(codex_home: Path, session_id: str) -> SessionRecord:
    for db_path in state_databases(codex_home):
        row = read_thread_row(db_path, session_id)
        if row is None:
            continue
        raw_path = str(row.get("rollout_path") or "")
        rollout = Path(raw_path).expanduser()
        if rollout.is_symlink():
            raise RecoveryError(
                f"rollout path is a symlink and is unsafe to recover: {rollout}",
                EXIT_USAGE_OR_NOT_FOUND,
            )
        if rollout.is_file():
            metadata = {key: value for key, value in row.items() if key != "rollout_path"}
            return SessionRecord(session_id, rollout.absolute(), db_path.resolve(), metadata)

    matches = fallback_rollouts(codex_home, session_id)
    if not matches:
        raise RecoveryError(
            f"session {session_id} was not found under {codex_home}",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    if len(matches) > 1:
        rendered = ", ".join(str(path) for path in matches)
        raise RecoveryError(
            f"session {session_id} has multiple rollout candidates: {rendered}",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    if matches[0].is_symlink():
        raise RecoveryError(
            f"rollout path is a symlink and is unsafe to recover: {matches[0]}",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    return SessionRecord(session_id, matches[0].absolute(), None, {})


def path_has_symlink_component(path: Path) -> bool:
    current = Path(path.anchor)
    for part in path.absolute().parts[1:]:
        current = current / part
        if current.is_symlink():
            return True
    return False


def validate_mutable_rollout(record: SessionRecord, codex_home: Path) -> os.stat_result:
    """Fail closed unless the rollout is a normal active-session artifact."""
    if path_has_symlink_component(record.rollout_path):
        raise RecoveryError("rollout path contains a symlink component", EXIT_USAGE_OR_NOT_FOUND)
    sessions_root = (codex_home / "sessions").resolve()
    rollout = record.rollout_path.resolve()
    active_matches = [
        path
        for path in fallback_rollouts(codex_home, record.session_id)
        if path.absolute().is_relative_to(sessions_root)
    ]
    if (
        len(active_matches) != 1
        or path_has_symlink_component(active_matches[0])
        or active_matches[0].resolve() != rollout
    ):
        raise RecoveryError(
            "session UUID does not resolve to exactly one canonical active rollout",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    if not rollout.is_relative_to(sessions_root):
        raise RecoveryError(
            f"refusing to mutate a rollout outside the active sessions directory: {rollout}",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    if not rollout.name.endswith(f"-{record.session_id}.jsonl"):
        raise RecoveryError(
            f"rollout filename does not match the exact session UUID: {rollout.name}",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    file_stat = rollout.stat()
    if not stat_module.S_ISREG(file_stat.st_mode):
        raise RecoveryError(f"rollout is not a regular file: {rollout}", EXIT_USAGE_OR_NOT_FOUND)
    if file_stat.st_nlink != 1:
        raise RecoveryError(
            f"rollout has {file_stat.st_nlink} hard links; refusing mutation",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    if hasattr(os, "getuid") and file_stat.st_uid != os.getuid():
        raise RecoveryError("rollout is owned by a different user", EXIT_USAGE_OR_NOT_FOUND)
    tail = tail_summary(rollout)
    if not tail["newlineComplete"] or not tail["lastRecordParsed"] or tail["invalidTailRecords"]:
        raise RecoveryError(
            "rollout tail is incomplete, too large to validate safely, or invalid JSON; "
            "do not compact it automatically",
            EXIT_USAGE_OR_NOT_FOUND,
        )
    if record.metadata.get("archived") not in (None, 0, False):
        raise RecoveryError("thread is archived; unarchive it through Codex first", EXIT_USAGE_OR_NOT_FOUND)
    return file_stat


@contextlib.contextmanager
def session_lock(codex_home: Path, session_id: str) -> Iterable[Path]:
    """Take a private advisory lock used by cooperating recovery processes."""
    lock_root = codex_home / "session-recovery-locks"
    lock_root.mkdir(parents=True, exist_ok=True)
    try:
        lock_root.chmod(0o700)
    except OSError:
        pass
    lock_path = lock_root / f"{session_id}.lock"
    flags = os.O_CREAT | os.O_RDWR
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(lock_path, flags, 0o600)
    except OSError as exc:
        raise RecoveryError(f"cannot create private session lock: {exc}", EXIT_BUSY) from exc
    handle = os.fdopen(descriptor, "a+b")
    try:
        lock_path.chmod(0o600)
    except OSError:
        pass
    try:
        if os.name == "posix":
            import fcntl

            try:
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as exc:
                raise RecoveryError("another recovery process holds the session lock", EXIT_BUSY) from exc
        else:
            raise RecoveryError(
                "automatic mutation is unsupported without a verified per-session lock on this platform",
                EXIT_UNSUPPORTED,
            )
        yield lock_path
    finally:
        if os.name == "posix":
            try:
                import fcntl

                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
            except OSError:
                pass
        handle.close()


def linux_rollout_owners(path: Path) -> OwnerCheck:
    proc = Path("/proc")
    if not proc.is_dir():
        return OwnerCheck(False, "linux-procfs-unavailable", ())
    try:
        target_stat = path.stat()
    except OSError as exc:
        raise RecoveryError(f"cannot stat rollout {path}: {exc}", EXIT_USAGE_OR_NOT_FOUND) from exc

    owners: dict[int, Owner] = {}
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        pid = int(entry.name)
        if pid == os.getpid():
            continue
        fd_dir = entry / "fd"
        try:
            descriptors = list(fd_dir.iterdir())
        except (OSError, PermissionError):
            continue
        matched = False
        for descriptor in descriptors:
            try:
                opened = descriptor.stat()
            except (OSError, PermissionError):
                continue
            if opened.st_dev == target_stat.st_dev and opened.st_ino == target_stat.st_ino:
                matched = True
                break
        if not matched:
            continue
        try:
            process = (entry / "comm").read_text(encoding="utf-8", errors="replace").strip()
        except OSError:
            process = "unknown"
        owners[pid] = Owner(pid, process[:128])
    return OwnerCheck(True, "linux-procfs-fd-inode", tuple(owners[pid] for pid in sorted(owners)))


def lsof_rollout_owners(path: Path) -> OwnerCheck:
    lsof = shutil.which("lsof")
    if not lsof:
        return OwnerCheck(False, "lsof-unavailable", ())
    result = subprocess.run(
        [lsof, "-Fpc", "--", str(path)],
        stdout=subprocess.PIPE,
        stderr=subprocess.DEVNULL,
        text=True,
        check=False,
    )
    if result.returncode not in (0, 1):
        return OwnerCheck(False, f"lsof-exit-{result.returncode}", ())
    owners: list[Owner] = []
    current_pid: int | None = None
    current_name = "unknown"
    for line in result.stdout.splitlines():
        if line.startswith("p") and line[1:].isdigit():
            if current_pid is not None and current_pid != os.getpid():
                owners.append(Owner(current_pid, current_name[:128]))
            current_pid = int(line[1:])
            current_name = "unknown"
        elif line.startswith("c"):
            current_name = line[1:] or "unknown"
    if current_pid is not None and current_pid != os.getpid():
        owners.append(Owner(current_pid, current_name[:128]))
    return OwnerCheck(True, "lsof", tuple(owners))


def rollout_owners(path: Path) -> OwnerCheck:
    lsof_check = lsof_rollout_owners(path)
    if lsof_check.verified:
        return lsof_check
    if sys.platform.startswith("linux"):
        return linux_rollout_owners(path)
    return lsof_check


def assert_idle(path: Path) -> OwnerCheck:
    check = rollout_owners(path)
    if check.owners:
        details = ", ".join(f"pid={owner.pid} ({owner.process})" for owner in check.owners)
        raise RecoveryError(
            f"rollout is open by another process: {details}; stop or detach that session first",
            EXIT_BUSY,
        )
    if not check.verified:
        raise RecoveryError(
            "could not verify rollout ownership on this platform; use inspect and perform "
            "manual Codex /compact recovery instead",
            EXIT_BUSY,
        )
    return check


def process_tree_pids(root_pid: int) -> set[int]:
    """Return a best-effort process tree rooted at a tool-owned PID."""
    if not sys.platform.startswith("linux"):
        return {root_pid}
    parents: dict[int, int] = {}
    proc = Path("/proc")
    for entry in proc.iterdir():
        if not entry.name.isdigit():
            continue
        try:
            status = (entry / "status").read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        match = re.search(r"^PPid:\s+(\d+)$", status, flags=re.M)
        if match:
            parents[int(entry.name)] = int(match.group(1))
    owned = {root_pid}
    changed = True
    while changed:
        changed = False
        for pid, parent in parents.items():
            if parent in owned and pid not in owned:
                owned.add(pid)
                changed = True
    return owned


def assert_only_tool_owners(path: Path, root_pid: int) -> OwnerCheck:
    check = rollout_owners(path)
    if not check.verified:
        raise RecoveryError("could not re-verify rollout ownership after resume", EXIT_BUSY)
    allowed = process_tree_pids(root_pid)
    unexpected = [owner for owner in check.owners if owner.pid not in allowed]
    if unexpected:
        details = ", ".join(f"pid={owner.pid} ({owner.process})" for owner in unexpected)
        raise RecoveryError(
            f"another process opened the rollout during recovery: {details}",
            EXIT_BUSY,
        )
    return check


def read_tail_lines(path: Path, line_limit: int = 200, byte_limit: int = 8 * 1024 * 1024) -> list[bytes]:
    size = path.stat().st_size
    if size == 0:
        return []
    data = b""
    with path.open("rb") as handle:
        position = size
        while position > 0 and data.count(b"\n") <= line_limit and len(data) < byte_limit:
            amount = min(256 * 1024, position, byte_limit - len(data))
            position -= amount
            handle.seek(position)
            data = handle.read(amount) + data
    lines = data.splitlines()
    if position > 0 and lines:
        lines = lines[1:]
    return lines[-line_limit:]


def tail_summary(path: Path) -> dict[str, Any]:
    lines = read_tail_lines(path)
    last_record: dict[str, Any] | None = None
    invalid_tail_records = 0
    final_record_is_object = False
    latest_token_info: dict[str, Any] | None = None
    latest_events: list[str] = []
    for index, raw in enumerate(lines):
        try:
            record = json.loads(raw)
        except (json.JSONDecodeError, UnicodeDecodeError):
            invalid_tail_records += 1
            continue
        if isinstance(record, dict):
            last_record = record
            if index == len(lines) - 1:
                final_record_is_object = True
            if record.get("type") == "event_msg":
                payload = record.get("payload") or {}
                event_type = payload.get("type")
                if isinstance(event_type, str):
                    latest_events.append(event_type)
                if event_type == "token_count" and isinstance(payload.get("info"), dict):
                    latest_token_info = payload["info"]
    size = path.stat().st_size
    if size:
        with path.open("rb") as handle:
            handle.seek(-1, os.SEEK_END)
            newline_complete = handle.read(1) == b"\n"
    else:
        newline_complete = False
    last_payload = (last_record or {}).get("payload") or {}
    return {
        "newlineComplete": newline_complete,
        "lastRecordParsed": final_record_is_object,
        "invalidTailRecords": invalid_tail_records,
        "lastTimestamp": (last_record or {}).get("timestamp"),
        "lastRecordType": (last_record or {}).get("type"),
        "lastEventType": last_payload.get("type") if isinstance(last_payload, dict) else None,
        "recentEventTypes": latest_events[-12:],
        "latestTokenInfo": latest_token_info,
    }


def scan_rollout(path: Path) -> dict[str, Any]:
    patterns = {
        "inlineDataImageOccurrences": b"data:image",
        "compactionRecords": b'"type":"compacted"',
        "abortedTurns": b'"type":"turn_aborted"',
    }
    counts = {name: 0 for name in patterns}
    max_pattern = max(len(pattern) for pattern in patterns.values())
    buffer = b""
    newlines = 0
    total_bytes = 0
    with path.open("rb") as handle:
        while True:
            chunk = handle.read(8 * 1024 * 1024)
            if not chunk:
                break
            total_bytes += len(chunk)
            newlines += chunk.count(b"\n")
            buffer += chunk
            safe_start_limit = max(0, len(buffer) - max_pattern + 1)
            for name, pattern in patterns.items():
                start = 0
                while True:
                    index = buffer.find(pattern, start)
                    if index < 0 or index >= safe_start_limit:
                        break
                    counts[name] += 1
                    start = index + len(pattern)
            buffer = buffer[safe_start_limit:]
    for name, pattern in patterns.items():
        counts[name] += buffer.count(pattern)
    line_count = newlines
    if total_bytes and not tail_summary(path)["newlineComplete"]:
        line_count += 1
    return {
        "lineCount": line_count,
        "streamedBytes": total_bytes,
        "countMethod": "streamed-byte-patterns",
        **counts,
    }


def directory_size(path: Path) -> tuple[int, int]:
    files = 0
    total = 0
    if not path.is_dir():
        return files, total
    for item in path.rglob("*"):
        if not item.is_file():
            continue
        try:
            total += item.stat().st_size
            files += 1
        except OSError:
            continue
    return files, total


def codex_version(codex_bin: str) -> str | None:
    try:
        result = subprocess.run(
            [codex_bin, "--version"],
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            text=True,
            timeout=15,
            check=False,
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    output = result.stdout.strip()
    return output or None


def inspect_session(
    record: SessionRecord,
    codex_home: Path,
    codex_bin: str,
    scan: bool,
) -> dict[str, Any]:
    stat = record.rollout_path.stat()
    owner_check = rollout_owners(record.rollout_path)
    generated_dir = codex_home / "generated_images" / record.session_id
    generated_files, generated_bytes = directory_size(generated_dir)
    result: dict[str, Any] = {
        "ok": True,
        "operation": "inspect",
        "sessionId": record.session_id,
        "codexVersion": codex_version(codex_bin),
        "rolloutPath": record.rollout_path,
        "rolloutBytes": stat.st_size,
        "rolloutModifiedNs": stat.st_mtime_ns,
        "stateDatabase": record.state_db,
        "thread": record.metadata,
        "ownership": owner_check,
        "generatedImages": {"path": generated_dir, "files": generated_files, "bytes": generated_bytes},
        "tail": tail_summary(record.rollout_path),
    }
    if scan:
        result["scan"] = scan_rollout(record.rollout_path)
    return result


def sha256_stream(stream: Any) -> tuple[str, int]:
    digest = hashlib.sha256()
    total = 0
    while True:
        chunk = stream.read(8 * 1024 * 1024)
        if not chunk:
            break
        digest.update(chunk)
        total += len(chunk)
    return digest.hexdigest(), total


def sha256_file(path: Path) -> str:
    with path.open("rb") as handle:
        digest, _ = sha256_stream(handle)
    return digest


def decompressed_sha256(path: Path, compression: str) -> tuple[str, int]:
    if compression == "zstd":
        zstd = shutil.which("zstd")
        if not zstd:
            raise RecoveryError("zstd is required to verify this backup", EXIT_BACKUP)
        process = subprocess.Popen(
            [zstd, "-q", "-d", "-c", str(path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert process.stdout is not None
        actual_sha, actual_size = sha256_stream(process.stdout)
        _, stderr = process.communicate()
        if process.returncode != 0:
            detail = redact_text(stderr.decode(errors="replace").strip())[:300]
            raise RecoveryError(f"zstd decompression failed: {detail}", EXIT_BACKUP)
        return actual_sha, actual_size
    if compression == "gzip":
        with gzip.open(path, "rb") as stream:
            return sha256_stream(stream)
    raise RecoveryError(f"unsupported backup compression: {compression!r}", EXIT_BACKUP)


def secure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=False)
    try:
        path.chmod(0o700)
    except OSError as exc:
        raise RecoveryError(f"cannot make backup directory private: {exc}", EXIT_BACKUP) from exc
    if stat_module.S_IMODE(path.stat().st_mode) & 0o077:
        raise RecoveryError(f"backup directory is not private: {path}", EXIT_BACKUP)


def require_private_file(path: Path) -> None:
    try:
        path.chmod(0o600)
    except OSError as exc:
        raise RecoveryError(f"cannot make private file mode 0600 for {path}: {exc}", EXIT_BACKUP) from exc
    if stat_module.S_IMODE(path.stat().st_mode) & 0o077:
        raise RecoveryError(f"private file has permissive mode: {path}", EXIT_BACKUP)


def default_backup_parent(codex_home: Path, session_id: str) -> Path:
    stamp = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return codex_home / "session-recovery-backups" / session_id / stamp


def git_worktree_ancestor(path: Path) -> Path | None:
    candidate = path if path.exists() and path.is_dir() else path.parent
    for ancestor in (candidate, *candidate.parents):
        if (ancestor / ".git").exists():
            return ancestor
    return None


def write_json_secure(path: Path, payload: dict[str, Any]) -> None:
    temporary = path.with_name(path.name + ".part")
    with temporary.open("x", encoding="utf-8") as handle:
        handle.write(json.dumps(json_safe(payload), ensure_ascii=False, indent=2) + "\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(temporary, path)
    require_private_file(path)


def fsync_file(path: Path) -> None:
    with path.open("rb") as handle:
        os.fsync(handle.fileno())


def fsync_directory(path: Path) -> None:
    if os.name != "posix":
        return
    descriptor = os.open(path, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def backup_rollout(
    record: SessionRecord,
    codex_home: Path,
    codex_bin: str,
    output_dir: Path | None,
    quiet: bool,
) -> dict[str, Any]:
    owner_check = assert_idle(record.rollout_path)
    destination = (output_dir or default_backup_parent(codex_home, record.session_id)).expanduser().resolve()
    if destination.exists():
        raise RecoveryError(f"backup destination already exists: {destination}", EXIT_BACKUP)
    worktree = git_worktree_ancestor(destination)
    if worktree is not None:
        raise RecoveryError(
            f"refusing to place a private raw-session backup inside Git worktree {worktree}",
            EXIT_BACKUP,
        )
    destination.parent.mkdir(parents=True, exist_ok=True)
    secure_directory(destination)

    before = record.rollout_path.stat()
    free = shutil.disk_usage(destination).free
    required = before.st_size + 128 * 1024 * 1024
    if free < required:
        raise RecoveryError(
            f"not enough free space for a conservative backup: need {required}, have {free}",
            EXIT_BACKUP,
        )

    progress("Computing source SHA-256...", quiet)
    source_sha = sha256_file(record.rollout_path)
    zstd = shutil.which("zstd")
    if zstd:
        compression = "zstd"
        backup_name = "rollout-original.jsonl.zst"
    else:
        compression = "gzip"
        backup_name = "rollout-original.jsonl.gz"
    backup_path = destination / backup_name
    partial_path = destination / (backup_name + ".part")
    try:
        if zstd:
            progress("Compressing rollout with zstd...", quiet)
            result = subprocess.run(
                [zstd, "-T0", "-3", "-q", "-f", "-o", str(partial_path), str(record.rollout_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if result.returncode != 0:
                raise RecoveryError(f"zstd backup failed: {result.stderr.strip()}", EXIT_BACKUP)
            test = subprocess.run(
                [zstd, "-q", "-t", str(partial_path)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.PIPE,
                text=True,
                check=False,
            )
            if test.returncode != 0:
                raise RecoveryError(f"zstd verification failed: {test.stderr.strip()}", EXIT_BACKUP)
        else:
            progress("zstd is unavailable; compressing rollout with gzip...", quiet)
            with record.rollout_path.open("rb") as source, gzip.open(partial_path, "xb", compresslevel=6) as target:
                shutil.copyfileobj(source, target, length=8 * 1024 * 1024)
            with gzip.open(partial_path, "rb") as check_stream:
                _, verified_bytes = sha256_stream(check_stream)
            if verified_bytes != before.st_size:
                raise RecoveryError("gzip verification produced the wrong byte count", EXIT_BACKUP)
        fsync_file(partial_path)
        os.replace(partial_path, backup_path)
        fsync_directory(destination)
    finally:
        partial_path.unlink(missing_ok=True)

    after = record.rollout_path.stat()
    if (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns) != (
        after.st_dev,
        after.st_ino,
        after.st_size,
        after.st_mtime_ns,
    ):
        backup_path.unlink(missing_ok=True)
        raise RecoveryError(
            "rollout changed while it was being backed up; backup rejected and recovery stopped",
            EXIT_BACKUP,
        )
    require_private_file(backup_path)

    backup_sha = sha256_file(backup_path)
    restored_sha, restored_size = decompressed_sha256(backup_path, compression)
    if restored_sha != source_sha or restored_size != before.st_size:
        raise RecoveryError(
            "decompressed backup does not match the source SHA-256 and byte count",
            EXIT_BACKUP,
        )
    manifest = {
        "schemaVersion": 1,
        "createdAt": utc_now(),
        "sessionId": record.session_id,
        "codexVersion": codex_version(codex_bin),
        "sourcePath": record.rollout_path,
        "sourceSize": before.st_size,
        "sourceMtimeNs": before.st_mtime_ns,
        "sourceDevice": before.st_dev,
        "sourceInode": before.st_ino,
        "sourceSha256": source_sha,
        "compression": compression,
        "backupPath": backup_name,
        "backupSize": backup_path.stat().st_size,
        "backupSha256": backup_sha,
        "ownershipCheck": owner_check,
        "verified": True,
    }
    manifest_path = destination / "manifest.json"
    checksum_path = destination / "source.sha256"
    write_json_secure(manifest_path, manifest)
    checksum_temporary = destination / "source.sha256.part"
    with checksum_temporary.open("x", encoding="utf-8") as handle:
        handle.write(f"{source_sha}  {record.rollout_path.name}\n")
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(checksum_temporary, checksum_path)
    fsync_directory(destination)
    require_private_file(checksum_path)
    return {
        "ok": True,
        "operation": "backup",
        "manifestPath": manifest_path,
        "backupPath": backup_path,
        "sourceSha256": source_sha,
        "sourceBytes": before.st_size,
        "sourceMtimeNs": before.st_mtime_ns,
        "sourceDevice": before.st_dev,
        "sourceInode": before.st_ino,
        "backupBytes": backup_path.stat().st_size,
        "backupSha256": backup_sha,
        "compression": compression,
    }


def verify_backup(manifest_path: Path) -> dict[str, Any]:
    manifest_path = manifest_path.expanduser().absolute()
    if manifest_path.is_symlink():
        raise RecoveryError("backup manifest must not be a symlink", EXIT_BACKUP)
    manifest_path = manifest_path.resolve()
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RecoveryError(f"cannot read backup manifest {manifest_path}: {exc}", EXIT_BACKUP) from exc
    backup_name = str(manifest.get("backupPath") or "")
    if not backup_name or Path(backup_name).name != backup_name or Path(backup_name).is_absolute():
        raise RecoveryError("backup manifest contains an unsafe payload path", EXIT_BACKUP)
    backup_path = (manifest_path.parent / backup_name).resolve()
    if backup_path.parent != manifest_path.parent.resolve():
        raise RecoveryError("backup payload escapes its manifest directory", EXIT_BACKUP)
    expected_sha = str(manifest.get("sourceSha256") or "")
    expected_size = int(manifest.get("sourceSize") or -1)
    expected_backup_sha = str(manifest.get("backupSha256") or "")
    compression = manifest.get("compression")
    raw_backup_path = manifest_path.parent / backup_name
    if raw_backup_path.is_symlink():
        raise RecoveryError("backup payload must not be a symlink", EXIT_BACKUP)
    if not backup_path.is_file() or not expected_sha:
        raise RecoveryError("backup manifest is incomplete or its payload is missing", EXIT_BACKUP)
    actual_backup_sha = sha256_file(backup_path)
    if expected_backup_sha and actual_backup_sha != expected_backup_sha:
        raise RecoveryError("compressed backup SHA-256 mismatch", EXIT_BACKUP)

    actual_sha, actual_size = decompressed_sha256(backup_path, str(compression))

    matches = actual_sha == expected_sha and actual_size == expected_size
    if not matches:
        raise RecoveryError(
            f"backup verification mismatch: sha={actual_sha}, bytes={actual_size}",
            EXIT_BACKUP,
        )
    return {
        "ok": True,
        "operation": "verify-backup",
        "manifestPath": manifest_path,
        "backupPath": backup_path,
        "sha256": actual_sha,
        "backupSha256": actual_backup_sha,
        "bytes": actual_size,
    }


def sha256_prefix(path: Path, byte_count: int) -> str:
    digest = hashlib.sha256()
    remaining = byte_count
    with path.open("rb") as handle:
        while remaining:
            chunk = handle.read(min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise RecoveryError("live rollout became shorter than its backed-up prefix", EXIT_PROTOCOL)
            digest.update(chunk)
            remaining -= len(chunk)
    return digest.hexdigest()


def stable_rollout_snapshot(
    path: Path,
    exit_code: int = EXIT_PROTOCOL,
) -> tuple[os.stat_result, str]:
    """Hash one stable, non-symlink rollout inode and re-attest its path."""
    if path_has_symlink_component(path):
        raise RecoveryError("rollout path contains a symlink component", exit_code)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    try:
        descriptor = os.open(path, flags)
    except OSError as exc:
        raise RecoveryError(f"cannot open rollout for integrity verification: {exc}", exit_code) from exc
    try:
        current = os.fstat(descriptor)
        digest = hashlib.sha256()
        os.lseek(descriptor, 0, os.SEEK_SET)
        remaining = current.st_size
        while remaining:
            chunk = os.read(descriptor, min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise RecoveryError("rollout changed during integrity verification", exit_code)
            digest.update(chunk)
            remaining -= len(chunk)
        verified = os.fstat(descriptor)
        if (
            verified.st_dev,
            verified.st_ino,
            verified.st_size,
            verified.st_mtime_ns,
        ) != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns):
            raise RecoveryError("rollout changed during integrity verification", exit_code)
    finally:
        os.close(descriptor)

    if path_has_symlink_component(path):
        raise RecoveryError("rollout path gained a symlink component", exit_code)
    try:
        path_state = os.lstat(path)
    except OSError as exc:
        raise RecoveryError(f"cannot re-attest rollout path: {exc}", exit_code) from exc
    if stat_module.S_ISLNK(path_state.st_mode) or (
        path_state.st_dev,
        path_state.st_ino,
        path_state.st_size,
        path_state.st_mtime_ns,
    ) != (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns):
        raise RecoveryError("rollout path changed during integrity verification", exit_code)
    return current, digest.hexdigest()


def verify_live_matches_backup(path: Path, backup: dict[str, Any]) -> os.stat_result:
    current, actual_sha = stable_rollout_snapshot(path, EXIT_BACKUP)
    expected = (
        int(backup["sourceDevice"]),
        int(backup["sourceInode"]),
        int(backup["sourceBytes"]),
        int(backup["sourceMtimeNs"]),
    )
    actual = (current.st_dev, current.st_ino, current.st_size, current.st_mtime_ns)
    if actual != expected:
        raise RecoveryError("rollout identity or metadata changed after backup", EXIT_BACKUP)
    if actual_sha != backup["sourceSha256"]:
        raise RecoveryError("live rollout no longer matches the verified backup", EXIT_BACKUP)
    return current


def _append_only_postcheck(
    path: Path,
    before_stat: os.stat_result,
    prefix_sha256: str,
) -> dict[str, Any]:
    if path_has_symlink_component(path):
        raise RecoveryError("rollout path contains a symlink component during postflight", EXIT_PROTOCOL)
    flags = os.O_RDONLY
    if hasattr(os, "O_NOFOLLOW"):
        flags |= os.O_NOFOLLOW
    descriptor = os.open(path, flags)
    try:
        opened_before = os.fstat(descriptor)
        if (opened_before.st_dev, opened_before.st_ino) != (before_stat.st_dev, before_stat.st_ino):
            raise RecoveryError("Codex replaced the rollout inode during recovery", EXIT_PROTOCOL)
        if opened_before.st_size < before_stat.st_size:
            raise RecoveryError("Codex truncated the rollout during recovery", EXIT_PROTOCOL)

        digest = hashlib.sha256()
        remaining = before_stat.st_size
        os.lseek(descriptor, 0, os.SEEK_SET)
        while remaining:
            chunk = os.read(descriptor, min(8 * 1024 * 1024, remaining))
            if not chunk:
                raise RecoveryError("live rollout became shorter during postflight", EXIT_PROTOCOL)
            digest.update(chunk)
            remaining -= len(chunk)
        actual_prefix = digest.hexdigest()
        if actual_prefix != prefix_sha256:
            raise RecoveryError("the original rollout prefix changed during recovery", EXIT_PROTOCOL)

        tail_bytes = min(opened_before.st_size, 8 * 1024 * 1024)
        tail_data = os.pread(descriptor, tail_bytes, opened_before.st_size - tail_bytes)
        if not tail_data.endswith(b"\n"):
            raise RecoveryError("post-recovery rollout has no final newline", EXIT_PROTOCOL)
        tail_lines = tail_data.splitlines()
        if opened_before.st_size > tail_bytes and tail_lines:
            tail_lines = tail_lines[1:]
        if not tail_lines:
            raise RecoveryError("post-recovery final record is too large to validate", EXIT_PROTOCOL)
        try:
            final_record = json.loads(tail_lines[-1])
        except (json.JSONDecodeError, UnicodeDecodeError) as exc:
            raise RecoveryError("post-recovery final record is invalid JSON", EXIT_PROTOCOL) from exc
        if not isinstance(final_record, dict):
            raise RecoveryError("post-recovery final JSON record is not an object", EXIT_PROTOCOL)

        opened_after = os.fstat(descriptor)
        stable_fields_before = (
            opened_before.st_dev,
            opened_before.st_ino,
            opened_before.st_size,
            opened_before.st_mtime_ns,
        )
        stable_fields_after = (
            opened_after.st_dev,
            opened_after.st_ino,
            opened_after.st_size,
            opened_after.st_mtime_ns,
        )
        if stable_fields_after != stable_fields_before:
            raise RecoveryError("rollout changed while postflight verification was running", EXIT_PROTOCOL)
    finally:
        os.close(descriptor)

    if path_has_symlink_component(path):
        raise RecoveryError("rollout path gained a symlink component during postflight", EXIT_PROTOCOL)
    path_after = os.lstat(path)
    if stat_module.S_ISLNK(path_after.st_mode):
        raise RecoveryError("rollout path became a symlink during postflight", EXIT_PROTOCOL)
    if (
        path_after.st_dev,
        path_after.st_ino,
        path_after.st_size,
        path_after.st_mtime_ns,
    ) != stable_fields_after:
        raise RecoveryError("rollout path changed during postflight verification", EXIT_PROTOCOL)
    assert_idle(path)
    return {
        "sameDeviceAndInode": True,
        "sizeBefore": before_stat.st_size,
        "sizeAfter": opened_after.st_size,
        "bytesAppended": opened_after.st_size - before_stat.st_size,
        "prefixSha256": actual_prefix,
        "prefixUnchanged": True,
        "newlineComplete": True,
        "tailJsonValid": True,
    }


def append_only_postcheck(
    path: Path,
    before_stat: os.stat_result,
    prefix_sha256: str,
) -> dict[str, Any]:
    """Translate all filesystem failures into structured recovery failures."""
    try:
        return _append_only_postcheck(path, before_stat, prefix_sha256)
    except RecoveryError:
        raise
    except OSError as exc:
        raise RecoveryError(f"postflight filesystem verification failed: {exc}", EXIT_PROTOCOL) from exc


class AppServerClient:
    """Small JSONL client with reader threads to avoid buffered-pipe stalls."""

    def __init__(self, codex_bin: str, codex_home: Path, quiet: bool = False) -> None:
        self.codex_bin = codex_bin
        self.codex_home = codex_home.resolve()
        self.quiet = quiet
        self.process: subprocess.Popen[str] | None = None
        self.messages: queue.Queue[dict[str, Any] | BaseException | None] = queue.Queue()
        self.stderr_tail: collections.deque[str] = collections.deque(maxlen=30)
        self._next_id = 1
        self._write_lock = threading.Lock()
        self.initialize_result: dict[str, Any] = {}
        self.resume_result: dict[str, Any] = {}
        self.effort_change: dict[str, Any] | None = None
        self.compaction_progress: dict[str, Any] | None = None
        self.canary_progress: dict[str, Any] | None = None

    def __enter__(self) -> "AppServerClient":
        try:
            child_environment = os.environ.copy()
            child_environment["CODEX_HOME"] = str(self.codex_home)
            self.process = subprocess.Popen(
                [self.codex_bin, "app-server", "--disable", "hooks", "--stdio"],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                bufsize=1,
                start_new_session=(os.name == "posix"),
                env=child_environment,
            )
        except OSError as exc:
            raise RecoveryError(f"cannot start Codex app-server: {exc}", EXIT_UNSUPPORTED) from exc
        threading.Thread(target=self._read_stdout, daemon=True).start()
        threading.Thread(target=self._read_stderr, daemon=True).start()
        return self

    def __exit__(self, _type: Any, _value: Any, _traceback: Any) -> None:
        self.close()

    def _read_stdout(self) -> None:
        assert self.process is not None and self.process.stdout is not None
        try:
            for line in self.process.stdout:
                try:
                    message = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if isinstance(message, dict):
                    self.messages.put(message)
        except BaseException as exc:  # pragma: no cover - defensive reader boundary
            self.messages.put(exc)
        finally:
            self.messages.put(None)

    def _read_stderr(self) -> None:
        assert self.process is not None and self.process.stderr is not None
        for line in self.process.stderr:
            self.stderr_tail.append(redact_text(line.rstrip())[:300])

    def close(self) -> None:
        process = self.process
        if process is None:
            return
        try:
            if process.stdin is not None:
                process.stdin.close()
        except OSError:
            pass
        if process.poll() is None:
            try:
                process.wait(timeout=3)
            except subprocess.TimeoutExpired:
                if os.name == "posix":
                    try:
                        os.killpg(process.pid, signal.SIGTERM)
                    except ProcessLookupError:
                        pass
                else:
                    process.terminate()
                try:
                    process.wait(timeout=7)
                except subprocess.TimeoutExpired:
                    if os.name == "posix":
                        try:
                            os.killpg(process.pid, signal.SIGKILL)
                        except ProcessLookupError:
                            pass
                    else:
                        process.kill()
                    process.wait(timeout=5)
        self.process = None

    @property
    def root_pid(self) -> int:
        if self.process is None:
            raise RecoveryError("app-server is not running", EXIT_PROTOCOL)
        return self.process.pid

    def send(self, method: str, params: dict[str, Any] | None = None, request: bool = True) -> int | None:
        process = self.process
        if process is None or process.stdin is None:
            raise RecoveryError("app-server is not running", EXIT_PROTOCOL)
        payload: dict[str, Any] = {"method": method}
        request_id: int | None = None
        if request:
            request_id = self._next_id
            self._next_id += 1
            payload["id"] = request_id
        if params is not None:
            payload["params"] = params
        encoded = json.dumps(payload, ensure_ascii=False)
        try:
            with self._write_lock:
                process.stdin.write(encoded + "\n")
                process.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise RecoveryError(f"app-server input closed: {exc}", EXIT_PROTOCOL) from exc
        return request_id

    def next_message(self, deadline: float, phase: str, heartbeat: float = 15.0) -> dict[str, Any]:
        next_notice = time.monotonic() + heartbeat
        while True:
            now = time.monotonic()
            if now >= deadline:
                raise ProtocolTimeout(f"timed out during {phase}")
            if now >= next_notice:
                progress(f"{phase}: still working ({int(deadline - now)}s timeout remaining)", self.quiet)
                next_notice = now + heartbeat
            try:
                item = self.messages.get(timeout=min(1.0, deadline - now))
            except queue.Empty:
                process = self.process
                if process is not None and process.poll() is not None:
                    detail = " | ".join(self.stderr_tail)
                    raise RecoveryError(
                        f"app-server exited with code {process.returncode} during {phase}: {detail}",
                        EXIT_PROTOCOL,
                    )
                continue
            if isinstance(item, BaseException):
                raise RecoveryError(f"app-server reader failed during {phase}: {item}", EXIT_PROTOCOL)
            if item is None:
                detail = " | ".join(self.stderr_tail)
                raise RecoveryError(f"app-server closed output during {phase}: {detail}", EXIT_PROTOCOL)
            return item

    @staticmethod
    def response_error(message: dict[str, Any]) -> str | None:
        error = message.get("error")
        if error is None:
            return None
        return redact_text(json.dumps(error, ensure_ascii=False, sort_keys=True))[:500]

    def wait_response(self, request_id: int, timeout: float, phase: str) -> dict[str, Any]:
        deadline = time.monotonic() + timeout
        while True:
            message = self.next_message(deadline, phase)
            if "id" in message and "method" in message:
                raise RecoveryError(
                    f"unexpected app-server request during {phase}: {message.get('method')}",
                    EXIT_PROTOCOL,
                )
            if message.get("id") != request_id:
                continue
            error = self.response_error(message)
            if error:
                raise RecoveryError(f"{phase} failed: {error}", EXIT_PROTOCOL)
            return message.get("result") or {}

    def best_effort_interrupt(
        self,
        session_id: str,
        turn_id: str,
        timeout: float = 5.0,
    ) -> dict[str, Any]:
        """Request cancellation and briefly drain its acknowledgement/terminal event."""
        evidence: dict[str, Any] = {
            "attempted": True,
            "turnId": turn_id,
            "requestAccepted": False,
            "terminalStatus": None,
        }
        try:
            request_id = self.send(
                "turn/interrupt",
                {"threadId": session_id, "turnId": turn_id},
            )
            assert request_id is not None
        except RecoveryError as exc:
            evidence["error"] = redact_text(str(exc))[:300]
            return evidence

        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            try:
                message = self.next_message(deadline, "turn interrupt", heartbeat=timeout + 1)
            except RecoveryError as exc:
                evidence["error"] = redact_text(str(exc))[:300]
                break
            if message.get("id") == request_id:
                error = self.response_error(message)
                if error:
                    evidence["error"] = error
                    break
                evidence["requestAccepted"] = True
            elif message.get("method") == "turn/completed":
                params = message.get("params") or {}
                turn = params.get("turn") or {}
                if params.get("threadId") == session_id and str(turn.get("id") or "") == turn_id:
                    evidence["terminalStatus"] = turn.get("status")
            if evidence["requestAccepted"] and evidence["terminalStatus"] is not None:
                break
        return evidence

    def initialize(self, timeout: float = 30.0) -> None:
        request_id = self.send(
            "initialize",
            {
                "clientInfo": {
                    "name": "codex-session-recovery",
                    "title": "Codex Session Recovery",
                    "version": "1.0.0",
                },
                "capabilities": {
                    "experimentalApi": True,
                    "optOutNotificationMethods": [
                        "item/agentMessage/delta",
                        "item/reasoning/summaryTextDelta",
                        "item/reasoning/textDelta",
                        "item/plan/delta",
                        "item/commandExecution/outputDelta",
                        "item/fileChange/outputDelta",
                    ],
                },
            },
        )
        assert request_id is not None
        result = self.wait_response(request_id, timeout, "initialize")
        raw_home = result.get("codexHome")
        if not isinstance(raw_home, str) or Path(raw_home).expanduser().resolve() != self.codex_home:
            raise RecoveryError(
                "app-server initialize response reported a different CODEX_HOME",
                EXIT_UNSUPPORTED,
            )
        self.initialize_result = result
        self.send("initialized", {}, request=False)

    def resume(self, session_id: str, timeout: float) -> dict[str, Any]:
        request_id = self.send(
            "thread/resume",
            {"threadId": session_id, "excludeTurns": True},
        )
        assert request_id is not None
        result = self.wait_response(request_id, timeout, "thread resume")
        thread = result.get("thread")
        if not isinstance(thread, dict) or thread.get("id") != session_id:
            raise RecoveryError("thread/resume returned a missing or different thread id", EXIT_PROTOCOL)
        self.resume_result = result
        return result

    def update_effort(self, session_id: str, effort: str, timeout: float = 60.0) -> dict[str, Any]:
        previous = self.resume_result.get("reasoningEffort")
        self.effort_change = {
            "requested": effort,
            "previous": previous,
            "changed": previous != effort,
            "requestAccepted": False,
            "notificationVerified": previous == effort,
        }
        if previous == effort:
            self.effort_change["requestAccepted"] = True
            self.effort_change["verified"] = True
            return dict(self.effort_change)
        request_id = self.send(
            "thread/settings/update",
            {"threadId": session_id, "effort": effort},
        )
        assert request_id is not None
        deadline = time.monotonic() + timeout
        response_seen = False
        notification_seen = False
        while not (response_seen and notification_seen):
            message = self.next_message(deadline, "reasoning settings update")
            if "id" in message and "method" in message:
                raise RecoveryError("unexpected app-server request during settings update", EXIT_PROTOCOL)
            if message.get("id") == request_id:
                error = self.response_error(message)
                if error:
                    raise RecoveryError(
                        "this Codex build does not accept thread/settings/update: " + error,
                        EXIT_UNSUPPORTED,
                    )
                response_seen = True
                self.effort_change["requestAccepted"] = True
                continue
            if message.get("method") != "thread/settings/updated":
                continue
            params = message.get("params") or {}
            if params.get("threadId") != session_id:
                continue
            actual = (params.get("threadSettings") or {}).get("effort")
            if actual != effort:
                raise RecoveryError(
                    f"Codex confirmed an unexpected reasoning effort: {actual!r}",
                    EXIT_PROTOCOL,
                )
            notification_seen = True
            self.effort_change["notificationVerified"] = True
        self.resume_result["reasoningEffort"] = effort
        self.effort_change["verified"] = True
        return dict(self.effort_change)

    def compact(self, session_id: str, timeout: float) -> dict[str, Any]:
        request_id = self.send("thread/compact/start", {"threadId": session_id})
        assert request_id is not None
        deadline = time.monotonic() + timeout
        response_seen = False
        started_turn_id: str | None = None
        context_turn_id: str | None = None
        context_item_id: str | None = None
        context_started = False
        context_completed = False
        pending_item_completions: set[tuple[str, str]] = set()
        terminal_statuses: dict[str, str | None] = {}
        nonretry_errors: set[str] = set()
        retry_errors: collections.Counter[str] = collections.Counter()
        lifecycle: dict[str, Any] = {
            "requestAccepted": False,
            "turnId": None,
            "itemId": None,
            "turnStarted": False,
            "contextItemStarted": False,
            "contextItemCompleted": False,
            "terminalStatus": None,
            "retryingErrorsByTurn": {},
            "nonRetryableErrorTurnIds": [],
            "interrupt": None,
        }
        self.compaction_progress = lifecycle
        try:
            while True:
                message = self.next_message(deadline, "context compaction")
                if "id" in message and "method" in message:
                    raise RecoveryError("unexpected app-server request during compaction", EXIT_PROTOCOL)
                if message.get("id") == request_id:
                    error = self.response_error(message)
                    if error:
                        raise RecoveryError(f"context compaction failed to start: {error}", EXIT_PROTOCOL)
                    response_seen = True
                    lifecycle["requestAccepted"] = True
                else:
                    method = message.get("method")
                    params = message.get("params") or {}
                    if params.get("threadId") != session_id:
                        continue
                    if method == "error":
                        error_turn = str(params.get("turnId") or "")
                        if not error_turn or not isinstance(params.get("willRetry"), bool):
                            raise RecoveryError("malformed error notification during compaction", EXIT_PROTOCOL)
                        if params["willRetry"]:
                            retry_errors[error_turn] += 1
                            lifecycle["retryingErrorsByTurn"] = dict(retry_errors)
                        else:
                            nonretry_errors.add(error_turn)
                            lifecycle["nonRetryableErrorTurnIds"] = sorted(nonretry_errors)
                    elif method == "turn/started":
                        candidate_turn = str((params.get("turn") or {}).get("id") or "")
                        if not candidate_turn:
                            raise RecoveryError("compaction turn start omitted its turn id", EXIT_PROTOCOL)
                        if started_turn_id and candidate_turn != started_turn_id:
                            raise RecoveryError("multiple compaction turn starts were observed", EXIT_PROTOCOL)
                        if context_turn_id and candidate_turn != context_turn_id:
                            raise RecoveryError("compaction turn and item used different turn ids", EXIT_PROTOCOL)
                        started_turn_id = candidate_turn
                        lifecycle["turnId"] = candidate_turn
                        lifecycle["turnStarted"] = True
                    elif method == "item/started":
                        item = params.get("item") or {}
                        if item.get("type") == "contextCompaction":
                            candidate_turn = str(params.get("turnId") or "")
                            candidate_item = str(item.get("id") or "")
                            if not candidate_turn or not candidate_item:
                                raise RecoveryError("contextCompaction start omitted required ids", EXIT_PROTOCOL)
                            if context_turn_id and (candidate_turn, candidate_item) != (
                                context_turn_id,
                                context_item_id,
                            ):
                                raise RecoveryError("multiple contextCompaction items were observed", EXIT_PROTOCOL)
                            if started_turn_id and candidate_turn != started_turn_id:
                                raise RecoveryError("compaction turn and item used different turn ids", EXIT_PROTOCOL)
                            context_turn_id = candidate_turn
                            context_item_id = candidate_item
                            context_started = True
                            lifecycle["turnId"] = candidate_turn
                            lifecycle["itemId"] = candidate_item
                            lifecycle["contextItemStarted"] = True
                            if (candidate_turn, candidate_item) in pending_item_completions:
                                context_completed = True
                                lifecycle["contextItemCompleted"] = True
                    elif method == "item/completed":
                        item = params.get("item") or {}
                        if item.get("type") == "contextCompaction":
                            candidate = (str(params.get("turnId") or ""), str(item.get("id") or ""))
                            pending_item_completions.add(candidate)
                            if candidate == (context_turn_id, context_item_id):
                                context_completed = True
                                lifecycle["contextItemCompleted"] = True
                    elif method == "turn/completed":
                        turn = params.get("turn") or {}
                        candidate_turn = str(turn.get("id") or "")
                        if candidate_turn:
                            terminal_statuses[candidate_turn] = turn.get("status")
                            known_turn_id = context_turn_id or started_turn_id
                            if candidate_turn == known_turn_id:
                                lifecycle["terminalStatus"] = turn.get("status")

                known_turn_id = context_turn_id or started_turn_id
                if known_turn_id and known_turn_id in nonretry_errors:
                    raise RecoveryError(
                        f"Codex reported a non-retryable error for compaction turn {known_turn_id}",
                        EXIT_PROTOCOL,
                    )
                known_terminal = terminal_statuses.get(known_turn_id) if known_turn_id else None
                if known_terminal is not None:
                    lifecycle["terminalStatus"] = known_terminal
                if known_terminal is not None and known_terminal != "completed":
                    raise RecoveryError(
                        f"compaction turn {known_turn_id} ended with status {known_terminal!r}",
                        EXIT_PROTOCOL,
                    )
                if not context_started or not context_turn_id:
                    continue
                terminal = terminal_statuses.get(context_turn_id)
                if response_seen and context_completed and terminal == "completed":
                    return {
                        "turnId": context_turn_id,
                        "itemId": context_item_id,
                        "requestAccepted": True,
                        "contextItemStarted": True,
                        "contextItemCompleted": True,
                        "status": terminal,
                        "retryingErrorsObserved": retry_errors[context_turn_id],
                    }
        except BaseException as exc:
            interrupted: dict[str, Any] | None = None
            known_turn_id = context_turn_id or started_turn_id
            if known_turn_id and known_turn_id not in terminal_statuses:
                interrupted = self.best_effort_interrupt(session_id, known_turn_id)
                lifecycle["interrupt"] = interrupted
                if isinstance(exc, RecoveryError):
                    exc.details.setdefault("interrupt", interrupted)
            if isinstance(exc, RecoveryError):
                exc.details.setdefault("compaction", dict(lifecycle))
            if isinstance(exc, KeyboardInterrupt):
                details = {"interrupt": interrupted} if interrupted is not None else {}
                details["compaction"] = dict(lifecycle)
                raise RecoveryError("interrupted during context compaction", 130, details) from exc
            raise

    def probe(
        self,
        session_id: str,
        expected: str,
        timeout: float,
        effort: str | None = None,
    ) -> dict[str, Any]:
        prompt = (
            "Session recovery probe only. Do not call tools, edit files, or continue any "
            f"project task. Reply exactly: {expected}"
        )
        params: dict[str, Any] = {
            "threadId": session_id,
            "input": [{"type": "text", "text": prompt}],
        }
        if effort is not None:
            params["effort"] = effort
        request_id = self.send("turn/start", params)
        assert request_id is not None
        deadline = time.monotonic() + timeout
        response_seen = False
        turn_id: str | None = None
        pending_items: dict[str, list[dict[str, Any]]] = collections.defaultdict(list)
        observed_item_types: dict[str, set[str]] = collections.defaultdict(set)
        terminal_statuses: dict[str, str | None] = {}
        nonretry_errors: set[str] = set()
        retry_errors: collections.Counter[str] = collections.Counter()
        lifecycle: dict[str, Any] = {
            "requestAccepted": False,
            "turnId": None,
            "terminalStatus": None,
            "completedItemTypes": [],
            "observedItemTypes": [],
            "disallowedItems": [],
            "agentMessagesObserved": 0,
            "responseLength": None,
            "responseMatched": False,
            "retryingErrorsByTurn": {},
            "nonRetryableErrorTurnIds": [],
            "interrupt": None,
        }
        self.canary_progress = lifecycle
        try:
            while True:
                message = self.next_message(deadline, "responsiveness probe")
                if "id" in message and "method" in message:
                    raise RecoveryError("unexpected app-server request during canary", EXIT_PROBE)
                if message.get("id") == request_id:
                    error = self.response_error(message)
                    if error:
                        raise RecoveryError(f"probe failed to start: {error}", EXIT_PROTOCOL)
                    response_seen = True
                    lifecycle["requestAccepted"] = True
                    candidate = ((message.get("result") or {}).get("turn") or {}).get("id")
                    if candidate:
                        candidate_text = str(candidate)
                        if turn_id and candidate_text != turn_id:
                            raise RecoveryError("canary response returned a different turn id", EXIT_PROBE)
                        turn_id = candidate_text
                        lifecycle["turnId"] = candidate_text
                else:
                    method = message.get("method")
                    params_message = message.get("params") or {}
                    if params_message.get("threadId") != session_id:
                        continue
                    if method == "error":
                        error_turn = str(params_message.get("turnId") or "")
                        if not error_turn or not isinstance(params_message.get("willRetry"), bool):
                            raise RecoveryError("malformed error notification during canary", EXIT_PROBE)
                        if params_message["willRetry"]:
                            retry_errors[error_turn] += 1
                            lifecycle["retryingErrorsByTurn"] = dict(retry_errors)
                        else:
                            nonretry_errors.add(error_turn)
                            lifecycle["nonRetryableErrorTurnIds"] = sorted(nonretry_errors)
                    elif method == "turn/started":
                        candidate = (params_message.get("turn") or {}).get("id")
                        if candidate:
                            candidate_text = str(candidate)
                            if turn_id and candidate_text != turn_id:
                                raise RecoveryError("canary notifications used different turn ids", EXIT_PROBE)
                            turn_id = candidate_text
                            lifecycle["turnId"] = candidate_text
                    elif method in {"item/started", "item/completed"}:
                        item_turn = str(params_message.get("turnId") or "")
                        item = params_message.get("item") or {}
                        if not item_turn or not isinstance(item, dict):
                            raise RecoveryError("malformed item lifecycle event during canary", EXIT_PROBE)
                        item_type = str(item.get("type") or "<missing>")
                        observed_item_types[item_turn].add(item_type)
                        lifecycle["observedItemTypes"] = sorted(
                            observed_item_types.get(turn_id or item_turn, set())
                        )
                        if method == "item/completed":
                            pending_items[item_turn].append(item)
                            lifecycle["completedItemTypes"] = [
                                str(candidate.get("type") or "<missing>")
                                for candidate in pending_items.get(turn_id or item_turn, [])
                            ]
                    elif method == "turn/completed":
                        turn = params_message.get("turn") or {}
                        candidate = str(turn.get("id") or "")
                        if candidate:
                            terminal_statuses[candidate] = turn.get("status")
                            if candidate == turn_id:
                                lifecycle["terminalStatus"] = turn.get("status")

                if not response_seen or not turn_id or turn_id not in terminal_statuses:
                    continue
                if turn_id in nonretry_errors:
                    raise RecoveryError("Codex reported a non-retryable error during canary", EXIT_PROBE)
                status = terminal_statuses[turn_id]
                lifecycle["terminalStatus"] = status
                if status != "completed":
                    raise RecoveryError(f"canary turn ended with status {status!r}", EXIT_PROBE)
                final_messages: list[str] = []
                lifecycle["observedItemTypes"] = sorted(observed_item_types.get(turn_id, set()))
                disallowed_items = [
                    item_type
                    for item_type in observed_item_types.get(turn_id, set())
                    if item_type not in CANARY_ALLOWED_ITEM_TYPES
                ]
                for item in pending_items.get(turn_id, []):
                    item_type = str(item.get("type") or "")
                    if item_type == "agentMessage" and isinstance(item.get("text"), str):
                        final_messages.append(item["text"])
                if disallowed_items:
                    lifecycle["disallowedItems"] = sorted(set(disallowed_items))
                    raise RecoveryError(
                        f"canary unexpectedly used disallowed items: {sorted(set(disallowed_items))}",
                        EXIT_PROBE,
                    )
                final_text = final_messages[-1] if final_messages else None
                lifecycle["agentMessagesObserved"] = len(final_messages)
                lifecycle["responseLength"] = len(final_text or "")
                if (final_text or "").strip() != expected:
                    raise RecoveryError(
                        "canary response did not match the expected token "
                        f"(expectedLength={len(expected)}, receivedLength={len(final_text or '')})",
                        EXIT_PROBE,
                    )
                lifecycle["responseMatched"] = True
                return {
                    "turnId": turn_id,
                    "status": status,
                    "response": final_text,
                    "disallowedItems": [],
                    "retryingErrorsObserved": retry_errors[turn_id],
                }
        except BaseException as exc:
            interrupted: dict[str, Any] | None = None
            if turn_id and turn_id not in terminal_statuses:
                interrupted = self.best_effort_interrupt(session_id, turn_id)
                lifecycle["interrupt"] = interrupted
                if isinstance(exc, RecoveryError):
                    exc.details.setdefault("interrupt", interrupted)
            if isinstance(exc, RecoveryError):
                exc.details.setdefault("canary", dict(lifecycle))
            if isinstance(exc, KeyboardInterrupt):
                details = {"interrupt": interrupted} if interrupted is not None else {}
                details["canary"] = dict(lifecycle)
                raise RecoveryError("interrupted during canary", 130, details) from exc
            raise


def run_doctor(codex_bin: str) -> dict[str, Any]:
    version = codex_version(codex_bin)
    if version is None:
        raise RecoveryError(f"Codex executable is unavailable: {codex_bin}", EXIT_UNSUPPORTED)
    with tempfile.TemporaryDirectory(prefix="codex-session-recovery-schema-") as temp:
        result = subprocess.run(
            [codex_bin, "app-server", "generate-json-schema", "--experimental", "--out", temp],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=60,
            check=False,
        )
        if result.returncode != 0:
            raise RecoveryError(
                "Codex app-server schema generation failed: "
                + redact_text(result.stderr.strip())[:300],
                EXIT_UNSUPPORTED,
            )
        root = Path(temp)
        client_request = root / "ClientRequest.json"
        required_files = {
            "initialize": root / "v1" / "InitializeResponse.json",
            "resume": root / "v2" / "ThreadResumeParams.json",
            "resumeResponse": root / "v2" / "ThreadResumeResponse.json",
            "compact": root / "v2" / "ThreadCompactStartParams.json",
            "interrupt": root / "v2" / "TurnInterruptParams.json",
            "turnStart": root / "v2" / "TurnStartParams.json",
            "turnStarted": root / "v2" / "TurnStartedNotification.json",
            "itemStarted": root / "v2" / "ItemStartedNotification.json",
            "itemCompleted": root / "v2" / "ItemCompletedNotification.json",
            "turnCompleted": root / "v2" / "TurnCompletedNotification.json",
        }
        missing_files = [str(path) for path in [client_request, *required_files.values()] if not path.is_file()]
        if missing_files:
            raise RecoveryError(f"Codex omitted required schema files: {missing_files}", EXIT_UNSUPPORTED)
        client_schema = json.loads(client_request.read_text(encoding="utf-8"))
        client_text = json.dumps(client_schema, separators=(",", ":"), sort_keys=True)
        required_methods = ["thread/resume", "thread/compact/start", "turn/start", "turn/interrupt"]
        supported = {
            method: method in client_text
            for method in required_methods + ["thread/settings/update"]
        }
        missing = [method for method in required_methods if not supported[method]]
        if missing:
            raise RecoveryError(f"Codex app-server is missing required methods: {missing}", EXIT_UNSUPPORTED)
        schemas = {
            name: json.loads(path.read_text(encoding="utf-8"))
            for name, path in required_files.items()
        }
        expected_contract = {
            "initializeRequired": ["codexHome"],
            "resumeRequired": ["threadId"],
            "resumeResponseRequired": ["thread"],
            "resumeProperties": ["excludeTurns", "threadId"],
            "compactRequired": ["threadId"],
            "interruptRequired": ["threadId", "turnId"],
            "turnStartRequired": ["input", "threadId"],
            "turnStartedRequired": ["threadId", "turn"],
            "itemStartedRequired": ["item", "threadId", "turnId"],
            "itemCompletedRequired": ["item", "threadId", "turnId"],
            "turnCompletedRequired": ["threadId", "turn"],
            "contextCompactionItem": True,
        }
        projection = {
            "initializeRequired": sorted(
                key
                for key in (schemas["initialize"].get("required") or [])
                if key == "codexHome"
            ),
            "resumeRequired": sorted(schemas["resume"].get("required") or []),
            "resumeResponseRequired": sorted(
                key
                for key in (schemas["resumeResponse"].get("required") or [])
                if key == "thread"
            ),
            "resumeProperties": sorted(
                key for key in (schemas["resume"].get("properties") or {}) if key in {"threadId", "excludeTurns"}
            ),
            "compactRequired": sorted(schemas["compact"].get("required") or []),
            "interruptRequired": sorted(schemas["interrupt"].get("required") or []),
            "turnStartRequired": sorted(schemas["turnStart"].get("required") or []),
            "turnStartedRequired": sorted(
                key
                for key in (schemas["turnStarted"].get("required") or [])
                if key in {"threadId", "turn"}
            ),
            "itemStartedRequired": sorted(
                key
                for key in (schemas["itemStarted"].get("required") or [])
                if key in {"item", "threadId", "turnId"}
            ),
            "itemCompletedRequired": sorted(
                key
                for key in (schemas["itemCompleted"].get("required") or [])
                if key in {"item", "threadId", "turnId"}
            ),
            "turnCompletedRequired": sorted(
                key
                for key in (schemas["turnCompleted"].get("required") or [])
                if key in {"threadId", "turn"}
            ),
            "contextCompactionItem": "contextCompaction"
            in json.dumps(schemas["itemStarted"], separators=(",", ":")),
        }
        if projection != expected_contract:
            raise RecoveryError(
                "installed Codex app-server schema is incompatible with the guarded recovery contract",
                EXIT_UNSUPPORTED,
            )
        fingerprint = hashlib.sha256(
            json.dumps(projection, sort_keys=True, separators=(",", ":")).encode("utf-8")
        ).hexdigest()
    return {
        "ok": True,
        "operation": "doctor",
        "codexVersion": version,
        "codexBinary": shutil.which(codex_bin) or codex_bin,
        "methods": supported,
        "contractFingerprint": fingerprint,
        "zstd": shutil.which("zstd"),
        "platform": sys.platform,
    }


def require_confirmation(args: argparse.Namespace) -> None:
    if getattr(args, "dry_run", False):
        return
    if not getattr(args, "yes", False):
        raise RecoveryError(
            f"this command appends to the Codex session; review inspect/backup first and rerun with {MUTATION_CONFIRMATION}",
            EXIT_USAGE_OR_NOT_FOUND,
        )


def open_prepared_client(
    codex_bin: str,
    codex_home: Path,
    session_id: str,
    resume_timeout: float,
    quiet: bool,
    pre_resume_check: Callable[[], None] | None = None,
) -> AppServerClient:
    client = AppServerClient(codex_bin, codex_home, quiet)
    client.__enter__()
    try:
        client.initialize()
        if pre_resume_check is not None:
            pre_resume_check()
        progress("Resuming session through the official app-server API...", quiet)
        client.resume(session_id, resume_timeout)
    except BaseException:
        client.close()
        raise
    return client


def resolve_record(args: argparse.Namespace) -> tuple[Path, SessionRecord]:
    codex_home = Path(args.codex_home).expanduser().resolve()
    record = locate_session(codex_home, args.session_id)
    return codex_home, record


def command_doctor(args: argparse.Namespace) -> dict[str, Any]:
    return run_doctor(args.codex_bin)


def command_inspect(args: argparse.Namespace) -> dict[str, Any]:
    codex_home, record = resolve_record(args)
    return inspect_session(record, codex_home, args.codex_bin, args.scan)


def command_backup(args: argparse.Namespace) -> dict[str, Any]:
    codex_home, record = resolve_record(args)
    output = Path(args.output_dir) if args.output_dir else None
    with session_lock(codex_home, record.session_id):
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)
        return backup_rollout(record, codex_home, args.codex_bin, output, args.quiet)


def command_verify_backup(args: argparse.Namespace) -> dict[str, Any]:
    return verify_backup(Path(args.manifest))


def dry_run_payload(operation: str, record: SessionRecord, args: argparse.Namespace) -> dict[str, Any]:
    return {
        "ok": True,
        "dryRun": True,
        "operation": operation,
        "sessionId": record.session_id,
        "rolloutPath": record.rollout_path,
        "willBackup": operation in {"compact", "recover"},
        "willCompact": operation in {"compact", "recover"},
        "willLoadProbe": operation == "probe",
        "willCanary": operation == "canary" or (operation == "recover" and args.canary),
        "requestedEffort": getattr(args, "effort", None),
    }


def perform_compaction(args: argparse.Namespace, operation: str) -> dict[str, Any]:
    require_confirmation(args)
    codex_home, record = resolve_record(args)
    if args.dry_run:
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)
        return dry_run_payload(operation, record, args)

    run_doctor(args.codex_bin)
    with session_lock(codex_home, record.session_id):
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)
        backup = backup_rollout(
            record,
            codex_home,
            args.codex_bin,
            Path(args.backup_dir) if args.backup_dir else None,
            args.quiet,
        )
        try:
            validate_mutable_rollout(record, codex_home)
            before_stat = verify_live_matches_backup(record.rollout_path, backup)
            assert_idle(record.rollout_path)
        except RecoveryError as exc:
            raise RecoveryError(
                str(exc),
                exc.exit_code,
                {"backup": backup, "preflight": {"verified": False}},
            ) from exc

        def pre_resume_check() -> None:
            validate_mutable_rollout(record, codex_home)
            verify_live_matches_backup(record.rollout_path, backup)
            assert_idle(record.rollout_path)

        client: AppServerClient | None = None
        compacted: dict[str, Any] | None = None
        canary_result: dict[str, Any] | None = None
        effort_change: dict[str, Any] | None = None
        primary_error: BaseException | None = None
        try:
            client = open_prepared_client(
                args.codex_bin,
                codex_home,
                record.session_id,
                args.resume_timeout,
                args.quiet,
                pre_resume_check,
            )
            assert_only_tool_owners(record.rollout_path, client.root_pid)
            if args.effort:
                effort_change = client.update_effort(record.session_id, args.effort)
                assert_only_tool_owners(record.rollout_path, client.root_pid)
            compacted = client.compact(record.session_id, args.operation_timeout)
            if getattr(args, "canary", False):
                expected = args.expected or f"SESSION_OK_{uuid.uuid4().hex[:8].upper()}"
                canary_started = time.monotonic()
                try:
                    canary_result = client.probe(record.session_id, expected, args.operation_timeout)
                except RecoveryError as exc:
                    raise RecoveryError(
                        f"compaction completed, but the optional canary failed: {exc}",
                        exc.exit_code,
                        exc.details,
                    ) from exc
                canary_result["elapsedSeconds"] = round(time.monotonic() - canary_started, 3)
        except BaseException as exc:
            primary_error = exc
        finally:
            if client is not None:
                if effort_change is None and client.effort_change is not None:
                    effort_change = dict(client.effort_change)
                if compacted is None and client.compaction_progress is not None:
                    compacted = dict(client.compaction_progress)
                if canary_result is None and client.canary_progress is not None:
                    canary_result = dict(client.canary_progress)
                try:
                    client.close()
                except BaseException as exc:
                    if primary_error is None:
                        primary_error = exc

        postflight: dict[str, Any] | None = None
        postflight_error: BaseException | None = None
        try:
            postflight = append_only_postcheck(
                record.rollout_path,
                before_stat,
                backup["sourceSha256"],
            )
        except BaseException as exc:
            postflight_error = exc

        partial: dict[str, Any] = {
            "backup": backup,
            "effortChange": effort_change,
            "compaction": compacted,
            "canary": canary_result,
            "postflight": postflight,
        }
        if postflight_error is not None:
            partial["postflightError"] = redact_text(str(postflight_error))[:500]

        if isinstance(primary_error, RecoveryError):
            if primary_error.details:
                partial["operationDetails"] = primary_error.details
            message = str(primary_error)
            if postflight_error is not None:
                message += f"; postflight also failed: {postflight_error}"
            raise RecoveryError(message, primary_error.exit_code, partial) from primary_error
        if isinstance(primary_error, KeyboardInterrupt):
            message = "interrupted after guarded recovery cleanup"
            if postflight_error is not None:
                message += f"; postflight also failed: {postflight_error}"
            raise RecoveryError(message, 130, partial) from primary_error
        if primary_error is not None:
            raise primary_error
        if postflight_error is not None:
            postflight_code = (
                postflight_error.exit_code
                if isinstance(postflight_error, RecoveryError)
                else 130
                if isinstance(postflight_error, KeyboardInterrupt)
                else EXIT_PROTOCOL
            )
            raise RecoveryError(
                f"postflight integrity check failed: {postflight_error}",
                postflight_code,
                partial,
            ) from postflight_error

        return {
            "ok": True,
            "operation": operation,
            "sessionId": record.session_id,
            "backup": backup,
            "effortChange": effort_change,
            "compaction": compacted,
            "canary": canary_result,
            "postflight": postflight,
            "tail": tail_summary(record.rollout_path),
            "limitation": "supported compaction reduces model-visible context but does not shrink the rollout file",
        }


def command_compact(args: argparse.Namespace) -> dict[str, Any]:
    return perform_compaction(args, "compact")


def command_probe(args: argparse.Namespace) -> dict[str, Any]:
    codex_home, record = resolve_record(args)
    if args.dry_run:
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)
        return dry_run_payload("probe", record, args)
    run_doctor(args.codex_bin)
    with session_lock(codex_home, record.session_id):
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)

        def probe_pre_resume_check() -> None:
            validate_mutable_rollout(record, codex_home)
            assert_idle(record.rollout_path)

        started = time.monotonic()
        client = open_prepared_client(
            args.codex_bin,
            codex_home,
            record.session_id,
            args.resume_timeout,
            args.quiet,
            probe_pre_resume_check,
        )
        try:
            ownership = assert_only_tool_owners(record.rollout_path, client.root_pid)
        finally:
            client.close()
        elapsed = round(time.monotonic() - started, 3)
    return {
        "ok": True,
        "operation": "probe",
        "sessionId": record.session_id,
        "loadProbe": {"resumed": True, "elapsedSeconds": elapsed, "ownership": ownership},
        "tail": tail_summary(record.rollout_path),
    }


def command_canary(args: argparse.Namespace) -> dict[str, Any]:
    require_confirmation(args)
    codex_home, record = resolve_record(args)
    if args.dry_run:
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)
        return dry_run_payload("canary", record, args)
    run_doctor(args.codex_bin)
    with session_lock(codex_home, record.session_id):
        validate_mutable_rollout(record, codex_home)
        assert_idle(record.rollout_path)
        before_stat, prefix_sha256 = stable_rollout_snapshot(record.rollout_path)
        baseline = {
            "sourceDevice": before_stat.st_dev,
            "sourceInode": before_stat.st_ino,
            "sourceBytes": before_stat.st_size,
            "sourceMtimeNs": before_stat.st_mtime_ns,
            "sourceSha256": prefix_sha256,
        }

        def canary_pre_resume_check() -> None:
            validate_mutable_rollout(record, codex_home)
            verify_live_matches_backup(record.rollout_path, baseline)
            assert_idle(record.rollout_path)

        client: AppServerClient | None = None
        result: dict[str, Any] | None = None
        effort_change: dict[str, Any] | None = None
        primary_error: BaseException | None = None
        started = time.monotonic()
        try:
            client = open_prepared_client(
                args.codex_bin,
                codex_home,
                record.session_id,
                args.resume_timeout,
                args.quiet,
                canary_pre_resume_check,
            )
            assert_only_tool_owners(record.rollout_path, client.root_pid)
            if args.effort:
                effort_change = client.update_effort(record.session_id, args.effort)
                assert_only_tool_owners(record.rollout_path, client.root_pid)
            result = client.probe(record.session_id, args.expected, args.operation_timeout)
        except BaseException as exc:
            primary_error = exc
        finally:
            if client is not None:
                if effort_change is None and client.effort_change is not None:
                    effort_change = dict(client.effort_change)
                if result is None and client.canary_progress is not None:
                    result = dict(client.canary_progress)
                try:
                    client.close()
                except BaseException as exc:
                    if primary_error is None:
                        primary_error = exc

        postflight: dict[str, Any] | None = None
        postflight_error: BaseException | None = None
        try:
            postflight = append_only_postcheck(record.rollout_path, before_stat, prefix_sha256)
        except BaseException as exc:
            postflight_error = exc

        partial: dict[str, Any] = {
            "effortChange": effort_change,
            "canary": result,
            "postflight": postflight,
        }
        if postflight_error is not None:
            partial["postflightError"] = redact_text(str(postflight_error))[:500]
        if isinstance(primary_error, RecoveryError):
            if primary_error.details:
                partial["operationDetails"] = primary_error.details
            message = str(primary_error)
            if postflight_error is not None:
                message += f"; postflight also failed: {postflight_error}"
            raise RecoveryError(message, primary_error.exit_code, partial) from primary_error
        if isinstance(primary_error, KeyboardInterrupt):
            message = "interrupted after guarded canary cleanup"
            if postflight_error is not None:
                message += f"; postflight also failed: {postflight_error}"
            raise RecoveryError(message, 130, partial) from primary_error
        if primary_error is not None:
            raise primary_error
        if postflight_error is not None:
            postflight_code = (
                postflight_error.exit_code
                if isinstance(postflight_error, RecoveryError)
                else 130
                if isinstance(postflight_error, KeyboardInterrupt)
                else EXIT_PROTOCOL
            )
            raise RecoveryError(
                f"postflight integrity check failed: {postflight_error}",
                postflight_code,
                partial,
            ) from postflight_error
        assert result is not None
        result["elapsedSeconds"] = round(time.monotonic() - started, 3)
        return {
            "ok": True,
            "operation": "canary",
            "sessionId": record.session_id,
            "effortChange": effort_change,
            "canary": result,
            "postflight": postflight,
            "tail": tail_summary(record.rollout_path),
        }


def command_recover(args: argparse.Namespace) -> dict[str, Any]:
    return perform_compaction(args, "recover")


def add_global_session_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("session_id", type=validate_session_id, help="Codex thread/session UUID")


def add_mutation_options(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--yes", action="store_true", help="Confirm the session mutation")
    parser.add_argument("--dry-run", action="store_true", help="Resolve and describe steps without mutating")
    parser.add_argument("--resume-timeout", type=float, default=600, help="Seconds allowed to load history")
    parser.add_argument("--operation-timeout", type=float, default=1800, help="Seconds allowed per turn")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Safely inspect, back up, compact, probe, and recover stalled Codex sessions",
    )
    parser.add_argument(
        "--codex-home",
        default=os.environ.get("CODEX_HOME", str(Path.home() / ".codex")),
        help="Codex state directory (default: CODEX_HOME or ~/.codex)",
    )
    parser.add_argument("--codex-bin", default="codex", help="Codex executable")
    parser.add_argument("--json", action="store_true", help="Print structured JSON")
    parser.add_argument("--quiet", action="store_true", help="Suppress progress messages")
    subparsers = parser.add_subparsers(dest="command", required=True)

    doctor = subparsers.add_parser("doctor", help="Check local Codex recovery API support")
    doctor.set_defaults(func=command_doctor)

    inspect_parser = subparsers.add_parser("inspect", help="Inspect session state without reading prompt text")
    add_global_session_options(inspect_parser)
    inspect_parser.add_argument("--scan", action="store_true", help="Stream the whole rollout for aggregate counts")
    inspect_parser.set_defaults(func=command_inspect)

    backup = subparsers.add_parser("backup", help="Create a verified private rollout backup")
    add_global_session_options(backup)
    backup.add_argument("--output-dir", help="New destination directory; must not already exist")
    backup.set_defaults(func=command_backup)

    verify = subparsers.add_parser("verify-backup", help="Decompress and verify a backup manifest")
    verify.add_argument("manifest", help="Path to manifest.json")
    verify.set_defaults(func=command_verify_backup)

    compact = subparsers.add_parser("compact", help="Back up and compact a session through app-server")
    add_global_session_options(compact)
    add_mutation_options(compact)
    compact.add_argument("--backup-dir", help="New backup directory")
    compact.add_argument("--effort", choices=EFFORTS, help="Explicitly change sticky reasoning effort first")
    compact.set_defaults(canary=False, expected=None)
    compact.set_defaults(func=command_compact)

    probe = subparsers.add_parser("probe", help="Cold-load a thread without adding a model turn")
    add_global_session_options(probe)
    probe.add_argument("--dry-run", action="store_true", help="Resolve and describe steps without loading")
    probe.add_argument("--resume-timeout", type=float, default=600, help="Seconds allowed to load history")
    probe.set_defaults(canary=False, effort=None, expected=None)
    probe.set_defaults(func=command_probe)

    canary = subparsers.add_parser("canary", help="Append an explicit tool-free model response check")
    add_global_session_options(canary)
    add_mutation_options(canary)
    canary.add_argument("--expected", default="SESSION_OK", help="Exact response token")
    canary.add_argument("--effort", choices=EFFORTS, help="Explicitly change sticky reasoning effort first")
    canary.set_defaults(canary=True, backup_dir=None)
    canary.set_defaults(func=command_canary)

    recover = subparsers.add_parser("recover", help="Back up, compact, and verify a stalled session")
    add_global_session_options(recover)
    add_mutation_options(recover)
    recover.add_argument("--backup-dir", help="New backup directory")
    recover.add_argument("--effort", choices=EFFORTS, help="Explicitly change sticky reasoning effort")
    recover.add_argument("--canary", action="store_true", help="Also append a tool-free model response check")
    recover.add_argument("--expected", help="Exact canary token; defaults to a random token")
    recover.set_defaults(func=command_recover)
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    if os.name == "posix":
        os.umask(0o077)
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)
    try:
        payload = args.func(args)
    except RecoveryError as exc:
        safe_error = redact_text(str(exc))[:1000]
        if getattr(args, "json", False):
            failure: dict[str, Any] = {
                "ok": False,
                "error": safe_error,
                "exitCode": exc.exit_code,
            }
            if exc.details:
                failure["partial"] = json_safe(exc.details)
            print(json.dumps(failure, ensure_ascii=False, indent=2, sort_keys=True))
        else:
            print(f"error: {safe_error}", file=sys.stderr)
            if exc.details:
                partial = json.dumps(
                    json_safe(exc.details),
                    ensure_ascii=False,
                    sort_keys=True,
                    separators=(",", ":"),
                )
                print(f"partial: {partial}", file=sys.stderr)
        return exc.exit_code
    except KeyboardInterrupt:
        print("error: interrupted", file=sys.stderr)
        return 130
    emit(payload, args.json)
    return EXIT_OK


if __name__ == "__main__":
    raise SystemExit(main())
