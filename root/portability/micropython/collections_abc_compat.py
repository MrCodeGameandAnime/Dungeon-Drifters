"""Small collections.abc boundary for the pinned MicroPython runtime."""

import sys


_installed_module = None
_installed_collections = None
_installed_readonly_mapping = None


class _CollectionsAbcModule:
    _dd_myp8_module = True
    __name__ = "collections.abc"

    def __init__(self, mapping, sequence, native_collections):
        self.Mapping = mapping
        self.Sequence = sequence
        self._native_collections = native_collections


def install(native_collections, readonly_mapping_type):
    """Install and return the qualified collections.abc child module."""
    global _installed_collections
    global _installed_module
    global _installed_readonly_mapping

    if (
        _installed_module is not None
        and _installed_collections is native_collections
        and _installed_readonly_mapping is readonly_mapping_type
    ):
        sys.modules["collections.abc"] = _installed_module
        return _installed_module

    implementation = getattr(getattr(sys, "implementation", None), "name", None)
    if implementation == "micropython":
        mapping = (dict, readonly_mapping_type)
        sequence = (list, tuple)
    else:
        import collections.abc as native_abc

        mapping = native_abc.Mapping
        sequence = native_abc.Sequence

    module = _CollectionsAbcModule(mapping, sequence, native_collections)
    _installed_collections = native_collections
    _installed_module = module
    _installed_readonly_mapping = readonly_mapping_type
    sys.modules["collections.abc"] = module
    return module


__all__ = ["install"]
