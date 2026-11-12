"""Settings for every test process.

Many board tests start `HerdboardApp` without a shared base case, so the release check is turned off here,
before any test runs: no test calls GitHub. A test of the check removes the variable and patches
`herdboard.updates.latest_release`.
"""

import os

import pytest

os.environ["HERDBOARD_NO_UPDATE_CHECK"] = "1"


@pytest.fixture(autouse=True)
def _pi_has_every_extension(request, monkeypatch):
    """No test runs the real `pi --help`: pi reports every pi-extensions flag unless the test patches it.

    A test of the check itself is marked `real_pi_flags` and fakes the command."""
    if request.node.get_closest_marker("real_pi_flags"):
        return
    from herdboard import pi_extensions

    monkeypatch.setattr(pi_extensions, "pi_flags", lambda directory: frozenset(pi_extensions.EXTENSION_FLAGS))
