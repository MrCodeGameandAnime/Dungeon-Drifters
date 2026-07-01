"""Plain-value helpers for in-memory state inspection."""

import math


STATE_SCHEMA_VERSION = 3


def to_plain_value(value, path="snapshot"):
    if value is None or isinstance(value, (str, bool, int)):
        return value

    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError(f"{path} contains a non-finite float")
        return value

    if isinstance(value, tuple):
        return [
            to_plain_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]

    if isinstance(value, list):
        return [
            to_plain_value(item, f"{path}[{index}]")
            for index, item in enumerate(value)
        ]

    if isinstance(value, dict):
        plain = {}
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} contains a non-string dictionary key: {key!r}")
            plain[key] = to_plain_value(item, f"{path}.{key}")
        return plain

    raise TypeError(f"{path} contains unsupported value type: {type(value).__name__}")


def validate_plain_value(value, path="snapshot"):
    if value is None or isinstance(value, (str, bool, int)):
        return True

    if isinstance(value, float):
        if not math.isfinite(value):
            raise TypeError(f"{path} contains a non-finite float")
        return True

    if isinstance(value, list):
        for index, item in enumerate(value):
            validate_plain_value(item, f"{path}[{index}]")
        return True

    if isinstance(value, dict):
        for key, item in value.items():
            if not isinstance(key, str):
                raise TypeError(f"{path} contains a non-string dictionary key: {key!r}")
            validate_plain_value(item, f"{path}.{key}")
        return True

    if isinstance(value, tuple):
        raise TypeError(f"{path} contains unsupported value type: tuple")

    raise TypeError(f"{path} contains unsupported value type: {type(value).__name__}")
