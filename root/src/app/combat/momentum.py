"""Encounter-scoped shared battlefield control state."""


class MomentumState:
    MIN_POSITION = 0
    NEUTRAL_POSITION = 5
    MAX_POSITION = 10

    def __init__(self):
        self._position = self.NEUTRAL_POSITION

    @property
    def position(self):
        return self._position

    def advantage_for(self, is_enemy_faction):
        if not isinstance(is_enemy_faction, bool):
            raise TypeError("faction identity must be a boolean")
        if is_enemy_faction:
            return max(0, self.NEUTRAL_POSITION - self._position)
        return max(0, self._position - self.NEUTRAL_POSITION)

    def critical_bonus_percent_points(self, is_enemy_faction):
        return self.advantage_for(is_enemy_faction) * 2

    def outgoing_damage_bonus_percent(self, is_enemy_faction):
        return self._dominance_bonus_percent(is_enemy_faction)

    def incoming_mitigation_percent(self, is_enemy_faction):
        return self._dominance_bonus_percent(is_enemy_faction)

    def shift(self, delta):
        if isinstance(delta, bool) or not isinstance(delta, int):
            raise TypeError("momentum shift must be an integer")

        self._position = min(
            self.MAX_POSITION,
            max(self.MIN_POSITION, self._position + delta),
        )
        return self._position

    def reset(self):
        self._position = self.NEUTRAL_POSITION
        return self._position

    def _dominance_bonus_percent(self, is_enemy_faction):
        advantage = self.advantage_for(is_enemy_faction)
        if advantage == 5:
            return 10
        if advantage >= 3:
            return 5
        return 0
