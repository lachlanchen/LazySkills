#!/usr/bin/env python3
"""Isolated fixture tests for codex_session_recovery.py.

These tests never use the real HOME, CODEX_HOME, Codex binary, or network.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import os
import signal
import sqlite3
import stat
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path


TOOL = Path(__file__).with_name("codex_session_recovery.py")
SESSION_ID = "11111111-2222-4333-8444-555555555555"


FAKE_CODEX = r'''#!/usr/bin/env python3
import json
import os
import sys
from pathlib import Path

def emit(value):
    print(json.dumps(value, separators=(",", ":")), flush=True)

def record(value):
    path = os.environ.get("FAKE_EVENT_LOG")
    if not path:
        return
    with open(path, "a", encoding="utf-8") as handle:
        handle.write(json.dumps(value, separators=(",", ":")) + "\n")

def schema_file(path, required, properties=None, context=False):
    payload = {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": required,
        "properties": {key: {"type": "string"} for key in (properties or required)},
    }
    if context:
        payload["definitions"] = {
            "ThreadItem": {
                "oneOf": [{
                    "type": "object",
                    "properties": {"type": {"enum": ["contextCompaction"]}},
                }]
            }
        }
    path.write_text(json.dumps(payload), encoding="utf-8")

if sys.argv[1:] == ["--version"]:
    print("codex-cli 0.fixture")
    raise SystemExit(0)

if sys.argv[1:3] == ["app-server", "generate-json-schema"]:
    if os.environ.get("FAKE_CODEX_MODE") == "schema_error":
        print("Bearer sk-SUPERSECRET", file=sys.stderr)
        raise SystemExit(2)
    out = Path(sys.argv[sys.argv.index("--out") + 1])
    (out / "v2").mkdir(parents=True, exist_ok=True)
    (out / "v1").mkdir(parents=True, exist_ok=True)
    methods = [
        "thread/resume",
        "thread/compact/start",
        "turn/start",
        "turn/interrupt",
        "thread/settings/update",
    ]
    if os.environ.get("FAKE_CODEX_MODE") == "schema_missing_interrupt":
        methods.remove("turn/interrupt")
    client = {"methods": methods}
    (out / "ClientRequest.json").write_text(json.dumps(client), encoding="utf-8")
    schema_file(out / "v1/InitializeResponse.json", ["codexHome"])
    schema_file(out / "v2/ThreadResumeParams.json", ["threadId"], ["threadId", "excludeTurns"])
    schema_file(out / "v2/ThreadResumeResponse.json", ["thread"])
    schema_file(out / "v2/ThreadCompactStartParams.json", ["threadId"])
    if os.environ.get("FAKE_CODEX_MODE") != "schema_missing_interrupt":
        schema_file(out / "v2/TurnInterruptParams.json", ["threadId", "turnId"])
    schema_file(out / "v2/TurnStartParams.json", ["input", "threadId"])
    if os.environ.get("FAKE_CODEX_MODE") != "schema_missing_turn_started":
        schema_file(out / "v2/TurnStartedNotification.json", ["threadId", "turn"])
    schema_file(out / "v2/ItemStartedNotification.json", ["item", "startedAtMs", "threadId", "turnId"], context=True)
    schema_file(out / "v2/ItemCompletedNotification.json", ["completedAtMs", "item", "threadId", "turnId"], context=True)
    schema_file(out / "v2/TurnCompletedNotification.json", ["threadId", "turn"])
    raise SystemExit(0)

if sys.argv[1:] != ["app-server", "--disable", "hooks", "--stdio"]:
    raise SystemExit(2)

mode = os.environ.get("FAKE_CODEX_MODE", "happy")
race_handle = None
for line in sys.stdin:
    message = json.loads(line)
    method = message.get("method")
    request_id = message.get("id")
    params = message.get("params") or {}
    thread_id = params.get("threadId")
    record({"method": method, "params": params})
    if method == "initialize":
        if mode == "probe_owner_race":
            race_handle = open(os.environ["FAKE_ROLLOUT"], "rb")
        reported_home = os.environ.get("CODEX_HOME", "")
        if mode == "initialize_mismatch":
            reported_home = str(Path(reported_home).parent / "different-codex-home")
        emit({"id": request_id, "result": {
            "codexHome": reported_home,
            "platformFamily": "unix",
            "platformOs": "linux",
            "userAgent": "fixture",
        }})
    elif method == "initialized":
        pass
    elif method == "thread/resume":
        returned_id = "00000000-0000-4000-8000-000000000000" if mode == "wrong_resume" else thread_id
        emit({"id": request_id, "result": {
            "thread": {"id": returned_id},
            "reasoningEffort": "medium",
        }})
    elif method == "thread/settings/update":
        if mode != "settings_no_notification":
            emit({"method": "thread/settings/updated", "params": {
                "threadId": thread_id, "threadSettings": {"effort": params.get("effort")}
            }})
        emit({"id": request_id, "result": {}})
    elif method == "thread/compact/start":
        turn_id = "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee"
        item_id = "context-item"
        emit({"method": "turn/started", "params": {
            "threadId": thread_id,
            "turn": {"id": turn_id, "items": [], "status": "inProgress"}
        }})
        if mode == "preitem_compaction_timeout":
            emit({"id": request_id, "result": {}})
            continue
        # Notifications-before-ack deliberately exercises event buffering.
        emit({"method": "item/started", "params": {
            "threadId": thread_id, "turnId": turn_id, "startedAtMs": 1,
            "item": {"id": item_id, "type": "contextCompaction"}
        }})
        if mode == "retry_error":
            emit({"method": "error", "params": {
                "threadId": thread_id, "turnId": turn_id, "willRetry": True,
                "error": {"message": "temporary"}
            }})
        elif mode == "unrelated_error":
            emit({"method": "error", "params": {
                "threadId": thread_id, "turnId": "unrelated-turn", "willRetry": False,
                "error": {"message": "unrelated"}
            }})
        emit({"id": request_id, "result": {}})
        if mode in {"compaction_timeout", "mutate_prefix_compaction_timeout"}:
            rollout = os.environ.get("FAKE_ROLLOUT")
            if mode == "mutate_prefix_compaction_timeout" and rollout:
                with open(rollout, "r+b") as handle:
                    handle.seek(0)
                    handle.write(b"X")
                    handle.flush()
                    os.fsync(handle.fileno())
            continue
        if mode != "missing_item_completed":
            emit({"method": "item/completed", "params": {
                "threadId": thread_id, "turnId": turn_id, "completedAtMs": 2,
                "item": {"id": item_id, "type": "contextCompaction"}
            }})
        emit({"method": "turn/completed", "params": {
            "threadId": thread_id,
            "turn": {"id": turn_id, "items": [], "status": "completed"}
        }})
        rollout = os.environ.get("FAKE_ROLLOUT")
        if mode == "append" and rollout:
            with open(rollout, "ab") as handle:
                handle.write(b'{"timestamp":"2026-01-01T00:00:02Z","type":"event_msg","payload":{"type":"task_complete"}}\n')
        elif mode == "mutate_prefix" and rollout:
            with open(rollout, "r+b") as handle:
                handle.seek(0)
                handle.write(b"X")
        elif mode == "delete_rollout" and rollout:
            os.unlink(rollout)
    elif method == "turn/start":
        turn_id = "99999999-8888-4777-8666-555555555555"
        expected = (params.get("input") or [{}])[0].get("text", "").split("Reply exactly: ")[-1]
        emit({"id": request_id, "result": {"turn": {"id": turn_id, "items": [], "status": "inProgress"}}})
        if mode == "canary_timeout":
            continue
        if mode == "collab_canary":
            emit({"method": "item/completed", "params": {
                "threadId": thread_id, "turnId": turn_id, "completedAtMs": 2,
                "item": {"id": "collab", "type": "collabAgentToolCall"}
            }})
        elif mode == "collab_started_only":
            emit({"method": "item/started", "params": {
                "threadId": thread_id, "turnId": turn_id, "startedAtMs": 2,
                "item": {"id": "collab", "type": "collabAgentToolCall"}
            }})
        elif mode == "auto_compact_canary":
            emit({"method": "item/completed", "params": {
                "threadId": thread_id, "turnId": turn_id, "completedAtMs": 2,
                "item": {"id": "auto-compact", "type": "contextCompaction"}
            }})
        emit({"method": "item/completed", "params": {
            "threadId": thread_id, "turnId": turn_id, "completedAtMs": 3,
            "item": {"id": "agent-message", "type": "agentMessage", "text": expected}
        }})
        emit({"method": "turn/completed", "params": {
            "threadId": thread_id,
            "turn": {"id": turn_id, "items": [], "status": "completed"}
        }})
    elif method == "turn/interrupt":
        emit({"id": request_id, "result": {}})
        emit({"method": "turn/completed", "params": {
            "threadId": thread_id,
            "turn": {"id": params.get("turnId"), "items": [], "status": "interrupted"}
        }})
'''


class RecoveryFixture(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory(prefix="codex-recovery-test-")
        self.root = Path(self.temporary.name)
        self.home = self.root / "home"
        self.codex_home = self.home / ".codex"
        self.session_dir = self.codex_home / "sessions" / "2026" / "01" / "01"
        self.session_dir.mkdir(parents=True)
        self.rollout = self.session_dir / f"rollout-2026-01-01T00-00-00-{SESSION_ID}.jsonl"
        records = [
            {"timestamp": "2026-01-01T00:00:00Z", "type": "session_meta", "payload": {"id": SESSION_ID}},
            {"timestamp": "2026-01-01T00:00:01Z", "type": "event_msg", "payload": {"type": "task_complete"}},
        ]
        self.original = b"".join(
            json.dumps(record, separators=(",", ":")).encode("utf-8") + b"\n" for record in records
        )
        self.rollout.write_bytes(self.original)
        database = sqlite3.connect(self.codex_home / "state_5.sqlite")
        database.execute(
            "CREATE TABLE threads (id TEXT PRIMARY KEY, rollout_path TEXT, cwd TEXT, model TEXT, "
            "reasoning_effort TEXT, tokens_used INTEGER, updated_at INTEGER, archived INTEGER, history_mode TEXT)"
        )
        database.execute(
            "INSERT INTO threads VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (SESSION_ID, str(self.rollout), str(self.root), "fixture-model", "medium", 12, 1, 0, "legacy"),
        )
        database.commit()
        database.close()
        self.fake_codex = self.root / "fake-codex"
        self.fake_codex.write_text(FAKE_CODEX, encoding="utf-8")
        self.fake_codex.chmod(0o755)
        self.event_log = self.root / "fake-events.jsonl"
        self.env = os.environ.copy()
        self.env.update({
            "HOME": str(self.home),
            "CODEX_HOME": str(self.codex_home),
            "FAKE_ROLLOUT": str(self.rollout),
            "FAKE_EVENT_LOG": str(self.event_log),
        })

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def tool_command(self, *arguments: str, json_output: bool = True) -> list[str]:
        command = [
            sys.executable,
            str(TOOL),
            "--codex-home",
            str(self.codex_home),
            "--codex-bin",
            str(self.fake_codex),
        ]
        if json_output:
            command.append("--json")
        command.extend(["--quiet", *arguments])
        return command

    def run_tool(self, *arguments: str, mode: str = "happy", timeout: float = 30) -> subprocess.CompletedProcess[str]:
        env = self.env.copy()
        env["FAKE_CODEX_MODE"] = mode
        command = self.tool_command(*arguments)
        return subprocess.run(command, text=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, env=env, timeout=timeout)

    def read_events(self) -> list[dict[str, object]]:
        if not self.event_log.exists():
            return []
        return [json.loads(line) for line in self.event_log.read_text(encoding="utf-8").splitlines()]

    def test_doctor_and_read_only_inspect(self) -> None:
        doctor = self.run_tool("doctor")
        self.assertEqual(doctor.returncode, 0, doctor.stderr)
        self.assertTrue(json.loads(doctor.stdout)["methods"]["thread/compact/start"])
        inspect = self.run_tool("inspect", SESSION_ID, "--scan")
        self.assertEqual(inspect.returncode, 0, inspect.stderr)
        payload = json.loads(inspect.stdout)
        self.assertEqual(payload["scan"]["lineCount"], 2)
        self.assertEqual(self.rollout.read_bytes(), self.original)

    def test_doctor_requires_interrupt_contract(self) -> None:
        result = self.run_tool("doctor", mode="schema_missing_interrupt")
        self.assertEqual(result.returncode, 8, result.stderr)
        self.assertIn("TurnInterruptParams", result.stdout)

    def test_doctor_requires_turn_started_contract(self) -> None:
        result = self.run_tool("doctor", mode="schema_missing_turn_started")
        self.assertEqual(result.returncode, 8, result.stderr)
        self.assertIn("TurnStartedNotification", result.stdout)

    def test_backup_roundtrip_and_private_modes(self) -> None:
        destination = self.root / "private-backup"
        backup = self.run_tool("backup", SESSION_ID, "--output-dir", str(destination))
        self.assertEqual(backup.returncode, 0, backup.stderr)
        payload = json.loads(backup.stdout)
        manifest = Path(payload["manifestPath"])
        verified = self.run_tool("verify-backup", str(manifest))
        self.assertEqual(verified.returncode, 0, verified.stderr)
        self.assertEqual(stat.S_IMODE(destination.stat().st_mode), 0o700)
        for path in destination.iterdir():
            self.assertEqual(stat.S_IMODE(path.stat().st_mode), 0o600, path)

    def test_recover_requires_confirmation_and_mandatory_backup(self) -> None:
        rejected = self.run_tool("recover", SESSION_ID)
        self.assertEqual(rejected.returncode, 2)
        parser_rejects_bypass = self.run_tool("recover", SESSION_ID, "--yes", "--skip-backup")
        self.assertEqual(parser_rejects_bypass.returncode, 2)

        destination = self.root / "recovery-backup"
        recovered = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(destination),
        )
        self.assertEqual(recovered.returncode, 0, recovered.stderr)
        payload = json.loads(recovered.stdout)
        self.assertTrue(payload["compaction"]["contextItemCompleted"])
        self.assertIsNone(payload["canary"])
        self.assertTrue(payload["postflight"]["prefixUnchanged"])
        self.assertEqual(self.rollout.read_bytes(), self.original)

    def test_initialize_rejects_different_codex_home(self) -> None:
        result = self.run_tool("probe", SESSION_ID, mode="initialize_mismatch")
        self.assertEqual(result.returncode, 8, result.stderr)
        self.assertIn("different CODEX_HOME", result.stdout)

    def test_resume_rejects_different_thread_id(self) -> None:
        result = self.run_tool("probe", SESSION_ID, mode="wrong_resume")
        self.assertEqual(result.returncode, 5, result.stderr)
        self.assertIn("different thread id", result.stdout)

    def test_probe_rechecks_owner_immediately_before_resume(self) -> None:
        result = self.run_tool("probe", SESSION_ID, mode="probe_owner_race")
        self.assertEqual(result.returncode, 3, result.stderr)
        self.assertIn("open by another process", result.stdout)
        methods = [event.get("method") for event in self.read_events()]
        self.assertIn("initialize", methods)
        self.assertNotIn("thread/resume", methods)

    def test_retrying_compaction_error_is_counted_and_recovery_succeeds(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "retry-backup"),
            mode="retry_error",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        payload = json.loads(result.stdout)
        self.assertEqual(payload["compaction"]["retryingErrorsObserved"], 1)

    def test_unrelated_nonretry_error_does_not_fail_compaction(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "unrelated-error-backup"),
            mode="unrelated_error",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(json.loads(result.stdout)["compaction"]["contextItemCompleted"])

    def test_unchanged_effort_needs_no_settings_notification(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--effort",
            "medium",
            "--backup-dir",
            str(self.root / "unchanged-effort-backup"),
            mode="settings_no_notification",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        effort_change = json.loads(result.stdout)["effortChange"]
        self.assertEqual(effort_change["previous"], "medium")
        self.assertEqual(effort_change["requested"], "medium")
        self.assertFalse(effort_change["changed"])
        self.assertTrue(effort_change["verified"])

    def test_missing_compaction_lifecycle_fails_closed(self) -> None:
        destination = self.root / "failed-backup"
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(destination),
            "--operation-timeout",
            "0.25",
            mode="missing_item_completed",
        )
        self.assertEqual(result.returncode, 6)
        self.assertIn("timed out", result.stdout)
        progress = json.loads(result.stdout)["partial"]["compaction"]
        self.assertTrue(progress["requestAccepted"])
        self.assertTrue(progress["turnStarted"])
        self.assertTrue(progress["contextItemStarted"])
        self.assertFalse(progress["contextItemCompleted"])
        self.assertEqual(progress["terminalStatus"], "completed")

    def test_explicit_canary_only(self) -> None:
        canary = self.run_tool("canary", SESSION_ID, "--yes", "--expected", "FIXTURE_OK")
        self.assertEqual(canary.returncode, 0, canary.stderr)
        self.assertEqual(json.loads(canary.stdout)["canary"]["response"], "FIXTURE_OK")

    def test_canary_rejects_collaboration_tool_item(self) -> None:
        result = self.run_tool(
            "canary",
            SESSION_ID,
            "--yes",
            "--expected",
            "FIXTURE_OK",
            mode="collab_canary",
        )
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertIn("collabAgentToolCall", result.stdout)

    def test_canary_rejects_started_only_tool_item(self) -> None:
        result = self.run_tool(
            "canary",
            SESSION_ID,
            "--yes",
            "--expected",
            "FIXTURE_OK",
            mode="collab_started_only",
        )
        self.assertEqual(result.returncode, 7, result.stderr)
        progress = json.loads(result.stdout)["partial"]["canary"]
        self.assertIn("collabAgentToolCall", progress["observedItemTypes"])

    def test_canary_allows_automatic_context_compaction(self) -> None:
        result = self.run_tool(
            "canary",
            SESSION_ID,
            "--yes",
            "--expected",
            "FIXTURE_OK",
            mode="auto_compact_canary",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(json.loads(result.stdout)["canary"]["response"], "FIXTURE_OK")

    def test_canary_reports_explicit_sticky_effort_change(self) -> None:
        result = self.run_tool(
            "canary",
            SESSION_ID,
            "--yes",
            "--effort",
            "low",
            "--expected",
            "FIXTURE_OK",
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        effort = json.loads(result.stdout)["effortChange"]
        self.assertTrue(effort["changed"])
        self.assertTrue(effort["verified"])

    def test_compaction_timeout_interrupts_inflight_turn(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "compaction-timeout-backup"),
            "--operation-timeout",
            "0.2",
            mode="compaction_timeout",
            timeout=10,
        )
        self.assertEqual(result.returncode, 6, result.stderr)
        interrupts = [event for event in self.read_events() if event.get("method") == "turn/interrupt"]
        self.assertEqual(len(interrupts), 1)
        self.assertEqual(
            interrupts[0]["params"],
            {
                "threadId": SESSION_ID,
                "turnId": "aaaaaaaa-bbbb-4ccc-8ddd-eeeeeeeeeeee",
            },
        )

    def test_preitem_compaction_timeout_interrupts_started_turn(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "preitem-timeout-backup"),
            "--operation-timeout",
            "0.2",
            mode="preitem_compaction_timeout",
            timeout=10,
        )
        self.assertEqual(result.returncode, 6, result.stderr)
        interrupts = [event for event in self.read_events() if event.get("method") == "turn/interrupt"]
        self.assertEqual(len(interrupts), 1)
        progress = json.loads(result.stdout)["partial"]["compaction"]
        self.assertTrue(progress["turnStarted"])
        self.assertFalse(progress["contextItemStarted"])
        self.assertTrue(progress["interrupt"]["requestAccepted"])

    def test_canary_timeout_interrupts_inflight_turn(self) -> None:
        result = self.run_tool(
            "canary",
            SESSION_ID,
            "--yes",
            "--expected",
            "FIXTURE_OK",
            "--operation-timeout",
            "0.2",
            mode="canary_timeout",
            timeout=10,
        )
        self.assertEqual(result.returncode, 6, result.stderr)
        interrupts = [event for event in self.read_events() if event.get("method") == "turn/interrupt"]
        self.assertEqual(len(interrupts), 1)
        self.assertEqual(
            interrupts[0]["params"],
            {
                "threadId": SESSION_ID,
                "turnId": "99999999-8888-4777-8666-555555555555",
            },
        )

    def test_failure_preserves_backup_effort_and_postflight_evidence(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--effort",
            "low",
            "--backup-dir",
            str(self.root / "partial-evidence-backup"),
            "--operation-timeout",
            "0.2",
            mode="mutate_prefix_compaction_timeout",
            timeout=10,
        )
        self.assertEqual(result.returncode, 6, result.stderr)
        payload = json.loads(result.stdout)
        partial = payload["partial"]
        self.assertEqual(partial["backup"]["sourceSha256"], hashlib.sha256(self.original).hexdigest())
        self.assertTrue(partial["effortChange"]["changed"])
        self.assertTrue(partial["effortChange"]["verified"])
        self.assertIn("postflight", partial)
        evidence = (payload["error"] + json.dumps(partial["postflight"])).lower()
        self.assertIn("prefix changed", evidence)

    def test_postflight_filesystem_failure_keeps_structured_evidence(self) -> None:
        result = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "deleted-rollout-backup"),
            mode="delete_rollout",
        )
        self.assertEqual(result.returncode, 5, result.stderr)
        payload = json.loads(result.stdout)
        self.assertIn("filesystem verification failed", payload["error"])
        self.assertTrue(payload["partial"]["backup"]["sourceSha256"])
        self.assertNotIn("Traceback", result.stderr)

    def test_keyboard_interrupt_preserves_backup_interrupt_and_postflight(self) -> None:
        env = self.env.copy()
        env["FAKE_CODEX_MODE"] = "compaction_timeout"
        process = subprocess.Popen(
            self.tool_command(
                "recover",
                SESSION_ID,
                "--yes",
                "--backup-dir",
                str(self.root / "keyboard-interrupt-backup"),
                "--operation-timeout",
                "30",
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
        )
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            if any(event.get("method") == "thread/compact/start" for event in self.read_events()):
                break
            time.sleep(0.02)
        else:
            process.kill()
            self.fail("fake app-server never received compaction request")
        process.send_signal(signal.SIGINT)
        stdout, stderr = process.communicate(timeout=10)
        self.assertEqual(process.returncode, 130, stderr)
        payload = json.loads(stdout)
        self.assertTrue(payload["partial"]["backup"]["sourceSha256"])
        interrupt = payload["partial"]["operationDetails"]["interrupt"]
        self.assertTrue(interrupt["requestAccepted"])
        self.assertTrue(payload["partial"]["postflight"]["prefixUnchanged"])

    def test_plain_failure_prints_partial_evidence(self) -> None:
        env = self.env.copy()
        env["FAKE_CODEX_MODE"] = "compaction_timeout"
        result = subprocess.run(
            self.tool_command(
                "recover",
                SESSION_ID,
                "--yes",
                "--backup-dir",
                str(self.root / "plain-failure-backup"),
                "--operation-timeout",
                "0.2",
                json_output=False,
            ),
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            env=env,
            timeout=10,
        )
        self.assertEqual(result.returncode, 6)
        self.assertIn("partial:", result.stderr)
        self.assertIn("manifestPath", result.stderr)

    def test_append_only_postflight_accepts_append_and_rejects_prefix_change(self) -> None:
        appended = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "append-backup"),
            mode="append",
        )
        self.assertEqual(appended.returncode, 0, appended.stderr)
        self.assertGreater(json.loads(appended.stdout)["postflight"]["bytesAppended"], 0)

        # Reset to a clean fixture before testing forbidden prefix mutation.
        self.rollout.write_bytes(self.original)
        mutated = self.run_tool(
            "recover",
            SESSION_ID,
            "--yes",
            "--backup-dir",
            str(self.root / "mutated-backup"),
            mode="mutate_prefix",
        )
        self.assertEqual(mutated.returncode, 5)
        self.assertIn("prefix changed", mutated.stdout)

    def test_backup_refuses_git_worktree_destination(self) -> None:
        worktree = self.root / "repo"
        (worktree / ".git").mkdir(parents=True)
        result = self.run_tool(
            "backup",
            SESSION_ID,
            "--output-dir",
            str(worktree / "private"),
        )
        self.assertEqual(result.returncode, 4)
        self.assertIn("Git worktree", result.stdout)

    def test_schema_error_redacts_secret(self) -> None:
        result = self.run_tool("doctor", mode="schema_error")
        self.assertNotEqual(result.returncode, 0)
        combined = result.stdout + result.stderr
        self.assertNotIn("sk-SUPERSECRET", combined)
        self.assertIn("REDACTED", combined)

    def test_oversized_unparseable_final_record_fails_closed(self) -> None:
        with self.rollout.open("ab") as handle:
            handle.write(b"x" * (9 * 1024 * 1024) + b"\n")
        result = self.run_tool("recover", SESSION_ID, "--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("too large to validate", result.stdout)

    def test_final_json_array_is_rejected(self) -> None:
        with self.rollout.open("ab") as handle:
            handle.write(b"[]\n")
        result = self.run_tool("recover", SESSION_ID, "--dry-run")
        self.assertEqual(result.returncode, 2)
        self.assertIn("invalid JSON", result.stdout)

    def test_same_size_live_mutation_is_rejected_by_backup_match(self) -> None:
        module_name = "codex_session_recovery_fixture_import"
        spec = importlib.util.spec_from_file_location(module_name, TOOL)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            before = self.rollout.stat()
            expected_sha = hashlib.sha256(self.original).hexdigest()
            backup = {
                "sourceDevice": before.st_dev,
                "sourceInode": before.st_ino,
                "sourceBytes": before.st_size,
                "sourceMtimeNs": before.st_mtime_ns,
                "sourceSha256": expected_sha,
            }
            mutated = bytearray(self.original)
            mutated[0] = ord("X") if mutated[0] != ord("X") else ord("Y")
            self.rollout.write_bytes(mutated)
            os.utime(self.rollout, ns=(before.st_atime_ns, before.st_mtime_ns))
            after = self.rollout.stat()
            self.assertEqual(
                (after.st_dev, after.st_ino, after.st_size, after.st_mtime_ns),
                (before.st_dev, before.st_ino, before.st_size, before.st_mtime_ns),
            )
            with self.assertRaises(module.RecoveryError) as raised:
                module.verify_live_matches_backup(self.rollout, backup)
            self.assertEqual(raised.exception.exit_code, 4)
            self.assertIn("no longer matches", str(raised.exception))
        finally:
            sys.modules.pop(module_name, None)

    def test_postflight_rejects_parent_symlink_swap(self) -> None:
        module_name = "codex_session_recovery_parent_symlink_import"
        spec = importlib.util.spec_from_file_location(module_name, TOOL)
        self.assertIsNotNone(spec)
        self.assertIsNotNone(spec.loader)
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        try:
            spec.loader.exec_module(module)
            before = self.rollout.stat()
            prefix = hashlib.sha256(self.original).hexdigest()
            real_directory = self.session_dir.with_name("01-real")
            self.session_dir.rename(real_directory)
            self.session_dir.symlink_to(real_directory.name, target_is_directory=True)
            self.assertEqual(self.rollout.stat().st_ino, before.st_ino)
            with self.assertRaises(module.RecoveryError) as raised:
                module.append_only_postcheck(self.rollout, before, prefix)
            self.assertIn("symlink component", str(raised.exception))
        finally:
            sys.modules.pop(module_name, None)


if __name__ == "__main__":
    unittest.main(verbosity=2)
