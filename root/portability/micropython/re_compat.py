"""Small native-regex proxy for the MicroPython fullmatch subset."""


_installed_proxy = None


class _PortablePattern:
    _dd_myp7_pattern = True

    def __init__(self, native_pattern):
        self._native_pattern = native_pattern

    def fullmatch(self, string):
        match = self._native_pattern.match(string)
        if match is None or match.group(0) != string:
            return None
        return match

    def __getattr__(self, name):
        return getattr(self._native_pattern, name)


class _PortableRe:
    _dd_myp7_proxy = True
    __name__ = "re"

    def __init__(self, native_re):
        self._native_re = native_re

    def compile(self, pattern, flags=0):
        if flags:
            raise NotImplementedError(
                "portable re.compile does not support flags"
            )
        return _PortablePattern(self._native_re.compile(pattern))

    def fullmatch(self, pattern, string):
        return self.compile(pattern).fullmatch(string)

    def __getattr__(self, name):
        return getattr(self._native_re, name)


def install(native_re):
    global _installed_proxy

    if isinstance(native_re, _PortableRe):
        return native_re
    if _installed_proxy is not None and _installed_proxy._native_re is native_re:
        return _installed_proxy

    _installed_proxy = _PortableRe(native_re)
    return _installed_proxy


__all__ = ["install"]
