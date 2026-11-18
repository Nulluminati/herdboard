"""Git changes: the lines that a card's worktree adds and removes since its branch left the base."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from herdboard import git_changes
from herdboard.git_changes import Changes
from herdboard.store import CardView
from support.git_env import isolated


def card(ref, worktree=True, repoless=False):
    return CardView(
        ref=ref,
        board="api",
        path=None,
        column="In progress",
        title="Ship it",
        checked=False,
        due=None,
        tags=[],
        body=[],
        worktree=worktree,
        repoless=repoless,
    )


class WorktreeCase(unittest.TestCase):
    """A repository with a `main` branch and a worktree of the branch `feat/x` made from it."""

    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.enterContext(patch.dict(os.environ, isolated()))
        self.repo = self.root / "repo"
        self.repo.mkdir()
        self.git(self.repo, "init", "-q", "-b", "main")
        (self.repo / "app.py").write_text("one\ntwo\nthree\n")
        self.git(self.repo, "add", ".")
        self.git(self.repo, "commit", "-q", "-m", "init")
        self.worktree = self.root / "work"
        self.git(self.repo, "worktree", "add", "-q", "-b", "feat/x", str(self.worktree), "main")

    def git(self, directory, *args):
        subprocess.run(["git", "-C", str(directory), *args], check=True, capture_output=True)

    def commit(self, message="change"):
        self.git(self.worktree, "add", ".")
        self.git(self.worktree, "commit", "-q", "-m", message)


class GitChangesTests(WorktreeCase):
    def test_a_commit_counts_its_added_and_removed_lines(self):
        (self.worktree / "app.py").write_text("one\nthree\nfour\nfive\nsix\n")
        self.commit()
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(3, 1, 1))

    def test_an_uncommitted_edit_to_a_tracked_file_counts(self):
        (self.worktree / "app.py").write_text("one\ntwo\nthree\nfour\n")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(1, 0, 1))

    def test_commits_and_uncommitted_edits_add_up(self):
        (self.worktree / "app.py").write_text("one\ntwo\nthree\nfour\n")
        self.commit()
        (self.worktree / "app.py").write_text("one\ntwo\nthree\nfour\nfive\n")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(2, 0, 1))

    def test_an_untracked_text_file_adds_its_lines_and_one_file(self):
        (self.worktree / "notes.md").write_text("a\nb\nc\nd\ne\n")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(5, 0, 1))

    def test_an_untracked_file_without_a_final_newline_counts_its_last_line(self):
        (self.worktree / "notes.md").write_text("a\nb")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(2, 0, 1))

    def test_an_ignored_file_does_not_count(self):
        (self.worktree / ".gitignore").write_text("*.log\n")
        self.commit()
        (self.worktree / "run.log").write_text("x\ny\n")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(1, 0, 1))

    def test_an_untracked_file_whose_name_is_not_utf8_counts(self):
        (self.worktree / os.fsdecode(b"bad-\xff.txt")).write_text("x\n")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(1, 0, 1))

    def test_a_renamed_file_is_one_file_with_no_lines(self):
        self.git(self.worktree, "mv", "app.py", "main.py")
        self.commit()
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(0, 0, 1))

    def test_counting_does_not_write_the_index(self):
        # A file whose time no longer matches the index makes a plain `git diff` refresh and write
        # the index, and an agent's `git add` at that moment fails on index.lock.
        os.utime(self.worktree / "app.py", (1_000_000_000, 1_000_000_000))
        found = subprocess.run(
            ["git", "-C", str(self.worktree), "rev-parse", "--git-path", "index"], capture_output=True, text=True
        )
        index = Path(found.stdout.strip())
        index = index if index.is_absolute() else self.worktree / index
        before = index.stat().st_mtime_ns
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(0, 0, 0))
        self.assertEqual(index.stat().st_mtime_ns, before)

    def test_a_git_command_that_hangs_gives_none(self):
        hung = subprocess.TimeoutExpired(["git"], git_changes.GIT_TIMEOUT)
        with patch.object(git_changes.subprocess, "run", side_effect=hung) as run:
            self.assertIsNone(git_changes.worktree_changes(self.worktree, "main", "feat/x"))
        self.assertEqual(run.call_args.kwargs["timeout"], git_changes.GIT_TIMEOUT)

    def test_an_untracked_binary_file_does_not_count(self):
        (self.worktree / "image.bin").write_bytes(b"\x89PNG\x00\x01\n\n\n")
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(0, 0, 0))

    def test_an_untracked_file_over_one_megabyte_does_not_count(self):
        (self.worktree / "big.txt").write_text("line\n" * 300_000)
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(0, 0, 0))

    def test_a_worktree_with_no_changes_gives_zero_counts(self):
        self.assertEqual(git_changes.worktree_changes(self.worktree, "main", "feat/x"), Changes(0, 0, 0))

    def test_a_record_with_no_base_uses_the_branch_upstream(self):
        self.git(self.worktree, "branch", "--set-upstream-to", "main", "feat/x")
        (self.worktree / "app.py").write_text("one\ntwo\nthree\nfour\n")
        self.commit()
        self.assertEqual(git_changes.worktree_changes(self.worktree, None, "feat/x"), Changes(1, 0, 1))

    def test_no_base_and_no_upstream_gives_none(self):
        self.assertIsNone(git_changes.worktree_changes(self.worktree, None, "feat/x"))

    def test_an_unknown_base_gives_none(self):
        self.assertIsNone(git_changes.worktree_changes(self.worktree, "nope", "feat/x"))

    def test_a_folder_that_is_not_a_git_repository_gives_none(self):
        folder = self.root / "plain"
        folder.mkdir()
        self.assertIsNone(git_changes.worktree_changes(folder, "main", "feat/x"))


class MarkTests(WorktreeCase):
    def setUp(self):
        super().setUp()
        self.state = self.root / "state" / "herdboard"
        self.state.mkdir(parents=True)
        self.enterContext(patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")}))

    def write(self, records):
        (self.state / "starts.json").write_text(json.dumps(records))

    def record(self, **extra):
        return {"ref": "t123", "worktree_path": str(self.worktree), "base": "main", "branch": "feat/x", **extra}

    def test_mark_sets_the_changes_of_a_card_with_a_worktree(self):
        self.write({"t123": self.record()})
        (self.worktree / "app.py").write_text("one\ntwo\nthree\nfour\n")
        item = card("t123")
        git_changes.mark([item])
        self.assertEqual(item.changes, Changes(1, 0, 1))

    def test_mark_counts_each_card_in_its_own_worktree(self):
        other = self.root / "other"
        self.git(self.repo, "worktree", "add", "-q", "-b", "feat/y", str(other), "main")
        self.write(
            {"t123": self.record(), "t456": {**self.record(ref="t456", branch="feat/y"), "worktree_path": str(other)}}
        )
        (self.worktree / "app.py").write_text("one\ntwo\nthree\nfour\n")
        (other / "app.py").write_text("one\n")
        cards = [card("t123"), card("t456")]
        git_changes.mark(cards)
        self.assertEqual([item.changes for item in cards], [Changes(1, 0, 1), Changes(0, 2, 1)])

    def test_a_record_found_by_its_ref_field_counts(self):
        self.write({"api/t123": self.record()})
        item = card("t123")
        git_changes.mark([item])
        self.assertEqual(item.changes, Changes(0, 0, 0))

    def test_mark_sets_none_for_a_card_with_no_worktree(self):
        self.write({"t123": self.record()})
        item = card("t123", worktree=False)
        item.changes = Changes(1, 1, 1)
        git_changes.mark([item])
        self.assertIsNone(item.changes)

    def test_mark_sets_none_for_a_repoless_card(self):
        self.write({"t123": self.record(mode="repoless")})
        item = card("t123", repoless=True)
        git_changes.mark([item])
        self.assertIsNone(item.changes)

    def test_mark_sets_none_for_a_card_with_no_record(self):
        self.write({})
        item = card("t123")
        git_changes.mark([item])
        self.assertIsNone(item.changes)

    def test_an_unreadable_state_file_sets_none(self):
        (self.state / "starts.json").write_text("not json")
        item = card("t123")
        git_changes.mark([item])
        self.assertIsNone(item.changes)


if __name__ == "__main__":
    unittest.main()
