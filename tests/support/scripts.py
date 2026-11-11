"""Load a bin script as a module."""

import importlib.util

from support.paths import ROOT


def load_script(name):
    """Load bin/<name>.py and return it as the module <name>."""
    path = ROOT / "bin" / f"{name}.py"
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Cannot load {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module
