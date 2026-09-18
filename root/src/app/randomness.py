"""Portable runtime randomness for Dungeon Drifters gameplay."""

import random as _backend


def _randbelow(limit):
    if limit <= 0:
        raise ValueError("random range must be positive")

    getrandbits = getattr(_backend, "getrandbits", None)
    if not callable(getrandbits):
        raise TypeError("random backend must provide getrandbits")

    bits = 0
    maximum = limit - 1
    while maximum:
        bits += 1
        maximum >>= 1

    if bits == 0:
        return 0

    while True:
        candidate = getrandbits(bits)
        if candidate < limit:
            return candidate


def randint(start, end):
    native = getattr(_backend, "randint", None)
    if callable(native):
        return native(start, end)

    span = end - start + 1
    if span <= 0:
        raise ValueError("empty range for randint")

    return start + _randbelow(span)


def choice(values):
    native = getattr(_backend, "choice", None)
    if callable(native):
        return native(values)

    length = len(values)
    if length == 0:
        raise IndexError("cannot choose from an empty sequence")

    return values[_randbelow(length)]
