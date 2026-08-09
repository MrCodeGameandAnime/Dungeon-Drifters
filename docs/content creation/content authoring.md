# Content Authoring

Dungeon Drifters has one supported workflow for each portable content type.
Run commands from the `root/` project directory. The virtual environment lives
one level above it at the repository root.

## Scaffold Content

Use an already-normalized lowercase snake-case ID:

```powershell
..\.venv\Scripts\python.exe -m tools.scaffold_content enemy new_enemy
..\.venv\Scripts\python.exe -m tools.scaffold_content weapon new_weapon
..\.venv\Scripts\python.exe -m tools.scaffold_content drifter new_drifter
..\.venv\Scripts\python.exe -m tools.scaffold_content encounter new_encounter
..\.venv\Scripts\python.exe -m tools.scaffold_content route new_route
```

Each command creates one package, one primary module, one conventional export,
and one focused test:

| Type | Primary module | Export |
| --- | --- | --- |
| Enemy | `content/enemies/<id>/enemy.py` | `ENEMY` |
| Weapon | `content/weapons/<id>/weapon.py` | `WEAPON` |
| Drifter | `content/drifters/<id>/drifter.py` | `DRIFTER` |
| Encounter | `content/encounters/<id>/encounter.py` | `ENCOUNTER` |
| Route | `content/routes/<id>/route.py` | `ROUTE` |

Scaffolding refuses collisions and never overwrites files. Its conservative
placeholder definitions import successfully, but validation intentionally fails
until every `TODO(CONTENT-AUTHORING)` marker has been replaced with authored values.

## Identity And References

Stable content IDs are runtime and persistence contracts. Do not rename an ID
that has shipped in schema-8 saves. Weapon `persistence_key` values are the
serialized weapon identity and must also remain stable and globally unique.
Drifter selection choices and route-node IDs are persistent identities.

Encounters reference enemy archetype IDs. Routes reference encounter IDs, and
their immediate successors derive from node order. References must resolve
through `app.content.catalog`; do not duplicate enemy, reward, Boss, or successor
data in another table.

## Generate And Validate

Never edit `src/app/content/_generated_catalog.py` manually. Regenerate it with:

```powershell
..\.venv\Scripts\python.exe -m tools.generate_content_catalog
```

Run the read-only validator before tests:

```powershell
..\.venv\Scripts\python.exe -m tools.validate_content
..\.venv\Scripts\python.exe -m pytest tests\test_content_tooling.py
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m compileall src tests tools
git diff --check
```

The validator checks catalog freshness, exports, immutable specifications,
identity uniqueness, references, factories, authored move compatibility, and
schema-8 reconstruction.

Adding content means composing behavior already supported by the engine. A new
move mechanic, runtime state owner, persistence field, target rule, or combat
contract is engine work and must receive its own design and tests before content
can reference it.
