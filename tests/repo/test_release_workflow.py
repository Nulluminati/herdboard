import re
import unittest

import yaml

from support.paths import ROOT

WORKFLOW = ROOT / ".github/workflows/release.yml"


class ReleaseWorkflowTests(unittest.TestCase):
    def setUp(self):
        self.text = WORKFLOW.read_text(encoding="utf-8")
        self.workflow = yaml.safe_load(self.text)
        self.steps = self.workflow["jobs"]["release"]["steps"]

    def test_runs_on_version_tag_pushes_only(self):
        self.assertEqual(self.workflow["on"], {"push": {"tags": ["v*"]}})

    def test_may_write_releases_and_nothing_else(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "write"})
        self.assertNotIn("permissions", self.workflow["jobs"]["release"])

    def test_checks_out_without_keeping_the_token(self):
        checkout = self.steps[0]
        self.assertTrue(checkout["uses"].startswith("actions/checkout@"))
        self.assertFalse(checkout["with"]["persist-credentials"])

    def test_pins_every_action_by_commit_with_a_version_comment(self):
        uses = re.findall(r"uses: (\S+)(.*)", self.text)
        self.assertTrue(uses)
        for action, comment in uses:
            with self.subTest(action=action):
                self.assertRegex(action, r"@[0-9a-f]{40}$")
                self.assertRegex(comment, r"^ # v\d")

    def test_the_tag_reaches_the_scripts_only_through_the_environment(self):
        for step in self.steps:
            if "run" in step:
                with self.subTest(step=step["name"]):
                    self.assertNotIn("${{", step["run"])
        self.assertEqual(self.steps[1]["env"]["TAG"], "${{ github.ref_name }}")

    def test_checks_the_versions_then_publishes_the_changelog_section(self):
        commands = [step.get("run", "") for step in self.steps]
        self.assertEqual(commands[1], 'python3 bin/release_notes.py "${TAG#v}" > notes.md')
        self.assertTrue(commands[2].startswith('gh release create "$TAG"'))
        self.assertIn("--notes-file notes.md", commands[2])
        self.assertEqual(self.steps[2]["env"]["GH_TOKEN"], "${{ github.token }}")


if __name__ == "__main__":
    unittest.main()
