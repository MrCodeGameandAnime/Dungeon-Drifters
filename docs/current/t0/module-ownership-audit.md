# T0 Current Test-Module Ownership Audit

**Audited tree:** `t0` at `3acd725` (`test reduction 2`), 2026-10-29. This is a module ownership review, not a claim that every assertion is globally unique. Structural counts and source hashes are in the ignored final-pass inventory; this file records the human-reviewed responsibility and the reason a neighboring layer is not a substitute.

## Scope And Disposition

The current tree contains **148 Python test/support files**: 140 files with test functions and 8 fixtures/helpers. The set is the root test tree, web tests, and profile-service tests. The baseline `module-inventory.csv` remains a historical 147-file structural inventory; it is not the current ownership map. The three removed baseline modules and four added support/test modules are accounted for below and in [removed-test-equivalence](removed-test-equivalence.md).

Disposition rule for this audit:

- **KEEP**: the module owns a distinct domain rule, contract, flow, or adapter boundary.
- **PROTECTED**: removing it would erase migration, sync/conflict, database/concurrency, browser, or real-runtime evidence; requires equivalent proof at that same boundary first.
- **SUPPORT**: test infrastructure only; it owns no gameplay assertion and must not become a hidden test framework.

No additional test deletion was approved by this audit. Existing reductions are recorded separately with named replacement evidence. Similar subject matter across layers is retained when the layer owns a different failure boundary.

## Domain And Authored-Data Ownership

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/tests/test_character_state.py` | UNIT: character resources, levels, permanent stats | Owns character-level validation and resource/stat mutation; player ownership and persistence projection are separate. | KEEP |
| `root/tests/test_character_run_state.py` | UNIT: encounter-scoped Drifter resources | Owns per-character payload isolation, consumption and snapshot shape; weapon inventory and global inventory do not own this temporary state. | KEEP |
| `root/tests/test_game_state.py` | UNIT: aggregate runtime ownership | Verifies GameState accepts and owns its state objects and does not share containers; snapshot encoding is separately owned. | KEEP |
| `root/tests/test_game_snapshot.py` | CONTRACT: aggregate snapshot schema and defensive conversion | Owns world/story snapshot shape, plain-value conversion and non-finite rejection; per-player and save-document projection are separate. | KEEP |
| `root/tests/test_story_state.py` | UNIT: story-state values and collections | Story location/value ownership is separate from route progression and world completion. | KEEP |
| `root/tests/test_world_state.py` | UNIT: world completion collection | Owns completion IDs and duplicate prevention; route cursor and rest order live in OverworldState. | KEEP |
| `root/tests/test_overworld_state.py` | UNIT: route cursor and rest progression | Owns ordered route transitions and authored rest tracking; presenter projection and session orchestration are separate. | KEEP |
| `root/tests/test_player_state.py` | UNIT: player ownership, inventory/equipment, effective stats | Owns the player aggregate and equipment conservation; CharacterState owns underlying character rules and snapshots own serialization. | KEEP |
| `root/tests/test_player_scaling.py` | UNIT: pure stat/resource scaling | Owns mathematical milestones and interpolation; progression state owns level/XP transitions. | KEEP |
| `root/tests/test_player_snapshot.py` | CONTRACT: player persistent snapshot projection | Proves supported values and rejection of unsupported runtime objects; GameSnapshot and SaveDocument have distinct outer boundaries. | KEEP |
| `root/tests/test_player_battle_checkpoint.py` | CONTRACT: in-memory battle rollback checkpoint | Checkpoints restore the live owner graph and are intentionally absent from persistent snapshots; this is not save/load coverage. | KEEP |
| `root/tests/test_party_state.py` | UNIT: party roster/economy and shared materials | Owns recruitment, shared crafting progression/material spending, and party snapshot validation; session owns navigation and transitions. | KEEP |
| `root/tests/test_party_battle.py` | UNIT/FLOW: party turn ownership and order | Owns interleaved Dexterity ordering, reranking, party actor identity and party defeat; terminal projection is separate. | KEEP |
| `root/tests/test_combatant_contract.py` | CONTRACT: structural combatant protocol | Ensures PlayerState and EnemyState interoperate without type-specific branches; implementations remain owned by their state tests. | KEEP |
| `root/tests/test_move_contract.py` | UNIT: authored Move value validation | Owns immutable move fields, costs, scaling and presentation metadata shape; catalog authorship is separate. | KEEP |
| `root/tests/test_move_result.py` | UNIT: resolver result value contract | Owns immutable accepted/rejected result shape and field validation; resolver behavior is tested at its own boundary. | KEEP |
| `root/tests/test_combat_state.py` | UNIT: temporary combat lifecycle state | Owns defend/Brace identity tracking, expiry and turn completion; the resolver owns applying combat math. | KEEP |
| `root/tests/test_combat_resolver.py` | UNIT: combat decision and arithmetic | Owns action validation, target rules, RNG use, hit/crit/damage/healing, mitigation and transaction atomicity; Battle tests verify orchestration rather than duplicating the full formula matrix. | KEEP |
| `root/tests/test_enemy_state.py` | UNIT: enemy definition-to-runtime isolation | Owns fresh runtime enemy state, immutable capabilities/moves and factory validation; encounter composition is a separate authored boundary. | KEEP |
| `root/tests/test_m10_enemy_definitions.py` | CONTRACT: authored enemy combat values and move selection | Owns the exact existing enemy values and legal mana-move selection/spend; generic EnemyState ownership is separate. | KEEP |
| `root/tests/test_m10e_progression.py` | UNIT: level/XP progression primitive | Owns level caps, nonlinear threshold carry and invalid XP; award distribution and Growth Points are owned by the growth flow. | KEEP |
| `root/tests/test_m10e_player_growth.py` | FLOW: encounter reward and permanent growth | Owns reward atomicity, Growth Point allocation, resource recalculation and four-Drifter isolation; pure scaling constants are separate. | KEEP |
| `root/tests/test_azhvielle_gravemantle.py` | UNIT: Gravemantle charge/break/backlash | Owns that mechanic's capture, target binding, discharge, backlash and damage-type semantics; other elemental status systems remain distinct. | KEEP |
| `root/tests/test_joruun_air_route.py` | UNIT/CONTRACT: Air route and turbulence | Owns Air-specific status application/consumption and its presentation; Water and Storm have different status lifecycle rules. | KEEP |
| `root/tests/test_joruun_water_route.py` | UNIT/CONTRACT: Water route and conductive setup | Owns Hydro/Conductive application, lightning interaction and stun; Air turbulence is not an equivalent state. | KEEP |
| `root/tests/test_joruun_lightning_storm.py` | UNIT/FLOW: combined Storm setup | Owns setup-order equivalence, exclusive multiplier and consumption of both linked states; it is not a duplicate of either individual route. | KEEP |
| `root/tests/test_infused_barb_integration.py` | UNIT/FLOW: prepared infusion move integration | Owns payload validation/consumption and exact Burn/Poison application for accepted hit, miss, and rejection; generic status ticks are separate. | KEEP |
| `root/tests/test_frost_status_state.py` | UNIT: generic Frost state machine | Owns charge/proc, frozen/stun ordering, source identity and cleanup independent of a particular authored move. | KEEP |
| `root/tests/test_storm_status_state.py` | UNIT: shared Storm status lifecycle | Owns Conductive/Turbulence/Stun coexistence, refresh and cleanup; application-specific formulas stay in Joruun route tests. | KEEP |
| `root/tests/test_status_state.py` | UNIT: Burn/Poison lifecycle | Owns snapshot potency, duration/tick/refresh, mitigation bypass and deterministic cross-status ordering; move-specific application is separate. | KEEP |
| `root/tests/test_mournglass_frost_route.py` | FLOW: Mournglass authored Frost/backlash route | Owns the exact authored multi-action route, backlash and source/target presentation; generic Frost rules are not replayed as its owner. | KEEP |
| `root/tests/test_m9b5_frost_hardening.py` | FLOW: Frozen opportunity suppression and Frost regressions | Owns player/enemy skip lifecycle and cross-status cleanup alongside the authored Mournglass route; primitive Frost state transitions are lower-level. | KEEP |
| `root/tests/test_m9c_zhaivra_hardening.py` | FLOW: Zhaivra prepared-resource lifecycle | Owns stock prepare-through-expiration journeys and personal run-resource boundaries; generic inventory recipes and status ticks are separate. | KEEP |
| `root/tests/test_m9d_joruun_hardening.py` | FLOW: Joruun Storm route regression | Owns deterministic multi-step Joruun routes, identity linkage and terminal route behavior; Air/Water/combined mechanics remain split by specific contracts. | KEEP |
| `root/tests/test_inventory.py` | UNIT: generic inventory semantics | Owns collection behavior and defensive snapshots; recipe/action validation is separate. | KEEP |
| `root/tests/test_inventory_action_resolver.py` | UNIT: atomic preparation recipes | Owns ingredient consumption and prepared-payload creation/rejection; menu display and terminal input translation are separate. | KEEP |
| `root/tests/test_item_first_inventory.py` | FLOW: item-first interaction | Owns inspect/confirm/back navigation, stable item identity and resolver routing; inventory resolver tests do not own user-choice semantics. | KEEP |
| `root/tests/test_heal_action.py` | CONTRACT/FLOW: universal Heal lifecycle | Spans formula, cooldown, accepted-action lifecycle, presenter and terminal reporting; each checks integration at a different boundary, while resolver tests own general healing arithmetic. | KEEP |
| `root/tests/test_weapon.py` | UNIT: generic Weapon value | Owns identity/scalar/stat-bonus validation and immutability; authored signature-weapon catalogs are separate. | KEEP |
| `root/tests/test_weapon_content.py` | CONTRACT: signature weapon and progression authorship | Owns exact authored slots, components, recipes, references, materials and definition validation; runtime projection/progression math are separate. | KEEP |
| `root/tests/test_weapon_progression.py` | UNIT/FLOW: reusable weapon progression operations | Owns improvement gates/rolls, Tier V atomicity, dismantle bounds and craft-install ownership; presenter and persistence boundaries remain complementary. | KEEP |
| `root/tests/test_character_loadout_regression.py` | CONTRACT: independent Drifter loadout oracle | Expected starting stats/moves/mechanics are independent of production content; generated catalog validity is separately owned. | KEEP |
| `root/tests/test_character_profiles.py` | CONTRACT: player-facing Drifter roster/profile | Owns stable ordered selection and profile rendering shape; actual session selection and character construction are separate. | KEEP |
| `root/tests/test_drifter_content.py` | CONTRACT: authored Drifter catalog/factory | Owns catalog generation, canonical identity, immutable specs and fresh generic runtime graph; move oracle and runtime combat are separate. | KEEP |
| `root/tests/test_enemy_content.py` | CONTRACT: authored enemy catalog/factory | Owns enemy spec authoring, generated catalog freshness and validation; runtime EnemyState behavior and encounter manifests are separate. | KEEP |
| `root/tests/test_route_content.py` | CONTRACT: route/encounter content | Owns authored route order, cross-references, reward derivation and generated catalog freshness; instantiated enemy identity and route execution are separate. | KEEP |
| `root/tests/test_m10b_encounter_manifest.py` | CONTRACT: route manifest facts | Owns exact authored node/count/reward/boss manifest and inspection lookup semantics; route content validation owns source definitions, not manifest behavior. | KEEP |
| `root/tests/test_m10b_encounter_instantiation.py` | CONTRACT: encounter-to-runtime construction | Owns exact order, factory calls, duplicate enemy identity isolation and fail-before-mutation; manifest correctness and Battle execution are separate. | KEEP |
| `root/tests/test_m10b_map_inspection.py` | CONTRACT: read-only player-facing map inspection | Owns adjacency aggregation and inspection projection without runtime enemy creation; authored route data is tested elsewhere. | KEEP |
| `root/tests/test_m10e_enemy_rewards.py` | CONTRACT: enemy reward ownership/aggregation | Owns canonical reward values, scaling/delegation and route totals independently from player reward application. | KEEP |
| `root/tests/content_test_support.py` | SUPPORT: shared content-validator subprocess runner | Shares invocation mechanics only; independent fixtures and each tooling module's assertions remain local. | SUPPORT |
| `root/tests/test_content_tooling.py` | CONTRACT: content scaffolder/validator behavior | Owns deterministic generation, collision refusal, rollback and cross-reference diagnostics; source import boundaries are owned separately. | KEEP |
| `root/tests/test_content_creation_boundaries.py` | CONTRACT: engine/content dependency direction | Owns import boundaries, canonical content loading and end-to-end scaffold acceptance; scaffolder failure behavior is separately tested. | KEEP |

## Combat, Route And Session Flows

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/tests/test_battle_player_state.py` | FLOW: Battle orchestration over PlayerState | Owns semantic input phases, resolver delegation, action completion, player/enemy lifecycle and rollback of rejected actions; the resolver alone cannot prove phase behavior. | KEEP |
| `root/tests/test_battle_ui_hardening.py` | FLOW/CONTRACT: generic semantic Battle integration | Owns all-Drifter move availability, one deterministic battle slice and presenter purity; class-specific mechanics have dedicated owners. | KEEP |
| `root/tests/test_m10c_participant_contracts.py` | CONTRACT: Battle participant collections | Owns one-to-four enemy normalization, stable IDs/labels, resolver/RNG ownership and invalid participant rejection. | KEEP |
| `root/tests/test_m10c_enemy_phases.py` | FLOW: enemy phase lifecycle | Owns enemy ordering, skipped actions, lifecycle completion, victory/defeat conditions and cleanup; target selection is separate. | KEEP |
| `root/tests/test_m10c_exact_targeting.py` | CONTRACT/FLOW: exact multi-enemy target selection | Owns target-specific previews, stale/invalid targets, affordability revalidation and no implicit retargeting; participant shape and enemy phase remain separate. | KEEP |
| `root/tests/test_m10c_hardening.py` | FLOW: representative multi-enemy gameplay | Owns real terminal pair route, authored boss layout and Drifter-specific cross-target interactions; lower-level phase/target tests own matrices. | KEEP |
| `root/tests/test_m10c_route_integration.py` | FLOW: route completion around multi-enemy battles | Owns one-time advancement/reward and pausing at Rest; session route transitions are tested at their own layer. | KEEP |
| `root/tests/test_m10g_session_integration.py` | FLOW: session save/load user path | Owns options load/save replacement and startup loading through terminal route; storage codec/coordinator contracts are lower-level owners. | KEEP |
| `root/tests/test_m11_cross_encounter.py` | FLOW: real Battle lifecycle across encounters | Owns fresh combat state, status cleanup, retry rollback and one-time rewards using actual battles; single-encounter unit rules do not cover the lifecycle boundary. | KEEP |
| `root/tests/test_m11_session_ownership.py` | CONTRACT/FLOW: persistent owner graph across gameplay | Owns exact selected-Drifter graph, schema exclusion of runtime objects, independent session state and weapon inspection; save serialization has separate owners. | KEEP |
| `root/tests/test_m11_surface_routes.py` | FLOW: full Surface route with all Drifters | Owns end-to-end class mechanic coverage, universal Heal, multi-enemy defeat and terminal boss presentation; browser qualification separately proves browser deployment. | KEEP |
| `root/tests/test_m11_save_continue.py` | FLOW/CONTRACT: full-route save/quit/restart/continue | Owns all-Drifter route-boundary round trips and continuation without duplicate rewards; schema and coordinator rules are lower-level owners. | PROTECTED |
| `root/tests/test_floor_one_run.py` | FLOW: Floor I risk/reward lifecycle | Owns run start, rewards, Rest/save/extract/death/replay and no-rewind checkpoint semantics; Hub tutorial flow is not an equivalent dungeon run. | KEEP |
| `root/tests/test_hub_extraction.py` | FLOW: tutorial Hub recruitment/readiness/extraction | Owns tutorial party encounter, delayed reward bank, defeat/reselect and load reconstruction; Floor I death/extraction rules are distinct. | KEEP |
| `root/tests/test_hub_flow.py` | FLOW: Hub navigation/recruitment/merchant | Owns authoritative menu actions, exact companion target and transaction rejection; merchant progression mechanics are domain-owned. | KEEP |
| `root/tests/test_overworld_session.py` | FLOW: session-owned surface route and Hub actions | Owns session transitions, rest, merchant, skills, save boundary and stale-action rejection; presenter and terminal adapters only project/translate. | KEEP |
| `root/tests/test_m10a_hardening.py` | FLOW/CONTRACT: menu shell and transient state | Owns supported navigation, stale battle-frame clearing and proof that UI selection/confirmation is not saved. | KEEP |
| `root/tests/test_event_character_selection.py` | FLOW: character-selection confirmation | Owns reprompt/back/confirm behavior and delayed construction; roster data is covered by profile contracts. | KEEP |
| `root/tests/test_main_flow_player_state.py` | FLOW: application composition | Owns one persistent session from chosen Drifter; individual session behavior is tested separately. | KEEP |
| `root/tests/smoke_test_vertical_slice.py` | FLOW: minimal legacy terminal smoke | Owns the minimal first attack-to-victory and quit-from-start path; it is not a replacement for deeper journey tests. | KEEP |
| `root/tests/test_runtime_new_game.py` | CONTRACT: headless new-game composition | Owns canonical Drifter creation and independent session state without terminal/browser concerns. | KEEP |
| `root/tests/test_runtime_overworld.py` | FLOW: step-driven session orchestration | Owns mode routing, battle/rest delegation, retry and quit semantics independent of blocking terminal input. | KEEP |
| `root/tests/test_runtime_battle.py` | FLOW: step-driven Battle behavior | Owns UI-free input steps, navigation, target phases and representative class-mechanic completion; terminal input is a separate adapter. | KEEP |
| `root/tests/test_runtime_compatibility.py` | CONTRACT: legacy terminal-driver bridge | Owns exactly-once delegation from the older driver into semantic steps; it does not re-prove the step runtime. | KEEP |
| `root/tests/test_runtime_qualification.py` | QUALIFICATION: headless semantic route | Owns an executable no-persistence route completion marker; parser/unit contracts do not substitute for executing the semantic journey. | PROTECTED |
| `root/tests/test_party_terminal_ui.py` | CONTRACT: party-specific terminal presentation | Owns active Drifter marking and extraction reward/semantic action display; the generic terminal adapter owns other screens. | KEEP |
| `root/tests/test_terminal_battle_ui.py` | CONTRACT: terminal Battle adapter | Owns textual input translation, width/ANSI fallbacks and display of semantic outcomes; presenter owns values, not terminal rendering. | KEEP |
| `root/tests/test_terminal_overworld_ui.py` | CONTRACT: terminal Overworld adapter | Owns screen layouts, mnemonic-only inputs, responsive width and action translation; session owns state transitions. | KEEP |
| `root/tests/test_battle_ui_contract.py` | CONTRACT: semantic Battle UI protocol | Owns the immutable input vocabulary and runtime-checkable adapter surface; concrete terminal behavior is separate. | KEEP |

## Presentation Ownership

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/tests/test_battle_presentation_models.py` | CONTRACT: Battle presentation values | Owns immutable display-only models and availability/rejection shape; presenter construction is separate. | KEEP |
| `root/tests/test_battle_presentation_session.py` | CONTRACT: bounded Battle log/session | Owns transient log retention and rejection display replacement without combat state ownership. | KEEP |
| `root/tests/test_battle_presenter.py` | CONTRACT: Battle read model | Owns pure projection of resources, moves, status and party views; terminal/browser rendering and combat mutation are separate. | KEEP |
| `root/tests/test_overworld_presentation_models.py` | CONTRACT: Overworld action/value models | Owns screen-specific model validation and legal control matrices; presenter population is separate. | KEEP |
| `root/tests/test_overworld_presenter.py` | CONTRACT: Overworld read model | Owns pure rendering data for Hub, route, character, merchant, map and items, including installed component effects; session transition semantics are separate. | KEEP |

## Persistence, Sync And Service Ownership

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/tests/test_save_contract.py` | CONTRACT: lightweight SavePort boundary | Owns structural acceptance and status/error types used by session; it intentionally avoids persistence implementation details. | KEEP |
| `root/tests/test_session_persistence_boundary.py` | CONTRACT: session-to-save adapter isolation | Owns lazy composition/import boundaries and menu behavior under adapter failures; SaveCoordinator owns storage policy. | KEEP |
| `root/tests/test_save_document_boundary.py` | CONTRACT: storage-neutral document codec | Owns persistent payload shape, round trips and exclusion of runtime-only values; envelope integrity is separate. | KEEP |
| `root/tests/test_save_state.py` | CONTRACT: schema migration and reconstruction | Owns runtime/disk schema split, validation-before-reconstruction, legacy behavior and fresh runtime graphs; local disk atomicity is separate. | PROTECTED |
| `root/tests/test_save_envelope.py` | CONTRACT: canonical envelope and digest | Owns canonical bytes, strict envelope parsing and legacy digest immutability; schema migration behavior is in save-state tests. | PROTECTED |
| `root/tests/test_save_coordinator.py` | CONTRACT/FLOW: local save orchestration | Owns local profile sequencing, bootstrap/load and schema advancement through the coordinator; file atomicity and remote sync have distinct owners. | PROTECTED |
| `root/tests/test_legacy_save_migration.py` | CONTRACT: legacy file bootstrap | Owns migration-without-source-mutation and no-op when missing/invalid; payload migration logic is separate. | PROTECTED |
| `root/tests/test_local_profile_store.py` | CONTRACT: local filesystem durability | Owns atomic replace, sequence rules, conflict evidence and recovery archive idempotency; coordinator handles orchestration. | PROTECTED |
| `root/tests/test_remote_profile_client.py` | CONTRACT: HTTP profile client | Owns wire parsing, digest/revision checks and service error mapping; sync coordinator owns retry/conflict policy. | PROTECTED |
| `root/tests/test_profile_sync.py` | CONTRACT: sync/replay/local-first behavior | Owns expected operational failures, replay ancestry and retry behavior using the memory service; PostgreSQL integration proves server behavior. | PROTECTED |
| `root/tests/test_credentials.py` | CONTRACT: credential value parsing and capability separation | Owns response shape, UTC timestamps, secret redaction and separation from offline game saves; service auth behavior is separately tested. | PROTECTED |
| `root/tests/test_profile_conflicts.py` | CONTRACT: conflict crash/restart recovery | Owns sidecar reconciliation, Keep Local/Use Remote/Fork Local and fault injection; ordinary pending sync is not equivalent. | PROTECTED |
| `root/tests/credential_test_support.py` | SUPPORT: in-memory credential store | Models the credential capability for tests; it does not share or emulate game-save persistence. | SUPPORT |
| `root/tests/persistence_test_support.py` | SUPPORT: isolated save-port and storage paths | Shares test composition/path setup only; save contract assertions stay with their owning modules. | SUPPORT |
| `root/tests/remote_sync_test_support.py` | SUPPORT: in-memory remote and sync fixtures | Provides a deterministic service double and profile builders; actual HTTP/PostgreSQL service behavior remains independently qualified. | SUPPORT |
| `root/services/profile_api/tests/conftest.py` | SUPPORT: isolated service fixtures | Owns test app/database/payload setup only; no service behavior is attributed to fixtures. | SUPPORT |
| `root/services/profile_api/tests/test_auth_sessions.py` | CONTRACT: account/session HTTP behavior | Owns credential hashing, refresh/revoke and sanitized auth errors; identity linking and profile ownership are separate. | PROTECTED |
| `root/services/profile_api/tests/test_identity.py` | CONTRACT: verified identity/recovery rules | Owns verifier trust and recovery prerequisites at service layer; real races are owned by PostgreSQL concurrency tests. | PROTECTED |
| `root/services/profile_api/tests/test_entitlements.py` | CONTRACT: account-scoped entitlement isolation | Owns separation of entitlements from progression/profile state; other profile endpoint tests do not cover that data boundary. | PROTECTED |
| `root/services/profile_api/tests/test_profiles.py` | CONTRACT: account-scoped profile/revision API | Owns claims, idempotency, immutable history, schema upgrade and stale writes; client sync simulation is separate. | PROTECTED |
| `root/services/profile_api/tests/test_client_sync_integration.py` | FLOW/QUALIFICATION: production profile API sync | Owns client behavior against the actual API and PostgreSQL, complementing the deterministic memory-server client tests. | PROTECTED |
| `root/services/profile_api/tests/test_postgres_concurrency.py` | QUALIFICATION: PostgreSQL race invariants | Owns real concurrent revision and recovery-path races; SQLite or in-memory tests cannot establish row-lock behavior. | PROTECTED |
| `root/services/profile_api/tests/test_migrations.py` | QUALIFICATION: database migration lifecycle | Owns clean migration up/down and immutable revision triggers on PostgreSQL; Alembic model checks are an additional boundary. | PROTECTED |

## Portability And Qualification Ownership

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/tests/test_character_module_boundaries.py` | CONTRACT: package/import ownership | Owns canonical support imports, isolation and prohibition on display-name/class-name mechanic dispatch. | KEEP |
| `root/tests/test_enemy_domain_boundaries.py` | CONTRACT: enemy catalog dependency direction | Owns public/private import and generated-catalog boundaries, distinct from general content tooling. | KEEP |
| `root/tests/test_dataclass_contract.py` | CONTRACT: actual DD dataclass usage census | Owns production dataclass field/default/frozen/post-init contract independent from compatibility overlay implementation. | KEEP |
| `root/tests/test_enum_contract.py` | CONTRACT: actual DD enum usage census | Owns native and production enum surface constraints; overlay behavior has a separate owner. | KEEP |
| `root/tests/test_keyword_contract.py` | CONTRACT: actual keyword dependency contract | Owns narrow production dependency and native semantics; overlay implementation tests are separate. | KEEP |
| `root/tests/test_typing_contract.py` | CONTRACT: typing/protocol census | Owns runtime type/protocol surface and discovered requirements; forced overlay compatibility is separate. | KEEP |
| `root/tests/test_regex_contract.py` | CONTRACT: production regex usage census | Owns supported runtime regex operation discovery; the compatibility proxy has its own behavior tests. | KEEP |
| `root/tests/test_string_contract.py` | CONTRACT: runtime string-method audit | Owns discovery/exclusion rules for runtime use, not semantics of a specific portable validator. | KEEP |
| `root/tests/test_collections_contract.py` | CONTRACT: dynamic runtime collection census | Owns classification of runtime collection usage and scoped audit boundaries. | KEEP |
| `root/tests/test_readonly_mapping.py` | CONTRACT: mapping immutability adapter | Owns native/fallback read-only surface and production import boundary; collection protocol audit is separate. | KEEP |
| `root/tests/test_random_contract.py` | CONTRACT: portable random capability | Owns fallback correctness, delegation and no direct stdlib random imports; individual Battle RNG injection is tested elsewhere. | KEEP |
| `root/tests/test_next_default_contract.py` | CONTRACT: portable `next(default)` boundary | Owns helper behavior and scoped production-call audit, independent from application logic. | KEEP |
| `root/tests/test_itertools_contract.py` | CONTRACT: itertools exclusion | Owns targeted production import classifier; other builtin-call audits do not cover this import. | KEEP |
| `root/tests/test_strict_zip_contract.py` | CONTRACT: strict zip exclusion | Owns scoped direct-builtin call classification, independent from starred tuple audit. | KEEP |
| `root/tests/test_starred_tuple_contract.py` | CONTRACT: portable starred tuple syntax/use audit | Owns AST context distinction and production scope; strict zip has a different syntax boundary. | KEEP |
| `root/tests/test_portable_collections_abc.py` | CONTRACT: collections.abc overlay | Owns the qualified child-module overlay and real weapon-path compatibility. | PROTECTED |
| `root/tests/test_portable_counter_removal.py` | CONTRACT: Counter-free runtime behavior | Owns equivalent target labels/IDs and same-instance rejection after removing Counter dependency; not a stdlib overlay test. | PROTECTED |
| `root/tests/test_portable_dataclasses.py` | CONTRACT: dataclass compatibility overlay | Owns forced overlay initialization/field/default/frozen behavior and generated manifest identity; native usage census is separate. | PROTECTED |
| `root/tests/test_portable_enum.py` | CONTRACT: enum compatibility overlay | Owns StrEnum transformation and persisted UUID/enum integration under forced overlay. | PROTECTED |
| `root/tests/test_portable_keyword.py` | CONTRACT: keyword compatibility overlay | Owns native-equivalent hard/soft keyword behavior and real DD validation paths. | PROTECTED |
| `root/tests/test_portable_regex.py` | CONTRACT: regex compatibility proxy | Owns native regex preservation plus the narrow fullmatch boundary and real validators. | PROTECTED |
| `root/tests/test_portable_string_validation.py` | CONTRACT: ASCII identifier validation portability | Owns the exact Drifter ID acceptance/error semantics through the proxy; not merely regex primitive compatibility. | PROTECTED |
| `root/tests/test_portable_typing.py` | CONTRACT: typing compatibility overlay | Owns alias/protocol loading and real combat/UI contract compatibility without host-process leakage. | PROTECTED |
| `root/tests/test_micropython_route_probe_contract.py` | CONTRACT: probe scenario/evidence ordering | Owns full route/Hub/Floor I stage design, resource release and heap-map capture contract; does not itself qualify the binary. | PROTECTED |
| `root/tests/test_micropython_heap_sweep.py` | CONTRACT: heap sweep tooling | Owns subprocess argument handling, memory classification and repeated frontier result summarization. | PROTECTED |
| `root/tests/test_runtime_qualification_matrix.py` | CONTRACT: qualification signature/frontier policy | Owns output semantic parity, stage order and closure threshold decisions; execution evidence is separately required. | PROTECTED |

## Browser Ownership

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/web_tests/test_browser_bridge_contract.py` | CONTRACT: Python-to-browser command bridge | Owns translation/projection and verifies state remains authoritative in Python; does not establish actual browser rendering or interaction. | PROTECTED |
| `root/web_tests/test_browser_site_build_contract.py` | CONTRACT: static site artifact/deployment shape | Owns deterministic staging, paths, public site layout and exclusion of internal files; browser runtime behavior is separate. | PROTECTED |
| `root/web_tests/test_browser_smoke_contract.py` | QUALIFICATION: actual browser semantic journey | Owns execution in a real browser and visible authoritative outcomes; source-string tests are not a substitute. | PROTECTED |
| `root/web_tests/test_pyodide_boot_contract.py` | CONTRACT: runtime archive contents/reproducibility | Owns the shipped Python archive boundary, distinct from shell markup and route setup. | PROTECTED |
| `root/web_tests/test_pyodide_mobile_contract.py` | CONTRACT/QUALIFICATION: responsive shell interaction | Owns mobile viewport, touch, isolated panels and orientation behavior, including actual responsive smoke. | PROTECTED |
| `root/web_tests/test_pyodide_route_contract.py` | QUALIFICATION: browser-backed semantic route | Owns the built route execution with real session and ephemeral save port; bridge command shape is separately owned. | PROTECTED |
| `root/web_tests/test_pyodide_shell_contract.py` | CONTRACT: play shell wiring and launch/presentation | Owns assets, controls and shell-to-bridge flow; real-browser journeys establish execution and rendering. | PROTECTED |

## Shared Test Infrastructure

| Module | Primary owner | Why this is a distinct owner | Disposition |
| --- | --- | --- | --- |
| `root/tests/combat_test_support.py` | SUPPORT: semantically identical combat fixtures | Shares only accepted-result/move projection/common deterministic doubles/recorded RNG; specialized resolvers and RNG doubles remain local. | SUPPORT |
| `root/tests/game_test_support.py` | SUPPORT: valid semantic game-state builders | Centralizes Hub, recruited pair and Rest setup via domain transitions; tests retain the transition under test and their distinct mutations. | SUPPORT |
| `root/tests/portable_test_support.py` | SUPPORT: isolated compatibility subprocess launcher | Shares `python -S -c` mechanics only; each overlay's prelude, contract and assertions stay local. | SUPPORT |
| `root/tests/test_game_test_support.py` | CONTRACT: builder validity and isolation | Proves shared builders produce valid domain states and independent mutable graphs; consumers cannot establish builder correctness collectively. | KEEP |
| `root/tests/test_balance_probe_tool.py` | CONTRACT: balance probe artifact/tooling | Owns reproducible seed sets, stable output, atomic failure handling and report format; it is not a gameplay balance test suite. | KEEP |

## Cross-Layer Ownership Map

| Invariant family | Primary owner | Complementary proof retained because |
| --- | --- | --- |
| Combat validation, damage, status and turn completion | Resolver/state unit tests | Battle flow proves accepted/rejected actions advance lifecycle correctly; presenter and adapters prove faithful projection/translation. |
| Authored content correctness | Independent content/loadout/weapon oracles and catalog contracts | Factories, runtime instances and content tools have separate immutability, discovery and failure boundaries. |
| Hub/Floor I transitions and reward security | PartyState/session/Floor I flow tests | Save tests own restart checkpoints; browser smoke owns shipped interaction; terminal tests own mnemonic and layout behavior. |
| Signature weapon progression | Weapon domain/content tests | Session targeting, presenter filtering, save reconstruction, browser reload and service validation each own a distinct boundary. |
| Persistence | Save state/document/envelope/store/coordinator tests | Each layer validates a different representation or durability boundary; profile service and PostgreSQL own server-side history/races. |
| Runtime portability | Native usage census plus forced-overlay tests | Census defines what production uses; overlay tests verify emulation; actual pinned MicroPython qualification proves execution and memory behavior. |
| Client behavior | Bridge/shell contract tests | Real browser smoke proves runtime interaction and saved reload; neither source inspection nor Python bridge tests can replace it. |
| Account identity/profile | Service contracts | Real PostgreSQL tests prove concurrency/locking; in-memory remote tests exercise game client replay/conflict policy. |

## Audit Conclusion

The reviewed test set is not one undifferentiated layer. Its largest recurring overlap is deliberate: a rule is checked at its owning domain boundary, then one representative flow proves orchestration, and a client/service/runtime qualification proves the corresponding external boundary. The named equivalence record documents the actual mergers; no further module-level duplicate was found whose removal preserves its same-layer contract.

The largest files remain candidates for future responsibility-oriented splitting (`test_combat_resolver.py`, `test_battle_player_state.py`, `test_overworld_session.py`, and the terminal UI modules). Their current contents have multiple coherent sections but still share one production owner per file; splitting would improve navigation, not reduce LOC, and is not required to settle ownership. Avoid using the 1.20 ratio as a deletion quota: after retaining flow and qualification layers, reaching that number would require removing roughly half of unit/contract LOC. The current ratio is therefore an explicit, evidence-backed exception, not a claim that test/application size is ideal.

After this ownership review, three redundant Surface journey tests were removed in a local test-only follow-up based on `3acd725`. The resulting test-source digest and 1,821-pass root run are recorded in [qualification](qualification.md) and [metrics after](metrics-after.json). Other qualification boundaries remain recorded at `3acd725`; this file does not claim hosted verification for the local follow-up.
