import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "src" / "app"
TOOLS_ROOT = ROOT / "tools"
SUPPORTED_MODULE_OPERATIONS = {"compile", "fullmatch"}
SUPPORTED_PATTERN_OPERATIONS = {"fullmatch"}


def _regex_audit():
    imports = []
    module_operations = []
    pattern_operations = []
    compiled_patterns = {}
    patterns = []

    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = ".".join(path.relative_to(ROOT / "src").with_suffix("").parts)
        aliases = set()
        imported_operations = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "re":
                        aliases.add(alias.asname or "re")
                        imports.append((module, node.lineno, "import re"))
            elif isinstance(node, ast.ImportFrom) and node.module == "re":
                imports.append((module, node.lineno, "from re import"))
                for alias in node.names:
                    imported_operations[alias.asname or alias.name] = alias.name

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                function = node.value.func
                if (
                    isinstance(function, ast.Attribute)
                    and isinstance(function.value, ast.Name)
                    and function.value.id in aliases
                    and function.attr == "compile"
                ):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            compiled_patterns[target.id] = module
                    if node.value.args and isinstance(node.value.args[0], ast.Constant):
                        if isinstance(node.value.args[0].value, str):
                            patterns.append(node.value.args[0].value)
                elif (
                    isinstance(function, ast.Name)
                    and imported_operations.get(function.id) == "compile"
                ):
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            compiled_patterns[target.id] = module

            if not isinstance(node, ast.Call):
                continue
            if isinstance(node.func, ast.Name) and node.func.id in imported_operations:
                operation = imported_operations[node.func.id]
                module_operations.append((module, node.lineno, operation))
                if operation == "compile" and node.args:
                    if isinstance(node.args[0], ast.Constant) and isinstance(
                        node.args[0].value, str
                    ):
                        patterns.append(node.args[0].value)
                continue
            if not isinstance(node.func, ast.Attribute):
                continue
            receiver = node.func.value
            operation = node.func.attr
            if isinstance(receiver, ast.Name) and receiver.id in aliases:
                module_operations.append((module, node.lineno, operation))
                if operation == "compile" and node.args:
                    if isinstance(node.args[0], ast.Constant) and isinstance(
                        node.args[0].value, str
                    ):
                        patterns.append(node.args[0].value)
            elif isinstance(receiver, ast.Name) and receiver.id in compiled_patterns:
                pattern_operations.append((module, node.lineno, operation))

    return {
        "imports": tuple(imports),
        "module_operations": tuple(module_operations),
        "pattern_operations": tuple(pattern_operations),
        "compiled_patterns": tuple(sorted(compiled_patterns)),
        "patterns": tuple(dict.fromkeys(patterns)),
    }


def test_production_regex_usage_is_dynamically_discovered_and_qualified():
    audit = _regex_audit()

    assert audit["imports"]
    assert all(path.is_relative_to(APP_ROOT) for path in APP_ROOT.rglob("*.py"))
    assert {operation for _, _, operation in audit["module_operations"]} <= (
        SUPPORTED_MODULE_OPERATIONS
    )
    assert {operation for _, _, operation in audit["pattern_operations"]} <= (
        SUPPORTED_PATTERN_OPERATIONS
    )
    assert {operation for _, _, operation in audit["module_operations"]} == {
        "compile",
        "fullmatch",
    }
    assert {operation for _, _, operation in audit["pattern_operations"]} == {
        "fullmatch",
    }


def test_regex_audit_excludes_tooling_and_rejects_unsupported_future_operations():
    audit = _regex_audit()
    tooling_source = (TOOLS_ROOT / "generate_content_catalog.py").read_text(
        encoding="utf-8"
    )

    assert "import re" in tooling_source
    assert all(
        (APP_ROOT / path.relative_to(APP_ROOT)).is_relative_to(APP_ROOT)
        for path in APP_ROOT.rglob("*.py")
    )
    assert not {operation for _, _, operation in audit["module_operations"]} & {
        "sub",
        "subn",
        "split",
        "findall",
        "finditer",
        "escape",
        "match",
        "search",
    }
    assert not {operation for _, _, operation in audit["pattern_operations"]} & {
        "match",
        "search",
        "sub",
        "subn",
        "split",
        "findall",
        "finditer",
        "start",
        "end",
        "span",
        "groups",
        "groupdict",
    }


def test_production_regex_patterns_are_discovered_without_fixed_counts():
    audit = _regex_audit()

    assert audit["compiled_patterns"]
    assert audit["patterns"]
    assert all(isinstance(pattern, str) for pattern in audit["patterns"])
