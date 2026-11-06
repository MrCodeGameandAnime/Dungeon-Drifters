"""Atomic resolution of Floor II rewards and searchable discoveries."""

import re
from dataclasses import dataclass
from enum import StrEnum

from app.content.enemy_spec import ItemDropSpec
from app.content.catalog import (
    get_permanent_discovery_search_node_id,
    get_permanent_discovery_source,
)
from app.content.permanent_discovery_spec import PermanentDiscoverySource
from app.game.game_state import GameState
from app.game.party_state import DungeonPhase
from app.persistence.save_port_contract import (
    SaveLoadStatus,
    SavePortError,
    is_save_port,
)
from app.player.scaling import discovery_bonus_bps_from_intuition


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
        if party.phase is not DungeonPhase.OUTING or party.floor_two_run_id is None:
            raise ValueError("encounter rewards require an active Floor II run")

        event_key = _event_key(party.floor_two_run_id, node_id, "encounter_rewards")
        existing = party.run_event(event_key)
        if existing is not None:
            result = existing["result"]
            if (
                result["experience"] != experience
                or result["gold"] != gold
                or result["enemy_count"] != len(tables)
            ):
                raise ValueError("encounter event key was reused with different inputs")
            for position, table in enumerate(tables):
                drop_event = party.run_event(result["drop_event_keys"][position])
                if drop_event is None:
                    raise ValueError("encounter event is missing drop evidence")
                recorded_entries = drop_event["result"]["entries"]
                expected_entries = tuple(
                    (drop.item_id, drop.quantity, drop.chance_bps)
                    for drop in table
                )
                actual_entries = tuple(
                    (
                        entry["item_id"],
                        entry["quantity"],
                        entry["chance_bps"],
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
                tuple(sorted(result["items"].items())),
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
                entries.append(
                    {
                        "item_id": drop.item_id,
                        "quantity": drop.quantity,
                        "chance_bps": drop.chance_bps,
                        "roll": roll,
                        "awarded": awarded,
                    }
                )
                if awarded:
                    enemy_items[drop.item_id] = (
                        enemy_items.get(drop.item_id, 0) + drop.quantity
                    )
                    item_totals[drop.item_id] = (
                        item_totals.get(drop.item_id, 0) + drop.quantity
                    )
            drop_key = _event_key(
                party.floor_two_run_id,
                node_id,
                "enemy_drop",
                position,
            )
            drop_event = _event_record(
                event_key=drop_key,
                run_id=party.floor_two_run_id,
                node_id=node_id,
                kind="enemy_drop",
                position=position,
                result={"entries": entries, "items": enemy_items},
            )
            candidate_party.record_run_event(drop_event)
            all_drop_events.append(drop_key)

        total_items = _positive_item_stacks(item_totals)
        candidate_party.add_floor_two_rewards(
            experience=experience,
            gold=gold,
            items=total_items,
        )
        candidate_party.record_run_event(
            _event_record(
                event_key=event_key,
                run_id=party.floor_two_run_id,
                node_id=node_id,
                kind="encounter_rewards",
                position=None,
                result={
                    "experience": experience,
                    "gold": gold,
                    "items": total_items,
                    "enemy_count": len(tables),
                    "drop_event_keys": all_drop_events,
                },
            )
        )
        status, committed = self._commit(candidate)
        if status is not RunEventStatus.RESOLVED:
            return RunEventResult(status, game_state)
        return RunEventResult(
            RunEventStatus.RESOLVED,
            committed,
            tuple(sorted(total_items.items())),
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
        if party.phase is not DungeonPhase.OUTING or party.floor_two_run_id is None:
            raise ValueError("discovery search requires an active Floor II run")
        if searcher_drifter_id not in party.active_drifter_ids:
            return RunEventResult(RunEventStatus.INVALID_TARGET, game_state)

        event_key = _event_key(party.floor_two_run_id, node_id, "discovery_search")
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
                run_id=party.floor_two_run_id,
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


def _event_key(run_id, node_id, kind, position=None):
    key = f"floor_two:{run_id}:{node_id}:{kind}"
    if position is not None:
        key += f":{position}"
    return key


def _event_record(*, event_key, run_id, node_id, kind, position, result):
    return {
        "event_key": event_key,
        "run_id": run_id,
        "floor_id": "floor_two",
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
