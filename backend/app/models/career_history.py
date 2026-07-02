"""
Career trajectory modeling.

Architectural decision (PRD Sec. 3 - Strict Node Encapsulation):
`_JobNode` is nested INSIDE `CareerHistory` so the linked-list mechanics
(pointers, traversal) are never exposed to the ranking service. Callers only
ever interact with `CareerHistory.add_role(...)` and
`CareerHistory.calculate_velocity()`.

This keeps memory footprint predictable during large batch evaluations
(no shared/global node pool) and prevents accidental external mutation of
the timeline.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Iterator, Optional


class CareerHistory:
    """Encapsulated singly-linked list of a candidate's roles."""

    class _JobNode:
        """Private node type. Not importable/usable outside CareerHistory."""

        __slots__ = ("title", "duration", "is_promotion", "next_node")

        def __init__(self, title: str, duration_years: float, is_promotion: bool):
            self.title = title
            self.duration = duration_years
            self.is_promotion = is_promotion
            self.next_node: Optional["CareerHistory._JobNode"] = None

    def __init__(self) -> None:
        self.head: Optional["CareerHistory._JobNode"] = None
        self.total_years: float = 0.0
        self.promotions: int = 0
        self.role_count: int = 0

    def add_role(self, title: str, duration_years: float, is_promotion: bool) -> None:
        """Prepend a role to the timeline (most recent role added last-in)."""
        if duration_years < 0:
            raise ValueError(f"duration_years must be >= 0, got {duration_years}")
        if not title or not title.strip():
            raise ValueError("title must be a non-empty string")

        new_node = self._JobNode(title.strip(), float(duration_years), bool(is_promotion))
        new_node.next_node = self.head
        self.head = new_node

        self.total_years += duration_years
        self.role_count += 1
        if is_promotion:
            self.promotions += 1

    def titles(self) -> Iterator[str]:
        """Safe read-only traversal exposed for the explainability layer."""
        node = self.head
        while node is not None:
            yield node.title
            node = node.next_node

    def calculate_velocity(self, k_factor: float = 2.0, hop_penalty_threshold: float = 1.0,
                            hop_penalty_value: float = 0.2) -> float:
        """
        Career Velocity (S_velocity):
            S_velocity = min(1.0, (sum(promotions) / sum(years)) * k)

        Anti-bias guard: candidates who job-hop extremely fast
        (avg tenure < hop_penalty_threshold years) get a flat penalty
        subtracted, so velocity does not simply reward frequent title
        changes over genuine promotion/tenure trajectories.
        """
        if self.total_years <= 0 or self.role_count == 0:
            return 0.0

        base_velocity = self.promotions / self.total_years
        normalized_velocity = min(1.0, base_velocity * k_factor)

        avg_tenure = self.total_years / self.role_count
        hop_penalty = hop_penalty_value if avg_tenure < hop_penalty_threshold else 0.0

        return max(0.0, normalized_velocity - hop_penalty)

    def summary(self) -> "CareerHistorySummary":
        return CareerHistorySummary(
            total_years=round(self.total_years, 2),
            promotions=self.promotions,
            role_count=self.role_count,
            avg_tenure_years=round(self.total_years / self.role_count, 2) if self.role_count else 0.0,
            velocity_score=round(self.calculate_velocity(), 4),
            titles=list(self.titles()),
        )


@dataclass
class CareerHistorySummary:
    total_years: float
    promotions: int
    role_count: int
    avg_tenure_years: float
    velocity_score: float
    titles: list = field(default_factory=list)
