# Dungeon Drifters Windows Executable Plan

**Authority:** This document is the controlling implementation plan for the first official Windows executable distribution of Dungeon Drifters.

**Goal:** Produce a reproducible Windows x64 build of Dungeon Drifters that a player can download, extract, and launch by double-clicking `DungeonDrifters.exe` without installing Python, creating a virtual environment, using pip, or interacting with the repository.

**Precondition:** The SAVE-ARCH work in `docs/save/` must be fully implemented, reviewed, merged, and sealed before this plan begins. This plan consumes the finished save/account/profile architecture. It must not redesign persistence.

**Planning reference:** At the time this plan was written, the repository's public checkpoint was v0.4 and the Python project lived under `root/`. The implementation executor must record the actual post-SAVE-ARCH `master` SHA before branching and use that SHA as the Windows packaging baseline.

**Packaging stack:** Python 3.14, PyInstaller 6.22.3, Windows x64, console-enabled `onedir` bundle, GitHub Actions Windows runner.

---

# Global Constraints

- This is a Windows client/distribution milestone, not a gameplay milestone.
- Do not alter combat rules, balance, Drifter data, enemy data, route behavior, progression rules, content-authoring contracts, presentation contracts, or game-state semantics to make packaging easier.
- SAVE-ARCH is authoritative for profile identity, local persistence, remote synchronization, account/session semantics, conflict behavior, and entitlements.
- The Windows client must consume the SAVE-ARCH ports/adapters. It must not introduce a second Windows-only save format.
- The remote DD profile service is a separate deployment. It must NOT be bundled inside `DungeonDrifters.exe`, started as a child process, or installed beside the game.
- Offline play must remain functional exactly as SAVE-ARCH defines it.
- A valid local profile must be loadable when the network and backend are unavailable.
- Persistent authentication credentials must remain outside profile/save data.
- Windows credential persistence must implement the existing SAVE-ARCH `CredentialStore` contract using the Windows credential facility.
- No plaintext auth token may be written into the game directory, `%LOCALAPPDATA%` profile files, logs, crash output, or release ZIP.
- Keep DD console-enabled. Do not use PyInstaller `--windowed`/`--noconsole`.
- Start with PyInstaller `onedir`. Do not pursue `onefile` during this milestone.
- Build Windows binaries on Windows. Do not attempt to cross-compile the release artifact from Linux.
- The release output must not depend on the developer's active venv, repository checkout, source tree, Python installation, or user-specific absolute paths.
- `build/`, `dist/`, temporary packaging output, and generated ZIPs remain untracked.
- Hidden imports, hooks, data collection, DLL collection, and runtime hooks must be added only when a reproduced packaging failure proves they are needed.
- Do not broadly collect `app.*`, the entire repository, or the filesystem "just in case."
- Preserve the deterministic content catalog. Packaging must not add runtime content scanning.
- The player-facing artifact is a ZIP containing the complete `onedir` distribution.
- The first official Windows build is x64 only.
- Installer/MSIX, Microsoft Store, code signing, auto-update, launcher, browser build, Linux package, macOS bundle, mobile packaging, PlayStation packaging, and `onefile` optimization are out of scope.
- A SmartScreen/reputation warning on an unsigned first release is an expected distribution limitation, not a reason to disable security features or ship unsafe workarounds.
- Do not call the work complete because PyInstaller emitted an `.exe`. The frozen artifact must be exercised through real gameplay, persistence, restart/load, and release-style extraction.

---

# Why the Existing Architecture Is Packaging-Friendly

The current executable entry point is intentionally small:

```python
from app.game.main_loop import main


if __name__ == "__main__":
    main()
```

The Windows build should continue to use that bootstrap rather than creating a second game launcher.

The content system already uses committed deterministic imports rather than runtime filesystem discovery. PyInstaller's normal import analysis should therefore be sufficient unless a specific frozen-build failure proves otherwise.

After SAVE-ARCH, the client should already have explicit boundaries for:

```text
GameState
    ↓
save-document codec
    ↓
SaveCoordinator
    ├── local profile storage
    ├── optional RemoteProfileClient
    └── CredentialStore port
```

The Windows milestone supplies Windows-specific composition:

```text
DungeonDrifters.exe
    │
    ├── Windows profile/cache root
    ├── Windows CredentialStore
    ├── DD remote API configuration
    └── existing platform-neutral DD client
```

It does not redesign those contracts.

---

# Target Repository Surface

Prefer this layout unless the post-SAVE-ARCH tree establishes a clearly better existing home:

```text
root/
├── packaging/
│   └── windows/
│       ├── DungeonDrifters.spec
│       └── README.md
├── requirements-build-windows.txt
├── src/
│   └── ...
├── tests/
│   ├── ...
│   ├── test_windows_platform.py
│   └── test_windows_release_tools.py
└── tools/
    ├── build_windows.py
    ├── smoke_windows_exe.py
    └── package_windows_release.py

.github/
└── workflows/
    ├── tests.yml
    └── windows-build.yml

docs/
└── exe/
    └── exe-plan.md
```

Do not create `exe-spec.md` merely for symmetry. This plan is sufficient unless implementation discovers a durable Windows client contract that genuinely deserves an independent long-term specification.

---

# Windows Runtime Layout

The distributed ZIP should expand to:

```text
DungeonDrifters/
├── DungeonDrifters.exe
└── _internal/
    └── bundled Python/PyInstaller runtime files
```

The game MUST NOT save into this directory.

Player data should resolve through the sealed SAVE-ARCH storage abstraction into a stable user-owned Windows location, for example:

```text
%LOCALAPPDATA%\DungeonDrifters\
```

The exact sub-layout is owned by SAVE-ARCH/platform composition, but conceptually it may contain:

```text
DungeonDrifters/
├── profiles/
├── conflicts/
├── cache/
└── config/
```

Credentials do not belong there if SAVE-ARCH defines them as secrets.

Authentication credentials live behind the Windows `CredentialStore` adapter.

---

# Windows Credential Boundary

Implement the sealed SAVE-ARCH `CredentialStore` port with Windows Credential Manager / WinCred.

The adapter owns only platform credential persistence.

It must not know:

```text
GameState
combat
inventory
profile payload structure
entitlements
route state
```

It may know the credential/session types required by the sealed account contract.

Use stable DD-owned credential target names. Do not include raw secrets in target names, usernames, log messages, or exception text.

Required behavior:

```text
write credential
read credential
replace credential
delete credential
missing credential
platform API failure
```

Tests must use a fake/injected WinCred boundary rather than reading/writing the developer's real Credential Manager.

A small low-level Windows API wrapper may use `ctypes` against the native WinCred API if that keeps the runtime dependency surface smaller and the code testable. Do not add a third-party credential package merely for convenience without reviewing its packaging/runtime consequences.

---

# Windows Application Data Boundary

Do not derive player-data ownership from:

```text
__file__
sys.executable directory
current working directory
repository path
PyInstaller _MEIPASS
temporary extraction directory
```

Resolve the Windows application-data root through a dedicated platform path provider consumed by SAVE-ARCH composition.

Preferred conceptual contract:

```python
class WindowsPlatformPaths:
    def local_data_root(self) -> Path:
        ...
```

The implementation should use the Windows per-user local application-data facility rather than relying on the release folder.

Tests must be able to inject/fake the resolved known-folder path.

Moving or deleting the extracted release folder must not delete the player's profile/cache data.

---

# Build Dependency Contract

Create:

```text
root/requirements-build-windows.txt
```

Pin the accepted build toolchain:

```text
pyinstaller==6.22.3
pyinstaller-hooks-contrib==2026.7
```

If SAVE-ARCH adds ordinary client runtime dependencies, those continue to live in their normal dependency surface. PyInstaller is a build dependency, not a game runtime dependency.

Do not add PyInstaller imports to production DD source code.

The accepted PyInstaller and hooks versions should remain pinned until intentionally upgraded and requalified.

---

# WINDOWS-0 — Baseline and Packaging Freeze

## Purpose

Establish the exact post-SAVE-ARCH source state and prove that Windows packaging work begins from a known-good game.

## Files

- Update only if needed: `docs/exe/exe-plan.md`
- No production packaging code yet.

## Steps

- [ ] Checkout `master`.
- [ ] Pull/fetch and prove local `master` equals `origin/master`.
- [ ] Record the exact post-SAVE-ARCH `master` SHA in the implementation log/PR description.
- [ ] Confirm SAVE-ARCH is sealed and the active game uses its final `SaveCoordinator`, profile storage, remote sync, and `CredentialStore` boundaries.
- [ ] Confirm no legacy `SaveRepository` or source-tree save ownership remains active.
- [ ] Confirm working tree is clean.
- [ ] From `root/`, run the normal content validator.
- [ ] Run the complete current pytest suite.
- [ ] Run `python -m compileall src tests tools`.
- [ ] Run `git diff --check`.
- [ ] Run one normal source launch with `python src/run_game.py`.
- [ ] Save, quit, restart from source, and load through the sealed SAVE-ARCH path.
- [ ] Record current Python version and architecture (`3.14`, 64-bit).
- [ ] Create the Windows packaging branch from that exact SHA.
- [ ] Commit only if documentation/baseline evidence requires a tracked change.

## Acceptance

Nothing about gameplay, persistence semantics, accounts, or content has changed.

## Suggested commit if needed

```text
WINDOWS-0 - Freeze Windows Packaging Baseline
```

---

# WINDOWS-1 — Windows Platform Composition

## Purpose

Provide the Windows-specific adapters required by the already-sealed SAVE-ARCH contracts before freezing the application.

This gate is NOT allowed to redesign SAVE-ARCH.

## Likely files

Exact names must follow the final SAVE-ARCH package layout, but the responsibilities should map approximately to:

```text
root/src/app/platform/
├── __init__.py
└── windows/
    ├── __init__.py
    ├── paths.py
    └── credentials.py
```

Possible composition-root modification:

```text
root/src/app/game/main_loop.py
```

or the platform composition module introduced by SAVE-ARCH.

Tests:

```text
root/tests/test_windows_platform.py
root/tests/test_windows_credentials.py
```

## Interfaces consumed

Use the final SAVE-ARCH interfaces as implemented.

Conceptually:

```python
CredentialStore
ProfileStore / LocalProfileStore
SaveCoordinator
RemoteProfileClient
```

Do not duplicate them.

## Windows paths

Implement stable per-user application-data resolution.

Requirements:

- [ ] production profile/cache root is outside the EXE/release directory
- [ ] path resolution is independent of current working directory
- [ ] path resolution is independent of source checkout
- [ ] path resolution is independent of PyInstaller internals
- [ ] directories are created only when actually needed
- [ ] tests can inject the platform root
- [ ] the game can run from a folder containing spaces
- [ ] the game can run after the release folder is moved
- [ ] player data remains available after the release folder is replaced

## Windows credentials

Implement the SAVE-ARCH `CredentialStore` contract through Windows Credential Manager.

Requirements:

- [ ] no secrets in save/profile envelopes
- [ ] no secrets in normal files
- [ ] no secrets in command-line arguments
- [ ] no secrets in log/error strings
- [ ] credential replacement works
- [ ] credential deletion works
- [ ] missing credentials are a normal state
- [ ] native API failures become the sealed platform-neutral credential error/result
- [ ] tests never mutate the developer's real credential set

## Offline behavior

With the remote profile service unreachable:

```text
launch
→ valid local profile loads
→ play
→ save locally
→ quit
→ restart
→ local profile loads
```

No Windows adapter may turn an optional remote service into a launch requirement.

## Source-mode behavior

Running:

```powershell
python src\run_game.py
```

on Windows must use the same production Windows platform composition unless a test explicitly injects alternatives.

Do not maintain separate "source save" and "EXE save" systems.

## Gate proof

Run:

```text
focused Windows platform tests
focused SAVE-ARCH tests
full pytest suite
content validator
compileall
git diff --check
```

Then manually source-run the game on Windows and prove save/restart/load.

## Commit

```text
WINDOWS-1 - Add Windows Platform Adapters
```

Stop for review before packaging.

---

# WINDOWS-2 — Reproducible PyInstaller Build

## Purpose

Create the first frozen Windows executable using the smallest packaging configuration that works.

## Files

Create:

```text
root/requirements-build-windows.txt
root/packaging/windows/DungeonDrifters.spec
root/packaging/windows/README.md
root/tools/build_windows.py
root/tests/test_windows_release_tools.py
```

Update `.gitignore` only if current rules do not already cover all generated build output.

The current repository already ignores normal `build/`, `dist/`, ZIP, and temp output; preserve that behavior rather than adding redundant patterns.

## Build mode

Use:

```text
Windows x64
Python 3.14 x64
PyInstaller 6.22.3
onedir
console enabled
entry point: root/src/run_game.py
executable name: DungeonDrifters.exe
```

PyInstaller `onedir` is the default and produces a distribution folder containing the executable and supporting files.

Do NOT use:

```text
--onefile
--windowed
--noconsole
--hide-console
```

DD is a terminal game. The console is the game window.

## Initial discovery build

Before adding custom hooks or data rules, prove the minimal graph.

From repository root:

```powershell
Set-Location root

py -3.14 -m venv .venv-build
.\.venv-build\Scripts\Activate.ps1

python -m pip install --upgrade pip
python -m pip install -r requirements-dev.txt
python -m pip install -r requirements-build-windows.txt

python -m PyInstaller `
    --noconfirm `
    --clean `
    --onedir `
    --console `
    --name DungeonDrifters `
    --paths src `
    src\run_game.py
```

Expected:

```text
root/
├── build/
└── dist/
    └── DungeonDrifters/
        ├── DungeonDrifters.exe
        └── _internal/
```

## Inspect warnings before modifying configuration

Review PyInstaller's warning/import analysis output.

A warning is not automatically a defect.

Only add:

```text
hidden import
hook
data file
binary/DLL
runtime hook
path override
```

when:

1. a real frozen runtime/build failure exists,
2. the missing resource/import is identified,
3. the narrow packaging rule fixes that exact problem,
4. the packaged regression test proves it.

If the executable starts successfully using the generated static content catalog, do not add broad `collect_submodules("app")` behavior.

## Freeze the build in a spec file

After the minimal build works, create/check in:

```text
packaging/windows/DungeonDrifters.spec
```

The spec becomes the canonical frozen-build configuration.

It must declare:

```text
entry point
src import path
executable name
console=True
onedir collection
only proven data/import/binary additions
```

Do not generate the spec dynamically on every CI run.

## Build wrapper

`tools/build_windows.py` should:

```text
verify running on Windows
verify 64-bit Python
verify supported Python major/minor
clean only DD-owned packaging output
invoke PyInstaller with the tracked spec
fail on non-zero build
verify expected EXE exists
print final artifact path
```

It must not:

```text
git clean -fdx
delete arbitrary user files
modify source
install dependencies itself
silently download tools
```

Dependency installation belongs outside the build script.

## Reproducibility metadata

The build script should emit a small build manifest into the distribution or release staging area containing non-secret metadata:

```text
source commit SHA
Python version
PyInstaller version
build architecture
build timestamp
```

Do not include:

```text
user home directory
tokens
credentials
backend secrets
absolute developer paths
```

If embedding the Git SHA requires git at build time, CI/local release builds may provide it explicitly through an environment variable. The executable must not require git at runtime.

## Gate proof

Run a clean build twice from the same source/configuration.

The requirement is deterministic **contents/behavior/configuration**, not necessarily byte-for-byte identical PE binaries or timestamps unless the toolchain naturally provides that.

Prove:

```text
expected executable exists
expected _internal directory exists
no repository source path is required at runtime
no venv path is required at runtime
content imports succeed
application reaches first interactive screen
```

## Commit

```text
WINDOWS-2 - Add Reproducible Windows Build
```

Stop for review.

---

# WINDOWS-3 — Frozen Executable Smoke and Runtime Acceptance

## Purpose

Prove the frozen artifact is an actual playable DD client, not merely a successful PyInstaller command.

## Files

Create:

```text
root/tools/smoke_windows_exe.py
```

Add tests for the smoke harness itself if it contains parsing/process-control logic.

Do not write a fake game for the smoke test.

## Automated frozen smoke

Launch:

```text
dist/DungeonDrifters/DungeonDrifters.exe
```

through a subprocess with:

```text
fresh temporary local-data root
memory/fake-safe credential state where supported
backend intentionally unavailable unless the test explicitly uses it
scripted stdin
captured stdout/stderr
bounded timeout
```

Use the real packaged executable.

A minimal interaction should prove:

```text
launch
title screen
continue
Drifter selection
select Branoc
confirm
reach overworld
open Options
quit
confirm quit
process exits 0
```

The expected current terminal key sequence is approximately:

```text
Enter
1
Y
O
Q
Y
```

The implementation must verify the actual accepted UI sequence from the post-SAVE-ARCH build rather than blindly hard-coding stale assumptions.

## Smoke assertions

Require:

```text
exit code == 0
title/selection evidence observed
Branoc selection evidence observed
overworld evidence observed
no Python traceback
no missing-module error
no missing-DLL error
no repository-path lookup failure
```

Do not make the smoke test depend on terminal timing sleeps when process I/O synchronization can be explicit.

## Release-style isolation test

Create a temporary directory with spaces:

```text
C:\...\Dungeon Drifters Release Test\
```

Copy only the built `DungeonDrifters/` distribution into it.

The source repository and venv are not part of the copied tree.

Launch there.

This proves the artifact is not accidentally reading from:

```text
repo
current working directory
developer src tree
venv
```

## Local profile test

Using isolated Windows local-data state:

```text
launch EXE
create/start profile
play enough to mutate persistent state
save
quit
relaunch EXE
load
verify state survived
```

If SAVE-ARCH supports local-only guest profiles, perform this proof with the DD backend unavailable.

## Release-folder replacement test

After producing a valid local save/profile:

```text
quit game
delete/move old release folder
copy in a fresh build folder
launch fresh EXE
load same local profile
```

The profile must survive because its ownership is outside the release directory.

## Credential integration test

Where cloud/account support is available after SAVE-ARCH:

```text
authenticate/establish session
credential persists through Windows CredentialStore
quit
restart
session recovery uses CredentialStore contract
profile/save files contain no raw token
```

Do not require live production infrastructure for automated CI.

Use a controlled local/test backend for integration proof.

## Manual game acceptance

From the actual EXE, verify manually:

```text
all four Drifters can be selected
terminal clears correctly
Unicode borders render acceptably
ASCII fallback still works where applicable
terminal width detection behaves
combat input works
multi-enemy combat renders
Save works
Load works
Quit works
restart/load works
offline local play works
```

Then complete one full current campaign from the frozen executable through the current playable endpoint.

The manual run is not a replacement for pytest. It proves the frozen runtime environment.

## Commit

```text
WINDOWS-3 - Prove Frozen Runtime Behavior
```

Stop for review.

---

# WINDOWS-4 — Automated Windows CI Artifact

## Purpose

Make the Windows executable reproducible by GitHub Actions from an exact source SHA.

## Files

Create:

```text
.github/workflows/windows-build.yml
```

Do not overload the existing Linux/client test workflow unless there is a concrete reason to merge them.

## Runner

Use:

```text
windows-latest
Python 3.14 x64
```

The workflow builds Windows on Windows because PyInstaller is not a cross-compiler.

## Trigger policy

At minimum:

```text
workflow_dispatch
pull_request targeting master when Windows packaging files change
push to the Windows packaging branch / master as appropriate
```

Do not automatically publish a GitHub Release from every push.

## Job stages

The Windows job must:

1. checkout the exact SHA
2. setup Python 3.14
3. install normal development/client dependencies
4. install `requirements-build-windows.txt`
5. run content validation
6. run relevant Windows/SAVE-ARCH tests
7. run the full client pytest suite
8. run compileall
9. run `tools/build_windows.py`
10. run `tools/smoke_windows_exe.py` against the frozen EXE
11. stage the release folder
12. produce the ZIP
13. upload the ZIP as a workflow artifact

## Exact-SHA evidence

The build manifest and workflow summary must make it possible to answer:

```text
Which commit produced this EXE?
Which Python version produced it?
Which PyInstaller version produced it?
Did the frozen smoke run against that same build?
```

No manual "I think this was the right commit" release process.

## CI backend behavior

The default packaging smoke must not require production DD backend availability.

If remote-sync integration is included, start an isolated test profile service/database using the same SAVE-ARCH integration approach already accepted in CI.

Never put production credentials into the build.

## Artifact

The uploaded Actions artifact should be named clearly:

```text
DungeonDrifters-Windows-x64
```

and contain the release ZIP:

```text
DungeonDrifters-Windows-x64.zip
```

Avoid baking a stale hard-coded game version into the workflow filename. GitHub Release/tag metadata can provide the release version when publishing.

## Commit

```text
WINDOWS-4 - Build Windows Artifact in CI
```

Stop for review.

---

# WINDOWS-5 — Release ZIP and Player-Facing Distribution

## Purpose

Turn the validated build directory into the exact artifact a player receives.

## Files

Create:

```text
root/tools/package_windows_release.py
```

Optional tracked release text:

```text
root/packaging/windows/PLAYER_README.txt
```

Modify:

```text
README.md
```

only after the frozen artifact is accepted.

## ZIP contract

Input:

```text
root/dist/DungeonDrifters/
```

Output:

```text
DungeonDrifters-Windows-x64.zip
```

ZIP root:

```text
DungeonDrifters/
├── DungeonDrifters.exe
└── _internal/
```

Do not produce:

```text
ZIP
└── dist/
    └── DungeonDrifters/
```

The player should get one obvious folder.

## Packaging tool behavior

`package_windows_release.py` should:

```text
verify expected EXE exists
verify expected onedir structure
reject source files accidentally staged outside expected bundle structure
optionally include PLAYER_README.txt
create fresh ZIP
print SHA-256 checksum of ZIP
fail if output already exists unless explicit --force is supplied
```

It must not modify the built executable or source tree.

## Player README

Keep it short:

```text
Dungeon Drifters — Windows

1. Extract the entire DungeonDrifters folder.
2. Open the folder.
3. Run DungeonDrifters.exe.

Python is not required.

Dungeon Drifters stores player data separately from the extracted release folder.
Do not move individual files out of the DungeonDrifters folder.

This build is not code-signed, so Windows may display a reputation/SmartScreen warning.
```

Do not tell users to disable SmartScreen globally or weaken Windows security.

## Main README

Add a player-first Windows section before source-development instructions.

Conceptual structure:

```text
## Play Dungeon Drifters

### Windows build
Download the latest Windows x64 release asset.
Extract it.
Run DungeonDrifters.exe.
No Python installation is required.

### Run from source
existing developer/source instructions
```

Do not delete source-run instructions; they remain useful for contributors/developers.

## Release-source proof

Before publishing, download the exact Actions artifact generated from the accepted SHA and perform the release-style manual test against that downloaded artifact.

Do not substitute a different local build for the release candidate.

## Commit

```text
WINDOWS-5 - Add Windows Release Packaging
```

Stop for review.

---

# WINDOWS-6 — Seal the First Windows Distribution

## Purpose

Perform the complete acceptance cycle and establish the first downloadable Windows DD client as a reproducible project artifact.

## Automated acceptance

From `root/`:

```text
python -m tools.validate_content
python -m pytest
python -m compileall src tests tools
```

Repository:

```text
git diff --check
clean working tree
local branch == origin branch
```

Windows:

```text
clean build
frozen smoke
release ZIP creation
ZIP checksum
```

SAVE-ARCH regression:

```text
offline local profile
save
quit
restart
load

account/cloud path where test infrastructure supports it
credential persistence boundary
no credential leakage
revision/sync tests remain green
```

## Manual acceptance matrix

Perform against the exact CI artifact:

```text
Windows 11
x64
normal non-admin user
folder path with spaces
launch by double-click
launch from PowerShell
network available
network unavailable
fresh local data
existing local profile
release folder replaced
```

Verify:

```text
console appears
title renders
Drifter selection works
all four Drifters selectable
overworld renders
combat works
save works
load works
restart works
offline works
no source checkout required
no Python required
no venv required
no backend process bundled locally
no traceback
no missing DLL/module
profile data outside release folder
credentials outside profile data
```

Complete one full current campaign through the current gameplay endpoint using the release artifact.

## Cumulative review

Review all Windows commits from the exact WINDOWS-0 base.

Reject scope drift involving:

```text
combat changes
balance changes
content changes
route changes
save schema redesign
account redesign
sync redesign
entitlement redesign
unrelated refactor
```

Packaging-specific fixes are acceptable only when tied to reproduced Windows/frozen behavior.

## CI

Require exact-SHA green evidence for:

```text
existing repository tests
Windows build workflow
frozen smoke
release artifact upload
```

## Release

Create the GitHub Release manually after acceptance.

Attach:

```text
DungeonDrifters-Windows-x64.zip
```

Optionally publish the SHA-256 checksum in release notes.

Do not publish:

```text
build directory
spec cache
venv
raw source ZIP as the Windows player artifact
credentials
test database
internal logs containing machine paths/secrets
```

## Commit

```text
WINDOWS-6 - Seal Windows Executable Distribution
```

**Disposition when accepted:**

```text
WINDOWS EXECUTABLE: SEALED
READY FOR GITHUB RELEASE
```

---

# Explicitly Deferred

These are not WINDOWS-1 through WINDOWS-6 work:

```text
PyInstaller onefile
Windows installer
MSIX
Microsoft Store
code signing certificate
SmartScreen reputation program
auto updater
launcher
patcher
GUI conversion
graphical frontend
browser/WebAssembly build
Linux bundle
macOS bundle
Android/iOS package
PlayStation package
Steam SDK
Epic SDK
Discord integration
crash telemetry platform
automatic production backend deployment
```

Any of these may receive their own plan later.

---

# Reviewer Stop Conditions

Stop and review immediately if implementation does any of the following:

```text
stores profiles beside DungeonDrifters.exe
stores profiles under PyInstaller temporary/runtime paths
stores auth tokens in profile JSON
stores auth tokens in normal config files
bundles FastAPI/PostgreSQL backend with the game client
requires backend availability to open a valid offline profile
adds a Windows-only save schema
reintroduces legacy SaveRepository ownership
scans content directories at runtime
collects the entire repository into the bundle
adds broad hidden imports without reproduced need
uses --windowed or removes the console
switches to onefile during this milestone
changes gameplay to solve packaging
changes save/account architecture instead of consuming SAVE-ARCH
requires administrator privileges for ordinary play
requires Python to be installed on the player's computer
requires the source checkout beside the EXE
automatically publishes releases before artifact acceptance
tells players to disable Windows security protections
```

These are packaging/architecture failures, not cleanup items.

---

# Expected Commit Chain

```text
WINDOWS-0 - Freeze Windows Packaging Baseline       (only if a tracked baseline change is needed)
WINDOWS-1 - Add Windows Platform Adapters
WINDOWS-2 - Add Reproducible Windows Build
WINDOWS-3 - Prove Frozen Runtime Behavior
WINDOWS-4 - Build Windows Artifact in CI
WINDOWS-5 - Add Windows Release Packaging
WINDOWS-6 - Seal Windows Executable Distribution
```

Corrective review commits may use the established suffix convention:

```text
WINDOWS-2A
WINDOWS-3A
WINDOWS-4A
```

Do not advance simply because PyInstaller builds successfully. Every gate must prove its own behavioral contract.

---

# Definition of Done

The Windows executable milestone is complete only when all of the following are true:

```text
A player can download one Windows x64 ZIP.

The player can extract it and double-click DungeonDrifters.exe.

The player does not need Python, pip, a venv, Git, or the repository.

DD remains a console application and its terminal UI works normally.

The packaged client uses the sealed SAVE-ARCH persistence system.

Player profiles live outside the release folder.

Replacing the release folder does not destroy player progression.

Offline play works with a valid local profile.

Cloud/account support uses the same SAVE-ARCH contracts as source execution.

Persistent Windows credentials use the Windows CredentialStore adapter.

Raw authentication secrets never enter save/profile files.

The DD backend is not bundled or launched locally with the client.

The deterministic content catalog works without runtime filesystem scanning.

A clean Windows machine/build runner can reproduce the artifact from the exact source SHA.

The frozen EXE passes automated smoke.

The exact CI artifact passes manual play/save/restart/load acceptance.

One full current campaign has been completed from the frozen release artifact.

The normal DD regression suite remains green.

The release ZIP is ready to attach directly to a GitHub Release.
```
