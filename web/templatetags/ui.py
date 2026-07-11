"""Small presentation filters for the web UI."""

from django import template

register = template.Library()


@register.filter
def bosh_harflar(nomi: str) -> str:
    """Avatar initials: first letters of up to two words, apostrophes stripped."""
    sozlar = str(nomi).replace("'", "").replace("ʼ", "").split()
    return "".join(soz[0].upper() for soz in sozlar[:2])


@register.filter
def foiz(qism: int | None, jami: int | None) -> int:
    """Integer percentage of qism/jami, clamped to 0..100; 0 when unknown."""
    if not qism or not jami:
        return 0
    return min(100, round(100 * qism / jami))
