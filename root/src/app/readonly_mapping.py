"""Small read-only mapping boundary for authored runtime values."""

try:
    from types import MappingProxyType as _NATIVE_MAPPING_PROXY
except ImportError:
    _NATIVE_MAPPING_PROXY = None


class _ReadonlyMapping:
    def __init__(self, source):
        self._data = dict(source)

    def __getitem__(self, key):
        return self._data[key]

    def __contains__(self, key):
        return key in self._data

    def __iter__(self):
        return iter(self._data)

    def __len__(self):
        return len(self._data)

    def keys(self):
        return self._data.keys()

    def items(self):
        return self._data.items()


def readonly_mapping(source):
    if _NATIVE_MAPPING_PROXY is not None:
        return _NATIVE_MAPPING_PROXY(source)
    return _ReadonlyMapping(source)


__all__ = ["readonly_mapping"]
