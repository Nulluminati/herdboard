"""bin/release_notes.py: the version check and the release notes of the Release workflow."""

import contextlib
import io
import tempfile
import unittest
from pathlib import Path

from support.scripts import load_script

notes = load_script("release_notes")

CHANGELOG = """# Changelog

## [Unreleased]

## [0.2.0] - 2026-11-11

### Added

- The update indicator.

## [0.1.0] - 2026-10-01

### Added

- The board.
"""


class ReleaseNotesTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self.tmp.cleanup)
        self.root = Path(self.tmp.name)
        self.write("0.2.0", "0.2.0")
        (self.root / "CHANGELOG.md").write_text(CHANGELOG)

    def write(self, project, plugin):
        (self.root / "pyproject.toml").write_text(f'[project]\nname = "herdboard"\nversion = "{project}"\n')
        (self.root / "herdr-plugin.toml").write_text(f'id = "nulluminati.herdboard"\nversion = "{plugin}"\n')

    def run_notes(self, version, expect=0):
        out, err = io.StringIO(), io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
            code = notes.main([version], root=self.root)
        self.assertEqual(code, expect, f"stdout={out.getvalue()!r} stderr={err.getvalue()!r}")
        return out.getvalue(), err.getvalue()

    def test_prints_the_section_of_the_version(self):
        out, _ = self.run_notes("0.2.0")
        self.assertEqual(out, "### Added\n\n- The update indicator.\n")

    def test_the_last_section_runs_to_the_end(self):
        self.write("0.1.0", "0.1.0")
        out, _ = self.run_notes("0.1.0")
        self.assertEqual(out, "### Added\n\n- The board.\n")

    def test_refuses_a_tag_that_differs_from_pyproject(self):
        self.write("0.1.0", "0.2.0")
        _, err = self.run_notes("0.2.0", expect=1)
        self.assertIn("pyproject.toml", err)

    def test_refuses_a_tag_that_differs_from_the_plugin(self):
        self.write("0.2.0", "0.1.0")
        _, err = self.run_notes("0.2.0", expect=1)
        self.assertIn("herdr-plugin.toml", err)

    def test_refuses_a_version_without_a_section(self):
        self.write("0.3.0", "0.3.0")
        _, err = self.run_notes("0.3.0", expect=1)
        self.assertIn("## [0.3.0]", err)

    def test_refuses_an_empty_section(self):
        (self.root / "CHANGELOG.md").write_text("# Changelog\n\n## [0.2.0] - 2026-11-11\n\n")
        _, err = self.run_notes("0.2.0", expect=1)
        self.assertIn("empty", err)

    def test_refuses_a_version_that_is_not_x_y_z(self):
        _, err = self.run_notes("main", expect=1)
        self.assertIn("X.Y.Z", err)
