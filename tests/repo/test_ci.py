import unittest

import yaml

from support.paths import ROOT

WORKFLOW = ROOT / ".github/workflows/ci.yml"


class CiTests(unittest.TestCase):
    def setUp(self):
        self.workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))

    def test_runs_on_main_pushes_and_all_pull_requests(self):
        self.assertEqual(
            self.workflow["on"],
            {
                "push": {"branches": ["main"]},
                "pull_request": None,
            },
        )

    def test_uses_read_only_repository_permissions(self):
        self.assertEqual(self.workflow["permissions"], {"contents": "read"})
        checkout = self.workflow["jobs"]["test"]["steps"][0]
        self.assertTrue(checkout["uses"].startswith("actions/checkout@"))
        self.assertFalse(checkout["with"]["persist-credentials"])

    def test_runs_the_full_suite_with_locked_dependencies_on_latest_python(self):
        job = self.workflow["jobs"]["test"]
        self.assertEqual(job["runs-on"], "ubuntu-latest")
        steps = job["steps"]
        setup_python = next(step for step in steps if step.get("uses", "").startswith("actions/setup-python@"))
        self.assertEqual(setup_python["with"]["python-version"], "3.x")
        self.assertTrue(any(step.get("uses", "").startswith("astral-sh/setup-uv@") for step in steps))
        self.assertIn(
            "uv run --locked pytest -n auto --cov=src --cov=bin --cov-report=term-missing",
            [step.get("run") for step in steps],
        )

    def test_lints_and_checks_the_format_before_the_tests(self):
        job = self.workflow["jobs"]["test"]
        self.assertEqual(job["timeout-minutes"], 10)
        commands = [step.get("run") for step in job["steps"]]
        tests = commands.index("uv run --locked pytest -n auto --cov=src --cov=bin --cov-report=term-missing")
        self.assertLess(commands.index("uv run --locked ruff check ."), tests)
        self.assertLess(commands.index("uv run --locked ruff format --check ."), tests)

    def test_checks_that_the_lock_file_matches_the_manifest(self):
        commands = [step.get("run") for step in self.workflow["jobs"]["test"]["steps"]]
        self.assertIn("uv lock --check", commands)

    def test_names_the_test_job_for_the_required_status_check(self):
        self.assertEqual(self.workflow["jobs"]["test"]["name"], "Lint, format, test")


class SecretScanTests(unittest.TestCase):
    def setUp(self):
        workflow = yaml.safe_load(WORKFLOW.read_text(encoding="utf-8"))
        self.job = workflow["jobs"]["secrets"]

    def test_names_the_job_for_the_required_status_check(self):
        self.assertEqual(self.job["name"], "Secret scan (gitleaks)")
        self.assertEqual(self.job["runs-on"], "ubuntu-latest")
        self.assertEqual(self.job["timeout-minutes"], 5)

    def test_checks_out_the_full_history_without_credentials(self):
        checkout = self.job["steps"][0]
        self.assertRegex(checkout["uses"], r"^actions/checkout@[0-9a-f]{40} ?")
        self.assertEqual(checkout["with"]["fetch-depth"], 0)
        self.assertFalse(checkout["with"]["persist-credentials"])

    def test_installs_a_pinned_gitleaks_and_checks_its_checksum(self):
        self.assertEqual(self.job["env"]["GITLEAKS_VERSION"], "8.30.1")
        self.assertRegex(self.job["env"]["GITLEAKS_SHA256"], r"^[0-9a-f]{64}$")
        install = next(step for step in self.job["steps"] if step.get("name") == "Install gitleaks")
        self.assertIn("sha256sum -c -", install["run"])

    def test_scans_every_ref_in_the_history(self):
        scan = next(step for step in self.job["steps"] if step.get("name") == "Scan the history")
        self.assertIn('git --redact --no-banner --log-opts="--all" .', scan["run"])


if __name__ == "__main__":
    unittest.main()
