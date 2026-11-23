# M8.2: Signature Weapon Grade Expansion

**Status:** Gate A approved with adjustments. Gate B implementation is in progress; focused tests are being qualified locally. Exact-SHA hosted qualification and Gate C remain pending.
**Parent authority:** [M8 master plan and finite manifest](m8-region-content-loop.md)
**Planning baseline:** `dungeon` HEAD `141513ff8946e4992e2f99472e27f79151150362`, runtime/disk schema 26.
**Sealed dependency:** M8.1 implementation `9ef0e6fd05da8a57602372d8b431c1a27b3bb36a`; exact-SHA CI run [45195824408](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45195824408) passed. Qualification record `141513ff8946e4992e2f99472e27f79151150362` passed CI [45197625564](https://github.com/MrCodeGameandAnime/Dungeon-Drifters/actions/runs/45197625564).

## Goal

Add Grade-II, Grade-III, and Grade-IV components to each of the 16 existing signature-weapon component families. Preserve M3's crafting eligibility, target and Crafting XP rules, M6.5's shared component ownership/commerce, and the sealed M8.1 floor-clear authority.

## Approved Boundary

- Exactly 48 IDs: each approved Grade-I base ID receives `_grade_ii`, `_grade_iii`, and `_grade_iv` variants, prefixed with `m8_` as specified in the parent manifest.
- Grade II unlocks after a genuine Floor-II clear, Grade III after Floor III, and Grade IV after Floor IV. These are availability gates, not recipe purchases or new progression state.
- Preserve exact Drifter/weapon targeting, slot compatibility, material spending, craft-and-install behavior, party Crafting XP, shared component stacks, quantity commerce, displaced-component recovery, and no lifetime craft limit.
- No new component families, weapon identities, moves, mechanics, damage types, save fields, or per-character recipe-purchase records.

## Gate A: Approved Authored Recipe Contract

The proposal uses the current Grade-I component as the reference. Each new component's modifier is an absolute modifier to the unmodified move; it does not stack with an older component in the same slot. Replacing a component continues to return the displaced component to the shared stack.

### Effect Values

| Component effect profile | Grade II | Grade III | Grade IV | Preserved content |
| --- | --- | --- | --- | --- |
| Move-power profile (13 recipes; Grade-I baseline is `power +2`, `accuracy -2`) | `power +3`, `accuracy -2` | `power +4`, `accuracy -2` | `power +5`, `accuracy -2` | Resource cost and authored damage type unchanged. Existing identity and point contribution unchanged. |
| Mana-cost profile, excluding Cinderlung (2 recipes; Grade-I baseline is `resource_cost -1`) | `resource_cost -2` | `resource_cost -3` | `resource_cost -4` | Power, accuracy, damage type, identity and point contribution unchanged. Existing projection clamps final resource cost at zero. |
| Cinderlung Vesper (`sunder_spire_grip_braided`) | `resource_cost -2` | `resource_cost -2`, `power +1` | `resource_cost -2`, `power +2` | Accuracy and damage type unchanged; keeps effective Mana cost at 1. Heavy identity +1 is retained. |

For split-damage moves, the existing deterministic component-power projection continues to distribute a changed total power; M8.2 does not rewrite damage identities, defense classes, scaling attributes, or M7 arithmetic.

`Cinderlung Vesper` costs 3 Mana before component effects. Its authored component deltas keep its effective cost at 1 for all three new grades; Grades III and IV also add the approved power bonuses. The other two cost-profile moves retain the approved flat deltas: `Gloamweight Sepulcher` (8 Mana -> 6/5/4) and `Lightning Palm` (7 Mana -> 5/4/3). No global resource-cost rule changes.

### The 48 Recipe Definitions

The IDs in the last column are exact: prepend `m8_` to the base ID, then append the listed grade suffix. For every row, the material family is the existing slot family; cost is 2 units of that grade's family material at Grade II, 3 at Grade III, and 4 at Grade IV. All three grades retain the existing component-crafting award of 10 Crafting XP.

| Existing Grade-I base ID | Affected move | Slot material family | Identity retained | Effect profile | Grade-II / III / IV ID suffixes |
| --- | --- | --- | --- | --- | --- |
| `needle_focus_fitted` | Scepter Sweep | metal | Refined +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `needle_binding_warded` | Gloamweight Sepulcher | fiber | Refined +1 | Mana cost | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `needle_haft_ashwood` | Mournglass Bloom | timber | Refined +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `needle_seal_faded` | Gravemantle Rupture | cores | Mystic +2 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sky_needle_head_balanced` | Bring the Horse to Water | metal | Refined +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sky_needle_binding_conductive` | Lightning Palm | fiber | Refined +1 | Mana cost | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sky_needle_shaft_flexible` | Tempest Surge | timber | Refined +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sky_needle_focus_stormglass` | Coagulated Torrent | cores | Attuned +2 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sathren_grip_precision` | Mournpoint Verdict | metal | Fast +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sathren_string_taut` | Hollowstring Trine | fiber | Fast +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sathren_limbs_reinforced` | Nightskein Deluge | timber | Fast +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sathren_reservoir_alchemical` | Infused Barb | cores | Attuned +2 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sunder_spire_blade_reinforced` | Crestgrave Reaping | metal | Heavy +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sunder_spire_grip_braided` | Cinderlung Vesper | fiber | Heavy +1 | Mana cost | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sunder_spire_hilt_ashwood` | Ironwake Dismemberment | timber | Heavy +1 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |
| `sunder_spire_crest_faded` | Third Gate Obsequy | cores | Enchanted +2 | Move power | `_grade_ii` / `_grade_iii` / `_grade_iv` |

Examples of the ID/cost rule:

- `needle_focus_fitted` produces `m8_needle_focus_fitted_grade_ii`, `_grade_iii`, `_grade_iv`; costs are 2 `grade_ii_metal`, 3 `grade_iii_metal`, and 4 `grade_iv_metal` respectively.
- `sunder_spire_grip_braided` produces `m8_sunder_spire_grip_braided_grade_ii`, `_grade_iii`, `_grade_iv`; costs are 2 `grade_ii_fiber`, 3 `grade_iii_fiber`, and 4 `grade_iv_fiber` respectively.

The quantity curve follows the existing authored weapon-improvement recipe costs for Grades II-IV (2/3/4 units). The current component craft awards remain 10 XP rather than inheriting the higher slot-improvement awards. This avoids changing Crafting progression as a side effect of adding component grades.

## Implementation Approach

1. Add the 12 variants to each of the four existing weapon progression catalogs. Reuse the present `WeaponComponentSpec` and `ComponentMoveModifierSpec`; preserve the Grade-I entries unchanged.
2. Extend content validation from the current Grade-I-only recipe check to require matching material family and material grade for each variant, exactly one Grade-II/III/IV variant per base, unique stable IDs, valid target moves, and unchanged identity contributions.
3. Derive availability from the sealed `PartyState` clear flags. Enforce it in Python presentation and at every authoritative transaction boundary: craft, purchase, and install. A stale view, forged input, already-owned stack, or stale stocked offer must not bypass a tier gate.
4. M6.5's current component merchandise generation derives offers from the weapon catalog at 20 gold for each non-starting component. Grade-I prices, stock, replenishment, and existing sale/buyback behavior remain unchanged. Grade II-IV offers retain the authored 20-gold price and one-unit cap but have zero initial and automatic replenishment stock; only legitimate player sales may supply them through the existing future-stock queue.
5. Higher-grade offers require both the target wielder's permanent recruitment and the matching existing clear (`floor_two_cleared`, `floor_three_cleared`, or M8.1's `floor_four_cleared`). The existing M8.1 clear is authoritative. Pass Floor IV through vendor stock initialization/replenishment and enforce both conditions for stock eligibility and purchase. No duplicate clear state or save field is added.
6. New component IDs join the existing shared `component_stacks` and catalog-derived save allowlist. No save-shape migration is proposed. Old saves gain no components, clears, or purchases; their existing installed parts and stacks round-trip unchanged.
7. Keep existing terminal/browser semantic inputs and Python projections. Clients display the same recipe availability, cost, effect and lock reason; JavaScript does not calculate grade eligibility or resolve effects.

If source revalidation shows the conjunctive offer extension cannot be made without changing a sealed M6.5 transaction contract or requiring a new save representation, stop at that concrete conflict for review rather than adding parallel progression state.

### Source Ownership Map

| Concern | Current owner | M8.2 change boundary |
| --- | --- | --- |
| Authored components and move modifiers | `root/src/app/content/weapons/*/weapon.py`; `root/src/app/content/weapon_progression_spec.py` | Add only the 48 variants and matching-grade/family validation. Keep Grade-I specs unchanged. |
| Vendor offers and stock eligibility | `root/src/app/content/vendor_catalog.py`; `root/src/app/game/hub_economy_state.py` | Catalog already derives component merchandise from weapon specs; extend existing floor/recruit eligibility composition for the new tier gates without changing prices, stock lifecycle, or transaction sequence rules. |
| Craft and install transactions | `root/src/app/game/weapon_progression.py`; `root/src/app/game/hub_vendor.py`; `root/src/app/game/overworld_session.py` | Add authoritative grade-clear checks; preserve candidate-state atomic commit, material spend, Crafting XP, stack consumption, and displaced-part recovery. |
| Save validation | `root/src/app/persistence/save_document.py` | The allowed component-ID set is catalog-derived. Additions require no schema field; test new IDs and unchanged schema-26 save round-trips. |
| Stat projection and presentation | `project_component_move_effects()` in `weapon_progression_spec.py`; `root/src/app/presentation/overworld_presenter.py`; terminal and browser bridge | Reuse Python projection and semantic actions; no client-side effect or unlock calculation. |

## Focused Test Requirements

- **Catalog completeness:** parameterize all 48 IDs and verify exact base/grade pairing, slot family, grade-matched material, 2/3/4 material quantity, 10 XP award, effect values, identity/points, and no duplicate or missing recipe. Confirm Grade-I catalog entries and commerce remain behaviorally unchanged.
- **Unlock boundary:** for every recipe grade, verify locked before its matching clear and available after; Grade III does not unlock on Floor II, Grade IV does not unlock on Floor III, and unrelated clears do not unlock it. Test migration/default saves as all three future tiers unavailable unless the genuine corresponding clear exists.
- **No bypass:** rejected craft, purchase, and install submissions for a locked grade leave gold, materials, stock, component stacks, installed parts, Crafting XP, and transaction sequence unchanged. Include forged/stale semantic inputs and already-owned component stacks.
- **Craft/install ownership:** exact target Drifter, correct weapon/slot, wrong-weapon rejection, same-installed rejection, material insufficiency, one-time spend, 10 Crafting XP, displaced-component recovery, shared-stack purchase/sale quantity, save failure rollback, and stale transaction replay.
- **Projection:** all 13 power recipes are exercised at all three grades on their authored moves; all three cost recipes are exercised at every grade. Cinderlung remains at 1 Mana, with no global cost change. Cover split-move total-power distribution, unaffected moves, and unchanged weapon identity thresholds.
- **Persistence/client parity:** save/reload installed and uninstalled grade components through schema 26; preserve old current-schema saves without schema changes; terminal and browser views show the same IDs, effects, costs, target and unlock reason. Full live Floor-IV route reachability remains M8.3's journey, not an M8.2 fixture requirement.
- **Cumulative qualification:** focused weapon/catalog/vendor/persistence tests, root and web suites, content validation, compilation, browser build and smoke, PostgreSQL/migration parity, and pinned MicroPython on the exact implementation SHA. Grade IV may use controlled `floor_four_cleared=True` test state only; do not fabricate an unfinished route.

The M8.2 catalog adds 48 authored component variants and increases the pinned probe's resident-content footprint. The previous 1280K stable point was intermittent on this worktree (2/3 complete passes, 1/3 `MemoryError`); 1408K passed 3/3 and 1216K produced the expected memory-limit classification 3/3. The probe qualification profile is therefore recalibrated to 1408K stable / 1216K expected memory limit. These values qualify the exact Windows MicroPython probe only; they are not a hardware-wide compatibility claim or product memory budget. The complete local matrix passed on the current implementation worktree; exact-SHA and hosted qualification remain pending.

Grade-IV material costs depend on legitimate Grade-IV content availability. M8.3 owns the authored Floor-IV drop quantities/chances; it must not alter approved M8.2 recipe quantities. Its Gate A content plan must show how the proposed four-unit Grade-IV recipe costs remain reachable through legitimate repeatable sources and existing finite Blacksmith stock/replenishment. If not, report the conflict rather than silently changing either package's approved values.

## Package Gates And Status

- **Gate A, plan approval:** Approved with adjustments. Cinderlung keeps a -2 resource-cost modifier at all grades and adds +1/+2 power at Grades III/IV. The other 15 component families retain their authored proposal values. New Grade II-IV vendor offers are sale-fed-only; Grade I commerce remains unchanged. Recruitment and matching-floor unlocks are conjunctive.
- **Gate B, implementation and focused tests:** Implemented in the current working tree. Local cumulative checks pass: 2,541 root tests, 94 web tests, authored-content validation, compileall, 183-file browser build, full Playwright smoke, and the pinned runtime matrix. Local PostgreSQL qualification was unavailable because the Docker engine was unreachable; hosted service qualification is pending.
- **Gate C, exact-SHA qualification and closure:** Not run.

| Implementation SHA | Hosted CI URL/results | Runtime/migration evidence | Independent review | Status |
| --- | --- | --- | --- | --- |
| Pending commit | Pending exact-SHA CI | 2,541 root / 94 web tests, content, compile, browser smoke, and full local pinned matrix pass; Docker unavailable locally; schema remains 26 | Pending | Gate B implementation complete; exact-SHA qualification pending |

Record implementation SHA, exact hosted CI, migration/runtime evidence, independent disposition, and owner closure in this package and the parent. Do not claim M8.2 complete by inheriting another package's qualification.
