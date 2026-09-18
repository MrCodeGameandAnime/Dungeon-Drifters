import os
import subprocess
import sys
from dataclasses import replace
from pathlib import Path

import pytest

from app.content.catalog import get_drifter_spec
from app.content.drifter_spec import _ASCII_DECIMAL_PATTERN


ROOT = Path(__file__).resolve().parents[1]
SRC_ROOT = ROOT / "src"
OVERLAY_ROOT = ROOT / "portability" / "micropython"
ERROR_MESSAGE = "choice must be a positive ASCII integer string"


def _existing_contract(value):
    return (
        isinstance(value, str)
        and bool(value)
        and value.isascii()
        and value.isdecimal()
        and int(value) >= 1
    )


def _portable_contract(value):
    return (
        isinstance(value, str)
        and bool(value)
        and _ASCII_DECIMAL_PATTERN.fullmatch(value) is not None
        and int(value) >= 1
    )


def _run_forced_regex(source):
    prelude = (
        "import dataclasses\n"
        "import enum\n"
        "import keyword\n"
        "import re as native_re\n"
        "import json\n"
        "import sys\n"
        f"sys.path.insert(0, {str(OVERLAY_ROOT)!r})\n"
        f"sys.path.insert(1, {str(SRC_ROOT)!r})\n"
        "from re_compat import install\n"
        "sys.modules['re'] = install(native_re)\n"
    )
    return subprocess.run(
        [sys.executable, "-S", "-c", prelude + source],
        cwd=ROOT,
        env=os.environ.copy(),
        capture_output=True,
        text=True,
    )


@pytest.mark.parametrize("value", ("1", "2", "9", "10", "99", "001"))
def test_real_drifter_spec_accepts_positive_ascii_decimal_choices(value):
    assert replace(get_drifter_spec("branoc"), choice=value).choice == value


@pytest.mark.parametrize(
    "value",
    (
        "0",
        "-1",
        "+1",
        "1.0",
        "1_0",
        "1 ",
        " 1",
        "\t1",
        "1\n",
        "a",
        "abc",
        "1a",
        "!",
        "#",
        "/",
        "１２３",
        "١٢٣",
        "²",
        "½",
        "Ⅻ",
        "1١",
        "١1",
    ),
)
def test_real_drifter_spec_rejects_non_positive_or_non_ascii_choices(value):
    with pytest.raises(ValueError, match="^choice must be a positive ASCII integer string$"):
        replace(get_drifter_spec("branoc"), choice=value)


def test_real_drifter_spec_preserves_empty_choice_validation():
    with pytest.raises(ValueError, match="^choice must not be empty$"):
        replace(get_drifter_spec("branoc"), choice="")


@pytest.mark.parametrize("value", (None, True, 1, object()))
def test_real_drifter_spec_preserves_non_string_type_error(value):
    with pytest.raises(TypeError):
        replace(get_drifter_spec("branoc"), choice=value)


def test_portable_expression_matches_the_existing_cpython_contract():
    values = (
        "0", "1", "2", "9", "10", "99", "001",
        "-1", "+1", "1.0", "1_0", "1 ", " 1", "\t1", "1\n",
        "a", "abc", "1a", "", "!", "#", "/",
        "１２３", "١٢٣", "²", "½", "Ⅻ", "1١", "١1",
    )
    assert [(_existing_contract(value), _portable_contract(value)) for value in values] == [
        (_existing_contract(value), _existing_contract(value)) for value in values
    ]


def test_forced_regex_compatibility_imports_catalog_past_old_string_wall():
    result = _run_forced_regex(
        """
from app.content.catalog import get_drifter_spec
spec = get_drifter_spec("branoc")
assert spec.choice == "1"
assert __import__("re")._dd_myp7_proxy is True
assert __import__("re").fullmatch(r"^[0-9]+$", "001") is not None
try:
    from dataclasses import replace
    replace(spec, choice="１２３")
except ValueError as exc:
    assert str(exc) == "choice must be a positive ASCII integer string"
else:
    raise AssertionError("Unicode decimal choice was accepted")
"""
    )
    assert result.returncode == 0, result.stdout + result.stderr
