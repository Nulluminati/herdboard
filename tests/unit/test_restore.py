"""Restore records: herdboard panes run their command again after a Herdr restart."""

import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from herdboard import restore, start
from support.herdboard_cli import CliTestCase

SHELL = {"foreground_processes": [{"argv": ["/usr/bin/fish"], "pid": 10}], "shell_pid": 10}
LAYOUT = {
    "foreground_processes": [
        {"argv": ["sh", "-c", "herdboard board; exec $SHELL"], "pid": 10},
        {"argv": ["herdboard", "board"], "pid": 11},
    ],
    "shell_pid": 10,
}
BUSY = {"foreground_processes": [{"argv": ["herdboard", "details", "t1"], "pid": 11}], "shell_pid": 10}
STARTING = {"foreground_processes": [], "shell_pid": 10}


class RestoreHerdr:
    """A fake `herdr` with a list of panes and the process info of each."""

    def __init__(self, panes=(), processes=None):
        self.calls = []
        self.panes = list(panes)
        self.processes = processes or {}

    def __call__(self, argv, timeout=120, stdin=None):
        args = argv[1:]
        self.calls.append(args)
        operation = " ".join(args[:2])
        result = {}
        if operation == "pane list":
            result = {"panes": self.panes}
        elif operation == "pane get":
            pane = next((p for p in self.panes if p["pane_id"] == args[2]), None)
            if pane is None:
                error = {"error": {"code": "pane_not_found", "message": "no"}}
                return subprocess.CompletedProcess(argv, 1, "", json.dumps(error))
            result = {"pane": pane}
        elif operation == "pane process-info":
            info = self.processes[args[3]]
            if isinstance(info, list):
                info = info.pop(0) if len(info) > 1 else info[0]
            result = {"process_info": {"pane_id": args[3], **info}}
        elif operation == "pane run":
            return subprocess.CompletedProcess(argv, 0, "", "")
        return subprocess.CompletedProcess(argv, 0, json.dumps({"result": result}), "")

    def runs(self):
        return [call[2:] for call in self.calls if call[:2] == ["pane", "run"]]


def pane(pane_id, label, cwd="/repo"):
    return {"pane_id": pane_id, "workspace_id": pane_id.split(":")[0], "label": label, "cwd": cwd}


class RestoreCase(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.state = Path(temp.name)
        env = mock.patch.dict(os.environ, {"XDG_STATE_HOME": str(self.state)})
        env.start()
        self.addCleanup(env.stop)
        self.fake = RestoreHerdr()
        patcher = mock.patch.object(start, "command", self.fake)
        patcher.start()
        self.addCleanup(patcher.stop)
        sleep = mock.patch.object(restore.time, "sleep")
        self.sleep = sleep.start()
        self.addCleanup(sleep.stop)

    def records(self):
        folder = self.state / "herdboard" / "restore"
        return sorted(
            (json.loads(p.read_text()) for p in folder.glob("*.json")), key=lambda r: (r["label"], r["workspace_id"])
        )


class RememberTests(RestoreCase):
    def test_writes_one_file_per_pane(self):
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        restore.remember("w1", "herdboard", "/repo", "herdboard board")
        self.assertEqual(
            self.records(),
            [
                {"workspace_id": "w1", "label": "details - t1", "cwd": "/repo", "command": "herdboard details t1"},
                {"workspace_id": "w1", "label": "herdboard", "cwd": "/repo", "command": "herdboard board"},
            ],
        )

    def test_the_same_pane_replaces_its_record(self):
        restore.remember("w1", "herdboard", "/repo", "herdboard board")
        restore.remember("w1", "herdboard", "/repo", "herdboard board --prs")
        self.assertEqual([r["command"] for r in self.records()], ["herdboard board --prs"])

    def test_forget_drops_the_records_of_a_workspace_or_one_label(self):
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        restore.remember("w1", "herdboard", "/repo", "herdboard board")
        restore.remember("w2", "herdboard", "/repo", "herdboard board")
        restore.forget("w1", "details - t1")
        self.assertEqual(
            [(r["workspace_id"], r["label"]) for r in self.records()], [("w1", "herdboard"), ("w2", "herdboard")]
        )
        restore.forget("w1")
        self.assertEqual([r["workspace_id"] for r in self.records()], ["w2"])

    def test_remember_pane_reads_the_label_workspace_and_cwd(self):
        self.fake.panes = [pane("w1:p3", "herdboard", "/work")]
        restore.remember_pane("w1:p3", "herdboard board")
        self.assertEqual(
            self.records(), [{"workspace_id": "w1", "label": "herdboard", "cwd": "/work", "command": "herdboard board"}]
        )

    def test_remember_pane_skips_a_pane_without_a_label(self):
        self.fake.panes = [{"pane_id": "w1:p3", "workspace_id": "w1", "cwd": "/work"}]
        restore.remember_pane("w1:p3", "herdboard board")
        self.assertEqual(self.records(), [])

    def test_remember_pane_is_best_effort(self):
        restore.remember_pane("w1:p9", "herdboard board")
        self.assertEqual(self.records(), [])


class RestorePanesTests(RestoreCase):
    def test_runs_the_command_in_an_idle_shell_with_the_same_label_and_cwd(self):
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        self.fake.panes = [pane("w1:p5", "details - t1"), pane("w1:p6", "details - t1", "/other")]
        self.fake.processes = {"w1:p5": SHELL, "w1:p6": SHELL}
        restore.restore_panes()
        self.assertEqual(self.fake.runs(), [["w1:p5", "herdboard details t1"]])

    def test_leaves_a_pane_that_runs_a_command(self):
        restore.remember("w1", "board", "/repo", "herdboard board")
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        self.fake.panes = [pane("w1:p1", "board"), pane("w1:p2", "details - t1")]
        self.fake.processes = {"w1:p1": LAYOUT, "w1:p2": BUSY}
        restore.restore_panes()
        self.assertEqual(self.fake.runs(), [])
        self.assertEqual(len(self.records()), 2)

    def test_waits_for_a_shell_that_has_not_started(self):
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        self.fake.panes = [pane("w1:p5", "details - t1")]
        self.fake.processes = {"w1:p5": [STARTING, STARTING, SHELL]}
        restore.restore_panes()
        self.assertEqual(self.fake.runs(), [["w1:p5", "herdboard details t1"]])

    def test_drops_a_record_without_a_pane(self):
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        restore.remember("w9", "herdboard", "/repo", "herdboard board")
        self.fake.panes = [pane("w1:p2", "files")]
        restore.restore_panes()
        self.assertEqual(self.records(), [])
        self.assertEqual(self.fake.runs(), [])

    def test_skips_a_record_that_is_not_valid(self):
        folder = self.state / "herdboard" / "restore"
        folder.mkdir(parents=True)
        (folder / "bad.json").write_text("{not json")
        (folder / "list.json").write_text("[]")
        restore.remember("w1", "details - t1", "/repo", "herdboard details t1")
        self.fake.panes = [pane("w1:p5", "details - t1")]
        self.fake.processes = {"w1:p5": SHELL}
        restore.restore_panes()
        self.assertEqual(self.fake.runs(), [["w1:p5", "herdboard details t1"]])


class IdleShellTests(unittest.TestCase):
    def test_a_plain_shell_is_idle(self):
        self.assertTrue(restore.idle_shell(SHELL))

    def test_a_command_or_a_launch_command_is_not_idle(self):
        self.assertFalse(restore.idle_shell(LAYOUT))
        self.assertFalse(restore.idle_shell(BUSY))
        self.assertFalse(restore.idle_shell(STARTING))
        self.assertFalse(
            restore.idle_shell({"foreground_processes": [{"argv": ["sh", "-c", "x"], "pid": 10}], "shell_pid": 10})
        )


class RestorePanesCliTests(CliTestCase):
    def test_restore_panes_runs_without_a_board_and_prints_nothing(self):
        with mock.patch("herdboard.restore.restore_panes") as restored:
            out, err = self.run_cli("restore-panes", directory=self.repo)
        restored.assert_called_once_with()
        self.assertEqual((out, err), ("", ""))
        self.assertFalse(self.todos.exists())
