"""Persistent story state for one active game session."""

from enum import StrEnum

from app.content.region_progression_spec import M8_KNOWLEDGE_FACT_IDS
from app.snapshot import to_plain_value


class KnowledgeStatus(StrEnum):
    UNKNOWN = "unknown"
    RUMORED = "rumored"
    CONFIRMED = "confirmed"


_KNOWLEDGE_RANK = {
    KnowledgeStatus.UNKNOWN: 0,
    KnowledgeStatus.RUMORED: 1,
    KnowledgeStatus.CONFIRMED: 2,
}


class StoryState:
    def __init__(self, current_chapter=None, current_scene=None, current_location=None):
        self.current_chapter = current_chapter
        self.current_scene = current_scene
        self.current_location = current_location
        self._story_flags = []
        self._completed_events = []
        self._player_decisions = {}
        self._knowledge_facts = {}

    @property
    def story_flags(self):
        return tuple(self._story_flags)

    @property
    def completed_events(self):
        return tuple(self._completed_events)

    @property
    def player_decisions(self):
        return dict(self._player_decisions)

    @property
    def knowledge_facts(self):
        return dict(self._knowledge_facts)

    def knowledge_status(self, fact_id):
        self._validate_fact_id(fact_id)
        return KnowledgeStatus(
            self._knowledge_facts.get(fact_id, KnowledgeStatus.UNKNOWN.value)
        )

    def reveal_knowledge_fact(self, fact_id, status):
        self._validate_fact_id(fact_id)
        try:
            status = KnowledgeStatus(status)
        except (TypeError, ValueError) as error:
            raise ValueError("knowledge status is invalid") from error
        current = self.knowledge_status(fact_id)
        if _KNOWLEDGE_RANK[status] <= _KNOWLEDGE_RANK[current]:
            return False
        if status is not KnowledgeStatus.UNKNOWN:
            self._knowledge_facts[fact_id] = status.value
        return True

    @staticmethod
    def _validate_fact_id(fact_id):
        if not isinstance(fact_id, str) or fact_id not in M8_KNOWLEDGE_FACT_IDS:
            raise ValueError(f"unknown knowledge fact: {fact_id}")

    def add_story_flag(self, flag):
        if flag not in self._story_flags:
            self._story_flags.append(flag)

    def complete_event(self, event):
        if event not in self._completed_events:
            self._completed_events.append(event)

    def record_decision(self, key, value):
        self._player_decisions[key] = value

    @classmethod
    def from_snapshot(cls, snapshot):
        state = cls(
            current_chapter=snapshot["current_chapter"],
            current_scene=snapshot["current_scene"],
            current_location=snapshot["current_location"],
        )
        state._story_flags = list(snapshot["story_flags"])
        state._completed_events = list(snapshot["completed_events"])
        state._player_decisions = dict(snapshot["player_decisions"])
        raw_facts = snapshot["knowledge_facts"]
        if not isinstance(raw_facts, dict):
            raise TypeError("knowledge_facts must be a mapping")
        for fact_id, status in raw_facts.items():
            state.reveal_knowledge_fact(fact_id, status)
        return state

    def snapshot(self):
        return to_plain_value(
            {
                "current_chapter": self.current_chapter,
                "current_scene": self.current_scene,
                "current_location": self.current_location,
                "story_flags": list(self.story_flags),
                "completed_events": list(self.completed_events),
                "player_decisions": self.player_decisions,
                "knowledge_facts": self.knowledge_facts,
            },
            "story",
        )
