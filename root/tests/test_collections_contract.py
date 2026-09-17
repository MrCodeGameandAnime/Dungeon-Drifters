import ast
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
APP_ROOT = ROOT / "src" / "app"

SUPPORTED_ABC_NAMES = {"Mapping", "Sequence"}
SUPPORTED_ABC_CONTEXTS = {"type_check", "generic_subscript"}
SUPPORTED_COLLECTION_NAMES = {"Counter"}
SUPPORTED_COUNTER_OPERATIONS = {"construct", "subscription", "increment"}


def _name(node):
    return node.id if isinstance(node, ast.Name) else None


def _collections_audit():
    imports = []
    abc_imports = []
    collection_imports = []
    abc_uses = []
    generic_subscripts = []
    counter_operations = []

    for path in sorted(APP_ROOT.rglob("*.py")):
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        module = ".".join(path.relative_to(ROOT / "src").with_suffix("").parts)
        collections_aliases = set()
        abc_module_aliases = set()
        abc_aliases = {}
        collection_aliases = {}
        counter_variables = set()

        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "collections":
                        name = alias.asname or "collections"
                        collections_aliases.add(name)
                        imports.append((module, node.lineno, "collections", name))
                    elif alias.name == "collections.abc":
                        name = alias.asname or "abc"
                        abc_module_aliases.add(name)
                        imports.append((module, node.lineno, "collections.abc", name))
            elif isinstance(node, ast.ImportFrom):
                if node.module == "collections.abc":
                    for alias in node.names:
                        name = alias.asname or alias.name
                        abc_aliases[name] = alias.name
                        abc_imports.append((module, node.lineno, alias.name, name))
                        imports.append(
                            (module, node.lineno, "collections.abc", alias.name)
                        )
                elif node.module == "collections":
                    for alias in node.names:
                        name = alias.asname or alias.name
                        collection_aliases[name] = alias.name
                        collection_imports.append((module, node.lineno, alias.name, name))
                        imports.append(
                            (module, node.lineno, "collections", alias.name)
                        )

        for node in ast.walk(tree):
            if isinstance(node, ast.Assign) and isinstance(node.value, ast.Call):
                function = node.value.func
                if isinstance(function, ast.Name) and collection_aliases.get(
                    function.id
                ) == "Counter":
                    counter_operations.append((module, node.lineno, "construct"))
                    for target in node.targets:
                        if isinstance(target, ast.Name):
                            counter_variables.add(target.id)

            if isinstance(node, ast.Call):
                function = node.func
                if isinstance(function, ast.Name) and function.id in abc_aliases:
                    abc_uses.append(
                        (module, node.lineno, abc_aliases[function.id], "call")
                    )
                elif isinstance(function, ast.Attribute):
                    receiver = _name(function.value)
                    if receiver in abc_module_aliases:
                        abc_uses.append(
                            (module, node.lineno, function.attr, "module_call")
                        )
                    elif receiver in collections_aliases:
                        collection_imports.append(
                            (module, node.lineno, function.attr, receiver)
                        )

                if isinstance(function, ast.Name) and function.id in collection_aliases:
                    if collection_aliases[function.id] == "Counter":
                        counter_operations.append((module, node.lineno, "construct"))

            if isinstance(node, ast.Call) and _name(node.func) in {
                "isinstance",
                "issubclass",
            }:
                if len(node.args) >= 2:
                    type_name = _name(node.args[1])
                    if type_name in abc_aliases:
                        abc_uses.append(
                            (
                                module,
                                node.lineno,
                                abc_aliases[type_name],
                                "type_check",
                            )
                        )

            if isinstance(node, ast.Subscript):
                type_name = _name(node.value)
                if type_name in abc_aliases:
                    generic_subscripts.append(
                        (module, node.lineno, abc_aliases[type_name])
                    )
                    abc_uses.append(
                        (
                            module,
                            node.lineno,
                            abc_aliases[type_name],
                            "generic_subscript",
                        )
                    )
                if type_name in counter_variables:
                    counter_operations.append((module, node.lineno, "subscription"))

            if isinstance(node, ast.AugAssign) and isinstance(node.target, ast.Subscript):
                if _name(node.target.value) in counter_variables:
                    counter_operations.append((module, node.lineno, "increment"))

    return {
        "imports": tuple(imports),
        "abc_imports": tuple(abc_imports),
        "collection_imports": tuple(collection_imports),
        "abc_uses": tuple(abc_uses),
        "generic_subscripts": tuple(generic_subscripts),
        "counter_operations": tuple(counter_operations),
    }


def test_production_collections_surface_is_dynamically_discovered():
    audit = _collections_audit()

    assert audit["imports"]
    assert {name for _, _, name, _ in audit["abc_imports"]} <= SUPPORTED_ABC_NAMES
    assert {name for _, _, name, _ in audit["collection_imports"]} <= (
        SUPPORTED_COLLECTION_NAMES
    )
    assert {context for _, _, _, context in audit["abc_uses"]} <= (
        SUPPORTED_ABC_CONTEXTS
    )
    assert {name for _, _, name in audit["generic_subscripts"]} <= (
        SUPPORTED_ABC_NAMES
    )
    assert {operation for _, _, operation in audit["counter_operations"]} <= (
        SUPPORTED_COUNTER_OPERATIONS
    )


def test_current_runtime_contract_is_classified_without_scanning_non_runtime_paths():
    audit = _collections_audit()

    assert {name for _, _, name, _ in audit["abc_imports"]} == {
        "Mapping",
        "Sequence",
    }
    assert {name for _, _, name, _ in audit["collection_imports"]} == {"Counter"}
    assert {name for _, _, name, context in audit["abc_uses"] if context == "type_check"} == {
        "Mapping",
        "Sequence",
    }
    assert {name for _, _, name in audit["generic_subscripts"]} == {"Mapping"}
    assert {operation for _, _, operation in audit["counter_operations"]} == {
        "construct",
        "subscription",
        "increment",
    }

    tooling_source = (ROOT / "tools" / "generate_content_catalog.py").read_text(
        encoding="utf-8"
    )
    assert "import re" in tooling_source
    assert all(path.is_relative_to(APP_ROOT) for path in APP_ROOT.rglob("*.py"))
