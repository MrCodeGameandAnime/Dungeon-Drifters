"""Build a deterministic zip package for the browser Python runtime."""

import argparse
from pathlib import Path
from zipfile import ZIP_STORED, ZipFile, ZipInfo


def _repository_root():
    return Path(__file__).resolve().parents[2]


def _runtime_files(source_root):
    app_root = Path(source_root) / "app"
    if not app_root.is_dir():
        raise FileNotFoundError(f"application package not found: {app_root}")
    return tuple(
        sorted(
            path
            for path in app_root.rglob("*.py")
            if "__pycache__" not in path.parts
        )
    )


def build_runtime(source_root, output_path):
    """Package the authoritative app source without copying or rewriting it."""
    source_root = Path(source_root)
    output_path = Path(output_path)
    files = _runtime_files(source_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with ZipFile(output_path, "w", compression=ZIP_STORED) as archive:
        for path in files:
            relative = path.relative_to(source_root).as_posix()
            info = ZipInfo(relative)
            info.date_time = (1980, 1, 1, 0, 0, 0)
            info.create_system = 3
            info.compress_type = ZIP_STORED
            info.external_attr = 0o644 << 16
            archive.writestr(info, path.read_bytes())

    return files


def _parser():
    repository_root = _repository_root()
    parser = argparse.ArgumentParser(
        description="Package root/src/app for browser-side Pyodide loading."
    )
    parser.add_argument(
        "--source",
        default=str(repository_root / "root" / "src"),
    )
    parser.add_argument(
        "--output",
        default=str(repository_root / "root" / "web" / "game" / "dd_runtime.zip"),
    )
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    files = build_runtime(args.source, args.output)
    print(
        "PYD0|RUNTIME_BUILD|PASS|FILES|%s|OUTPUT|%s"
        % (len(files), args.output)
    )


if __name__ == "__main__":
    main()
