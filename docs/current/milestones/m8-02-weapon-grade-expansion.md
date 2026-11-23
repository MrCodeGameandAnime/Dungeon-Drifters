# M8.2: Signature Weapon Grade Expansion

**Status:** Proposed work package. The 48 component recipe identities and grade/unlock relationships are approved under D1. Recipe effects, material costs and other package-level balance values remain open. No implementation is authorized.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Audit source baseline:** `29bab31cbfd3c24a0f6420a326bd5fd8b0e5d2dc`. Revalidate sources and current HEAD at package entry.

## Goal

Add the finite Grade-II, Grade-III, and Grade-IV recipes for the existing signature-weapon component families while preserving M3/M6.5 crafting and inventory contracts.

## Approval Boundary

**Already-approved inputs:** preserve M3's current weapon Crafting eligibility/progression and M6.5's shared component stacks, quantity commerce, and displaced-component recovery.

**Already approved:** all 48 recipe identities and their Grade II/III/IV unlock relationships in the parent manifest. **Package review remains:** authored effects and material costs; approval of IDs does not preapprove those numerical values.

## Scope

- 48 approved recipe identities: 16 existing Grade-I component identities x three new grades. Stable IDs follow `m8_<existing_component_id>_grade_ii`, `_grade_iii`, and `_grade_iv`, as enumerated by the parent manifest.
- Unlock each grade only after its matching floor clear: II after Floor II, III after Floor III, IV after Floor IV.
- Use existing component effects, exact Drifter targeting, slot compatibility, craft-and-install behavior, crafting materials, party Crafting XP, and M6.5 shared component stacks/replacement recovery.
- Keep components buyable/sellable through the Blacksmith under the M6.5 contract; do not add lifetime craft limits or independently owned installed parts.

## Exclusions And Open Content Values

No signature identity changes, new crafting progression, new component family, or Floor-IV clear implementation. Recipe material costs/effects remain package-level values for M8.2 Gate A approval. Grade-IV recipes may be implemented behind the M8.1 clear signal and tested with controlled states, but cannot be treated as available to players before M8.3 produces a genuine Floor-IV clear.

## Ownership And Handoff

| Concern | Existing owner to revalidate | Contract produced |
| --- | --- | --- |
| Craft eligibility and install | `root/src/app/game/weapon_progression.py` | Existing exact-target, slot, cost, installation and Crafting-XP semantics remain canonical. |
| Recipe definitions/catalog | `root/src/app/content/weapon_progression_spec.py`, generated catalog/content validation | Exactly 48 new stable recipes; no invented API or schema is preselected. |
| Shared component stacks and commerce | M6.5 vendor/component inventory owner in `root/src/app/game/` | Purchased/recovered unit is consumed on install; displaced component returns atomically. |
| Tier unlock evidence | M8.1 clear owner; M8.3 Floor-IV completion | Availability derives from authoritative clear state, not client state or a parallel recipe-purchase flag. |

**Persistence impact:** no per-character recipe-purchase state is proposed; availability derives from canonical floor clear evidence. Revalidate at entry. Any unavoidable new persistent state needs a reviewed migration plan.

## Tests, Package Gates, And Qualification History

Parameterize definition coverage across all 48 IDs. Test each grade locked before its clear and available after, migrated old saves, exact Drifter and slot validation, already-installed component handling, insufficient materials, stack consumption/recovery, failed-save rollback, buy/sell quantities, and representative combat-stat projection in terminal/browser clients.

- **Gate A, plan approval:** Open; approve the package implementation plan and authored recipe effects/material costs within the fixed 48 identities and unlock relationships. Do not reopen D1.
- **Gate B, implementation and focused tests:** Not started; red/green recipe, ownership, transaction and projection tests.
- **Gate C, exact-SHA qualification and closure:** Not run; root/web, content, compile/build, browser, PostgreSQL/migration parity, and pinned MicroPython because shared catalog/runtime compatibility is in scope.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Not implemented | Not run | Not run | Pending | Open |

Record review, hosted CI URL, full SHA and closure result before calling M8.2 complete.

