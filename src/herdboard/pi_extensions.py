"""Which pi-extensions flags pi has, and the warning when herdboard starts pi without them.

herdboard starts pi with flags that only the approval-mode and worker-sandbox extensions register. pi exits
on a flag it does not know, so herdboard asks `pi --help` before each pi start and leaves out the flags that
pi does not have. Extensions can be project-local, so the check runs in the card's folder.
"""

from __future__ import annotations

import re
import subprocess
import sys
from pathlib import Path

EXTENSIONS_URL = "https://github.com/Nulluminati/pi-extensions"
# Each flag that herdboard passes to pi, and the extension that registers it.
EXTENSION_FLAGS = {
    "--approval-mode": "approval-mode",
    "--approval-reject": "approval-mode",
    "--sandbox": "worker-sandbox",
}
# The flags that the work agent and the planner use, and those that reviewers use.
AGENT_FLAGS = ("--approval-reject",)
REVIEWER_FLAGS = ("--approval-mode", "--sandbox")
HELP_TIMEOUT_SECONDS = 30
# What runs without each extension, for each role.
EFFECTS = {
    ("approval-mode", "agent"): "the agent starts with no Jev command review",
    ("approval-mode", "reviewer"): "the reviewer starts without --approval-mode off; pi asks for no approvals",
    ("worker-sandbox", "reviewer"): "the reviewer runs with no sandbox",
}


def pi_flags(directory: Path) -> frozenset[str] | None:
    """The EXTENSION_FLAGS that `pi --help` lists in `directory`. None when pi does not answer."""
    try:
        result = subprocess.run(
            ["pi", "--help"], capture_output=True, text=True, timeout=HELP_TIMEOUT_SECONDS, cwd=directory
        )
    except (OSError, subprocess.TimeoutExpired):
        return None
    if result.returncode:
        return None
    return frozenset(flag for flag in EXTENSION_FLAGS if re.search(rf"(?<![\w-]){flag}(?![\w-])", result.stdout))


def missing_extensions(flags: frozenset[str] | None, needed: tuple[str, ...]) -> list[str]:
    """The extensions that register the `needed` flags that are not in `flags`. None counts as all present."""
    if flags is None:
        return []
    names = {EXTENSION_FLAGS[flag] for flag in needed if flag not in flags}
    return sorted(names)


def warning_text(missing: list[str], role: str) -> str:
    """One line per missing extension that says what runs without it, then where to get it."""
    lines = [f"pi has no {name} extension: {EFFECTS[(name, role)]}." for name in missing]
    return " ".join([*lines, f"Install {'it' if len(missing) == 1 else 'them'} from {EXTENSIONS_URL}."])


def warn(missing: list[str], role: str, store=None, ref: str | None = None) -> None:
    """Show the warning as a Herdr notification, on stderr, and in the card's log when there is a card."""
    # The start module imports this one.
    from . import activity
    from .model import HerdboardError
    from .start import notify

    text = warning_text(missing, role)
    print(f"herdboard: warning: {text}", file=sys.stderr)
    notify("pi extensions missing", text)
    if store is not None and ref:
        try:
            activity.append(store, ref, text, "herdboard")
        except HerdboardError as error:
            print(f"herdboard: cannot log the warning for {ref}: {error}", file=sys.stderr)


def check(directory: Path, needed: tuple[str, ...], role: str, store=None, ref: str | None = None):
    """pi's flags in `directory`, after a warning for each extension that a `needed` flag is missing from."""
    flags = pi_flags(directory)
    missing = missing_extensions(flags, needed)
    if missing:
        warn(missing, role, store, ref)
    return flags
