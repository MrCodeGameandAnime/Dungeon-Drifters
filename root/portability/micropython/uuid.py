"""Small UUID subset required by portable profile persistence."""

import os


_HEX_DIGITS = "0123456789abcdefABCDEF"


class UUID:
    __slots__ = ("_hex",)

    def __init__(self, hex):
        if not isinstance(hex, str):
            raise TypeError("UUID input must be a string")
        compact = hex.replace("-", "")
        if len(compact) != 32 or any(char not in _HEX_DIGITS for char in compact):
            raise ValueError("UUID string must contain 32 hexadecimal digits")
        self._hex = compact.lower()

    @property
    def hex(self):
        return self._hex

    @property
    def version(self):
        return int(self._hex[12], 16)

    @property
    def int(self):
        return int(self._hex, 16)

    def __str__(self):
        value = self._hex
        return "%s-%s-%s-%s-%s" % (
            value[:8],
            value[8:12],
            value[12:16],
            value[16:20],
            value[20:],
        )

    def __repr__(self):
        return "UUID('%s')" % self

    def __eq__(self, other):
        return isinstance(other, UUID) and self._hex == other._hex

    def __hash__(self):
        return hash(self._hex)


def uuid4():
    try:
        raw = bytearray(os.urandom(16))
    except (AttributeError, NotImplementedError, OSError):
        import random

        raw = bytearray(random.getrandbits(8) for _ in range(16))
    raw[6] = (raw[6] & 0x0F) | 0x40
    raw[8] = (raw[8] & 0x3F) | 0x80
    return UUID("".join("%02x" % value for value in raw))


__all__ = ["UUID", "uuid4"]
