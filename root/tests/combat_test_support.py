"""Strict, recorded roll sequences shared by mechanic contract tests."""


class RecordedRng:
    def __init__(self, *rolls):
        self.rolls = list(rolls)
        self.calls = []

    def randint(self, start, end):
        self.calls.append((start, end))
        return self.rolls.pop(0)
