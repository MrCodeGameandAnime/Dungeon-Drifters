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
