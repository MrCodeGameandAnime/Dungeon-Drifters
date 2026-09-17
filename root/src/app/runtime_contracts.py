"""Small shared helpers for runtime structural contracts."""


def has_required_members(value, member_names, callable_member_names=()):
    if value is None:
        return False

    callable_names = set(callable_member_names)
    for name in member_names:
        try:
            member = getattr(value, name)
        except Exception:
            return False
        if name in callable_names and not callable(member):
            return False
    return True
