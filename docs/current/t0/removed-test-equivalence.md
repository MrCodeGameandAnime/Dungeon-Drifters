# T0 Removed-Test Equivalence Record

This record covers the current uncommitted T0 pass on baseline `2af6e59b21d1c187ca4f2833fde04f6dd6f44cf8`. A renamed or deleted test function is not an assertion that its behavior was obsolete. The following named owners retain the inputs, expected outcomes and failure boundaries. All other test functions remain; setup-only edits are listed separately.

## Authored Loadout Authority

`test_character_move_data.py` is removed. Its duplicated authored expectations are owned by `test_character_loadout_regression.py::test_all_archetype_authored_loadout_data_is_unchanged`, backed by the existing independent `EXPECTED_LOADOUTS` oracle, not expectations computed from production content.

| Removed test | Remaining protection |
| --- | --- |
| `test_all_playable_classes_have_structured_moves` | Exact canonical move-field oracle plus explicit `isinstance(move, Move)` for every authored move |
| `test_loadout_resource_types_follow_authored_class_resources` | Exact resource type/cost for every move, every Drifter |
| `test_all_playable_rosters_keep_current_super_and_mechanic_boundary` | Exact ordered five-move oracle; existing no-Momentum and no-Focus/Ki-resource tests retained |
| `test_brawler_roster_is_four_standard_attacks_and_one_super` | Exact names/kinds/resources/mechanics plus new `test_branoc_authored_move_presentation` preserves role, Fire affinity and Heavy summary |
| `test_black_mage_roster_is_four_standard_attacks_and_one_super` | Exact names/kinds/resources/mechanics plus new `test_azhvielle_authored_spell_classification` |
| `test_rogue_archer_roster_is_four_standard_attacks_and_one_super` | Exact authored Zhaivra move oracle |
| `test_joruun_combat_moves_preserve_authored_order_and_resources` | Exact authored Joruun move oracle |
| `test_each_playable_class_has_a_distinct_mechanic` | Exact independent class-mechanic name/description for all four Drifters |

## Historical Identity Audit

`test_m9e_character_identity_audit.py` is removed only after the replacements and historical tests passed together (101 focused cases before removal).

| Removed test | Remaining protection |
| --- | --- |
| `test_branoc_complete_brace_loop_is_durable_and_single_use` | Moved to `test_combat_resolver.py` with all assertions, strict recorded RNG retained |
| `test_azhvielle_gravemantle_clean_and_miss_paths` | `test_azhvielle_gravemantle.py::test_gravemantle_charge_break_backlash_and_discharge`, clean-hit and clean-miss rows, including follow-up discharge |
| `test_azhvielle_backlash_is_real_risk_and_surviving_charge_is_unstable` | Same owner, hit/backlash row checks exact damage, typed outcome, charge and instability; miss/backlash row also retained |
| `test_azhvielle_accepted_discharge_miss_consumes_all_held_state` | `test_same_target_spell_discharge_uses_captured_break_and_clears_once`, explicit miss row preserves ordered consumption/clear outcomes |
| `test_azhvielle_instability_only_changes_physical_incoming_damage` | `test_instability_affects_physical_damage_but_not_magical_or_hybrid`, including physical vulnerability and unchanged magical/hybrid damage |
| `test_m9e_authored_identity_moves_remain_in_the_live_roster` | Independent exact all-move loadout oracle is stronger than subset-name checks |
| `test_m9e_no_identity_mechanics_branch_on_display_names_or_class_names` | Moved to `test_character_module_boundaries.py::test_identity_mechanics_do_not_branch_on_display_or_class_names`; same files/fragments checked |

The canonical instability test previously renamed a magical move to "Test Hybrid Spell" without changing its damage type. The fixture now explicitly sets `DamageType.HYBRID`. This strengthens a test, not production behavior.

## Historical Surface Hardening

`test_m10b_hardening.py` is removed after the historical and canonical replacements passed together. The independently expected values are retained rather than inferred only from authored route data.

| Removed test | Remaining protection |
| --- | --- |
| `test_all_encounter_completion_ids_remain_world_owned_and_schema_eight` | `test_game_snapshot.py::test_all_surface_completion_ids_round_trip_in_world_snapshot`: all eight IDs, schema 11 and world ownership explicitly asserted; original name was stale |
| `test_map_completion_uses_world_for_combat_and_overworld_for_rest` | Same test moved to `test_overworld_presenter.py`; eleven COMPLETED nodes and final CURRENT node retained |
| `test_every_composition_can_be_recreated_without_identity_leakage` | `test_m10b_encounter_instantiation.py::test_repeated_creation_never_reuses_runtime_or_resource_objects` parameterized over all eight independently specified compositions; resource and definition isolation |
| `test_first_victory_applies_rewards_and_pair_combat_is_next` | `test_overworld_session.py::test_surface_victory_adds_rewards_to_existing_progress` for all four Drifters, including Branoc: original nonzero XP/gold, exact reward, no GP/level change, actor/factory identity, next screen/node/action and empty Rest history |

`test_victory_preserves_battle_mutations_and_advances_to_pair_node` remains separate: Zhaivra's infusion lifecycle is not valid generic setup for Branoc. An attempted over-broad matrix was rejected by production's unsupported-payload validation and corrected before final verification.

## Equivalent Unit And Contract Matrices

| Original owner/functions | Replacement and preserved cases |
| --- | --- |
| `test_combat_resolver.py`: `test_dexterity_accuracy_and_dodge_adjust_final_hit_chance`, `test_final_hit_chance_caps_at_ninety_five_with_accuracy_and_dodge`, `test_final_hit_chance_floors_at_five`, `test_low_target_dexterity_negative_dodge_bonus_is_preserved_before_clamp` | `test_hit_chance_boundaries`: all original 14 Dexterity/accuracy rows plus 95/96 cap, 5/6 floor and 51/52 negative-dodge boundaries; exact RNG call count added |
| `test_combat_resolver.py`: `test_accepted_heavy_attack_consumes_brace_payoff_before_hit_resolution`, `test_heavy_brace_payoff_is_applied_before_final_crit_multiplier`, `test_brace_reduction_is_applied_before_final_crit_damage` | `test_brace_damage_pipeline`: noncritical Heavy 26, critical Heavy 39 and critical incoming physical 18; target HP, accepted/hit/critical, consumed payoff and strict two-roll contract |
| `test_azhvielle_gravemantle.py`: `test_gravemantle_hit_grants_overcharge_and_break_without_backlash`, `test_gravemantle_miss_grants_charge_without_break_and_backlash_can_apply` | Four-row charge/break/backlash/discharge matrix retains hit/miss and exact backlash values; additional cross-combinations strengthen the canonical owner |
| `test_battle_player_state.py`: `test_accepted_player_action_replaces_previous_displayed_turn`, `test_accepted_miss_starts_a_new_displayed_turn` | `test_accepted_action_replaces_previous_displayed_turn[hit/miss]`, same semantic UI, old-log seed and new displayed turn assertions |
| `test_battle_player_state.py`: `test_victory_returns_player`, `test_completed_actions_advance_turn_count` | `test_victory_returns_player_and_counts_completed_actions`: original Joruun/key 2/5 turns and Branoc/key 4/7 turns; same initiative script and terminal run |
| `test_character_state.py`: `test_explicit_resource_recalculation_updates_maximums_without_refill`, `test_explicit_resource_recalculation_can_increase_current_by_positive_delta` | `test_explicit_resource_recalculation_preserves_or_increases_current`: False/84 HP/48 mana and True/92 HP/50 mana, same initial damage/spend/level and maxima |
| `test_enemy_state.py`: `test_enemy_states_do_not_share_runtime_resources_stats_or_move_tuples`, `test_factory_enemy_states_do_not_share_runtime_state` | `test_enemy_instances_own_runtime_resources_stats_and_moves[direct/factory]`: original mutations, exact values and object isolation; both stats and definition checks now apply to both paths |
| `test_profile_sync.py`: `test_schema8_remote_head_advances_to_schema12_without_rewriting_history`, `test_schema9_cloud_head_advances_to_schema12_without_rewriting_history` | `test_legacy_remote_head_advances_without_rewriting_history[schema8/schema9]`: distinct original legacy builders, same real local store/coordinator/memory-remote boundary, pending-to-clean progression and immutable historical payload |

## Setup Refactors Without Test Deletion

- `game_test_support.py` centralizes Surface traversal, Hub, recruited pair, completed tutorial and Floor I Rest setup. It uses domain transitions, not replacement of private party/route fields. Four independent builder/save-reconstruction cases protect valid states and non-shared mutation.
- Consumers are Hub flow/extraction, Floor I run, terminal overworld, save state, overworld session/presenter, M11 save/continue/cross-encounter and weapon progression. Test-specific resources, identities, rewards, invalid actions and expected values remain at the call sites. Actual recruitment, rollback and transition contract tests still construct their subject explicitly.
- `RecordedRng` replaces six AST-identical strict recorded RNG implementations in Gravemantle, Heal, Joruun Air/Water/Lightning and Mournglass tests. Fallback RNG implementations are not considered equivalent and remain separate.
- Independent Surface route/content oracles remain. Traversal setup may follow authored route nodes, but expected route labels, successor IDs, resolved Rest IDs and final values do not derive from the builder.

## Protected Boundaries Left Intact

No browser journey, PostgreSQL/service test, migration test, concurrency test, fault-injection recovery test, Tier V atomicity test, profile trust-boundary test or pinned-runtime qualification path was removed. Shared setup is not a substitute for their execution. See the qualification record for actual reruns; a Python marker-parser test is not recorded as real MicroPython qualification.
