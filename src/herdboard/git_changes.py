"""The lines that a card's worktree adds and removes since its branch left the base, for the board.

The count covers the branch commits since the merge base with the base, the uncommitted edits to
tracked files, and the untracked text files. It is optional: a Git or state-file error gives no
count and no error.
"""

from __future__ import annotations

import subprocess
from dataclasses import dataclass
from pathlib import Path

from . import start
from .model import HerdboardError

# An untracked file larger than this, or with a NUL byte in its first BINARY_PROBE bytes, does not count.
MAX_UNTRACKED_BYTES = 1024 * 1024
BINARY_PROBE = 8000


@dataclass(frozen=True)
class Changes:
    added: int
    removed: int
    files: int


def _git(directory: Path, *args: str) -> str | None:
    try:
        result = subprocess.run(["git", "-C", str(directory), *args], capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout if result.returncode == 0 else None


def _untracked_lines(path: Path) -> int | None:
    """The line count of an untracked text file. None for a binary file, a large file or a read error."""
    try:
        if path.stat().st_size > MAX_UNTRACKED_BYTES:
            return None
        data = path.read_bytes()
    except OSError:
        return None
    if b"\0" in data[:BINARY_PROBE]:
        return None
    return data.count(b"\n") + (1 if data and not data.endswith(b"\n") else 0)


def worktree_changes(worktree: Path, base: str | None, branch: str | None) -> Changes | None:
    """The changes in the worktree since its branch left the base: the record base, else the branch
    upstream. None when a Git command fails or the base is unknown."""
    if not base:
        upstream = _git(worktree, "rev-parse", "--abbrev-ref", f"{branch}@{{upstream}}") if branch else None
        base = upstream.strip() if upstream else None
        if not base:
            return None
    merge_base = _git(worktree, "merge-base", base, "HEAD")
    if not merge_base:
        return None
    # --numstat, not --shortstat: its output is not translated. A binary file shows "-" counts.
    numstat = _git(worktree, "diff", "--numstat", merge_base.strip())
    untracked = _git(worktree, "ls-files", "-z", "--others", "--exclude-standard")
    if numstat is None or untracked is None:
        return None
    added = removed = files = 0
    for line in numstat.splitlines():
        plus, minus, _ = line.split("\t", 2)
        added += int(plus) if plus.isdigit() else 0
        removed += int(minus) if minus.isdigit() else 0
        files += 1
    for name in untracked.split("\0"):
        lines = _untracked_lines(worktree / name) if name else None
        if lines is not None:
            added += lines
            files += 1
    return Changes(added, removed, files)


def mark(cards) -> None:
    """Set the board-only changes of each card whose worktree exists. Run it after `start.mark_removed`."""
    try:
        # Writers replace the file atomically; this optional count needs no read lock.
        records = start._read(start.state_dir() / "starts.json")
    except HerdboardError:
        records = {}
    for card in cards:
        card.changes = None
        if not card.worktree or card.repoless:
            continue
        record = records.get(card.ref)
        if not isinstance(record, dict):
            record = next((r for r in records.values() if isinstance(r, dict) and r.get("ref") == card.ref), None)
        if not record or not record.get("worktree_path"):
            continue
        card.changes = worktree_changes(Path(record["worktree_path"]), record.get("base"), record.get("branch"))
