"""Immutable authored recruitment event specifications."""

from dataclasses import dataclass

from app.content.route_spec import validate_content_id


@dataclass(frozen=True)
class RecruitmentEventSpec:
    event_id: str
    route_id: str
    route_node_id: str
    candidate_drifter_ids: tuple[str, ...]
    cost: int

    def __post_init__(self):
        for name in ("event_id", "route_id", "route_node_id"):
            object.__setattr__(
                self,
                name,
                validate_content_id(name, getattr(self, name)),
            )
        if not isinstance(self.candidate_drifter_ids, tuple):
            raise TypeError("candidate_drifter_ids must be a tuple")
        candidates = tuple(
            validate_content_id("candidate Drifter ID", drifter_id)
            for drifter_id in self.candidate_drifter_ids
        )
        if not candidates:
            raise ValueError("a recruitment event must offer at least one Drifter")
        if len(candidates) != len(set(candidates)):
            raise ValueError("recruitment candidate IDs must be unique")
        object.__setattr__(self, "candidate_drifter_ids", candidates)
        if isinstance(self.cost, bool) or not isinstance(self.cost, int):
            raise TypeError("recruitment cost must be an integer")
        if self.cost < 0:
            raise ValueError("recruitment cost must not be negative")


__all__ = ["RecruitmentEventSpec"]
