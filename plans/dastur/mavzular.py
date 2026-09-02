"""Empty topic rows for the o'quv dastur's per-type mashg'ulot tables.

Row count is fully determined by the hour total — each topic occupies a
fixed number of academic hours in the standard form, so the teacher only
fills in titles.
"""

from dataclasses import dataclass

SOAT_MAVZUDA = 2
SOAT_MUSTAQIL_TOPSHIRIQDA = 4


@dataclass(frozen=True)
class Mavzu:
    code: str
    title: str
    hours: int


@dataclass(frozen=True)
class Natija:
    code: str
    text: str


def bosh_mavzular(
    soat: int, prefiks: str, *, soat_mavzuda: int = SOAT_MAVZUDA
) -> list[Mavzu]:
    """`soat // soat_mavzuda` blank rows numbered `{prefiks}1`, `{prefiks}2`,
    ... A trailing short row absorbs a leftover remainder; no rows below
    zero. `soat_mavzuda` differs for section 5 (2h/topic) vs section 6's
    self-study tasks (4h/task, per the reference document)."""
    if soat <= 0:
        return []
    to_liq, qoldiq = divmod(soat, soat_mavzuda)
    mavzular = [
        Mavzu(code=f"{prefiks}{i}", title="", hours=soat_mavzuda)
        for i in range(1, to_liq + 1)
    ]
    if qoldiq:
        mavzular.append(Mavzu(code=f"{prefiks}{to_liq + 1}", title="", hours=qoldiq))
    return mavzular
