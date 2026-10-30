"""Shared isolated-process launcher for MicroPython overlay tests."""

import os
import subprocess
import sys


def run_isolated_overlay_script(prelude, source, *, cwd):
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=cwd,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )
