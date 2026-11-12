"""The check for a newer herdboard release on GitHub, and the install of that release.

The board asks the GitHub Releases API once at start. `herdboard update` installs the latest release tag
for both the Herdr plugin and the `herdboard` command. Standard library only.
"""

import http.client
import importlib.metadata
import json
import os
import re
import subprocess
import urllib.request
from collections.abc import Callable

from .model import HerdboardError

RELEASES_URL = "https://api.github.com/repos/Nulluminati/herdboard/releases/latest"
# A non-empty value turns the release check off, so the board makes no network call.
NO_CHECK_VARIABLE = "HERDBOARD_NO_UPDATE_CHECK"
VERSION = re.compile(r"(\d+)\.(\d+)\.(\d+)")
PLUGIN_ID = "nulluminati.herdboard"
REPOSITORY = "Nulluminati/herdboard"
TOOL_SOURCE = "git+https://github.com/Nulluminati/herdboard"


class UpdateCheckFailedError(HerdboardError):
    """GitHub did not answer with a release."""

    code = "update_check_failed"


class UpdateUnsupportedError(HerdboardError):
    """herdboard is not a GitHub install of the Herdr plugin, such as a linked clone."""

    code = "update_unsupported"


class UpdateFailedError(HerdboardError):
    """A command of the update failed."""

    code = "update_failed"


def herdboard_version() -> str:
    """The installed herdboard version, or "" without package metadata."""
    try:
        return importlib.metadata.version("herdboard")
    except importlib.metadata.PackageNotFoundError:
        return ""


def latest_release(timeout: float = 3.0) -> str | None:
    """The version of the latest GitHub release, such as "0.2.0", or None when the check fails."""
    request = urllib.request.Request(
        RELEASES_URL, headers={"Accept": "application/vnd.github+json", "User-Agent": "herdboard"}
    )
    try:
        with urllib.request.urlopen(request, timeout=timeout) as reply:
            data = json.loads(reply.read())
    except (OSError, ValueError, http.client.HTTPException):
        # URLError, HTTPError and timeouts are OSErrors; bad JSON is a ValueError; a broken reply, such as
        # a truncated body or a bad status line, is an HTTPException.
        return None
    tag = data.get("tag_name") if isinstance(data, dict) else None
    if not isinstance(tag, str) or not tag:
        return None
    return tag.removeprefix("v")


def _parse(version: str) -> tuple[int, int, int] | None:
    match = VERSION.fullmatch(version)
    return (int(match[1]), int(match[2]), int(match[3])) if match else None


def is_newer(latest: str, current: str) -> bool:
    """True when `latest` is a higher X.Y.Z version than `current`; False when either does not parse."""
    new, old = _parse(latest), _parse(current)
    return new is not None and old is not None and new > old


def check_enabled() -> bool:
    """False when HERDBOARD_NO_UPDATE_CHECK has a value."""
    return not os.environ.get(NO_CHECK_VARIABLE)


def _run(argv: list[str]) -> subprocess.CompletedProcess:
    return subprocess.run(argv, capture_output=True, text=True)


def _checked(run: Callable[[list[str]], subprocess.CompletedProcess], argv: list[str]) -> str:
    """The command's output; UpdateFailedError with its error output when it fails."""
    try:
        result = run(argv)
    except OSError as error:
        raise UpdateFailedError(f"{argv[0]} did not run: {error}") from error
    if result.returncode != 0:
        detail = (result.stderr or result.stdout or "").strip() or f"exit code {result.returncode}"
        raise UpdateFailedError(f"{' '.join(argv[:3])} failed: {detail}")
    return result.stdout


def _plugin(herdr: str, run) -> dict:
    """The herdboard entry of `herdr plugin list`."""
    output = _checked(run, [herdr, "plugin", "list", "--plugin", PLUGIN_ID, "--json"])
    try:
        plugins = json.loads(output)["result"]["plugins"]
    except (ValueError, KeyError, TypeError) as error:
        raise UpdateFailedError(f"herdr plugin list gave output that herdboard cannot read: {error}") from error
    for plugin in plugins:
        if isinstance(plugin, dict) and plugin.get("plugin_id") == PLUGIN_ID:
            return plugin
    raise UpdateUnsupportedError(f"Herdr has no {PLUGIN_ID} plugin. Install it: herdr plugin install {REPOSITORY}")


def update(current: str, run: Callable[[list[str]], subprocess.CompletedProcess] = _run) -> dict:
    """Install the latest release for the Herdr plugin and the `herdboard` command, when it is newer.

    Only a GitHub install of the plugin updates. `run` runs each command and returns its result."""
    latest = latest_release()
    if latest is None:
        raise UpdateCheckFailedError(f"herdboard could not read the latest release from {RELEASES_URL}")
    if not is_newer(latest, current):
        return {"current": current, "latest": latest, "updated": False}
    herdr = os.environ.get("HERDR_BIN_PATH") or "herdr"
    plugin = _plugin(herdr, run)
    if (plugin.get("source") or {}).get("kind") != "github":
        root = plugin.get("plugin_root") or "the plugin folder"
        raise UpdateUnsupportedError(f"This install is a linked clone. Run git pull in {root} instead.")
    tag = f"v{latest}"
    _checked(run, [herdr, "plugin", "install", REPOSITORY, "--ref", tag, "--yes"])
    try:
        _checked(run, ["uv", "tool", "install", "--force", f"{TOOL_SOURCE}@{tag}"])
    except UpdateFailedError as error:
        raise UpdateFailedError(
            f"{error}\nThe Herdr plugin is at {tag}. Install the herdboard command for it: "
            f'uv tool install --force "{TOOL_SOURCE}@{tag}"'
        ) from error
    return {"current": current, "latest": latest, "updated": True}
