# MPY9 - Repair Portable ASCII String Validation

## Summary

Advance MicroPython `v1.29.0` beyond the `DrifterSpec` failure at:

```text
AttributeError: 'str' object has no attribute 'isascii'
```

Baseline:

```text
MPY8:
bb99b7e1e9360078b157a85400e3c9dea73a386f
```

The pinned runtime lacks both `str.isascii()` and `str.isdecimal()`. MPY9 will replace both assumptions with the already-qualified MPY7 regex boundary while preserving the exact existing validation semantics.

## Production Change

Modify only:

```text
root/src/app/content/drifter_spec.py
```

Add:

```python
_ASCII_DECIMAL_PATTERN = re.compile(r"^[0-9]+$")
```

Replace the existing `isascii()` and `isdecimal()` checks with:

```python
choice = _nonempty_string("choice", self.choice)
if (
    _ASCII_DECIMAL_PATTERN.fullmatch(choice) is None
    or int(choice) < 1
):
    raise ValueError("choice must be a positive ASCII integer string")
```

This preserves:

- non-string `TypeError` behavior;
- exact `ValueError` type and message;
- positive integer requirements;
- leading-zero acceptance;
- rejection of signs, whitespace, punctuation, letters, and Unicode digits;
- public APIs, content, persistence, and gameplay behavior.

The existing `isdecimal()` use in `root/tools/scaffold_content.py` remains unchanged because tooling is outside the runtime audit.

No compatibility module, bootstrap change, global string patch, string wrapper, source transformer, dataclass special case, or unrelated `Counter` work will be added.

## Audit And Tests

Add a dynamic audit at:

```text
root/tests/test_string_contract.py
```

It will inspect only `root/src/app/**/*.py` and verify the post-change production contract:

```text
Drifter choice validation:
    regex fullmatch
    +
    int(choice) >= 1

production isascii usage:
    none

production isdecimal usage:
    none

unsupported MicroPython string methods:
    none in the qualified audit surface
```

The audit must use discovered calls rather than permanent counts and must fail visibly if future production code introduces an unsupported string method.

Add focused regression coverage for:

- CPython reference-contract equivalence;
- ASCII positive integers;
- leading zeroes;
- zero and negative values;
- plus/minus signs;
- decimal and underscore forms;
- whitespace and punctuation;
- letters and empty strings;
- Arabic-Indic, full-width, superscript, fraction, Roman-numeral, and mixed Unicode digits;
- exact error type and message;
- preserved non-string `TypeError`;
- real `DrifterSpec` construction;
- generated catalog import beyond the former `isascii` wall.

The equivalence reference remains:

```python
isinstance(value, str)
and bool(value)
and value.isascii()
and value.isdecimal()
and int(value) >= 1
```

The portable regex expression must produce identical accept/reject results across the full corpus.

## MicroPython Qualification And Documentation

Before the raw probe, record:

```text
str.isascii: false
str.isdecimal: false
str.isdigit: true
setattr(str, "isascii", ...): AttributeError
builtins.str replacement: literal strings remain builtin str
```

Then run the real Drifter specification under the complete existing MPY compatibility stack and require successful construction.

Run the unchanged raw probe through the existing bootstrap. Record the exact next stage, exception, message, traceback, memory values, and dataclass census. Stop at that next unrelated wall without repairing it.

Update `docs/portability/micropython-probe.md` with:

- MPY8 sealed SHA;
- historical dual-method failure;
- post-MPY9 production audit;
- exact validation equivalence;
- rejected global string-patching mechanisms;
- direct MicroPython results;
- real DrifterSpec result;
- exact next raw-probe frontier;
- updated census and memory evidence;
- explicit scope counts.

Expected scope:

```text
root/src production files changed: 1
semantic behavior changed: 0
gameplay changed: 0
content changed: 0
persistence changed: 0
semantic API changed: 0
raw probe changed: 0
compatibility framework changes: 0
bootstrap changes: 0
```

## Verification And Release

Run the full suite, all prior MPY portability tests plus the new string tests, compileall for `root/src`, `root/tests`, `root/tools`, and `root/portability`, dataclass-manifest freshness, and `git diff --check`.

Review specifically for:

```text
no remaining production isascii/isdecimal calls
no tooling changes
no generated catalog changes
no overlay changes
no Counter repair
no save/schema changes
no gameplay drift
```

Commit exactly:

```text
MPY9 - Repair Portable ASCII String Validation
```

Push `mpy`, verify local and remote SHA equality, require exact-SHA green CI, and stop at the next observed MicroPython compatibility frontier.
