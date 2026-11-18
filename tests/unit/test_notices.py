import json
import os
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from herdboard import activity, notices, start
from herdboard.config import Config
from herdboard.store import Store
from support.herdboard_start import FakeHerdr

PROMPT = "Card {ref} changed: details. Run `herdboard --json show {ref}` and read the changes before you go on."


class NoticeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        env = patch.dict(os.environ, {"XDG_STATE_HOME": str(self.root / "state")})
        env.start()
        self.addCleanup(env.stop)
        os.environ.pop("HERDR_PANE_ID", None)
        self.config = Config(todos_dir=self.root / "todos")
        self.store = Store(self.config)
        inbox = self.store.ensure_inbox()
        self.card = self.store.add(inbox, "Ship it", body=["old"])
        self.fake = FakeHerdr(self.root)
        self.fake.agent = True
        runner = patch.object(start, "command", self.fake)
        runner.start()
        self.addCleanup(runner.stop)

    def record(self, **fields):
        record = {"ref": self.card.ref, "agent_name": f"hb-{self.card.ref}", "pane_id": "w9:p1", **fields}
        state = self.root / "state" / "herdboard"
        state.mkdir(parents=True, exist_ok=True)
        (state / "starts.json").write_text(json.dumps({self.card.ref: record}))

    def prompts(self):
        return [call for call in self.fake.calls if call[:2] == ["agent", "prompt"]]

    def log(self):
        return [entry["message"] for entry in activity.read(self.config, self.card.ref)]

    def test_details_change_prompts_the_live_agent_and_logs_it(self):
        self.record()
        notice = notices.notify_card_agent(self.store, self.card.ref, ["details"])
        expected = {
            "agent": f"hb-{self.card.ref}",
            "pane_id": "w9:p1",
            "changes": ["details"],
            "status": "sent",
            "reason": None,
            "error": None,
        }
        self.assertEqual(notice, expected)
        self.assertEqual(self.prompts(), [["agent", "prompt", "w9:p1", PROMPT.format(ref=self.card.ref)]])
        self.assertEqual(self.log(), [f"Told agent hb-{self.card.ref}: details."])

    def test_prompt_names_every_change(self):
        self.record()
        notices.notify_card_agent(self.store, self.card.ref, ["title", "details", "attachment spec.md added"])
        text = self.prompts()[0][3]
        self.assertTrue(text.startswith(f"Card {self.card.ref} changed: title, details, attachment spec.md added. "))

    def test_no_start_record_sends_nothing(self):
        self.assertIsNone(notices.notify_card_agent(self.store, self.card.ref, ["details"]))
        self.assertEqual(self.fake.calls, [])

    def test_no_live_agent_sends_nothing(self):
        self.record()
        self.fake.agent = False
        self.assertIsNone(notices.notify_card_agent(self.store, self.card.ref, ["details"]))
        self.assertEqual(self.prompts(), [])
        self.assertEqual(self.log(), [])

    def test_no_changes_sends_nothing(self):
        self.record()
        self.assertIsNone(notices.notify_card_agent(self.store, self.card.ref, []))
        self.assertEqual(self.fake.calls, [])

    def test_unreadable_start_state_sends_nothing(self):
        state = self.root / "state" / "herdboard"
        state.mkdir(parents=True)
        (state / "starts.json").write_text("not json")
        self.assertIsNone(notices.notify_card_agent(self.store, self.card.ref, ["details"]))

    def test_skip_sends_nothing(self):
        self.record()
        notice = notices.notify_card_agent(self.store, self.card.ref, ["details"], skip=True)
        self.assertEqual((notice["status"], notice["reason"]), ("skipped", "no_notify"))
        self.assertEqual(self.prompts(), [])
        self.assertEqual(self.log(), [])

    def test_change_from_the_agents_own_pane_sends_nothing(self):
        self.record()
        with patch.dict(os.environ, {"HERDR_PANE_ID": "w9:p1"}):
            notice = notices.notify_card_agent(self.store, self.card.ref, ["details"])
        self.assertEqual((notice["status"], notice["reason"]), ("skipped", "self"))
        self.assertEqual(self.prompts(), [])

    def test_failed_prompt_reports_the_error_and_logs_nothing(self):
        self.record()
        self.fake.fail = "agent prompt"
        notice = notices.notify_card_agent(self.store, self.card.ref, ["details"])
        self.assertEqual(notice["status"], "failed")
        self.assertIn("test failure", notice["error"])
        self.assertEqual(self.log(), [])

    def test_failed_liveness_check_reports_the_error(self):
        self.record()
        self.fake.fail = "agent get"
        notice = notices.notify_card_agent(self.store, self.card.ref, ["details"])
        self.assertEqual(notice["status"], "failed")
        self.assertIn("test failure", notice["error"])
        self.assertEqual(self.prompts(), [])


class EditChangesTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.store = Store(Config(todos_dir=Path(self.temp.name) / "todos"))
        self.card = self.store.add(self.store.ensure_inbox(), "Ship it", body=["old"])

    def test_title_and_details(self):
        after = self.store.edit(self.card.ref, title="Ship", body=["new"])
        self.assertEqual(notices.edit_changes(self.card, after), ["title", "details"])

    def test_tags_only_is_no_change(self):
        after = self.store.edit(self.card.ref, tags=["x"])
        self.assertEqual(notices.edit_changes(self.card, after), [])

    def test_title_set_to_its_current_value_is_no_change(self):
        after = self.store.edit(self.card.ref, title="Ship it")
        self.assertEqual(notices.edit_changes(self.card, after), [])


if __name__ == "__main__":
    unittest.main()
