"""Typed data model shared between the parser (producer) and formatter/future
serializers (consumers).

Numbers stay `int | None` (parsing concern); rendering to strings lives in the
formatter. These types make the producer↔consumer contract explicit and give
`dataclasses.asdict` a clean future JSON/DB path.
"""

from dataclasses import dataclass, field
from typing import NamedTuple


class ColumnLayout(NamedTuple):
    """0-based column indices for one curriculum sheet, detected dynamically."""

    num: int
    code: int
    name: int
    hours: int
    classroom: int
    lecture: int
    practice: int
    lab: int
    seminar: int
    course_proj: int

    @property
    def breakdown(self) -> tuple[int, int, int, int, int, int]:
        """The six hour-breakdown column indices, in canonical field order."""
        return (
            self.classroom,
            self.lecture,
            self.practice,
            self.lab,
            self.seminar,
            self.course_proj,
        )


@dataclass
class Course:
    """One mandatory (majburiy) course with its full hour breakdown."""

    num: str
    code: str
    name: str
    hours: int | None
    classroom: int
    lecture: int
    practice: int
    lab: int
    seminar: int
    course_proj: int
    semester_credits: dict[int, int] = field(default_factory=dict)
    semester_weekly_hours: dict[int, int] = field(default_factory=dict)

    @property
    def derived_credits(self) -> int | None:
        """Credits implied by total hours (1 credit = 30 hours).

        Duplicated on SelectiveSlot; kept separate so each dataclass stays a
        standalone record with no shared base to reason about.
        """
        return None if self.hours is None else self.hours // 30


@dataclass
class Alternative:
    """One course option offered within a selective slot."""

    code: str
    name: str
    classroom: int
    lecture: int
    practice: int
    lab: int
    seminar: int
    course_proj: int


@dataclass
class SelectiveSlot:
    """One selective (tanlov) slot: shared hours/credits plus its alternatives."""

    num: str
    hours: int | None
    semester_credits: dict[int, int] = field(default_factory=dict)
    semester_weekly_hours: dict[int, int] = field(default_factory=dict)
    alternatives: list[Alternative] = field(default_factory=list)

    @property
    def derived_credits(self) -> int | None:
        """Credits implied by total hours (1 credit = 30 hours)."""
        return None if self.hours is None else self.hours // 30
