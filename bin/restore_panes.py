"""Run herdboard's panes again after a Herdr restart, in the background.

Herdr restores the details and board panes as bare shells: it keeps their label and
folder, but not their command. Herdr runs this at startup. It starts
`herdboard restore-panes` in its own session and returns at once, so Herdr does not
wait for uv or for the restored shells to start.
"""

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = os.environ.get("HERDR_PLUGIN_ROOT") or str(Path(__file__).resolve().parents[1])
    argv = ["uv", "run", "--quiet", "--project", root, "herdboard", "restore-panes"]
    try:
        subprocess.Popen(
            argv, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, start_new_session=True
        )
    except OSError as error:
        print(f"herdboard: cannot start the pane restore: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
