"""Row data for Table 2 — the 17-row references/footer table (sections 7-10)."""

from plans.dastur.table_helpers import CellSpec, ParagraphSpec, RowSpec
from plans.dastur.template_text import (
    ASOSIY_ADABIYOTLAR,
    AXBOROT_MANBALARI,
    CREDIT_REQUIREMENTS,
    GRADING_POLICY_PARAGRAPHS,
    QOSHIMCHA_ADABIYOTLAR,
    TEACHING_METHODS_BULLETS,
)

TABLE2_COL_WIDTHS = [715, 9076]


def _numbered_header_row(number: str, title: str) -> RowSpec:
    return RowSpec([CellSpec(text=number, bold=True), CellSpec(text=title, bold=True)])


def _shaded_header_row(title: str) -> RowSpec:
    return RowSpec([CellSpec(text=title, bold=True, span=2, shaded=True)])


def _teaching_methods_row() -> RowSpec:
    paragraphs = tuple(
        ParagraphSpec(text=line, align="left") for line in TEACHING_METHODS_BULLETS
    )
    return RowSpec([CellSpec(paragraphs=paragraphs, span=2)])


def _section7_rows() -> list[RowSpec]:
    return [
        _numbered_header_row("7.", "Ta’lim texnologiyalari va metodlari"),
        _teaching_methods_row(),
    ]


def _section8_rows() -> list[RowSpec]:
    return [
        _numbered_header_row(
            "8.", "Talabalar tomonidan kreditlarni olish uchun talablar"
        ),
        RowSpec([CellSpec(text=CREDIT_REQUIREMENTS, span=2, align="justify")]),
    ]


def _grading_policy_row() -> RowSpec:
    paragraphs = tuple(
        ParagraphSpec(text=text, bold=bold, align=align)
        for text, bold, align in GRADING_POLICY_PARAGRAPHS
    )
    return RowSpec([CellSpec(paragraphs=paragraphs, span=2)])


def _section9_rows() -> list[RowSpec]:
    return [
        _numbered_header_row("9.", "Talabalar bilimini baholash mezoni"),
        _grading_policy_row(),
    ]


def _citation_row(number: str, text: str, url: str | None) -> RowSpec:
    """A hyperlinked citation's visible text is written by _add_hyperlink
    after the table exists, so its cell starts with empty text here."""
    return RowSpec([CellSpec(text=number), CellSpec(text="" if url else text)])


def _section10_rows() -> list[RowSpec]:
    return [
        _shaded_header_row("10. Foydalanilgan adabiyotlar"),
        _shaded_header_row("Asosiy adabiyotlar:"),
        *[_citation_row(n, text, url) for n, text, url in ASOSIY_ADABIYOTLAR],
        _shaded_header_row("Qo‘shimcha adabiyotlar:"),
        *[_citation_row(n, text, url) for n, text, url in QOSHIMCHA_ADABIYOTLAR],
        _shaded_header_row("Axborot manbalari:"),
        *[_citation_row(n, text, url) for n, text, url in AXBOROT_MANBALARI],
    ]


def table2_rows() -> list[RowSpec]:
    return [
        *_section7_rows(),
        *_section8_rows(),
        *_section9_rows(),
        *_section10_rows(),
    ]
