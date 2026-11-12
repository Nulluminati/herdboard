"""Release herdboard: bump the version, commit, tag vX.Y.Z and push.

Usage: python3 bin/release.py X.Y.Z [--no-push]

Write the CHANGELOG.md section `## [X.Y.Z] - YYYY-MM-DD` first; the release commit includes it. The script
checks everything before it changes anything: the version, a clean main that equals origin/main, a new
tag and the changelog section. The tag push starts the GitHub workflow that publishes the release.
"""

import argparse
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")
VERSION_LINE = re.compile(r'^version = "([^"]*)"$', re.M)
VERSION_FILES = ("pyproject.toml", "herdr-plugin.toml")
CHANGELOG = "CHANGELOG.md"


class ReleaseError(Exception):
    """A check or a command failed; the message says what to do."""


def command(argv: list[str], root: Path) -> subprocess.CompletedProcess:
    return subprocess.run(argv, cwd=root, capture_output=True, text=True)


def run(argv: list[str], root: Path) -> str:
    """The command's output; ReleaseError with its error output when it fails."""
    try:
        result = command(argv, root)
    except OSError as error:
        raise ReleaseError(f"{argv[0]} did not run: {error}") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or f"exit code {result.returncode}"
        raise ReleaseError(f"{' '.join(argv)} failed: {detail}")
    return result.stdout


def current_version(root: Path) -> str:
    match = VERSION_LINE.search((root / "pyproject.toml").read_text(encoding="utf-8"))
    if not match:
        raise ReleaseError("pyproject.toml has no version line")
    return match[1]


def parse(version: str) -> tuple[int, int, int] | None:
    match = VERSION.fullmatch(version)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def check(version: str, root: Path) -> None:
    """Refuse the release when a precondition fails. Changes nothing."""
    new = parse(version)
    if new is None:
        raise ReleaseError(f"The version must be X.Y.Z, such as 0.2.0, not {version!r}")
    current = current_version(root)
    old = parse(current)
    if old is None or new <= old:
        raise ReleaseError(f"The version must be higher than {current}")
    changes = [line[3:] for line in run(["git", "status", "--porcelain"], root).splitlines() if line.strip()]
    others = [path for path in changes if path != CHANGELOG]
    if others:
        raise ReleaseError("Commit or remove these changes first: " + ", ".join(others))
    branch = run(["git", "rev-parse", "--abbrev-ref", "HEAD"], root).strip()
    if branch != "main":
        raise ReleaseError(f"Release from main, not {branch}")
    run(["git", "fetch", "origin", "main"], root)
    local, remote = run(["git", "rev-parse", "main", "origin/main"], root).split()
    if local != remote:
        raise ReleaseError("main differs from origin/main. Pull or push first")
    tag = f"v{version}"
    if command(["git", "rev-parse", "-q", "--verify", f"refs/tags/{tag}"], root).returncode == 0:
        raise ReleaseError(f"The tag {tag} exists")
    changelog = root / CHANGELOG
    text = changelog.read_text(encoding="utf-8") if changelog.exists() else ""
    if not re.search(rf"^## \[{re.escape(version)}\] - \d{{4}}-\d{{2}}-\d{{2}}$", text, re.M):
        raise ReleaseError(f"Add the section `## [{version}] - YYYY-MM-DD` to {CHANGELOG} first")


def bump(version: str, root: Path) -> None:
    """Write the version in the version files and the lock; restore the files when the lock fails."""
    originals = {name: (root / name).read_text(encoding="utf-8") for name in VERSION_FILES}
    for name, text in originals.items():
        (root / name).write_text(VERSION_LINE.sub(f'version = "{version}"', text, count=1), encoding="utf-8")
    try:
        run(["uv", "lock"], root)
    except ReleaseError:
        for name, text in originals.items():
            (root / name).write_text(text, encoding="utf-8")
        raise


def release(version: str, root: Path, push: bool) -> None:
    tag = f"v{version}"
    check(version, root)
    bump(version, root)
    run(["git", "add", *VERSION_FILES, "uv.lock", CHANGELOG], root)
    run(["git", "commit", "-m", f"chore(release): {tag}"], root)
    run(["git", "tag", "-a", tag, "-m", tag], root)
    finish = f"git push origin main {tag}"
    if not push:
        print(f"Tagged {tag}. Push it to publish the release: {finish}")
        return
    try:
        run(["git", "push", "origin", "main"], root)
        run(["git", "push", "origin", tag], root)
    except ReleaseError as error:
        raise ReleaseError(f"{error}\nThe commit and the tag exist. Finish with: {finish}") from error
    print(f"Released {tag}. The Release workflow publishes it on GitHub.")


def main(args: list[str] | None = None, root: Path = ROOT) -> int:
    parser = argparse.ArgumentParser(prog="release.py", description="Release herdboard X.Y.Z.")
    parser.add_argument("version", help="the new version, X.Y.Z")
    parser.add_argument("--no-push", action="store_true", help="commit and tag, but do not push")
    options = parser.parse_args(sys.argv[1:] if args is None else args)
    try:
        release(options.version, root, push=not options.no_push)
    except ReleaseError as error:
        print(f"release: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
