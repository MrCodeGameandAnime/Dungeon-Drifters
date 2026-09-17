"""Small MicroPython StrEnum subset required by Dungeon Drifters."""

import builtins


class StrEnum(str):
    pass


_STATE_NAME = "_dd_portable_strenum_state"
_state = getattr(builtins, _STATE_NAME, None)


def _lookup_member(cls, value):
    try:
        return cls.__members__[value]
    except (KeyError, TypeError):
        raise ValueError("%r is not a valid %s" % (value, cls.__name__))


def _finish_enum(cls):
    candidates = []
    for name in tuple(cls.__dict__):
        if not isinstance(name, str):
            continue
        if not name.isupper() or name.startswith("_"):
            continue
        value = getattr(cls, name)
        if not isinstance(value, str):
            raise TypeError(
                "portable StrEnum member %s.%s must be a string"
                % (cls.__name__, name)
            )
        candidates.append((name, value))

    if not candidates:
        raise TypeError(
            "portable StrEnum %s must define at least one member" % cls.__name__
        )

    values = set(value for _, value in candidates)
    if len(values) != len(candidates):
        raise ValueError("portable StrEnum member values must be unique")

    members = {}
    for name, value in candidates:
        # Before lookup is installed, normal str-subclass construction creates
        # the canonical member object on MicroPython and CPython alike.
        member = cls(value)
        member.name = name
        member.value = value
        members[value] = member
        setattr(cls, name, member)

    setattr(cls, "__members__", members)
    setattr(cls, "__new__", _lookup_member)
    return cls


def _install_builder_hook():
    global _state
    if _state is not None:
        _state["base"] = StrEnum
        return

    original = builtins.__build_class__
    state = {"original": original, "base": StrEnum}

    def portable_build_class(function, name, *bases, **kwargs):
        cls = state["original"](function, name, *bases, **kwargs)
        if len(bases) == 1 and bases[0] is state["base"]:
            return _finish_enum(cls)
        return cls

    state["wrapper"] = portable_build_class
    setattr(builtins, _STATE_NAME, state)
    builtins.__build_class__ = portable_build_class
    _state = state


_install_builder_hook()


__all__ = ["StrEnum"]
