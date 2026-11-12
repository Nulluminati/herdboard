"""bin/release.py: the checks before a release, and the version bump, commit, tag and push."""

import contextlib
import io
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from support.scripts import load_script

release = load_script("release")

PYPROJECT = '[project]\nname = "herdboard"\nversion = "0.1.0"\n\n[tool.x]\nversion = "9.9.9"\n'
PLUGIN = 'id = "nulluminati.herdboard"\nname = "herdboard"\nversion = "0.1.0"\nmin_herdr_version = "0.9.0"\n'
CHANGELOG = "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 2026-11-11\n\n### Added\n\n- A thing.\n"
MAIN = "1111111111111111111111111111111111111111"


class FakeGit:
    """Answers the release's commands like a clean main that equals origin/main."""

    def __init__(self):
        self.calls = []
        self.status = ""
        self.branch = "main"
        self.origin = MAIN
        self.tags = set()
        self.fail = None

    def __call__(self, argv, root):
        self.calls.append(argv)
        if self.fail and argv[: len(self.fail)] == self.fail:
            return subprocess.CompletedProcess(argv, 1, "", "it broke\n")
        out = ""
        if argv == ["git", "status", "--porcelain"]:
            out = self.status
        elif argv == ["git", "rev-parse", "--abbrev-ref", "HEAD"]:
            out = self.branch + "\n"
        elif argv == ["git", "rev-parse", "main", "origin/main"]:
            out = f"{MAIN}\n{self.origin}\n"
        elif argv[:4] == ["git", "rev-parse", "-q", "--verify"]:
            tag = argv[4].removeprefix("refs/tags/")
            return subprocess.CompletedProcess(argv, 0 if tag in self.tags else 1, "", "")
        return subprocess.CompletedProcess(argv, 0, out, "")

    def writes(self):
        """The commands that change something: everything after the checks."""
        reads = (["git", "status"], ["git", "rev-parse"], ["git", "fetch"])
        return [argv for argv in self.calls if not any(argv[: len(read)] == read for read in reads)]


class ReleaseTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        (self.root / "pyproject.toml").write_text(PYPROJECT)
        (self.root / "herdr-plugin.toml").write_text(PLUGIN)
        (self.root / "CHANGELOG.md").write_text(CHANGELOG)
        self.git = FakeGit()

    def run_release(self, *argv, expect=0):
        out, err = io.StringIO(), io.StringIO()
        with (
            patch.object(release, "command", self.git),
            contextlib.redirect_stdout(out),
            contextlib.redirect_stderr(err),
        ):
            code = release.main(list(argv), root=self.root)
        self.assertEqual(code, expect, f"stdout={out.getvalue()!r} stderr={err.getvalue()!r}")
        return out.getvalue(), err.getvalue()

    def assert_unchanged(self):
        self.assertEqual((self.root / "pyproject.toml").read_text(), PYPROJECT)
        self.assertEqual((self.root / "herdr-plugin.toml").read_text(), PLUGIN)
        self.assertEqual(self.git.writes(), [])

    def refuse(self, *argv, message):
        _, err = self.run_release(*argv, expect=1)
        self.assertIn(message, err)
        self.assert_unchanged()

    def test_a_release_bumps_commits_tags_and_pushes(self):
        out, _ = self.run_release("0.2.0")
        self.assertIn('[project]\nname = "herdboard"\nversion = "0.2.0"\n', (self.root / "pyproject.toml").read_text())
        # Only the first version line changes.
        self.assertIn('[tool.x]\nversion = "9.9.9"\n', (self.root / "pyproject.toml").read_text())
        self.assertEqual(
            (self.root / "herdr-plugin.toml").read_text(),
            PLUGIN.replace('version = "0.1.0"', 'version = "0.2.0"'),
        )
        self.assertEqual(
            self.git.writes(),
            [
                ["uv", "lock"],
                ["git", "add", "pyproject.toml", "herdr-plugin.toml", "uv.lock", "CHANGELOG.md"],
                ["git", "commit", "-m", "chore(release): v0.2.0"],
                ["git", "tag", "-a", "v0.2.0", "-m", "v0.2.0"],
                ["git", "push", "origin", "main"],
                ["git", "push", "origin", "v0.2.0"],
            ],
        )
        self.assertIn(["git", "fetch", "origin", "main"], self.git.calls)
        self.assertIn("v0.2.0", out)

    def test_no_push_stops_after_the_tag(self):
        out, _ = self.run_release("0.2.0", "--no-push")
        self.assertEqual(self.git.writes()[-1], ["git", "tag", "-a", "v0.2.0", "-m", "v0.2.0"])
        self.assertNotIn("push", [argv[1] for argv in self.git.writes()])
        self.assertIn("git push origin main v0.2.0", out)

    def test_an_uncommitted_changelog_goes_into_the_release_commit(self):
        self.git.status = " M CHANGELOG.md\n"
        self.run_release("0.2.0")
        self.assertIn(["git", "commit", "-m", "chore(release): v0.2.0"], self.git.writes())

    def test_refuses_a_version_that_is_not_x_y_z(self):
        for version in ("0.2", "v0.2.0", "0.2.0-rc1", "latest"):
            with self.subTest(version=version):
                self.refuse(version, message="X.Y.Z")

    def test_refuses_a_version_that_is_not_higher(self):
        self.refuse("0.1.0", message="higher than 0.1.0")
        self.refuse("0.0.9", message="higher than 0.1.0")

    def test_refuses_a_dirty_working_tree(self):
        self.git.status = " M src/herdboard/board.py\n?? notes.txt\n"
        self.refuse("0.2.0", message="src/herdboard/board.py")

    def test_refuses_another_branch(self):
        self.git.branch = "feat/x"
        self.refuse("0.2.0", message="main")

    def test_refuses_a_main_that_differs_from_origin(self):
        self.git.origin = "2222222222222222222222222222222222222222"
        self.refuse("0.2.0", message="origin/main")

    def test_refuses_when_the_fetch_fails(self):
        self.git.fail = ["git", "fetch"]
        self.refuse("0.2.0", message="it broke")

    def test_refuses_an_existing_tag(self):
        self.git.tags.add("v0.2.0")
        self.refuse("0.2.0", message="v0.2.0 exists")

    def test_refuses_a_changelog_without_the_section(self):
        self.refuse("0.3.0", message="## [0.3.0] - YYYY-MM-DD")

    def test_refuses_an_empty_changelog_section(self):
        for text in (
            "# Changelog\n\n## [Unreleased]\n\n## [0.2.0] - 2026-11-11\n",
            "# Changelog\n\n## [0.2.0] - 2026-11-11\n\n\n## [0.1.0] - 2026-10-01\n\n- Old.\n",
        ):
            with self.subTest(text=text):
                (self.root / "CHANGELOG.md").write_text(text)
                self.refuse("0.2.0", message="empty")

    def test_refuses_a_missing_changelog(self):
        (self.root / "CHANGELOG.md").unlink()
        self.refuse("0.2.0", message="CHANGELOG.md")

    def test_a_failed_lock_restores_the_version_files(self):
        self.git.fail = ["uv", "lock"]
        _, err = self.run_release("0.2.0", expect=1)
        self.assertIn("it broke", err)
        self.assertEqual((self.root / "pyproject.toml").read_text(), PYPROJECT)
        self.assertEqual((self.root / "herdr-plugin.toml").read_text(), PLUGIN)
        self.assertEqual(self.git.writes(), [["uv", "lock"]])

    def test_a_failed_push_names_the_command_to_finish(self):
        self.git.fail = ["git", "push", "origin", "main"]
        _, err = self.run_release("0.2.0", expect=1)
        self.assertIn("it broke", err)
        self.assertIn("git push origin main v0.2.0", err)
