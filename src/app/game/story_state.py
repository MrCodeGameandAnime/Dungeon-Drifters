"""Persistent story state for one active game session."""

from app.snapshot import to_plain_value


class StoryState:
    def __init__(self, current_chapter=None, current_scene=None, current_location=None):
        self.current_chapter = current_chapter
        self.current_scene = current_scene
        self.current_location = current_location
        self._story_flags = []
        self._completed_events = []
        self._player_decisions = {}

    @property
    def story_flags(self):
        return tuple(self._story_flags)

    @property
    def completed_events(self):
        return tuple(self._completed_events)

    @property
    def player_decisions(self):
        return dict(self._player_decisions)

    def add_story_flag(self, flag):
        if flag not in self._story_flags:
            self._story_flags.append(flag)

    def complete_event(self, event):
        if event not in self._completed_events:
            self._completed_events.append(event)

    def record_decision(self, key, value):
        self._player_decisions[key] = value

    def snapshot(self):
        return to_plain_value(
            {
                "current_chapter": self.current_chapter,
                "current_scene": self.current_scene,
                "current_location": self.current_location,
                "story_flags": list(self.story_flags),
                "completed_events": list(self.completed_events),
                "player_decisions": self.player_decisions,
            },
            "story",
        )
