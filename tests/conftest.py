"""Settings for every test process.

Many board tests start `HerdboardApp` without a shared base case, so the release check is turned off here,
before any test runs: no test calls GitHub. A test of the check removes the variable and patches
`herdboard.updates.latest_release`.
"""

import os

os.environ["HERDBOARD_NO_UPDATE_CHECK"] = "1"
