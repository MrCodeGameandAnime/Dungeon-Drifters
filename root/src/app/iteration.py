"""Small portable iteration primitives used by the gameplay runtime."""


def first_or_none(values):
    for value in values:
        return value
    return None
