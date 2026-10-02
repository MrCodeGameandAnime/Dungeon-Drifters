"""Build the complete static GitHub Pages artifact."""

import argparse
import importlib.util
import shutil
import sys
from pathlib import Path


PUBLIC_ASSETS = (
    "Dungeon Drifters Heros.png",
    "Ser Branoc Sprite.png",
    "Azhvielle Sprite.png",
    "Zhaivra Kelyth Sprite.png",
    "Joruun Veyr Sprite.png",
    "screenshots/DD_001.jpeg",
    "screenshots/DD_002.jpeg",
    "screenshots/DD_003.jpeg",
)


def _repository_root():
    return Path(__file__).resolve().parents[2]


def _browser_site_builder():
    path = Path(__file__).with_name("build_browser_site.py")
    spec = importlib.util.spec_from_file_location("browser_site_builder", path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module.build_site


def _copy_public_assets(repository_root, output_root):
    for relative_path in PUBLIC_ASSETS:
        source = repository_root / "res" / relative_path
        destination = output_root / "res" / relative_path
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(source, destination)


def build_pages_site(output_root):
    repository_root = _repository_root()
    output_root = Path(output_root)
    if output_root.exists():
        if output_root.is_dir():
            shutil.rmtree(output_root)
        else:
            output_root.unlink()
    output_root.mkdir(parents=True, exist_ok=True)

    shutil.copy2(repository_root / "index.html", output_root / "index.html")
    shutil.copy2(repository_root / ".nojekyll", output_root / ".nojekyll")
    shutil.copytree(repository_root / "root" / "web" / "site", output_root / "site")
    _copy_public_assets(repository_root, output_root)

    _browser_site_builder()(
        repository_root / "root" / "src",
        output_root / "play",
        shell_root=repository_root / "root" / "web" / "play",
        bridge_path=repository_root / "root" / "web" / "python" / "dd_bridge.py",
    )
    return output_root


def _parser():
    parser = argparse.ArgumentParser(
        description="Build the complete Dungeon Drifters GitHub Pages artifact."
    )
    parser.add_argument("--output", default=str(_repository_root() / "pages-dist"))
    return parser


def main(argv=None):
    args = _parser().parse_args(argv)
    output = build_pages_site(args.output)
    print("PAGES|BUILD|PASS|OUTPUT|%s" % output)


if __name__ == "__main__":
    main()
