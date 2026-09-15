# Contributing to Dungeon Drifters

Thanks for your interest in Dungeon Drifters. The project values focused
changes, clear ownership, and preserving the behavior that has already been
proved and released.

## Project Layout

```text
root/src/       game code
root/tests/     automated tests
root/tools/     content and development tools
docs/           guides, design notes, and project history
res/            local visual assets
```

Run Python project commands from `root/`. Run Git commands from the repository
root.

## Before You Start

- Read the README and the documentation relevant to your change.
- Check existing issues and pull requests before starting duplicate work.
- Create a focused branch from the current `master`.
- Keep unrelated cleanup out of feature changes.
- Do not commit directly to `master`.

## Adding Content

Use the supported authoring tools from `root/`:

```powershell
..\.venv\Scripts\python.exe -m tools.scaffold_content enemy <id>
..\.venv\Scripts\python.exe -m tools.scaffold_content weapon <id>
..\.venv\Scripts\python.exe -m tools.scaffold_content drifter <id>
..\.venv\Scripts\python.exe -m tools.scaffold_content encounter <id>
..\.venv\Scripts\python.exe -m tools.scaffold_content route <id>
```

After authoring content:

- Replace every `TODO(CONTENT-AUTHORING)` marker.
- Edit the primary authored module, not generated files.
- Regenerate the catalog.
- Run `python -m tools.validate_content`.
- Never edit `_generated_catalog.py` manually.

Read the [content authoring guide](content%20creation/content%20authoring.md)
for the complete workflow.

## Engine Changes

Content additions should use the existing catalog and engine contracts. New
mechanics require an approved design, a clear ownership boundary, and focused
tests before implementation.

Preserve the existing authorities:

- `PlayerState` owns persistent player mutations.
- `GameState` owns one active session.
- `Battle` owns combat orchestration.
- `CombatResolver` owns move resolution.
- The content catalog owns authored definitions.
- Save reconstruction must use canonical content and preserve schema identity.

Do not duplicate authored values, bypass state owners, add platform-specific
game rules, or introduce future-milestone behavior without an approved scope.

## Testing

From `root/`, run the focused tests for the changed area and then the full
verification set:

```powershell
..\.venv\Scripts\python.exe -m tools.validate_content
..\.venv\Scripts\python.exe -m pytest
..\.venv\Scripts\python.exe -m compileall src tests tools
```

From the repository root, run:

```powershell
git diff --check
```

Cross-cutting changes should include integration coverage, not only isolated
unit tests.

## Pull Requests

Describe:

- What changed
- Why it changed
- The systems and files affected
- Tests and verification commands run
- Deferred work or compatibility concerns

Keep pull requests narrow. Call out intentional behavior changes clearly.

## Review Standards

Reviews prioritize:

- Behavioral regressions
- Duplicate or unclear state ownership
- Persistence incompatibility
- Raw IDs or debug data in player-facing output
- Runtime filesystem discovery
- Weakened or implementation-mirroring tests
- Unrelated refactors
- Accidental future-milestone work

## Commits

Use concise, descriptive commit messages. Keep one logical change per commit
where practical, and do not rewrite shared history unless explicitly agreed.

## Local Assets

`res/maps/` and `res/menu/` contain local visual assets and are intentionally
ignored by Git. Do not re-add them unless the project policy changes.

## Community Standards

Please follow the [Code of Conduct](CODE_OF_CONDUCT.md).

For questions, use GitHub Issues or contact the project maintainers.
