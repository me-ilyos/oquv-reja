"""Empty topic rows for the o'quv dastur's per-type mashg'ulot tables.

Row count is fully determined by the hour total — each topic occupies 2
academic hours in the standard form, so the teacher only fills in titles.
"""

from dataclasses import dataclass

SOAT_MAVZUDA = 2


@dataclass(frozen=True)
class Mavzu:
    code: str
    title: str
    hours: int


def bosh_mavzular(soat: int, prefiks: str) -> list[Mavzu]:
    """`soat // 2` blank rows numbered `{prefiks}1`, `{prefiks}2`, ... A
    trailing short row absorbs an odd leftover hour; no rows below zero."""
    if soat <= 0:
        return []
    to_liq, qoldiq = divmod(soat, SOAT_MAVZUDA)
    mavzular = [
        Mavzu(code=f"{prefiks}{i}", title="", hours=SOAT_MAVZUDA)
        for i in range(1, to_liq + 1)
    ]
    if qoldiq:
        mavzular.append(Mavzu(code=f"{prefiks}{to_liq + 1}", title="", hours=qoldiq))
    return mavzular
