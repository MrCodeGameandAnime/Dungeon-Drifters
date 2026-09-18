# MYP11 - Repair Portable Typing Protocol Boundary

**Goal:** Advance MicroPython beyond the missing `typing` import while preserving DD’s Protocol contracts, gameplay, persistence, content, and semantic APIs.

**Architecture:** Keep native Protocol declarations for CPython and static tooling. Add a minimal MicroPython-only typing overlay, replace only production Protocol runtime checks with contract-owned structural predicates, and rewrite only runtime-evaluated TypeAlias unions.

**Baseline:** `myp` at `00b7733c02a8b78ebfb856ccbe5fc9ea119f6fe9`. Historical untracked `docs/mpy/` files remain untouched.

## Audit

Create `root/tests/test_typing_contract.py` to dynamically inspect only `root/src/app/**/*.py`.

Classify every:

- `typing` import;
- `Protocol`, `runtime_checkable`, `TypeAlias`, `Sequence`, and `Union` use;
- PEP 604 `A | B` expression;
- Protocol `isinstance` or `issubclass` check;
- TypeAlias runtime assignment;
- runtime use or reflection of an alias.

The audit must distinguish:

- class annotations;
- function and method annotations;
- runtime TypeAlias assignments;
- ordinary runtime expressions.

Do not mechanically reject all PEP 604 syntax. Leave annotation-only unions unchanged when the pinned runtime accepts them. Correct only runtime-evaluated unions.

The current runtime aliases are:

```text
BattleInput
OverworldInput
SessionView
SessionInput
```

Prove that no alias is used as a runtime type operand, dispatch authority, persistence value, or reflection target.

The audit must identify the current Protocol checks in:

- `Battle._normalize_enemies`;
- `resolver._is_valid_combatant`;
- `OverworldSession.__init__`.

`BattleUI` remains a public Protocol contract but has no current production runtime check.

### Protocol/predicate parity

The audit must derive each Protocol’s declared members from the production AST.

Classify each member as:

- data/property member;
- callable method member.

Include inherited `Combatant` members when deriving `EnemyCombatant`.

Compare the discovered declarations against the exact member groups used by:

```text
is_combatant
is_enemy_combatant
is_battle_ui
is_overworld_ui
```

The test must fail if either the Protocol declaration or the predicate requirements gain, lose, or reclassify a member without the other changing.

## Implementation

### Portable typing overlay

Create `root/portability/micropython/typing.py`.

Export only:

```python
Protocol
runtime_checkable
TypeAlias
Sequence
Union
```

Implement:

- `Protocol` as a basic subclassable class;
- `runtime_checkable` as an identity decorator;
- `TypeAlias` as an inert marker;
- `Sequence` as a minimal subscriptable annotation marker;
- `Union` as a minimal object supporting `Union[...]` and returning an inert tuple-like representation.

The direct MicroPython preflight proves object subscription works while class subscription does not. Use `Union[...]`; do not use quoted aliases or a class-based generic mechanism.

Do not implement general typing, runtime union semantics, generic runtime checking, reflection, `get_type_hints`, or global `isinstance` replacement.

### Alias source correction

Modify only:

```text
root/src/app/ui/battle_ui.py
root/src/app/ui/overworld_ui.py
root/src/app/game/overworld_session.py
```

Change the four aliases to `Union[...]` and add `Union` to the existing imports.

Preserve native CPython typing semantics through standard-library `typing.Union`.

Do not rewrite annotation-only PEP 604 expressions elsewhere in `root/src/app`.

### Shared structural contract primitive

Create `root/src/app/runtime_contracts.py`:

```python
def has_required_members(
    value,
    member_names,
    callable_member_names=(),
) -> bool:
    ...
```

The primitive must:

- return `False` for `None`;
- require every data member to be accessible;
- require every callable member to be accessible and callable;
- reject missing, `None`, and non-callable method values;
- avoid signature inspection;
- avoid Protocol, metaclass, or global runtime patching.

### Contract-owned predicates

Add:

```python
app.combat.combatant.is_combatant(value) -> bool
app.combat.combatant.is_enemy_combatant(value) -> bool
app.ui.battle_ui.is_battle_ui(value) -> bool
app.ui.overworld_ui.is_overworld_ui(value) -> bool
```

Define the requirement groups once in immutable module-local tuples used directly by the predicates:

Combatant data members:

```text
display_name
health
mana_resource
super_resource
generates_super
can_defend
combat_moves
```

Combatant callable members:

```text
effective_stat
defend_reduction_percent
is_alive
```

EnemyCombatant adds data members:

```text
archetype_id
tier
```

Both UI contracts require callable:

```text
render
read_input
```

Expose no new public registry or second contract authority. The parity test may inspect the module-local requirement tuples to compare them with the AST-derived Protocol declarations.

Do not validate signatures. Preserve the resolver’s existing explicit property accesses and callable checks after the new predicate, even where that creates intentional redundancy.

### Production call sites

Replace only Protocol runtime checks:

- `Battle._normalize_enemies` uses `is_enemy_combatant`;
- `resolver._is_valid_combatant` uses `is_combatant`;
- `OverworldSession.__init__` uses `is_overworld_ui`.

Preserve all existing error messages, rejection behavior, lifecycle ordering, and non-Protocol `isinstance` checks.

Leave Protocol declarations and `runtime_checkable` decorators intact. Do not add a BattleUI production check where none currently exists.

## Tests

Create `root/tests/test_portable_typing.py` using subprocesses for forced-overlay qualification.

Prove:

- the subprocess imports `root/portability/micropython/typing.py`;
- normal CPython imports standard-library `typing`;
- Protocol declarations load under the overlay;
- `runtime_checkable` does not create fake global `isinstance` behavior;
- `Sequence[...]` and `Union[...]` load and subscribe;
- all four aliases import successfully;
- ordinary dataclasses remain unaffected;
- valid structural doubles satisfy each contract predicate;
- missing methods are rejected;
- methods set to `None` are rejected;
- non-callable method values are rejected;
- real `PlayerState` and `EnemyState` satisfy combat predicates;
- forced tests cannot leak `sys.modules` or process-global state.

Add Protocol/predicate parity tests proving:

- every Protocol member is discovered dynamically from AST;
- property members and method members are classified correctly;
- inherited `Combatant` requirements are included in `EnemyCombatant`;
- predicate member tuples exactly match the discovered declaration groups;
- data members are not accidentally classified as callable;
- callable members are not reduced to presence-only checks;
- adding or removing a Protocol member causes a visible test failure until its predicate contract is updated.

Extend native tests to prove:

- CPython Protocol `isinstance` behavior remains unchanged;
- helper predicates agree with native Protocol acceptance for representative valid and invalid objects;
- callable methods are required by the contract predicates;
- duplicate enemy identity rejection remains unchanged;
- resolver rejection reasons remain unchanged;
- OverworldSession’s existing UI validation message remains unchanged.

Add dynamic tests proving:

- all discovered TypeAlias assignments use the qualified `Union[...]` representation;
- annotation-only PEP 604 expressions remain untouched;
- no alias is passed to `isinstance` or `issubclass`;
- no alias is used for runtime dispatch, persistence, or reflection;
- unsupported future typing APIs fail the audit.

Retain all prior dataclass, enum, keyword, regex, collections, string, Counter, Battle, M10, and M11 coverage, including:

```text
tests/test_portable_counter_removal.py
```

## Documentation

Update `docs/portability/micropython-probe.md` with:

- MYP10 sealed SHA and the original `ImportError: no module named 'typing'`;
- the complete dynamic typing import audit;
- all discovered Protocol declarations and runtime checks;
- the distinction between Protocol declarations and runtime predicates;
- the data-member versus callable-member contract;
- the Protocol/predicate parity invariant;
- the distinction between annotation-only and runtime-evaluated PEP 604 unions;
- MicroPython evidence that `metaclass=` and custom `__instancecheck__` are unusable;
- successful object-subscription evidence for `Union[...]`;
- the selected import-only typing overlay;
- the shared structural predicate mechanism;
- preserved CPython Protocol behavior;
- native and forced-overlay results;
- pinned MicroPython results after the typing wall;
- exact next stage, exception, message, traceback, memory, and dataclass census;
- zero browser, Android, C++, persistence, schema, content, gameplay, and save changes.

Update future-gate wording so MYP11 records the typing boundary and the next gate is derived from the next observed raw-probe failure.

## Verification

Run:

```powershell
Push-Location root

& ..\.venv\Scripts\python.exe -m pytest

& ..\.venv\Scripts\python.exe -m pytest `
  tests\test_dataclass_contract.py `
  tests\test_portable_dataclasses.py `
  tests\test_enum_contract.py `
  tests\test_portable_enum.py `
  tests\test_keyword_contract.py `
  tests\test_portable_keyword.py `
  tests\test_regex_contract.py `
  tests\test_portable_regex.py `
  tests\test_collections_contract.py `
  tests\test_portable_collections_abc.py `
  tests\test_string_contract.py `
  tests\test_portable_string_validation.py `
  tests\test_portable_counter_removal.py `
  tests\test_typing_contract.py `
  tests\test_portable_typing.py `
  tests\test_combatant_contract.py `
  tests\test_battle_ui_contract.py `
  tests\test_overworld_presentation_models.py

Pop-Location

.\.venv\Scripts\python.exe -m compileall `
  root\src `
  root\tests `
  root\tools `
  root\portability

.\.venv\Scripts\python.exe root\tools\generate_dataclass_manifest.py --check

git diff --check
```

Then run:

1. Native CPython raw probe.
2. Forced-overlay CPython qualification.
3. Direct pinned MicroPython typing qualification.
4. The unchanged raw probe through `root/tools/micropython_probe_bootstrap.py`.

The MicroPython run must show that the `typing` wall is crossed. Stop at the first unrelated failure and preserve its original traceback, memory evidence, and dynamic dataclass census.

## Scope And Release

Permitted production changes are limited to:

- `root/portability/micropython/typing.py`;
- `root/src/app/runtime_contracts.py`;
- contract-owned predicates;
- the three Protocol runtime call sites;
- the three modules containing the four `Union[...]` aliases;
- focused tests;
- portability documentation.

Forbidden:

- global `isinstance` or `type` patching;
- Protocol metaclass emulation;
- broad typing implementation;
- source transformation;
- nominal combatant fallbacks;
- persistence or save-schema changes;
- gameplay, content, presenter, or semantic API changes;
- bootstrap redesign;
- speculative repair of the next MicroPython wall.

Commit exactly:

```text
MYP11 - Repair Portable Typing Protocol Boundary
```

Push `myp`, verify local and remote SHA equality, require exact-SHA green CI, and stop at the next compatibility frontier.
