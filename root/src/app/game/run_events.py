"""Atomic resolution of Floor II rewards and searchable discoveries."""

import re
from dataclasses import dataclass
from enum import StrEnum
from uuid import UUID, uuid4

from app.content.enemy_spec import ItemDropSpec
from app.content.catalog import (
    get_armor_reward_sources_for_event,
    get_fixed_item_reward_sources_for_event,
    get_permanent_discovery_search_node_id,
    get_permanent_discovery_search_floor_id,
    get_permanent_discovery_source,
)
from app.content.permanent_discovery_spec import PermanentDiscoverySource
from app.game.game_state import GameState
from app.game.armor_generation import ArmorGenerationService
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)
from app.player.scaling import discovery_bonus_bps_from_intuition
from app.content.route_spec import RouteNodeKind
from app.content.catalog import get_route_node_spec


_EVENT_PART_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")


class RunEventStatus(StrEnum):
    RESOLVED = "resolved"
    ALREADY_RESOLVED = "already_resolved"
    INVALID_TARGET = "invalid_target"
    INVALID_SOURCE = "invalid_source"
    ALREADY_FOUND = "already_found"
    SAVE_FAILED = "save_failed"


@dataclass(frozen=True)
class RunEventResult:
    status: RunEventStatus
    game_state: GameState
    items: tuple[tuple[str, int], ...] = ()
    found: bool = False
    source_id: str | None = None
    effective_chance_bps: int | None = None
    roll: int | None = None
    equipment_instance_id: str | None = None


class RunEventService:
    def __init__(self, *, save_port, rng):
        if not is_save_port(save_port):
            raise TypeError("save_port must satisfy SavePort")
        if not callable(getattr(rng, "randint", None)):
            raise TypeError("rng must provide randint")
        self._save_port = save_port
        self._rng = rng

    def resolve_encounter_rewards(
        self,
        game_state,
        *,
        node_id,
        experience,
        gold,
        enemy_drop_tables,
    ):
        _validate_game_and_node(game_state, node_id)
        experience = _nonnegative("experience", experience)
        gold = _nonnegative("gold", gold)
        tables = _validate_drop_tables(enemy_drop_tables)
        party = game_state.party_state
        if party.phase is not DungeonPhase.OUTING or party.active_run_id is None:
            raise ValueError("encounter rewards require an active dungeon run")
        floor_id = party.active_run_floor_id
        run_id = party.active_run_id
        armor_sources = get_armor_reward_sources_for_event(floor_id, node_id)
        fixed_item_sources = get_fixed_item_reward_sources_for_event(
            floor_id, node_id
        )
        authored_source_ids = tuple(
            source.source_id for source in armor_sources + fixed_item_sources
        )

        event_key = _event_key(
            run_id,
            node_id,
            "encounter_rewards",
            floor_id=floor_id,
        )
        existing = party.run_event(event_key)
        if existing is not None:
            result = existing["result"]
            if (
                result["experience"] != experience
                or result["gold"] != gold
                or result["enemy_count"] != len(tables)
            ):
                raise ValueError("encounter event key was reused with different inputs")
            has_source_evidence = "reward_source_ids" in result
            recorded_source_ids = tuple(result.get("reward_source_ids", ()))
            if has_source_evidence and recorded_source_ids != authored_source_ids:
                raise ValueError("encounter event key was reused with different rewards")
            if has_source_evidence:
                for source in fixed_item_sources:
                    reward_event = party.run_event(
                        _event_key(
                            run_id,
                            node_id,
                            "fixed_item_reward",
                            floor_id=floor_id,
                        )
                    )
                    if reward_event is None or reward_event["result"] != {
                        "source_id": source.source_id,
                        "item_id": source.item_id,
                        "quantity": source.quantity,
                    }:
                        raise ValueError("encounter event is missing fixed reward evidence")
                equipment_instance_id = None
                for source in armor_sources:
                    armor_event = party.run_event(
                        _event_key(
                            run_id,
                            node_id,
                            "armor_reward",
                            floor_id=floor_id,
                        )
                    )
                    if (
                        armor_event is None
                        or armor_event["result"]["source_id"] != source.source_id
                        or armor_event["result"]["template_id"] != source.template_id
                        or armor_event["result"]["floor"] != source.floor
                    ):
                        raise ValueError("encounter event is missing armor reward evidence")
                    equipment_instance_id = armor_event["result"]["instance"][
                        "instance_id"
                    ]
            else:
                # A legacy event from before M8.4 is immutable and is not retroactively
                # granted newly-authored source rewards.
                equipment_instance_id = None
                fixed_item_sources = ()
                armor_sources = ()
            replay_items = dict(result["items"])
            for source in fixed_item_sources:
                replay_items[source.item_id] = (
                    replay_items.get(source.item_id, 0) + source.quantity
                )
            for position, table in enumerate(tables):
                drop_event = party.run_event(result["drop_event_keys"][position])
                if drop_event is None:
                    raise ValueError("encounter event is missing drop evidence")
                recorded_entries = drop_event["result"]["entries"]
                expected_entries = tuple(
                    (
                        drop.item_id,
                        drop.quantity,
                        drop.chance_bps,
                        drop.source_id,
                    )
                    for drop in table
                )
                actual_entries = tuple(
                    (
                        entry["item_id"],
                        entry["quantity"],
                        entry["chance_bps"],
                        entry.get("source_id"),
                    )
                    for entry in recorded_entries
                )
                if actual_entries != expected_entries:
                    raise ValueError(
                        "encounter event key was reused with different inputs"
                    )
            return RunEventResult(
                RunEventStatus.ALREADY_RESOLVED,
                game_state,
                tuple(sorted(replay_items.items())),
                equipment_instance_id=equipment_instance_id,
            )

        candidate = game_state.clone()
        candidate_party = candidate.party_state
        all_drop_events = []
        item_totals = {}
        for position, table in enumerate(tables):
            entries = []
            enemy_items = {}
            for drop in table:
                roll = self._rng.randint(1, 10000)
                awarded = roll <= drop.chance_bps
                entry = {
                    "item_id": drop.item_id,
                    "quantity": drop.quantity,
                    "chance_bps": drop.chance_bps,
                    "roll": roll,
                    "awarded": awarded,
                }
                if drop.source_id is not None:
                    entry["source_id"] = drop.source_id
                entries.append(entry)
                if awarded:
                    enemy_items[drop.item_id] = (
                        enemy_items.get(drop.item_id, 0) + drop.quantity
                    )
                    item_totals[drop.item_id] = (
                        item_totals.get(drop.item_id, 0) + drop.quantity
                    )
            drop_key = _event_key(
                run_id,
                node_id,
                "enemy_drop",
                position,
                floor_id=floor_id,
            )
            drop_event = _event_record(
                event_key=drop_key,
                run_id=run_id,
                node_id=node_id,
                kind="enemy_drop",
                position=position,
                result={"entries": entries, "items": enemy_items},
                floor_id=floor_id,
            )
            candidate_party.record_run_event(drop_event)
            all_drop_events.append(drop_key)

        drop_items = _positive_item_stacks(item_totals)
        total_items = dict(drop_items)
        fixed_item_events = []
        for source in fixed_item_sources:
            total_items[source.item_id] = (
                total_items.get(source.item_id, 0) + source.quantity
            )
            fixed_item_events.append(
                _event_record(
                    event_key=_event_key(
                        run_id,
                        node_id,
                        "fixed_item_reward",
                        floor_id=floor_id,
                    ),
                    run_id=run_id,
                    node_id=node_id,
                    kind="fixed_item_reward",
                    position=None,
                    result={
                        "source_id": source.source_id,
                        "item_id": source.item_id,
                        "quantity": source.quantity,
                    },
                    floor_id=floor_id,
                )
            )
        armor_items = []
        for source in armor_sources:
            instance_id = str(uuid4())
            item = ArmorGenerationService(rng=self._rng).generate(
                template_id=source.template_id,
                floor=source.floor,
                source_id=source.source_id,
                instance_id=instance_id,
                secured=False,
            )
            armor_items.append((source, item))
        reward_source_ids = list(authored_source_ids)
        candidate_party.add_active_run_rewards(
            experience=experience,
            gold=gold,
            items=total_items,
        )
        encounter_result = {
            "experience": experience,
            "gold": gold,
            "items": drop_items,
            "enemy_count": len(tables),
            "drop_event_keys": all_drop_events,
        }
        if reward_source_ids:
            encounter_result["reward_source_ids"] = reward_source_ids
        candidate_party.record_run_event(
            _event_record(
                event_key=event_key,
                run_id=run_id,
                node_id=node_id,
                kind="encounter_rewards",
                position=None,
                result=encounter_result,
                floor_id=floor_id,
            )
        )
        for event in fixed_item_events:
            candidate_party.record_run_event(event)
        equipment_instance_id = None
        for source, item in armor_items:
            candidate_party.add_equipment_instance(item)
            candidate_party.record_run_event(
                _event_record(
                    event_key=_event_key(
                        run_id,
                        node_id,
                        "armor_reward",
                        floor_id=floor_id,
                    ),
                    run_id=run_id,
                    node_id=node_id,
                    kind="armor_reward",
                    position=None,
                    result={
                        "template_id": source.template_id,
                        "floor": source.floor,
                        "source_id": source.source_id,
                        "instance": item.snapshot(),
                    },
                    floor_id=floor_id,
                )
            )
            equipment_instance_id = item.instance_id
        status, committed = self._commit(candidate)
        if status is not RunEventStatus.RESOLVED:
            return RunEventResult(status, game_state)
        return RunEventResult(
            RunEventStatus.RESOLVED,
            committed,
            tuple(sorted(total_items.items())),
            equipment_instance_id=equipment_instance_id,
        )

    def search_discovery(
        self,
        game_state,
        *,
        node_id,
        searcher_drifter_id,
        source,
    ):
        _validate_game_and_node(game_state, node_id)
        if not isinstance(source, PermanentDiscoverySource) or (
            source.search_chance_bps is None
        ):
            return RunEventResult(RunEventStatus.INVALID_SOURCE, game_state)
        try:
            authored_source = get_permanent_discovery_source(source.source_id)
        except ValueError:
            return RunEventResult(RunEventStatus.INVALID_SOURCE, game_state)
        if (
            source != authored_source
            or get_permanent_discovery_search_node_id(source.source_id) != node_id
        ):
            return RunEventResult(RunEventStatus.INVALID_SOURCE, game_state)
        party = game_state.party_state
        source_floor_id = get_permanent_discovery_search_floor_id(source.source_id)
        if (
            source_floor_id is None
            or party.phase is not DungeonPhase.OUTING
            or party.active_run_id is None
            or party.active_run_floor_id != source_floor_id
        ):
            raise ValueError("discovery search requires its active authored floor run")
        if searcher_drifter_id not in party.active_drifter_ids:
            return RunEventResult(RunEventStatus.INVALID_TARGET, game_state)

        run_id = party.active_run_id
        event_key = _event_key(
            run_id,
            node_id,
            "discovery_search",
            floor_id=source_floor_id,
        )
        existing = party.run_event(event_key)
        if existing is not None:
            result = existing["result"]
            if result["source_id"] != source.source_id:
                raise ValueError("search event key was reused for another source")
            if result["searcher_drifter_id"] != searcher_drifter_id:
                raise ValueError("search event key was reused with another searcher")
            return RunEventResult(
                RunEventStatus.ALREADY_RESOLVED,
                game_state,
                found=result["found"],
                source_id=result["source_id"],
                effective_chance_bps=result["effective_chance_bps"],
                roll=result["roll"],
            )
        if (
            source.source_id in game_state.world_state.discovered_permanent_discovery_sources
            or source.source_id in game_state.world_state.permanent_discovery_claims
        ):
            return RunEventResult(
                RunEventStatus.ALREADY_FOUND,
                game_state,
                source_id=source.source_id,
            )

        searcher = game_state.member_for_drifter_id(searcher_drifter_id)
        intuition_bonus = discovery_bonus_bps_from_intuition(
            searcher.effective_stat("intuition")
        )
        chance = min(
            10000,
            source.search_chance_bps
            + source.search_chance_bps * intuition_bonus // 10000,
        )
        roll = self._rng.randint(1, 10000)
        found = roll <= chance
        candidate = game_state.clone()
        candidate_party = candidate.party_state
        if found:
            candidate.world_state.discover_permanent_discovery_source(
                source.source_id
            )
        candidate_party.record_run_event(
            _event_record(
                event_key=event_key,
                run_id=run_id,
                node_id=node_id,
                kind="discovery_search",
                position=None,
                result={
                    "source_id": source.source_id,
                    "searcher_drifter_id": searcher_drifter_id,
                    "effective_chance_bps": chance,
                    "roll": roll,
                    "found": found,
                },
                floor_id=source_floor_id,
            )
        )
        status, committed = self._commit(candidate)
        if status is not RunEventStatus.RESOLVED:
            return RunEventResult(status, game_state)
        return RunEventResult(
            RunEventStatus.RESOLVED,
            committed,
            found=found,
            source_id=source.source_id,
            effective_chance_bps=chance,
            roll=roll,
        )

    def resolve_armor_reward(
        self,
        game_state,
        *,
        node_id,
        template_id,
        source_id,
        instance_id_factory=uuid4,
    ):
        _validate_game_and_node(game_state, node_id)
        if not callable(instance_id_factory):
            raise TypeError("instance_id_factory must be callable")
        party = game_state.party_state
        floor_id = party.active_run_floor_id
        run_id = party.active_run_id
        floor_number = 2 if floor_id == "floor_two" else None
        if party.phase is not DungeonPhase.OUTING or run_id is None or floor_number is None:
            return RunEventResult(RunEventStatus.INVALID_TARGET, game_state)
        node = get_route_node_spec(node_id)
        if node.kind not in {RouteNodeKind.COMBAT, RouteNodeKind.BOSS}:
            return RunEventResult(RunEventStatus.INVALID_TARGET, game_state)

        event_key = _event_key(run_id, node_id, "armor_reward", floor_id=floor_id)
        existing = party.run_event(event_key)
        if existing is not None:
            result = existing["result"]
            if (
                result["template_id"] != template_id
                or result["source_id"] != source_id
            ):
                raise ValueError("armor reward event key was reused with different inputs")
            instance_snapshot = result["instance"]
            instance_id = instance_snapshot["instance_id"]
            instance = party.equipment_instance(instance_id)
            current_snapshot = instance.snapshot()
            expected_snapshot = dict(instance_snapshot)
            # The event keeps its acquisition-time state after a safe Rest secures gear.
            expected_snapshot["secured"] = current_snapshot["secured"]
            if current_snapshot != expected_snapshot:
                raise ValueError("armor reward event disagrees with its owned instance")
            return RunEventResult(
                RunEventStatus.ALREADY_RESOLVED,
                game_state,
                equipment_instance_id=instance_id,
            )

        instance_id = instance_id_factory()
        if isinstance(instance_id, UUID):
            instance_id = str(instance_id)
        item = ArmorGenerationService(rng=self._rng).generate(
            template_id=template_id,
            floor=floor_number,
            source_id=source_id,
            instance_id=instance_id,
            secured=False,
        )
        candidate = game_state.clone()
        candidate_party = candidate.party_state
        candidate_party.add_equipment_instance(item)
        candidate_party.record_run_event(
            _event_record(
                event_key=event_key,
                run_id=run_id,
                node_id=node_id,
                kind="armor_reward",
                position=None,
                result={
                    "template_id": template_id,
                    "floor": floor_number,
                    "source_id": source_id,
                    "instance": item.snapshot(),
                },
                floor_id=floor_id,
            )
        )
        status, committed = self._commit(candidate)
        if status is not RunEventStatus.RESOLVED:
            return RunEventResult(status, game_state)
        return RunEventResult(
            RunEventStatus.RESOLVED,
            committed,
            equipment_instance_id=item.instance_id,
        )

    def _commit(self, candidate):
        try:
            result = self._save_port.save(candidate)
        except (OSError, SavePortError, TypeError, ValueError):
            result = None
        if result is None or result.status is not SaveLoadStatus.SAVED:
            return RunEventStatus.SAVE_FAILED, None
        return RunEventStatus.RESOLVED, candidate


def _validate_game_and_node(game_state, node_id):
    if not isinstance(game_state, GameState):
        raise TypeError("game_state must be a GameState")
    if not isinstance(node_id, str) or _EVENT_PART_PATTERN.fullmatch(node_id) is None:
        raise ValueError("node_id must be a lowercase authored ID")


def _validate_drop_tables(enemy_drop_tables):
    if not isinstance(enemy_drop_tables, (tuple, list)):
        raise TypeError("enemy_drop_tables must be a sequence")
    tables = tuple(enemy_drop_tables)
    for table in tables:
        if not isinstance(table, (tuple, list)):
            raise TypeError("each enemy drop table must be a sequence")
        if any(not isinstance(drop, ItemDropSpec) for drop in table):
            raise TypeError("drop tables must contain ItemDropSpec values")
    return tuple(tuple(table) for table in tables)


def _positive_item_stacks(items):
    return {item_id: quantity for item_id, quantity in items.items() if quantity > 0}


def _event_key(run_id, node_id, kind, position=None, *, floor_id="floor_two"):
    key = f"{floor_id}:{run_id}:{node_id}:{kind}"
    if position is not None:
        key += f":{position}"
    return key


def _event_record(
    *,
    event_key,
    run_id,
    node_id,
    kind,
    position,
    result,
    floor_id="floor_two",
):
    return {
        "event_key": event_key,
        "run_id": run_id,
        "floor_id": floor_id,
        "node_id": node_id,
        "kind": kind,
        "position": position,
        "result": result,
    }


def _nonnegative(name, value):
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{name} must be an integer")
    if value < 0:
        raise ValueError(f"{name} must not be negative")
    return value


__all__ = ["RunEventResult", "RunEventService", "RunEventStatus"]
