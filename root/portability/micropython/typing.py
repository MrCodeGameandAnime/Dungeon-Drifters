"""Small MicroPython typing subset required by Dungeon Drifters."""


class Protocol:
    pass


def runtime_checkable(cls):
    return cls


class _SubscriptableMarker:
    def __getitem__(self, value):
        return self


class _UnionMarker:
    def __getitem__(self, value):
        if isinstance(value, tuple):
            return value
        return (value,)


TypeAlias = object()
Sequence = _SubscriptableMarker()
Union = _UnionMarker()


__all__ = ["Protocol", "runtime_checkable", "TypeAlias", "Sequence", "Union"]
