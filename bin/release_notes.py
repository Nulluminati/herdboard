"""Check the release versions and print the release notes, for the Release workflow.

Usage: python3 bin/release_notes.py X.Y.Z > notes.md

Fails when pyproject.toml or herdr-plugin.toml has another version, or when CHANGELOG.md has no section
`## [X.Y.Z] - YYYY-MM-DD` with text. Prints the section's text without its heading.
"""

import re
import sys
import tomllib
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"\d+\.\d+\.\d+")


def notes(version: str, root: Path) -> str:
    """The CHANGELOG section of `version`; ValueError when a check fails."""
    if not VERSION.fullmatch(version):
        raise ValueError(f"The version must be X.Y.Z, not {version!r}")
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))["project"]["version"]
    plugin = tomllib.loads((root / "herdr-plugin.toml").read_text(encoding="utf-8"))["version"]
    for name, found in (("pyproject.toml", project), ("herdr-plugin.toml", plugin)):
        if found != version:
            raise ValueError(f"The tag is v{version}, but {name} has version {found}")
    text = (root / "CHANGELOG.md").read_text(encoding="utf-8")
    match = re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}\n(.*?)(?=^## |\Z)", text, re.M | re.S)
    if not match:
        raise ValueError(f"CHANGELOG.md has no section `## [{version}] - YYYY-MM-DD`")
    body = match[1].strip()
    if not body:
        raise ValueError(f"The CHANGELOG.md section of {version} is empty")
    return body + "\n"


def main(args: list[str] | None = None, root: Path = ROOT) -> int:
    args = sys.argv[1:] if args is None else args
    if len(args) != 1:
        print("usage: release_notes.py X.Y.Z", file=sys.stderr)
        return 2
    try:
        print(notes(args[0], root), end="")
    except (OSError, KeyError, ValueError) as error:
        # A missing file or version key, a bad TOML file, or a failed check.
        print(f"release_notes: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
