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


def _emit_dataclass_census():
    try:
        module = sys.modules.get("dataclasses")
        census = getattr(module, "_dataclass_census", None)
        if census is None:
            print("MYP|DATACLASS|UNAVAILABLE")
            return
        expected, decorated, constructed = census()
        print("MYP|DATACLASS|EXPECTED|%s" % expected)
        print("MYP|DATACLASS|DECORATED|%s" % decorated)
        print("MYP|DATACLASS|CONSTRUCTED|%s" % constructed)
    except Exception:
        print("MYP|DATACLASS|UNAVAILABLE")


def _prepare_cpython_overlay():
    implementation = getattr(getattr(sys, "implementation", None), "name", None)
    if implementation != "cpython":
        return

    for module_name in (
        "re",
        "pathlib",
        "typing",
        "inspect",
        "annotationlib",
        "tempfile",
        "shutil",
        "compression",
    ):
        try:
            __import__(module_name)
        except ImportError:
            pass
    sys.modules.pop("enum", None)


def _install_micropython_regex_proxy():
    implementation = getattr(getattr(sys, "implementation", None), "name", None)
    if implementation != "micropython":
        return

    native_re = __import__("re")
    from re_compat import install

    sys.modules["re"] = install(native_re)


def _install_micropython_collections_abc(source_path):
    implementation = getattr(getattr(sys, "implementation", None), "name", None)
    if implementation != "micropython":
        return

    native_collections = __import__("collections")
    absolute_source_path = _absolute_path(source_path)
    inserted = absolute_source_path not in sys.path
    if inserted:
        sys.path.insert(1, absolute_source_path)
    try:
        from app.readonly_mapping import _ReadonlyMapping
        from collections_abc_compat import install

        install(native_collections, _ReadonlyMapping)
    finally:
        if inserted:
            sys.path.remove(absolute_source_path)


def main():
    if len(sys.argv) != 2:
        print("MYP|USAGE|FAIL|expected exactly one DD source directory")
        return 2

    bootstrap_path = _absolute_path(sys.argv[0])
    tools_root = _dirname(bootstrap_path)
    repository_root = _dirname(tools_root)
    overlay_root = repository_root + "/portability/micropython"
    probe_path = tools_root + "/micropython_probe.py"

    _prepare_cpython_overlay()
    sys.path.insert(0, overlay_root)
    _install_micropython_regex_proxy()
    _install_micropython_collections_abc(sys.argv[1])
    sys.argv[:] = [probe_path, sys.argv[1]]
    namespace = {"__name__": "__main__", "__file__": probe_path}
    try:
        with open(probe_path, "r") as probe_file:
            source = probe_file.read()
        exec(source, namespace, namespace)
    finally:
        _emit_dataclass_census()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
