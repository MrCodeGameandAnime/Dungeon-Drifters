"""Build the static GitHub Pages browser playtest artifact."""

import argparse
import importlib.util
import json
import shutil
from dataclasses import dataclass
from pathlib import Path


PYODIDE_VERSION = "314.0.7"


def _repository_root():
    return Path(__file__).resolve().parents[2]


def _runtime_builder():
    path = Path(__file__).with_name("build_browser_runtime.py")
    spec = importlib.util.spec_from_file_location("browser_runtime_builder", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.build_runtime


@dataclass(frozen=True)
class SiteBuildResult:
    output_root: Path
    runtime_file_count: int


def _copy(source, destination):
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_bytes(Path(source).read_bytes())


def build_site(source_root, output_root, shell_root=None, bridge_path=None):
    """Stage one deterministic static site around the authoritative app archive."""
    repository_root = _repository_root()
    source_root = Path(source_root)
    output_root = Path(output_root)
    shell_root = Path(shell_root or repository_root / "root" / "web" / "pyd4")
    bridge_path = Path(bridge_path or repository_root / "root" / "web" / "python" / "dd_bridge.py")

    required = (
        shell_root / "index.html",
        shell_root / "styles.css",
        shell_root / "js" / "pyd4.js",
        shell_root / "python" / "boot.py",
        bridge_path,
    )
    missing = [path for path in required if not path.is_file()]
    if missing:
        raise FileNotFoundError("browser site input missing: " + ", ".join(map(str, missing)))

    if output_root.exists():
        if output_root.is_dir():
            shutil.rmtree(output_root)
        else:
            output_root.unlink()
    output_root.mkdir(parents=True, exist_ok=True)

    _copy(shell_root / "index.html", output_root / "index.html")
    _copy(shell_root / "styles.css", output_root / "styles.css")
    _copy(shell_root / "js" / "pyd4.js", output_root / "js" / "pyd4.js")
    _copy(shell_root / "python" / "boot.py", output_root / "python" / "boot.py")
    _copy(bridge_path, output_root / "python" / "dd_bridge.py")

    runtime_path = output_root / "game" / "dd_runtime.zip"
    runtime_file_count = len(_runtime_builder()(source_root, runtime_path))

    qualification_root = output_root / "qualification"
    qualification_source = repository_root / "root" / "web" / "pyd2"
    _copy(qualification_source / "index.html", qualification_root / "index.html")
    _copy(qualification_source / "js" / "pyd2.js", qualification_root / "js" / "pyd2.js")
    _copy(qualification_source / "python" / "boot.py", qualification_root / "python" / "boot.py")
    _runtime_builder()(source_root, qualification_root / "game" / "dd_runtime.zip")

    (output_root / ".nojekyll").write_bytes(b"")
    metadata = {
        "pyodide_version": PYODIDE_VERSION,
        "runtime_file_count": runtime_file_count,
        "shell": "pyd4",
    }
    (output_root / "build-metadata.json").write_text(
        json.dumps(metadata, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return SiteBuildResult(output_root, runtime_file_count)


def _parser():
    repository_root = _repository_root()
    parser = argparse.ArgumentParser(
        description="Build the static Dungeon Drifters GitHub Pages site."
    )
    parser.add_argument("--source", default=str(repository_root / "root" / "src"))
    parser.add_argument(
        "--shell",
        default=str(repository_root / "root" / "web" / "pyd4"),
    )
    parser.add_argument(
        "--bridge",
        default=str(repository_root / "root" / "web" / "python" / "dd_bridge.py"),
    )
    parser.add_argument(
        "--output",
        default=str(repository_root / "root" / "web" / "dist"),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    result = build_site(args.source, args.output, args.shell, args.bridge)
    print(
        "PYD6|BUILD|PASS|FILES|%s|OUTPUT|%s"
        % (result.runtime_file_count, result.output_root)
    )


if __name__ == "__main__":
    main()
