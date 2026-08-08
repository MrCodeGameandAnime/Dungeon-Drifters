# Architecture Streamlining and Portable Content Foundation

## Authority

This document controls the `flat` architecture stream beginning from the v0.3
release at `e7a89c2cc83b961430a1d84a6738e1b3da3ba540`.

The objective is to flatten the developer experience without flattening the
runtime architecture. Domain state, game orchestration, presentation, terminal
UI, persistence, and content remain separate responsibilities.

Normal content additions must have one primary authored definition, no private
state manipulation, no duplicated authored values, no platform-specific rules,
and one deterministic validation path.

## Locked Decisions

- The first stream covers enemies, Drifters, signature weapons, encounters, and
  routes. Run-item recipes and Android implementation remain deferred.
- Authored assets use one package per asset and one primary definition module.
- Development tooling discovers content. Runtime code imports a committed,
  generated catalog and never scans the filesystem.
- Schema-8 save compatibility is mandatory. Old Python authoring imports are not
  compatibility contracts.
- `app.content` is the public authoring facade. Combat, game, presentation, UI,
  and persistence retain their current physical packages and ownership.
- Every migration must preserve v0.3 gameplay and presentation behavior.

## Gates

### FLAT-1 - Unify Enemy Authoring

Replace the five-file enemy packages with one immutable `EnemySpec` module per
enemy. Generate the deterministic runtime catalog, retain generic `Enemy` and
`EnemyState` runtime ownership, and delete registration, per-enemy scaling, and
concrete enemy class paths. Tier 0 remains the only supported enemy tier.

Enemy stats, resources, rewards, metadata, moves, descriptions, encounter
compositions, route rewards, combat behavior, and presentation must not change.

### FLAT-2 - Unify Signature Weapon Authoring

Move signature weapons behind immutable content specifications while preserving
schema-8 weapon identity, canonical reconstruction, bonuses, and inspection.

Each signature weapon has one `WeaponSpec` package and a stable lowercase
`item_id`. Runtime `Weapon` objects also retain the legacy class-name-shaped
`persistence_key` used by existing schema-8 `type` payloads. The generated
catalog owns both lookups, every construction path returns a fresh generic
`Weapon`, and save reconstruction validates canonical authored data through the
persistence-key lookup. The four data-only weapon subclasses are removed.

FLAT-2 does not generalize run items, recipes, prepared payload mechanics, or
accessory equipment.

### FLAT-3 - Unify Drifter Authoring

Replace concrete Character subclasses and split profile wiring with one immutable
`DrifterSpec` package per character. Each specification is the sole authored
owner of its stable ID and selection choice, archetype name, six Level-1 stats,
five moves, class-mechanic description, signature-weapon ID, current run-state
defaults, and complete player-facing profile text.

The generated catalog discovers Drifter packages only during development and
records them deterministically by directory ID. Runtime selection uses catalog
lookup by the stable choice string, while runtime construction produces a fresh
generic `Character` and fresh mutable resources, equipment, and run-state
containers. Immutable authored `Move` values may be shared, but each Character
receives a distinct runtime move collection. Profile-driven character selection
attaches the canonical `DrifterSpec`; direct catalog construction preserves the
legacy unselected-character identity used by engine tests and tooling.

Schema-8 identity payloads and reconstruction continue through the existing
selection-choice seam. Character mechanics, effective stats, resources,
snapshots, signature weapons, profile rendering, and balance-probe behavior do
not change. The four concrete Character subclasses, four loadout modules, and
four split profile-definition modules are removed after all production and test
callers migrate to `app.content`.

FLAT-3 does not generalize run items or payload recipes, alter combat mechanics,
change persistence schema, or begin encounter and route migration.

### FLAT-4 - Unify Encounter and Route Authoring

Move each of the eight surface encounters behind its own immutable
`EncounterSpec` package. Move the surface route behind one ordered immutable
`RouteSpec` package. Route nodes own stable IDs, player-facing labels, kinds,
and canonical encounter references; encounter packages own ordered enemy
compositions.

Immediate successors derive from authored route order, Boss state derives from
route-node kind, and atomic EXP/gold totals derive from canonical enemy values.
The generated catalog discovers encounter and route packages only during
development, validates every reference, and enforces globally unique route-node
IDs so schema-8 route positions remain unambiguous.

`OverworldState`, `OverworldSession`, Map presentation, and save validation read
the catalog directly. `OverworldState` remains the route-position and
Rest-completion owner, and `WorldState` remains the encounter-completion owner.

FLAT-4 does not alter route order, labels, compositions, rewards, Rest, combat,
Map presentation, progression, snapshots, schema 8, or the passive Dungeon
Entrance endpoint. It does not add routes, encounters, procedural generation,
fast travel, or post-v0.3 dungeon gameplay.

### FLAT-5 - Complete Content Tooling and Guides

Add one transactional scaffolding command for enemies, weapons, Drifters,
encounters, and routes. Every scaffold creates the conventional package,
primary definition, focused test, and deterministic catalog record without
overwriting existing work. New templates remain explicitly unfinished through
`TODO(FLAT-CONTENT)` markers until the author replaces every placeholder.

Add one strictly read-only validation command that independently discovers the
five supported content types, verifies catalog freshness and immutable exports,
checks IDs and cross-content references, delegates authored move compatibility
to the resolver's pure rule boundary, and proves schema-8 reconstruction for
every built-in Drifter. CI runs this command before pytest and compiles tooling
alongside source and tests.

Document the complete workflow in `docs/flat/content authoring.md`. Preserve the
catalog APIs established by FLAT-1 through FLAT-4; FLAT-5 adds no aliases,
gameplay, schema fields, runtime filesystem scanning, or FLAT-6 cleanup.

### FLAT-6 - Remove Obsolete Paths and Harden Boundaries

Remove superseded enemy factories, route and encounter adapters, profile roster
modules, concrete content imports, and legacy move dictionaries after all
built-in content uses the public catalog. No compatibility class or duplicate
authored-value table remains behind those paths.

Lock the platform-neutral dependency direction: authored content cannot import
game sessions, presenters, terminal UI, save repositories, or runtime
orchestration; engine and presentation modules cannot import concrete authored
asset packages; runtime catalog loading cannot scan the filesystem. Exercise
all five scaffolders in isolated projects and prove their completed output
passes the canonical validator.

FLAT-6 preserves terminal behavior, combat, progression, rewards, Rest,
schema-8 Save/Load, and every v0.3 session contract. It does not reorganize the
remaining packages, implement Android, add gameplay, alter persistence, or add
another content type.

## Gate Protocol

Each gate runs focused tests, the complete pytest suite, compileall, generated
catalog checks where applicable, and `git diff --check`. Each gate receives one
reviewed commit and green exact-SHA CI before the next gate begins.

Stop for behavioral drift, save incompatibility, runtime filesystem discovery,
an ownership rewrite, unrelated cleanup, or work belonging to a later gate.
