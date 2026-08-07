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

### FLAT-3 - Unify Drifter Authoring

Replace concrete Character subclasses and split profile wiring with one authored
Drifter specification per character while preserving all mechanics, identity,
resources, snapshots, and save reconstruction.

### FLAT-4 - Unify Encounter and Route Authoring

Move encounter compositions and route shells behind validated authored content
without changing route order, rewards, Rest behavior, or completion ownership.

### FLAT-5 - Complete Content Tooling and Guides

Extend deterministic catalog generation, add validation and scaffolding commands,
and document one obvious workflow for each supported content type.

### FLAT-6 - Remove Obsolete Paths and Harden Boundaries

Remove superseded internal authoring paths after all built-in content uses the
new facade. Lock platform-neutral boundaries without implementing Android.

## Gate Protocol

Each gate runs focused tests, the complete pytest suite, compileall, generated
catalog checks where applicable, and `git diff --check`. Each gate receives one
reviewed commit and green exact-SHA CI before the next gate begins.

Stop for behavioral drift, save incompatibility, runtime filesystem discovery,
an ownership rewrite, unrelated cleanup, or work belonging to a later gate.
