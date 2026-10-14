#!/usr/bin/env python3
"""Synthetic source tests; never touches a real project or browser."""

import contextlib
import io
import json
from pathlib import Path
import stat
import tempfile
from types import SimpleNamespace
import unittest
import warnings
import zipfile

import overleaf_sync as sync


class SyncTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)

    def tree(self, name, files):
        root = self.root / name
        root.mkdir()
        for relative, content in files.items():
            path = root / relative
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_bytes(content)
        return root

    def plan(self, base, local, remote, mapping=None):
        b = self.tree("base", base) if base is not None else None
        l, r = self.tree("local", local), self.tree("remote", remote)
        mapping_file = self.root / "mapping.json"
        mapping_file.write_text(json.dumps(mapping or {}))
        args = SimpleNamespace(base=b, local=l, remote=r, map=mapping_file, out=self.root / "plan")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sync.plan(args), 0)
        # Planning must preserve inputs, including untracked local files.
        self.assertEqual(sync.snapshot(l), local)
        self.assertEqual(sync.snapshot(r), remote)
        if b:
            self.assertEqual(sync.snapshot(b), base)
        return json.loads((args.out / "report.json").read_text()), args

    def test_pull_push_new_files_and_untracked_exclusion(self):
        base = {"a.tex": b"old", "b.tex": b"old", "same.cls": b"same"}
        local = {**base, "a.tex": b"local", "new.bib": b"new", "secret.txt": b"private"}
        remote = {**base, "b.tex": b"remote", "new.sty": b"style"}
        report, _ = self.plan(base, local, remote, {"files": {"new.bib": "new.bib"}})
        statuses = {r["remote_path"]: r["status"] for r in report["files"]}
        self.assertEqual(statuses, {"a.tex": "push", "b.tex": "pull", "same.cls": "unchanged",
                                    "new.bib": "push", "new.sty": "pull"})

    def test_nonoverlapping_edits_preserved_in_candidate(self):
        b = b"title\nkeep1\nkeep2\nkeep3\nkeep4\ncaption\n"
        local = b.replace(b"title", b"local title")
        remote = b.replace(b"caption", b"remote caption")
        report, args = self.plan({"main.tex": b}, {"main.tex": local}, {"main.tex": remote})
        row = report["files"][0]
        self.assertEqual(row["status"], "merge_review")
        self.assertEqual((args.out / row["candidate"]).read_bytes(),
                         b.replace(b"title", b"local title").replace(b"caption", b"remote caption"))

    def test_overlapping_text_and_binary_conflicts(self):
        base = {"main.tex": b"base\n", "fig.pdf": b"%PDF-base"}
        local = {"main.tex": b"local\n", "fig.pdf": b"%PDF-local"}
        remote = {"main.tex": b"remote\n", "fig.pdf": b"%PDF-remote"}
        report, args = self.plan(base, local, remote)
        self.assertEqual(report["counts"], {"conflict": 2})
        rows = {row["remote_path"]: row for row in report["files"]}
        self.assertNotIn("candidate", rows["fig.pdf"])
        candidate = (args.out / rows["main.tex"]["candidate"]).read_bytes()
        for marker in (b"<<<<<<< LOCAL", b"||||||| BASE", b">>>>>>> OVERLEAF"):
            self.assertIn(marker, candidate)

    def test_missing_files_are_reviewed_including_both_deleted(self):
        base = {"a.tex": b"a", "b.tex": b"b", "c.tex": b"c"}
        report, _ = self.plan(base, {"a.tex": b"a"}, {"b.tex": b"b"})
        self.assertEqual(report["counts"], {"review_missing": 3})

    def test_bootstrap_never_chooses_one_side(self):
        report, _ = self.plan(None, {"same.tex": b"x", "a.tex": b"l"},
                              {"same.tex": b"x", "a.tex": b"r", "b.tex": b"r"})
        self.assertEqual(report["counts"], {"bootstrap_review": 2, "converged": 1})

    def test_explicit_filename_and_literal_normalization(self):
        remote = {"main.tex": b"\\includegraphics{fig1.pdf}\n", "figures/fig1.pdf": b"pdf"}
        local = {"main.tex": b"\\includegraphics{reviewed.pdf}\n", "figures/reviewed.pdf": b"pdf"}
        mapping = {"files": {"figures/fig1.pdf": "figures/reviewed.pdf"},
                   "local_to_remote_text": {"main.tex": [{"local": "{reviewed.pdf}", "remote": "{fig1.pdf}"}]}}
        report, _ = self.plan(remote, local, remote, mapping)
        self.assertEqual(report["counts"], {"unchanged": 2})

    def test_existing_output_is_never_replaced(self):
        _, args = self.plan({}, {}, {})
        original = (args.out / "report.json").read_bytes()
        with self.assertRaisesRegex(ValueError, "fresh directory"):
            sync.plan(args)
        self.assertEqual((args.out / "report.json").read_bytes(), original)

    def test_verification_detects_wrong_asset_and_concurrent_edit(self):
        before = self.tree("before", {"main.tex": b"old", "fig.pdf": b"old"})
        after = self.tree("after", {"main.tex": b"collaborator edit", "fig.pdf": b"wrong"})
        expected = self.tree("expected", {"fig.pdf": b"right"})
        args = SimpleNamespace(before=before, after=after, allow=["fig.pdf"], expected=expected)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            self.assertEqual(sync.verify(args), 1)
        result = json.loads(out.getvalue())
        self.assertEqual(result["unexpected"], ["main.tex"])
        self.assertEqual(result["expected_mismatches"], ["fig.pdf"])
        (after / "main.tex").write_bytes(b"old")
        (after / "fig.pdf").write_bytes(b"right")
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(sync.verify(args), 0)

    def test_zip_paths_duplicates_and_symlinks_are_rejected(self):
        for i, name in enumerate(("../escape.tex", "/absolute.tex", "a/../escape", "a\\b", "C:/x")):
            archive = self.root / f"bad{i}.zip"
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr(name, b"x")
            with self.assertRaises(ValueError):
                sync.snapshot(archive)
        archive = self.root / "duplicate.zip"
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", UserWarning)
            with zipfile.ZipFile(archive, "w") as z:
                z.writestr("main.tex", b"a")
                z.writestr("main.tex", b"b")
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            sync.snapshot(archive)
        archive = self.root / "symlink.zip"
        with zipfile.ZipFile(archive, "w") as z:
            info = zipfile.ZipInfo("link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            z.writestr(info, "../outside")
        with self.assertRaisesRegex(ValueError, "Nonregular"):
            sync.snapshot(archive)

    def test_mapping_cannot_escape_or_alias_another_remote_file(self):
        outside = self.root / "outside.tex"
        outside.write_bytes(b"private")
        local = self.tree("local", {})
        (local / "link.tex").symlink_to(outside)
        with self.assertRaisesRegex(ValueError, "escapes"):
            sync.local_bytes(local, "link.tex")
        with self.assertRaises(ValueError):
            sync.local_bytes(local, "../outside.tex")
        with self.assertRaises(ValueError):
            sync.snapshot(local)
        remote = self.tree("remote", {"a.tex": b"a", "b.tex": b"b"})
        mapping = self.root / "mapping.json"
        mapping.write_text(json.dumps({"files": {"a.tex": "b.tex"}}))
        args = SimpleNamespace(local=local, remote=remote, base=None, map=mapping, out=self.root / "plan")
        with self.assertRaisesRegex(ValueError, "same local path"):
            sync.plan(args)


if __name__ == "__main__":
    unittest.main()
