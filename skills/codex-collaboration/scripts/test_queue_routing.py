"""Disposable routing tests; never invokes Codex or sends a real message."""
import argparse
import contextlib
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import codex_session as session


THREAD = "11111111-2222-4333-8444-555555555555"
OTHER = "66666666-7777-4888-8999-000000000000"


class QueueRoutingTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        self.sessions = root / "sessions"
        self.sessions.mkdir()
        self.project = root / "recipient"
        self.project.mkdir()
        self.other = root / "unrelated"
        self.other.mkdir()
        self.rollout = self.sessions / f"rollout-fixture-{THREAD}.jsonl"
        self.metadata()
        self.patch = patch.object(session, "SESSIONS", self.sessions)
        self.patch.start()
        self.addCleanup(self.patch.stop)

    def metadata(self, **changes):
        payload = {"id": THREAD, "cwd": str(self.project)}
        payload.update(changes)
        self.rollout.write_text(json.dumps({"type": "session_meta", "payload": payload}) + "\n")

    def args(self, **changes):
        values = dict(thread=THREAD, expected_cwd=str(self.project),
                      message="Build finished. Read the packet; no reply needed.",
                      image=[], dry_run=False, min_quota_percent=5, skip_quota_check=False)
        values.update(changes)
        return argparse.Namespace(**values)

    def test_exact_uuid_and_workspace_match(self):
        result = session.verify_queue_target(THREAD, str(self.project))
        self.assertEqual(result["thread"], THREAD)
        self.assertEqual(result["cwd"], str(self.project))

    def test_names_prefixes_and_multiple_targets_are_rejected(self):
        for value in ("recipient", THREAD[:8], f"{THREAD},{OTHER}"):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                session.verify_queue_target(value, str(self.project))

    def test_wrong_workspace_stops_before_quota_or_send(self):
        with patch.object(session, "quota_gate") as quota, patch.object(session.subprocess, "run") as send:
            with self.assertRaisesRegex(SystemExit, "recipient workspace"):
                session.cmd_queue(self.args(expected_cwd=str(self.other)))
            quota.assert_not_called()
            send.assert_not_called()

    def test_metadata_id_mismatch_is_rejected(self):
        self.metadata(id=OTHER)
        with self.assertRaisesRegex(SystemExit, "metadata ID"):
            session.verify_queue_target(THREAD, str(self.project))

    def test_missing_or_duplicate_rollouts_are_rejected(self):
        with self.assertRaisesRegex(SystemExit, "found 0"):
            session.verify_queue_target(OTHER, str(self.project))
        duplicate = self.sessions / f"rollout-another-{THREAD}.jsonl"
        duplicate.write_bytes(self.rollout.read_bytes())
        with self.assertRaisesRegex(SystemExit, "found 2"):
            session.verify_queue_target(THREAD, str(self.project))

    def test_invalid_metadata_is_rejected(self):
        for raw in ('not-json', '{"type":"turn_context","payload":{}}',
                    '[]', '{"type":"session_meta","payload":[]}',
                    "x" * (1024 * 1024 + 1)):
            with self.subTest(raw=raw[:40]):
                self.rollout.write_text(raw)
                with self.assertRaises(SystemExit):
                    session.verify_queue_target(THREAD, str(self.project))

    def test_missing_or_relative_directory_is_rejected(self):
        for value in ("relative", str(self.other / "missing")):
            with self.subTest(value=value), self.assertRaises(SystemExit):
                session.verify_queue_target(THREAD, value)

    def test_unverifiable_recorded_directory_is_rejected(self):
        for value in (None, "relative", str(self.other / "missing")):
            self.metadata(cwd=value)
            with self.subTest(value=value), self.assertRaises(SystemExit):
                session.verify_queue_target(THREAD, str(self.project))

    def test_directory_alias_resolves_to_same_project(self):
        alias = self.project.parent / "alias"
        alias.symlink_to(self.project, target_is_directory=True)
        self.assertEqual(session.verify_queue_target(THREAD, str(alias))["cwd"], str(self.project))

    def test_dry_run_never_queries_quota_sends_or_prints_message(self):
        output = io.StringIO()
        with patch.object(session, "quota_gate") as quota, patch.object(session.subprocess, "run") as send, \
                contextlib.redirect_stdout(output):
            self.assertEqual(session.cmd_queue(self.args(dry_run=True)), 0)
        quota.assert_not_called()
        send.assert_not_called()
        result = json.loads(output.getvalue())
        self.assertFalse(result["sent"])
        self.assertEqual(result["recipient"]["thread"], THREAD)
        self.assertNotIn(self.args().message, output.getvalue())

    def test_empty_message_stops_before_send(self):
        with patch.object(session, "quota_gate") as quota, patch.object(session.subprocess, "run") as send:
            with self.assertRaisesRegex(SystemExit, "empty message"):
                session.cmd_queue(self.args(message="  "))
        quota.assert_not_called()
        send.assert_not_called()

    def test_quota_failure_does_not_send(self):
        with patch.object(session, "quota_gate", side_effect=SystemExit("quota")), \
                patch.object(session.subprocess, "run") as send:
            with self.assertRaisesRegex(SystemExit, "quota"):
                session.cmd_queue(self.args())
        send.assert_not_called()

    def test_recipient_is_rechecked_after_quota(self):
        with patch.object(session, "quota_gate", side_effect=lambda *a, **kw: self.metadata(cwd=str(self.other))), \
                patch.object(session.subprocess, "run") as send:
            with self.assertRaisesRegex(SystemExit, "recipient workspace"):
                session.cmd_queue(self.args())
        send.assert_not_called()

    def test_verified_send_uses_exact_uuid_once(self):
        with patch.object(session, "quota_gate") as quota, patch.object(session.subprocess, "run") as send:
            send.return_value.returncode = 0
            self.assertEqual(session.cmd_queue(self.args()), 0)
        quota.assert_called_once()
        send.assert_called_once_with(["codex", "queue", "--thread", THREAD,
                                     "--message", self.args().message])

    def test_cli_requires_expected_workspace(self):
        with contextlib.redirect_stderr(io.StringIO()), patch.object(session.subprocess, "run") as send:
            with self.assertRaises(SystemExit) as result:
                session.main(["queue", "--thread", THREAD, "--message", "example"])
        self.assertEqual(result.exception.code, 2)
        send.assert_not_called()


if __name__ == "__main__":
    unittest.main()
