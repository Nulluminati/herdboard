"""Which pi-extensions flags pi has, and the warning when an extension is missing."""

import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import pytest

from herdboard import activity, pi_extensions
from herdboard.config import load_config
from herdboard.store import Store
from support.herdboard_store import write_board
from support.paths import ROOT

PI_FIXTURES = ROOT / "tests" / "fixtures" / "pi"


def help_result(name, returncode=0):
    text = (PI_FIXTURES / name).read_text(encoding="utf-8")
    return subprocess.CompletedProcess(["pi", "--help"], returncode, text, "")


@pytest.mark.real_pi_flags
class PiFlagsTests(unittest.TestCase):
    def flags(self, result):
        with patch.object(pi_extensions.subprocess, "run", return_value=result) as run:
            flags = pi_extensions.pi_flags(Path("/work/card"))
        return flags, run

    def test_all_extension_flags(self):
        flags, _ = self.flags(help_result("help-extensions.txt"))
        self.assertEqual(flags, frozenset({"--approval-mode", "--approval-reject", "--sandbox"}))

    def test_no_extension_flags(self):
        flags, _ = self.flags(help_result("help-no-extensions.txt"))
        self.assertEqual(flags, frozenset())

    def test_some_extension_flags(self):
        flags, _ = self.flags(help_result("help-approval-mode-only.txt"))
        self.assertEqual(flags, frozenset({"--approval-mode"}))

    def test_runs_pi_help_in_the_card_directory(self):
        _, run = self.flags(help_result("help-extensions.txt"))
        args, kwargs = run.call_args
        self.assertEqual(args[0], ["pi", "--help"])
        self.assertEqual(kwargs["cwd"], Path("/work/card"))
        self.assertTrue(kwargs["capture_output"])
        self.assertGreater(kwargs["timeout"], 0)

    def test_a_failed_check_is_none(self):
        self.assertIsNone(self.flags(help_result("help-no-extensions.txt", returncode=1))[0])
        for error in (OSError("no pi"), subprocess.TimeoutExpired(["pi"], 30)):
            with self.subTest(error=error), patch.object(pi_extensions.subprocess, "run", side_effect=error):
                self.assertIsNone(pi_extensions.pi_flags(Path("/work/card")))


class MissingExtensionsTests(unittest.TestCase):
    def test_none_missing(self):
        flags = frozenset({"--approval-mode", "--approval-reject", "--sandbox"})
        self.assertEqual(pi_extensions.missing_extensions(flags, pi_extensions.REVIEWER_FLAGS), [])

    def test_unknown_flags_count_as_present(self):
        self.assertEqual(pi_extensions.missing_extensions(None, pi_extensions.REVIEWER_FLAGS), [])

    def test_names_each_extension_once_in_a_fixed_order(self):
        missing = pi_extensions.missing_extensions(frozenset(), ("--sandbox", "--approval-mode", "--approval-reject"))
        self.assertEqual(missing, ["approval-mode", "worker-sandbox"])

    def test_only_the_needed_flags(self):
        self.assertEqual(pi_extensions.missing_extensions(frozenset(), pi_extensions.AGENT_FLAGS), ["approval-mode"])


class WarningTextTests(unittest.TestCase):
    def test_agent_without_approval_mode(self):
        text = pi_extensions.warning_text(["approval-mode"], "agent")
        self.assertIn("approval-mode", text)
        self.assertIn("no Jev command review", text)
        self.assertIn("https://github.com/Nulluminati/pi-extensions", text)

    def test_reviewer_without_worker_sandbox(self):
        text = pi_extensions.warning_text(["approval-mode", "worker-sandbox"], "reviewer")
        self.assertIn("approval-mode", text)
        self.assertIn("worker-sandbox", text)
        self.assertIn("the reviewer runs with no sandbox", text)
        self.assertIn("https://github.com/Nulluminati/pi-extensions", text)


class CheckTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        root = Path(self.tmp.name)
        config = root / "config.toml"
        config.write_text(f'todos_dir = "{root / "todos"}"\n')
        self.store = Store(load_config(config))
        write_board(root / "todos", "inbox", [("Todo", [{"id": "t3m9", "title": "Card"}])])
        self.ref = "t3m9"

    def check(self, flags, store=None, ref=None, role="agent", needed=pi_extensions.AGENT_FLAGS):
        with (
            patch.object(pi_extensions, "pi_flags", return_value=flags),
            patch("herdboard.start.notify") as notify,
            patch("sys.stderr") as stderr,
        ):
            result = pi_extensions.check(Path("/work/card"), needed, role, store, ref)
        return result, notify, stderr

    def test_missing_extension_warns_on_every_channel(self):
        flags, notify, stderr = self.check(frozenset(), self.store, self.ref)
        self.assertEqual(flags, frozenset())
        title, body = notify.call_args.args
        self.assertIn("pi", title)
        self.assertIn("approval-mode", body)
        self.assertIn("https://github.com/Nulluminati/pi-extensions", body)
        written = "".join(call.args[0] for call in stderr.write.call_args_list)
        self.assertIn("herdboard: warning: ", written)
        self.assertIn("approval-mode", written)
        [entry] = activity.read(self.store.config, self.ref)
        self.assertEqual(entry["author"], "herdboard")
        self.assertIn("approval-mode", entry["message"])
        self.assertIn("https://github.com/Nulluminati/pi-extensions", entry["message"])

    def test_without_a_card_no_log(self):
        _, notify, _ = self.check(frozenset())
        notify.assert_called_once()
        self.assertEqual(activity.read(self.store.config, self.ref), [])

    def test_no_warning_with_all_flags_or_a_failed_check(self):
        for flags in (frozenset({"--approval-mode", "--approval-reject", "--sandbox"}), None):
            with self.subTest(flags=flags):
                result, notify, _ = self.check(flags, self.store, self.ref)
                self.assertEqual(result, flags)
                notify.assert_not_called()
                self.assertEqual(activity.read(self.store.config, self.ref), [])
