# Dungeon Drifters MicroPython Closure

Qualification date: 2026-09-18

Final branch: `myp`

Final MYP20 SHA: this release commit; exact SHA is reported by Git at release

Pinned runtime:

```text
MicroPython: v1.29.0
source SHA: 0fd6c573ea815774668bbb16b8e197c8822368b2
platform: win32
```

## Architecture

Dungeon Drifters retains one authoritative Python gameplay implementation.
MicroPython qualification did not introduce a second combat engine, second
session implementation, alternate game state, alternate route/content
representation, platform-specific gameplay forks, or an interpreter fork.
Compatibility work remains narrow portable source correction and runtime
boundary work.

The qualified compatibility inventory is:

```text
readonly mapping compatibility
generated dataclass metadata and dataclass overlay
StrEnum compatibility
keyword compatibility
regex fullmatch compatibility
collections.abc compatibility
typing / Protocol compatibility
portable ASCII validation
Counter dependency removal
starred tuple expression portability
strict zip removal
session persistence import boundary
itertools.groupby removal
first_or_none iteration boundary
portable random adapter
```

These mechanisms are qualified application boundaries, not a claim that
each is a general-purpose library abstraction.

## Qualified Runtime Contract

Native CPython, forced-overlay CPython, and pinned MicroPython independently
passed the sealed stage sequence through route-session teardown and the exact
twelve-node surface route:

```text
surface_goblin_solo
surface_goblin_pair
surface_warrior_solo
surface_rest_after_warrior_solo
surface_warrior_pair
surface_shaman_solo
surface_shaman_pair
surface_rest_after_shaman_pair
surface_elite_patrol
surface_rest_before_goblin_lord
surface_goblin_lord
surface_dungeon_entrance
```

The semantic signature was the ordered stage PASS sequence, ordered route
PASS sequence, and the single completion marker
`MYP|RESULT|RAW_PROBE_STAGES_COMPLETE`. Memory telemetry, traceback text,
runtime identity, and dataclass census values were excluded from parity.

Runtime identity evidence:

```text
CPYTHON_NATIVE          cpython 3.14.6 win32
CPYTHON_FORCED_OVERLAY  cpython 3.14.6 win32
MICROPYTHON_DEFAULT     micropython 1.29.0 win32
MICROPYTHON_448K        micropython 1.29.0 win32
```

The route contract proved 8 encounters, 3 Rests, 8 Battles, 14 fresh
enemies, Goblin Lord defeat, Dungeon Entrance, level 9, EXP 68, 24 growth
points, 75 gold, `route_complete = True`,
`dungeon_entrance_reached = True`, `active_battle = None`, and no persistence
materialization.

## MYP19 Pressure Reconfirmation

MYP20 did not search for a new heap floor. It reran only the sealed pressure
points:

```text
MYP20|HEAP|448K|STABLE_PASS|3/3
MYP20|HEAP|416K|MEMORY_LIMIT_CONFIRMED|3/3
```

The 448K runs reached `ROUTE_FINAL_STATE`, `ROUTE_EVIDENCE_RELEASE`,
`ROUTE_SESSION_TEARDOWN`, and the completion marker. All three 416K runs
failed at:

```text
last stage: SESSION_IMPORT
last route node: none
exception: MemoryError
message: memory allocation failed, allocating 2344 bytes
```

The 448K result is an observed stable qualification floor for this Windows
MicroPython harness, not a product threshold or PS5 memory budget. The 416K
result is not a universal MicroPython failure point.

## Verification

```text
full CPython suite:       1467 passed
focused closure suite:      27 passed
cumulative portability:    577 passed
compileall:                passed
dataclass manifest:        current, 74 entries
git diff --check:          passed
```

The focused closure suite covered the matrix contract, sealed route-probe
contract, and sealed heap-sweep contract. The cumulative suite retained the
entire MYP19 list and added the matrix contract.

## Non-Claims

This closure does not claim that all future content is automatically
MicroPython-compatible, that every Drifter mechanic has been exhaustively
executed under MicroPython, that 448K is a recommended production heap or
PS5 RAM requirement, that the Windows port models PS5 hardware, or that
console graphics, audio, input, lifecycle, SDK, storage, packaging,
certification, or shipping are complete. SAVE-ARCH remains deferred;
MYP14 only decoupled the session persistence import boundary.

## Requalification Triggers

The nominal MYP sequence is closed. A new portability campaign is justified
only after a material change such as a MicroPython version change, a new
headless runtime dependency or language feature, newly exercised gameplay
content, core session/combat architecture changes, dataclass-contract or
overlay changes, persistence entering the constrained runtime contract, or a
material target-runtime change.

Normal Dungeon Drifters development should continue normally, with
MicroPython treated as a regression target rather than a gate-number-driven
design process.

```text
Dungeon Drifters MicroPython portability campaign MYP0-MYP20: CLOSED.

The current authoritative headless gameplay runtime and authored surface-route
contract are qualified on pinned MicroPython v1.29.0 without a second
gameplay implementation.

Future portability work is evidence-driven rather than gate-number-driven.
```
