"""Restore records: run herdboard's panes again after a Herdr restart.

Herdr restores a pane's workspace, label and working directory, but not the command that a
`herdr pane run` or a plugin pane started in it, so the pane comes back as a bare shell.
herdboard keeps one record for each pane it wants back, and the Herdr startup hook runs
`herdboard restore-panes`, which runs the recorded command again in each matching pane.

A record is one JSON file in `<state>/herdboard/restore/`, with the string fields
`workspace_id`, `label`, `cwd` and `command`. Pane IDs can change over a restore, so a record
matches every pane with the same workspace, label and working directory. Any tool can write a
record in this format.
"""

from __future__ import annotations

import hashlib
import json
import os
import tempfile
import time
from pathlib import Path

from .linear_source import state_dir
from .model import HerdboardError
from .start import herdr

FIELDS = ("workspace_id", "label", "cwd", "command")

# How long `restore_panes` waits for the shell of a restored pane to start.
SHELL_WAIT_SECONDS = 10
SHELL_POLL_SECONDS = 0.5


def restore_dir() -> Path:
    return state_dir() / "restore"


def _record_path(workspace_id: str, label: str, cwd: str) -> Path:
    key = hashlib.sha256("\0".join((workspace_id, label, cwd)).encode()).hexdigest()[:20]
    return restore_dir() / f"{key}.json"


def remember(workspace_id: str, label: str, cwd: str, command: str) -> None:
    """Keep a record that runs `command` again in the pane after a Herdr restart.

    Best effort: a pane without a record only comes back as a shell.
    """
    path = _record_path(workspace_id, label, cwd)
    record = {"workspace_id": workspace_id, "label": label, "cwd": cwd, "command": command}
    temp = None
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temp = tempfile.mkstemp(dir=path.parent, prefix=f".{path.name}.")
        with os.fdopen(fd, "w", encoding="utf-8") as handle:
            json.dump(record, handle)
        os.replace(temp, path)
        temp = None
    except OSError:
        pass
    finally:
        if temp is not None:
            Path(temp).unlink(missing_ok=True)


def remember_pane(pane_id: str, command: str) -> None:
    """Keep a record for a Herdr pane, read from Herdr. A pane without a label gets none:
    without one, the record would match every shell in the same folder."""
    try:
        pane = (herdr("pane", "get", pane_id, tolerated=("pane_not_found",)) or {}).get("pane") or {}
    except HerdboardError:
        return
    values = [pane.get("workspace_id"), pane.get("label"), pane.get("cwd")]
    if all(isinstance(value, str) and value for value in values):
        remember(*values, command)


def _records() -> list[tuple[Path, dict]]:
    found = []
    try:
        paths = sorted(restore_dir().glob("*.json"))
    except OSError:
        return found
    for path in paths:
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            continue
        if isinstance(record, dict) and all(isinstance(record.get(field), str) and record[field] for field in FIELDS):
            found.append((path, record))
    return found


def forget(workspace_id: str, label: str | None = None) -> None:
    """Drop the records of a workspace, or of the panes with one label in it."""
    for path, record in _records():
        if record["workspace_id"] == workspace_id and (label is None or record["label"] == label):
            path.unlink(missing_ok=True)


def idle_shell(info: dict) -> bool:
    """True when the pane's only foreground process is its own shell, with no `-c` command.

    A pane that Herdr starts with a launch command (`sh -c ...`) runs that command again by
    itself, so it is not idle.
    """
    processes = info.get("foreground_processes") or []
    if len(processes) != 1:
        return False
    process = processes[0]
    argv = process.get("argv") or []
    return process.get("pid") == info.get("shell_pid") and bool(argv) and "-c" not in argv[1:]


def _process_info(pane_id: str) -> dict | None:
    try:
        found = herdr("pane", "process-info", "--pane", pane_id, tolerated=("pane_not_found",))
    except HerdboardError:
        return None
    return (found or {}).get("process_info")


def restore_panes() -> None:
    """Run each record's command in its restored panes, and drop the records with no pane."""
    records = _records()
    if not records:
        return
    try:
        panes = herdr("pane", "list").get("panes") or []
    except HerdboardError:
        return
    waiting = []
    for path, record in records:
        matches = [
            p["pane_id"]
            for p in panes
            if p.get("workspace_id") == record["workspace_id"]
            and p.get("label") == record["label"]
            and p.get("cwd") == record["cwd"]
        ]
        if not matches:
            path.unlink(missing_ok=True)
        waiting += [(pane_id, record["command"]) for pane_id in matches]
    deadline = time.monotonic() + SHELL_WAIT_SECONDS
    while waiting:
        later = []
        for pane_id, command in waiting:
            info = _process_info(pane_id)
            if info is None:
                continue
            if idle_shell(info):
                try:
                    herdr("pane", "run", pane_id, command, tolerated=("pane_not_found",))
                except HerdboardError:
                    pass
            elif not info.get("foreground_processes"):
                later.append((pane_id, command))
        if not later or time.monotonic() >= deadline:
            return
        waiting = later
        time.sleep(SHELL_POLL_SECONDS)
