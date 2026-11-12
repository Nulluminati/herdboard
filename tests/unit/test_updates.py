"""The check for a newer herdboard release, and the `herdboard update` command."""

import http.client
import io
import json
import os
import subprocess
import unittest
import urllib.error
from unittest.mock import patch

from herdboard import updates
from support.herdboard_cli import CliTestCase


def response(body: bytes):
    """A fake urlopen result that a `with` block reads."""
    return io.BytesIO(body)


class LatestReleaseTests(unittest.TestCase):
    def latest(self, **kwargs):
        with patch("urllib.request.urlopen", **kwargs) as urlopen:
            result = updates.latest_release()
        return result, urlopen

    def test_returns_the_tag_without_the_v(self):
        result, urlopen = self.latest(return_value=response(json.dumps({"tag_name": "v0.2.0"}).encode()))
        self.assertEqual(result, "0.2.0")
        request = urlopen.call_args.args[0]
        self.assertEqual(request.full_url, updates.RELEASES_URL)
        self.assertEqual(request.get_header("Accept"), "application/vnd.github+json")
        self.assertEqual(request.get_header("User-agent"), "herdboard")
        self.assertEqual(urlopen.call_args.kwargs["timeout"], 3.0)

    def test_returns_none_without_a_network(self):
        self.assertIsNone(self.latest(side_effect=urllib.error.URLError("no route"))[0])

    def test_returns_none_when_no_release_exists(self):
        error = urllib.error.HTTPError(updates.RELEASES_URL, 404, "Not Found", {}, None)
        self.assertIsNone(self.latest(side_effect=error)[0])

    def test_returns_none_on_a_timeout(self):
        self.assertIsNone(self.latest(side_effect=TimeoutError("timed out"))[0])

    def test_returns_none_on_a_broken_http_reply(self):
        self.assertIsNone(self.latest(side_effect=http.client.BadStatusLine("HTTP/9"))[0])

        class Truncated(io.BytesIO):
            def read(self, *args):
                raise http.client.IncompleteRead(b"{", 10)

        self.assertIsNone(self.latest(return_value=Truncated())[0])

    def test_returns_none_on_bad_json(self):
        self.assertIsNone(self.latest(return_value=response(b"<html>"))[0])

    def test_returns_none_without_a_tag_name(self):
        self.assertIsNone(self.latest(return_value=response(b"{}"))[0])
        self.assertIsNone(self.latest(return_value=response(b"[]"))[0])
        self.assertIsNone(self.latest(return_value=response(b'{"tag_name": 2}'))[0])


class IsNewerTests(unittest.TestCase):
    def test_compares_numbers_not_text(self):
        self.assertTrue(updates.is_newer("0.2.0", "0.1.0"))
        self.assertTrue(updates.is_newer("0.10.0", "0.9.0"))
        self.assertTrue(updates.is_newer("1.0.0", "0.99.99"))

    def test_an_equal_or_older_release_is_not_newer(self):
        self.assertFalse(updates.is_newer("0.1.0", "0.1.0"))
        self.assertFalse(updates.is_newer("0.1.0", "0.2.0"))

    def test_an_unparsable_version_is_not_newer(self):
        self.assertFalse(updates.is_newer("0.2", "0.1.0"))
        self.assertFalse(updates.is_newer("0.2.0", ""))
        self.assertFalse(updates.is_newer("0.2.0-rc1", "0.1.0"))
        self.assertFalse(updates.is_newer("latest", "0.1.0"))


class CheckEnabledTests(unittest.TestCase):
    def test_the_check_runs_without_the_variable(self):
        with patch.dict(os.environ):
            os.environ.pop("HERDBOARD_NO_UPDATE_CHECK", None)
            self.assertTrue(updates.check_enabled())

    def test_the_variable_turns_the_check_off(self):
        with patch.dict(os.environ, {"HERDBOARD_NO_UPDATE_CHECK": "1"}):
            self.assertFalse(updates.check_enabled())

    def test_an_empty_variable_keeps_the_check(self):
        with patch.dict(os.environ, {"HERDBOARD_NO_UPDATE_CHECK": ""}):
            self.assertTrue(updates.check_enabled())


def plugin_list(kind: str, root: str = "/home/me/.config/herdr/plugins/github/nulluminati.herdboard-1") -> str:
    """The `herdr plugin list --json` output for an installed herdboard."""
    plugin = {"plugin_id": "nulluminati.herdboard", "plugin_root": root, "source": {"kind": kind}}
    return json.dumps({"id": "cli:plugin", "result": {"plugins": [plugin], "type": "plugin_list"}})


class FakeRunner:
    """Answers each command with a (returncode, stdout, stderr) from a list, and records the commands."""

    def __init__(self, *answers):
        self.answers = list(answers)
        self.calls = []

    def __call__(self, argv):
        self.calls.append(argv)
        code, out, err = self.answers.pop(0)
        return subprocess.CompletedProcess(argv, code, out, err)


class UpdateTests(unittest.TestCase):
    def update(self, runner, latest="0.2.0", current="0.1.0"):
        with (
            patch.dict(os.environ, {"HERDR_BIN_PATH": "/opt/herdr"}),
            patch("herdboard.updates.latest_release", return_value=latest),
        ):
            return updates.update(current, run=runner)

    def test_the_latest_release_installs_nothing(self):
        runner = FakeRunner()
        self.assertEqual(
            self.update(runner, latest="0.2.0", current="0.2.0"),
            {"current": "0.2.0", "latest": "0.2.0", "updated": False},
        )
        self.assertEqual(runner.calls, [])

    def test_no_release_fails_the_check(self):
        runner = FakeRunner()
        with self.assertRaises(updates.UpdateCheckFailedError) as caught:
            self.update(runner, latest=None)
        self.assertEqual(caught.exception.code, "update_check_failed")
        self.assertEqual(runner.calls, [])

    def test_a_linked_clone_is_not_updated(self):
        runner = FakeRunner((0, plugin_list("local", "/home/me/Projects/herdboard"), ""))
        with self.assertRaises(updates.UpdateUnsupportedError) as caught:
            self.update(runner)
        self.assertEqual(caught.exception.code, "update_unsupported")
        self.assertIn("git pull", str(caught.exception))
        self.assertIn("/home/me/Projects/herdboard", str(caught.exception))
        self.assertEqual(
            runner.calls, [["/opt/herdr", "plugin", "list", "--plugin", "nulluminati.herdboard", "--json"]]
        )

    def test_a_missing_plugin_is_not_updated(self):
        empty = json.dumps({"result": {"plugins": [], "type": "plugin_list"}})
        runner = FakeRunner((0, empty, ""))
        with self.assertRaises(updates.UpdateUnsupportedError):
            self.update(runner)
        self.assertEqual(len(runner.calls), 1)

    def test_a_github_install_installs_the_release_tag(self):
        runner = FakeRunner((0, plugin_list("github"), ""), (0, "", ""), (0, "", ""))
        self.assertEqual(self.update(runner), {"current": "0.1.0", "latest": "0.2.0", "updated": True})
        self.assertEqual(
            runner.calls[1:],
            [
                ["/opt/herdr", "plugin", "install", "Nulluminati/herdboard", "--ref", "v0.2.0", "--yes"],
                ["uv", "tool", "install", "--force", "git+https://github.com/Nulluminati/herdboard@v0.2.0"],
            ],
        )

    def test_a_failed_plugin_install_stops_the_update(self):
        runner = FakeRunner((0, plugin_list("github"), ""), (1, "", "network down\n"))
        with self.assertRaises(updates.UpdateFailedError) as caught:
            self.update(runner)
        self.assertEqual(caught.exception.code, "update_failed")
        self.assertIn("network down", str(caught.exception))
        self.assertEqual(len(runner.calls), 2)

    def test_a_failed_tool_install_fails_the_update(self):
        runner = FakeRunner((0, plugin_list("github"), ""), (0, "", ""), (2, "", "no uv here"))
        with self.assertRaises(updates.UpdateFailedError) as caught:
            self.update(runner)
        self.assertIn("no uv here", str(caught.exception))
        # The plugin half is done: the message says so, and gives the command to finish.
        self.assertIn("The Herdr plugin is at v0.2.0", str(caught.exception))
        finish = 'uv tool install --force "git+https://github.com/Nulluminati/herdboard@v0.2.0"'
        self.assertIn(finish, str(caught.exception))

    def test_a_failed_plugin_install_does_not_claim_the_plugin_updated(self):
        runner = FakeRunner((0, plugin_list("github"), ""), (1, "", "network down"))
        with self.assertRaises(updates.UpdateFailedError) as caught:
            self.update(runner)
        self.assertNotIn("The Herdr plugin is at", str(caught.exception))

    def test_a_failed_plugin_list_fails_the_update(self):
        runner = FakeRunner((1, "", "herdr is not running"))
        with self.assertRaises(updates.UpdateFailedError) as caught:
            self.update(runner)
        self.assertIn("herdr is not running", str(caught.exception))

    def test_a_missing_command_fails_the_update(self):
        def runner(argv):
            raise FileNotFoundError(2, "No such file or directory", argv[0])

        with self.assertRaises(updates.UpdateFailedError) as caught:
            self.update(runner)
        self.assertIn("/opt/herdr", str(caught.exception))


class UpdateCliTests(CliTestCase):
    def test_json_reports_the_update(self):
        with patch("herdboard.updates.update", return_value={"current": "0.1.0", "latest": "0.2.0", "updated": True}):
            self.assertEqual(self.run_json("update"), {"current": "0.1.0", "latest": "0.2.0", "updated": True})

    def test_text_reports_the_update(self):
        with patch("herdboard.updates.update", return_value={"current": "0.1.0", "latest": "0.2.0", "updated": True}):
            out, _ = self.run_cli("update")
        self.assertEqual(out, "Updated herdboard to v0.2.0. Reopen the board.\n")

    def test_text_reports_the_latest_release(self):
        with patch("herdboard.updates.update", return_value={"current": "0.2.0", "latest": "0.2.0", "updated": False}):
            out, _ = self.run_cli("update")
        self.assertEqual(out, "herdboard v0.2.0 is the latest release\n")

    def test_text_names_the_release_without_a_current_version(self):
        with patch("herdboard.updates.update", return_value={"current": "", "latest": "0.2.0", "updated": False}):
            out, _ = self.run_cli("update")
        self.assertEqual(out, "herdboard v0.2.0 is the latest release\n")

    def test_an_error_has_its_code(self):
        error = updates.UpdateUnsupportedError("This install is a linked clone. Run git pull in /x.")
        with patch("herdboard.updates.update", side_effect=error):
            data = self.run_json("update", expect=1)
        self.assertEqual(data["error"]["code"], "update_unsupported")

    def test_update_needs_no_board(self):
        with patch("herdboard.updates.update", return_value={"current": "0.2.0", "latest": "0.2.0", "updated": False}):
            self.run_json("update")
        self.assertFalse(self.todos.exists())
