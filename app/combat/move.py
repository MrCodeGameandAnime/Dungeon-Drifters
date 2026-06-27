from dataclasses import dataclass


@dataclass(frozen=True)
class Move:
    name: str
    kind: str
    mana_cost: int
    power: int
    scales_with: str
    accuracy: int
    target: str
    mechanic: str
    description: str
