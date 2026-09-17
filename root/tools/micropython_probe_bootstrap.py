"""Run the unchanged raw probe with the MicroPython dataclass overlay."""

import os
import sys


def _absolute_path(path):
    if path.startswith("/") or ":" in path[:3]:
        return path
    return os.getcwd().rstrip("/\\") + "/" + path


def _dirname(path):
    normalized = path.replace("\\", "/")
    if "/" not in normalized:
        return "."
    parent = normalized.rsplit("/", 1)[0]
    return parent or "/"


def main():
    if len(sys.argv) != 2:
        print("MYP|USAGE|FAIL|expected exactly one DD source directory")
        return 2

    bootstrap_path = _absolute_path(sys.argv[0])
    tools_root = _dirname(bootstrap_path)
    repository_root = _dirname(tools_root)
    overlay_root = repository_root + "/portability/micropython"
    probe_path = tools_root + "/micropython_probe.py"

    sys.path.insert(0, overlay_root)
    sys.argv[:] = [probe_path, sys.argv[1]]
    namespace = {"__name__": "__main__", "__file__": probe_path}
    with open(probe_path, "r") as probe_file:
        source = probe_file.read()
    exec(source, namespace, namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
