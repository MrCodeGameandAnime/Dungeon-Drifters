# FLAT - Portable Content Authoring Foundation

## Summary

Refactor `flat` from the sealed v0.3 baseline into a content-authoring platform without changing gameplay.

```text
Branch: flat
Baseline: e7a89c2cc83b961430a1d84a6738e1b3da3ba540
Baseline tests: 1,083 passed
```

The migration will unify enemies, Drifters, weapons, encounters, and routes under `app.content`. Combat, game orchestration, presentation, and terminal packages remain physically unchanged.

Runtime will use a committed deterministic catalog. Only development tools may scan content packages.

Schema 8 and existing v0.3 saves remain compatible. Obsolete internal Python authoring APIs do not.

## Public Content Contracts

Add immutable specifications:

- `StatBlockSpec`
- `EnemySpec`
- `WeaponSpec`
- `DrifterSpec`
- `EncounterSpec`
- `RouteNodeSpec`
- `RouteSpec`

Existing immutable `Move` remains the authored move contract.

Every asset uses a package containing one primary editable file:

```text
app/content/enemies/goblin/enemy.py
app/content/weapons/sunder_spire/weapon.py
app/content/drifters/branoc/drifter.py
app/content/encounters/surface_goblin_solo/encounter.py
app/content/routes/surface/route.py
```

Each module exports exactly one conventional symbol:

```text
ENEMY
WEAPON
DRIFTER
ENCOUNTER
ROUTE
```

`app.content.catalog` becomes the runtime front door:

```python
get_enemy_spec(archetype_id)
create_enemy_definition(archetype_id, tier=0)
create_enemy_state(archetype_id, tier=0)

get_weapon_spec(item_id)
create_weapon(item_id)

get_drifter_specs()
get_drifter_by_id(drifter_id)
get_drifter_by_choice(choice)
create_drifter(drifter_id)

get_encounter_spec(encounter_id)
get_route_spec(route_id)
find_route_node(node_id)
```

The generated catalog is tracked, deterministic, immutable at runtime, and contains the only concrete content imports.

## Migration Gates

### FLAT-0 - Lock v0.3 Content Parity

- Record this plan under `docs/flat/`.
- Add independent contract tests for all existing enemies, moves, rewards, weapons, Drifter identities, stats, equipment, run state, encounters, and route nodes.
- Lock representative schema-7 snapshots and schema-8 save documents for all four Drifters.
- Lock route endpoint totals and all M11 session acceptance behavior.
- Make no production changes.

### FLAT-1 - Unify Enemy Authoring

- Add the shared content-spec foundation and generated-catalog machinery.
- Move all five enemies into one-file `EnemySpec` packages.
- Store ordinary tier support directly on each spec; custom scaling remains an optional callable.
- Derive fresh `Enemy` definitions and independent `EnemyState` instances from specs.
- Replace the central registration tuple and per-enemy definition, registration, scaling, and move modules.
- Move supported mechanic identity into one engine-owned combat contract so validation does not duplicate resolver knowledge.
- Preserve every authored value, reward, move, enum value, tier rejection, and factory-isolation guarantee.

### FLAT-2 - Unify Weapon Authoring and Save Identity

- Move all four signature weapons into `WeaponSpec` packages.
- Give runtime `Weapon` objects stable `item_id` and `persistence_key` values.
- Preserve the existing schema-8 weapon payloads, including legacy type values such as `SunderSpire`.
- Replace `_WEAPON_TYPES` with catalog lookup by persistence key.
- Make every factory return a fresh weapon.
- Remove the four weapon subclasses after all consumers migrate.
- Do not generalize run items, recipes, payload mechanics, or accessory equipment.

### FLAT-3 - Unify Drifter Authoring

- Move profile text, six starting stats, combat moves, class-mechanic metadata, starting weapon ID, and optional existing run-state references into four `DrifterSpec` packages.
- Replace the four Character subclasses with generic `Character` construction from a spec.
- Derive character selection, roster order, canonical profile identity, starting equipment, and save reconstruction from the Drifter catalog.
- Preserve current profile choices and snapshot identity fields so schema-8 saves remain loadable.
- Remove loadout modules, profile modules, the manual roster, `create_legacy_moves()`, and `Character.moves`.
- Update the balance probe and tests to use stable Drifter IDs and catalog factories.
- Preserve all four mechanic families and fresh runtime ownership.

### FLAT-4 - Unify Encounter and Route Authoring

- Move the eight encounters into `EncounterSpec` packages.
- Move the surface route into one ordered `RouteSpec`.
- Derive encounter rewards from enemy composition.
- Derive Boss state from route-node kind.
- Derive immediate successors from authored route order.
- Enforce globally unique route-node IDs so current route position remains reconstructible without changing schema 8.
- Replace the duplicated route shell and manifest authoring sources.
- Update OverworldState, session orchestration, map presentation, and save validation to read the catalog.
- Preserve every route ID, label, composition, reward, Rest boundary, and Dungeon Entrance endpoint.

### FLAT-5 - Add Content Tooling and Guides

Add one scaffolding command:

```powershell
python -m tools.scaffold_content enemy skeleton_knight
python -m tools.scaffold_content weapon moonlit_spear
python -m tools.scaffold_content drifter mireya
python -m tools.scaffold_content encounter crypt_guard
python -m tools.scaffold_content route dungeon_one
```

The scaffolder will:

- validate normalized IDs and refuse collisions or overwrites
- create the asset package and primary file
- create a focused discoverability/factory test
- regenerate the tracked catalog
- leave intentionally unfinished authored fields visibly marked

Add one read-only validation command:

```powershell
python -m tools.validate_content
```

It will verify:

- generated catalog freshness
- required exports and immutable spec types
- duplicate IDs, choices, persistence keys, and node IDs
- Drifter stat totals and starting references
- move structures and engine-supported mechanics
- enemy tiers and rewards
- weapon bonuses and persistence identity
- encounter enemy references
- route encounter references and node compatibility
- schema-8 reconstruction coverage

Add the validator to CI before pytest and document the complete author workflow in one concise guide.

### FLAT-6 - Remove Legacy Paths and Harden Boundaries

- Remove residual old registries, concrete content imports, compatibility classes, and duplicate authored values once no built-in uses them.
- Ensure production performs no filesystem scanning.
- Ensure content modules do not import sessions, presenters, terminal UI, save repositories, or runtime orchestration.
- Ensure engine and presentation code import only public content catalog APIs, never concrete asset modules.
- Prove terminal behavior, battle behavior, progression, rewards, Rest, and save/load remain unchanged.
- Exercise every scaffolder in a temporary workspace and validate its output.
- Perform no Android implementation; only preserve a platform-neutral engine/content boundary.

## Test and Gate Protocol

Each gate must:

1. Run gate-focused content and parity tests.
2. Run `python -m tools.validate_content` once that command exists.
3. Run the full pytest suite.
4. Run `python -m compileall src tests tools`.
5. Run `git diff --check`.
6. Review the exact diff for duplicated authority, behavioral drift, runtime scanning, and unrelated cleanup.
7. Commit and push `flat`.
8. Verify local and remote SHA equality.
9. Verify green CI for that exact SHA.
10. Stop for gate review before continuing.

Final acceptance requires:

- every built-in asset authored through the new content surface
- schema-8 v0.3 saves loading without rewrite or data loss
- exact content, snapshot, route, and behavioral parity
- no obsolete authoring path remaining
- deterministic catalog generation on Windows and CI
- successful scaffold-and-validate proofs for every supported category
- full regression, M11 acceptance, compileall, diff-check, and exact-SHA CI green

## Locked Boundaries

- No combat mechanics, balance values, progression formulas, UI behavior, or route content changes.
- No schema bump.
- No runtime package scanning.
- No physical reorganization of combat, game, presentation, or UI packages.
- No Android code.
- No generalization of run items, crafting recipes, prepared payloads, accessories, or item-use mechanics.
- Drifter specs may reference existing run-item and payload IDs only.
- Historical v0.3 documentation remains historical; the new authoring guide describes the `flat` architecture.
