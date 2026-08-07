"""Generate deterministic imports for authored content packages."""

import argparse
import ast
import keyword
import re
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ENEMY_ROOT = ROOT / "src" / "app" / "content" / "enemies"
OUTPUT_PATH = ROOT / "src" / "app" / "content" / "_generated_catalog.py"
_CONTENT_ID_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


def _validate_content_module_id(value):
    if (
        not isinstance(value, str)
        or _CONTENT_ID_PATTERN.fullmatch(value) is None
        or keyword.iskeyword(value)
    ):
        raise ValueError(
            "content IDs must be lowercase snake-case Python module names"
        )
    return value


def _authored_archetype_id(path):
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    for node in tree.body:
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "ENEMY"
            for target in node.targets
        ):
            continue
        if not isinstance(node.value, ast.Call):
            break
        for keyword in node.value.keywords:
            if keyword.arg == "archetype_id":
                try:
                    value = ast.literal_eval(keyword.value)
                except (ValueError, TypeError) as error:
                    raise ValueError(
                        f"{path} archetype_id must be a string literal"
                    ) from error
                if not isinstance(value, str):
                    raise ValueError(
                        f"{path} archetype_id must be a string literal"
                    )
                return value
        break
    raise ValueError(f"{path} must assign ENEMY with an archetype_id")


def discover_enemy_ids(enemy_root=ENEMY_ROOT):
    enemy_ids = []
    for path in sorted(enemy_root.glob("*/enemy.py"), key=lambda item: item.parent.name):
        directory_id = _validate_content_module_id(path.parent.name)
        archetype_id = _validate_content_module_id(_authored_archetype_id(path))
        if directory_id != archetype_id:
            raise ValueError(
                "enemy directory ID does not match authored archetype ID: "
                f"{directory_id} != {archetype_id}"
            )
        enemy_ids.append(directory_id)
    return tuple(enemy_ids)


def render_catalog(enemy_ids):
    enemy_ids = tuple(_validate_content_module_id(value) for value in enemy_ids)
    imports = "\n".join(
        "from app.content.enemies."
        f"{enemy_id}.enemy import ENEMY as {enemy_id}_enemy"
        for enemy_id in enemy_ids
    )
    records = "\n".join(
        f'    ("{enemy_id}", {enemy_id}_enemy),'
        for enemy_id in enemy_ids
    )
    source = (
        '"""Generated content imports. Do not edit by hand."""\n\n'
        f"{imports}\n\n\n"
        "GENERATED_ENEMY_SPECS = (\n"
        f"{records}\n"
        ")\n\n\n"
        '__all__ = ["GENERATED_ENEMY_SPECS"]\n'
    )
    ast.parse(source, filename=str(OUTPUT_PATH))
    return source


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--check",
        action="store_true",
        help="fail when the committed catalog is stale",
    )
    args = parser.parse_args()
    expected = render_catalog(discover_enemy_ids())

    if args.check:
        actual = OUTPUT_PATH.read_text(encoding="utf-8")
        if actual != expected:
            raise SystemExit("generated content catalog is stale")
        return

    with OUTPUT_PATH.open("w", encoding="utf-8", newline="\n") as output:
        output.write(expected)


if __name__ == "__main__":
    main()
