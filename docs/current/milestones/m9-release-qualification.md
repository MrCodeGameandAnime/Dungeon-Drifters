# M9 Integrated Economy And Release Qualification Implementation Plan

> Implementation method: use `superpowers:executing-plans` for native gate-by-gate execution. No payment product, live-service system, or new distribution target is authorized by this planning document.

**Status:** Draft for review, 2026-10-29. Final release/content decisions and current repository evidence must be revalidated at entry.

**Goal:** Tune and qualify the accepted finite gameplay release, give every included future-design requirement an explicit disposition, and preserve a defensible exact-revision closure record.

**Architecture:** Tune approved authored policies through existing owners; add only separately approved missing release behavior. Qualify the integrated Python-authoritative game, clients, persistent source state, profile service and real pinned runtime. Do not redesign sealed architecture to satisfy a benchmark or payment integration.

**Tech stack:** The accepted M1-M8 runtime/content/client/service stack, current pytest/Playwright/content/migration tooling, deterministic balance probes, real PostgreSQL and pinned MicroPython qualification.

## Authority, Scope, And Entry

- [Roadmap](../development-roadmap.md), M9, W1 and shared implementation/qualification contract.
- [Party design](../../future/party-and-expedition-core-loop.md), rotation/specialization/full-party pressure.
- [Economy](../../future/dungeon-progression-difficulty-and-economy.md), free access, soft walls, monetization, optional endgame/services and preparation risk.
- [Character growth](../../future/character-growth-and-stat-scaling.md), provisional curves and earned power fantasy.
- [Enemy design](../../future/enemy-archetypes-scaling-and-capability-progression.md), authored capabilities and selected content; [Armor](../../future/armor.md), early-piece viability.
- [Momentum](../../future/momentum.md), only if accepted into release; [website report](../../future/website-profile-report.md), historical W1 measurement, not current performance proof.
- The accepted implementation/evidence records for [M1](m1-permanent-roster.md), [M2](m2-preparation-trading-escape.md), [M3](m3-character-advancement.md), [M4](m4-enemy-progression.md), [M5](m5-armor-accessories.md), [M6](m6-expeditions.md), [M7](m7-momentum.md) if selected, and [M8](m8-region-content-loop.md).

Entry means the agreed gameplay loops are already playable, not just unit-test green or planned. Resolve M8's finite manifest and remaining category consumers before measuring a release. M4A/M4B and Floor III boss evidence must be distinct; M6 Floor IV unlock cannot precede them.

`docs/future/longterm.md` and all `docs/future/exe/` work are excluded. This milestone does not promise console certification, mobile app packaging, an executable, an unbounded campaign, multiplayer/PvP, or every illustrative seasonal/cosmetic/payment system. Exclusion from this release is not a claim that those features were implemented.

## Historical Baseline Versus New Evidence

The Hub reference at `8099b895` recorded 1,809 root Python tests, 60 web tests, 31 PostgreSQL tests, full browser smoke, migrations and pinned runtime evidence in [probe record](../../probe.md). These are historical facts to preserve, not counts to copy into M9. Future test totals, binary identity, heap frontier, startup timing and current SHA must be actually observed again.

The September [website report](../../future/website-profile-report.md) measured a different revision and lists proposals, not guaranteed current budgets. W1 remains an independent delivery lane. M9 checks accepted release-facing website behavior and W1 evidence where scheduled; it must not silently absorb all W1 optimization work or treat new telemetry/accessibility policy as already approved.

## Canonical Balance And Release Contract

Tune with real, reproducible runs and editable authored values. Record seeds, starting builds/party, carried supplies, progression/equipment state, player actions, outcome, rewards, costs and duration. Existing `root/tools/balance_probe.py` is a possible reuse point; revalidate what it simulates and do not equate a single-move simulation with a campaign/economy playtest.

Cover rotation, favored-pair focus, underleveled catch-up, all-six-pair legality, story-required pairings, full-party boss readiness, early-floor replay farming, partial extraction, death and alternate emergency exits. Evaluate level/GP opportunity costs, passive/move choices, Crafting speed, grade scarcity, material drops, gold sinks, sell versus dismantle, Alchemy, supply capacity, armor investment and expedition efficiency together. A faster Crafting curve is a tunable issue, not a reason to change component ownership or let Floor I yield Grade II.

Preserve dungeon entry without energy/payment, viable free story progression, meaningful soft power walls, and earned extreme late-game returns. Do not add a hard level gate to fix overtuned content or flatten late-game power just to equalize all matchups. Recommended levels remain advice unless a separate authored story/unlock gate applies.

Source prototype curves are provisional but not silently replaceable. Any changed curve/reward/cap requires an explicit reviewed numerical diff, scenario evidence and regression expectation. If no tuning change is needed, M9 may close that area with evidence rather than forcing code churn.

## Requirement And Optional-Work Ledger

At Gate 0 create the actual release ledger from every section of the included owning documents. Each row needs a requirement/source anchor, mandatory versus illustrative status, milestone/gate owner, content IDs/consumer, current observed implementation, tests/playthrough evidence, and disposition. Allowed closure dispositions are implemented with evidence, deferred by explicit approval to a named scope, or rejected by explicit decision. "Helper exists," "category enum exists," and "CI green" do not by themselves prove a gameplay requirement.

The following map establishes minimum ownership; it is not a substitute for the final row-by-row audit:

| Source requirement group | Delivery owner and required proof |
| --- | --- |
| Permanent four-person roster, Hub selection/inspection and six pairs | M1 identity/migration; M4B actual D4/full-party proof; M6 all-six live split |
| Dungeon knowledge, free/required/locked pair restrictions | M8 selection/reveal/content journeys |
| Gameplay-event expeditions, reports, reunion, categories and pair effects | M6 engine/Training/Material/Equipment/Recovery; M8 Scouting/Story/Elite and actual consumers |
| Reduced expedition XP, rotation and specialization pressure | M3/M6 accounting; M9 observed catch-up/rotation scenarios |
| Major boss convergence and post-boss story/region changes | First Floor III boss in M4B; later approved reunion/region loop in M8 |
| Secured/unsecured rewards, death, normal/Rest/smoke/talisman outcomes | Existing Floor I baseline plus M2/M8 exit policy and no-rewind proofs |
| Trader, gold, carrying, potions, Alchemy and preparation | M2 real purchase/use/return loop; M9 tune with independent weapon Crafting preserved |
| Soft walls, numerical/behavioral/enemy/environmental pressure | M4 selected mechanics; M8 content; M9 real-run counterplay evidence |
| Stats, levels, GP, resource/output curves and hard permanent caps | Preserve existing baseline; M3 remaining consumers/purchases/respec; M9 approved numerical tuning only |
| Independent damage components and Intuition potency/XP/discovery/Super | M3 real combat/security consumers, M4/M8 real search/reward use, M7 limited interaction if selected |
| Permanent resource discoveries and optional awards | M3 claim contract; M8 actual locations; M9 no repeat grants or required optional altar for survival |
| Weapons and Grade I-IV progression | Sealed generic system; M4/M6/M8 floor sources/components/recipes; no replacement signatures or repeated component stacks |
| Armor/accessories, early-piece viability, swap/upgrade/sell/dismantle | M5 ownership/ceiling/provenance; M8 actual release rewards; M9 investment comparisons |
| Momentum | M7 if approved; otherwise explicit release-scope disposition, not accidental activation |
| Enemy/media assets and selected formations/phases | M4 mechanics/M8 manifest and real presentation proof; no automatic graphical-engine scope |
| Website speed/size/SEO/appearance | W1 independently approved before/after work; M9 release web parity and accurate links/metadata where delivered |
| Optional commercial/live-service/equipment extensions below | Explicit approved implemented/deferred/rejected entries, never silently counted complete |

### Commercial And Optional Decisions

These remain visible because the owning sources mention them. Do not automatically implement or silently discard them:

- Energy refills/capacity upgrades, extra expedition options, reward bonuses, convenience bundles and passes.
- Cosmetics, skins, visual effects, Hub/camp decorations and account cosmetics.
- Daily/login rewards, achievements, story/dungeon/boss/level milestone refills, limited free refills and earned capacity upgrades.
- Rotating/seasonal challenges, prestige, score-based runs, restricted-party challenges, endless modes and optional endgame dungeons.
- Equipment degradation/durability, persistent injuries/treatment, set bonuses, special accessory progression and cosmetic/transmog systems.

An implemented real-money offer requires a separately approved concrete product/provider/platform scope: service-owned account entitlements, verified purchase receipts, idempotent grants, interrupted purchase recovery, refund/revocation behavior, security/privacy review, and offline/free-play policy. Never trust browser flags or store restricted currency/receipt credentials in game progression. Reuse DD-owned account/profile boundaries; Firebase/provider selection and platform certification are separate decisions, not reasons to replace the save architecture.

Daily/refill/achievement grants require stable claim identities and once-only evidence. Paid and earned sources remain distinguishable. A purchase being disabled cannot make dungeon entry, essential mechanics, a Drifter, ordinary recovery, basic materials, or story completion unavailable. If no commercial work is selected, no payment code/dependencies are required for this release.

## State, Persistence, Content, And Client Implications

Tuning normally changes authored definitions rather than adding player state. Revalidate how changed definitions affect existing derived stats, prerequisites and item values; a tuned starting distribution must not silently rewrite a developed Drifter. If an approved feature adds persistent state, specify migration and owner at that feature gate and obtain scope approval; do not sneak it into qualification.

Use disposable profiles/databases for destructive fixtures. Retain immutable historical revisions/digests, atomic local saves, explicit conflicts, local-first/offline operation, and no credentials/provider data in progression. Run updated legacy-to-current migrations and real current-profile advancement, not only schema shape tests.

Terminal and built browser must present equivalent actual rewards, costs, progression, party/instance identity and legal choices. Test full reload/new-runtime storage, not only a JavaScript view refresh. Include actual phone portrait/landscape and desktop checks with recorded viewports/device details. Ordinary site Home/Play navigation, Start/fullscreen fallback, music gesture behavior and save/load remain intact; website delivery cannot replace the homepage with Play.

## Review Focus

- A helper/category placeholder must not be counted as delivered gameplay; Gates 0/5 require source-to-consumer evidence.
- A prior/near-final SHA's green run must not certify later runtime changes; Gates 3/4/5 pin exact tree and workflow evidence.
- Mocked storage/runtime/parser tests must not stand in for real reload, PostgreSQL or pinned-interpreter execution; Gates 3/4 run the real boundaries.
- Tuning must not silently change free entry, grade locks or extraction/ownership policy; Gate 1 reviews actual numerical and behavioral diffs.
- Optional payment/injury systems must not become mandatory or client-authoritative by implication; Gate 2 requires explicit scope/security approval and proofs.

## Gates And Tests

### Gate 0 - Freeze Release Scope And Evidence Matrix

- [ ] Verify accepted milestone records and the final finite manifest; re-read every included source section and assign all requirements to the ledger.
- [ ] Resolve M9-D1 through D4. List unimplemented mandatory behavior separately from selected optional work; unresolved mandatory rows block closure, not just an audit sentence.
- [ ] Pin release runtime/tool versions, target clients/devices, disposable test databases, seeds/builds and candidate commit/tree for measurements. No fake future test-count target.

Proof: complete traceability and explicit approved optional dispositions; no excluded `longterm.md`/`exe/` work leaks into requirements.

### Gate 1 - Integrated Playthrough And Balance Pass

- [ ] Run representative new-game/legacy-save routes through D1 -> D2 -> D3 -> D4 -> Floor III boss -> Floor IV expeditions -> approved region conclusion. Include favored pair, rotation/catch-up, prepared/underprepared runs, legal failure/return and high-investment early-floor return.
- [ ] Record progression, consumption, reward and cost data. Make only reviewed numerical changes; add/update deterministic tests around changed caps, rounding, probabilities and failure cases, without duplicating whole route tests per tuning value.
- [ ] Repeat the affected scenarios on the tuned content. Keep grade locks, no-payment gameplay, loot/weapon ownership, participant rewards and early-armor ceiling intact.

Proof: reviewed before/after scenario evidence, not a claim that one seed proves universal balance. Zero tuning edits is acceptable if the evidence supports the existing values.

### Gate 2 - Approved Extension Dispositions And Security

- [ ] For every optional row, record actual approval to implement, defer or reject. For an implemented extension, attach a separate bounded implementation/acceptance plan; do not invent unspecified products or all seasonal modes here.
- [ ] If commercial work is selected, test verified receipts/grants, replay, rejection, interruption, revocation/refund and free/offline behavior on the approved platform/provider. Payment state remains service-owned.
- [ ] If a gameplay extension such as durability/injury is selected, test its resource/recovery/save effects and explicitly review any change to Hub full HP/mana; no source example silently overrides sealed recovery.

Proof: no unowned optional promise; actual implemented extensions have real consumer/security evidence, not a simulated entitlement flag.

### Gate 3 - Final Client, Service, Migration, And Content Qualification

- [ ] Run all shared root/web/content/compile/build checks and real built-browser smoke on the release candidate. Verify all manifest references/required assets, exact-target state, illegal-action atomicity and bounded terminal/browser journeys.
- [ ] Run real PostgreSQL client/service/concurrency tests plus migration-from-zero and Alembic drift checks. Exercise historical save migrations, immutable profile history, save/sync recovery, and current schema advancement with actual service validation.
- [ ] Check desktop and phone screenshots/flows, console errors, offline/local save behavior, full reload persistence and W1-delivered navigation/SEO/performance changes if scheduled. Do not quote September timings as new measurements.

Proof: exact observed totals and environment/log references, no still-running required checks, no reused result disguised as a rerun. Fix failures before proceeding.

### Gate 4 - Real Pinned Runtime And Pressure Frontier

- [ ] Verify the actual executable size/hash against `docs/probe.md`; run native/overlay CPython, default MicroPython, semantic parity and the final real probe including new release state/loop transitions and teardown.
- [ ] Confirm the passing pressure point three times and measure the lower frontier three times. The present 608K/576K harness assumptions must be revalidated, not imposed as a product-device ceiling.
- [ ] On MemoryError, capture the heap map first in the handler before formatted logging/GC where supported; retain failure stage and raw evidence. If harness expectations change, review and rerun the final tree rather than claiming a larger stock binary passed the pinned contract.

Proof: actual pinned-interpreter outputs for the final gameplay/probe tree and honest historical-versus-current memory evidence. Unit tests of the output parser are not runtime qualification.

### Gate 5 - Final Review And Exact-SHA Seal

- [ ] Review cumulative changes for unintended architecture/ownership changes, duplicated derived state, stale docs, test overgrowth, source behavior conflicts and unsupported claims. Run `git diff --check` and all manifest drift checks.
- [ ] Record release candidate SHA, commands, test totals, migrations, browser/device proof, content manifest, runtime identity/parity/frontier, unresolved/deferred ledger, CI run URLs and remaining known risks.
- [ ] Obtain review and commit/push authorization separately. Require green applicable hosted workflows for the exact published implementation SHA. If gameplay/probe code changes afterward, repeat affected qualification; distinguish doc-only closure notes.

Closure: the accepted finite game scope is genuinely playable and qualified, every included source requirement has an evidenced/approved disposition, free gameplay remains viable, and no known required check is open. A green ordinary CI run alone is not the seal.

## Unresolved Product Decisions

| ID | Decision and blocking gate |
| --- | --- |
| M9-D1 | Final release manifest, target platforms/devices and accepted balance/playthrough criteria; Gate 0 |
| M9-D2 | Each optional commercial/endgame/equipment/live-service item: implement, explicitly defer, or reject; before Gate 2 closure |
| M9-D3 | Concrete paid offers/provider/platform, entitlement/refund/offline rules if any; before any commercial implementation |
| M9-D4 | Whether W1 ships with this release; performance budgets, Play indexing, icon semantics and telemetry require their own approvals, not an assumption from the historical report |

Later low-level APIs and exact budgets are revalidated at entry; fixed free-play, security, recruitment and ownership boundaries are not negotiable defaults for the implementer.
