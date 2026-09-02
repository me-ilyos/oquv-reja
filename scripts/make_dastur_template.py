"""Build plans/dastur/oquv_dastur.docx from the real reference document.

Run once, and again only if the university reissues the form itself:

    env\\Scripts\\python.exe scripts\\make_dastur_template.py

Opens sources/Kiberxavfsizlik_asoslari_fan_dasturi_ATDT.docx read-only (never
modified) and swaps concrete values for Jinja tags, collapsing repeating rows
into {%tr for %} loops. Keeps every border, merge, and font from the source
byte-for-byte — only text content changes.

After this runs, plans/dastur/oquv_dastur.docx can be opened and tweaked in
Word like any other document (reword a heading, adjust a border); re-run this
script only when the reference document itself changes.
"""

from __future__ import annotations

import copy
import sys
from pathlib import Path

from docx import Document
from docx.table import Table, _Cell
from docx.text.paragraph import Paragraph

ROOT = Path(__file__).resolve().parent.parent
SOURCE = ROOT / "sources" / "Kiberxavfsizlik_asoslari_fan_dasturi_ATDT.docx"
TEMPLATE = ROOT / "plans" / "dastur" / "oquv_dastur.docx"


# --------------------------------------------------------------------------
# low-level helpers
# --------------------------------------------------------------------------


def set_para_text(p: Paragraph, text: str) -> None:
    """Replace a paragraph's text, keeping the first run's formatting.

    Word splits text into many runs (spell-check artefacts), so a naive
    search-and-replace misses tags straddling a run boundary. Collapsing to
    one run sidesteps that entirely — verified against the source document,
    where e.g. "60610100 - 1.19" is three separate runs.
    """
    runs = p.runs
    if not runs:
        p.add_run(text)
        return
    runs[0].text = text
    for r in runs[1:]:
        r._element.getparent().remove(r._element)


def retext_paragraph(p: Paragraph, replacements: list[tuple[str, str]]) -> None:
    """Collapse a mixed paragraph to one run, applying substring replacements
    to its full text first. For paragraphs where only part of the text
    becomes a tag (e.g. the kafedra-attribution sentence) and the paragraph
    otherwise has no stable per-run split to hook onto.
    """
    text = p.text
    for old, new in replacements:
        if old not in text:
            raise LookupError(f"{old!r} not found in paragraph {p.text!r}")
        text = text.replace(old, new)
    set_para_text(p, text)


def body_para(doc: Document, needle: str) -> Paragraph:
    matches = [p for p in doc.paragraphs if needle in p.text]
    if not matches:
        raise LookupError(f"body paragraph not found: {needle!r}")
    if len(matches) > 1:
        raise LookupError(
            f"paragraph text {needle!r} is ambiguous ({len(matches)} hits)"
        )
    return matches[0]


def cell_para(table: Table, row: int, col: int, idx: int = 0) -> Paragraph:
    """1-based row/col on python-docx's expanded grid; idx is 0-based paragraph."""
    return table.rows[row - 1].cells[col - 1].paragraphs[idx]


def set_cell(table: Table, row: int, col: int, text: str, idx: int = 0) -> None:
    set_para_text(cell_para(table, row, col, idx), text)


def visible_cells(row) -> list[_Cell]:
    """A merged row's `.cells` repeats the same _Cell per grid position; this
    returns each backing cell once, in order."""
    seen: set[int] = set()
    cells = []
    for cell in row.cells:
        if id(cell._tc) in seen:
            continue
        seen.add(id(cell._tc))
        cells.append(cell)
    return cells


def find_row(table: Table, needle: str, *, start: int = 1) -> int:
    """1-based index of the first row (at or after `start`) whose visible
    cells contain `needle`. Anchoring edits on content instead of hardcoded
    row numbers keeps each edit function correct regardless of how many rows
    earlier functions already removed."""
    for i in range(start, len(table.rows) + 1):
        if any(needle in c.text for c in visible_cells(table.rows[i - 1])):
            return i
    raise LookupError(f"no row containing {needle!r} at or after row {start}")


def delete_para(p: Paragraph) -> None:
    p._p.getparent().remove(p._p)


def delete_rows(table: Table, first: int, last: int) -> None:
    """Delete 1-based rows first..last inclusive, bottom-up so indices stay valid."""
    for i in range(last, first - 1, -1):
        tr = table.rows[i - 1]._tr
        tr.getparent().remove(tr)


def _tag_row(row, tag: str) -> None:
    """Blank every cell of a control row and put the tag in the first one."""
    for i, cell in enumerate(visible_cells(row)):
        for j, p in enumerate(cell.paragraphs):
            if j == 0:
                set_para_text(p, tag if i == 0 else "")
            else:
                delete_para(p)


def wrap_rows(table: Table, first: int, last: int, opener: str, closer: str) -> None:
    """Put `opener` in a new row before `first` and `closer` after `last`.

    docxtpl deletes a row whose text is a {%tr %} tag, so the cloned
    formatting of these control rows never reaches rendered output.
    """
    tail = copy.deepcopy(table.rows[last - 1]._tr)
    if last == len(table.rows):
        table._tbl.append(tail)
        closer_row = table.rows[-1]
    else:
        table.rows[last]._tr.addprevious(tail)
        closer_row = table.rows[last]
    _tag_row(closer_row, closer)

    head = copy.deepcopy(table.rows[first - 1]._tr)
    table.rows[first - 1]._tr.addprevious(head)
    _tag_row(table.rows[first - 1], opener)


# --------------------------------------------------------------------------
# the edits
# --------------------------------------------------------------------------


def edit_cover(doc: Document) -> None:
    set_para_text(body_para(doc, "KIBERXAVFSIZLIK ASOSLARI"), "{{ course.name|upper }}")
    set_para_text(
        body_para(doc, "kunduzgi ta’lim uchun"), "({{ education_form }} uchun)"
    )
    set_para_text(
        body_para(doc, "Bilim sohasi:"), "Bilim sohasi:\t{{ major.bilim_sohasi }}"
    )
    set_para_text(
        body_para(doc, "Ta’lim sohasi:"), "Ta’lim sohasi:\t{{ major.talim_sohasi }}"
    )
    set_para_text(
        body_para(doc, "Ta’lim yo‘nalishi:"),
        "Ta’lim yo‘nalishi:\t{{ major.talim_yonalishi }}",
    )
    retext_paragraph(
        body_para(doc, "Namangan – 2026"),
        [("Namangan – 2026", "{{ city }} – {{ year }}")],
    )

    kafedra = body_para(doc, "kafedrasi tomonidan taqdim etilgan")
    retext_paragraph(
        kafedra,
        [
            (
                "Turan International University Filologiya kafedrasi tomonidan "
                "taqdim etilgan (kafedraning 2026-yil"
                + "_" * 19
                + "-sonli yig‘ilish bayoni).",
                "{{ university }} {{ kafedra }} kafedrasi tomonidan taqdim etilgan "
                "(kafedraning {{ kafedra_council.year }}-yil "
                "{{ kafedra_council.date }}-sonli yig‘ilish bayoni).",
            )
        ],
    )

    # Approval box: "TASDIQLAYMAN" cell, university name + date fill-ins.
    approval = doc.tables[0].rows[0].cells[1]
    set_para_text(approval.paragraphs[1], "{{ university }}")
    set_para_text(approval.paragraphs[4], "{{ year }}-yil “___” _________")

    # Tuzuvchi/Taqrizchilar: real names in the source, blanked for the teacher.
    set_para_text(body_para(doc, "S.Komilov"), "")
    set_para_text(body_para(doc, "S.Xashimov"), "")


def edit_fan_malumotlari(doc: Document) -> None:
    """Section 1, table[1] rows 1-6. Vertically merged block — scalar edits
    only, no rows added or removed."""
    t = doc.tables[1]
    set_cell(t, 2, 1, "{{ course.code }}", idx=1)
    set_cell(t, 2, 4, "{{ academic_years_str }}", idx=1)
    set_cell(t, 2, 5, "{{ semesters_str }}", idx=1)
    set_cell(t, 2, 8, "{{ credits_str }}", idx=1)
    set_cell(t, 3, 1, "{{ course.module_type }}", idx=1)
    set_cell(t, 3, 4, "{{ language }}", idx=1)
    set_cell(t, 3, 5, "{{ plan_number }}", idx=1)
    set_cell(t, 3, 8, "{{ weekly_hours_str }}", idx=1)
    set_cell(t, 4, 1, "{{ course.name }}", idx=1)

    retext_paragraph(
        cell_para(t, 4, 5),
        [("jami – 72 soat, shundan:", "jami – {{ classroom_total }} soat, shundan:")],
    )

    set_cell(t, 6, 4, "{{ total_hours }}")
    set_cell(t, 6, 5, "{{ hours.lecture }}")
    set_cell(t, 6, 6, "{{ hours.practice }}")
    set_cell(t, 6, 7, "{{ hours.lab }}")
    set_cell(t, 6, 8, "{{ hours.self_study }}")
    set_cell(t, 6, 9, "{{ hours.coursework }}")


def edit_mazmuni(doc: Document) -> None:
    """Section 2: purpose and tasks are two paragraphs in one cell."""
    t = doc.tables[1]
    row = find_row(t, "Fanning maqsadi")
    set_cell(t, row, 1, "{{ purpose }}", idx=0)
    set_cell(t, row, 1, "{{ tasks }}", idx=1)


def _collapse_to_one_row(
    t: Table, header_needle: str, first_item_needle: str, group_size: int
) -> int:
    """Deletes rows 2..group_size of a repeating block (found fresh by
    content, so this is safe to call repeatedly without tracking how earlier
    calls shifted row numbers) and returns the surviving first-item row."""
    header = find_row(t, header_needle)
    item1 = find_row(t, first_item_needle, start=header)
    delete_rows(t, item1 + 1, item1 + group_size - 1)
    return item1


def edit_prerequisites(doc: Document) -> None:
    """Section 3: 3 real prerequisites -> loop."""
    t = doc.tables[1]
    item1 = _collapse_to_one_row(t, "Fanni o‘zlashtirish uchun zarur", "(ATD1308)", 3)
    set_cell(t, item1, 1, "{{ loop.index }}.")
    set_cell(t, item1, 2, "{{ item }}")
    wrap_rows(t, item1, item1, "{%tr for item in prerequisites %}", "{%tr endfor %}")


def edit_outcomes(doc: Document) -> None:
    """Section 4: TN1-5 professional, TN6-10 skills -> one data row + loop
    per group. Each anchor is re-found by content after both collapses run,
    since collapsing the (higher-up) professional block shifts every row
    number below it, including the skills block's."""
    t = doc.tables[1]
    _collapse_to_one_row(t, "Ko‘nikmalar:", "TN6", 5)
    _collapse_to_one_row(t, "Kasbiy kompetensiyalar:", "TN1", 5)

    tn1 = find_row(t, "TN1")
    tn6 = find_row(t, "TN6", start=tn1)
    for row in (tn6, tn1):
        set_cell(t, row, 1, "{{ o.code }}")
        set_cell(t, row, 2, "{{ o.text }}")
    wrap_rows(t, tn6, tn6, "{%tr for o in outcomes.skills %}", "{%tr endfor %}")
    wrap_rows(t, tn1, tn1, "{%tr for o in outcomes.professional %}", "{%tr endfor %}")


def edit_topics(doc: Document) -> None:
    """Section 5: M1-12/A1-12/L1-12 -> one data row + loop per lesson type.
    Collapses run bottom-up (a block only shifts rows below it), but since
    later collapses (A, then M) sit above earlier ones, every anchor is
    re-found by content once all three collapses are done."""
    t = doc.tables[1]
    _collapse_to_one_row(t, "Laboratoriya mashg‘ulot (L)", "L1", 12)
    _collapse_to_one_row(t, "Amaliy mashg‘ulot (A)", "A1", 12)
    _collapse_to_one_row(t, "Ma’ruza (M)", "M1", 12)

    m1 = find_row(t, "M1")
    a1 = find_row(t, "A1", start=m1)
    l1 = find_row(t, "L1", start=a1)
    a_hdr, l_hdr = a1 - 1, l1 - 1

    for row in (l1, a1, m1):
        set_cell(t, row, 1, "{{ t.code }}")
        set_cell(t, row, 2, "{{ t.title }}")
        set_cell(t, row, 10, "{{ t.hours }}")
    set_cell(t, m1 - 1, 10, "{{ hours.lecture }}")
    set_cell(t, a_hdr, 10, "{{ hours.practice }}")
    set_cell(t, l_hdr, 10, "{{ hours.lab }}")
    wrap_rows(t, l1, l1, "{%tr for t in labs %}", "{%tr endfor %}")
    wrap_rows(t, a1, a1, "{%tr for t in practicals %}", "{%tr endfor %}")
    wrap_rows(t, m1, m1, "{%tr for t in lectures %}", "{%tr endfor %}")


def edit_self_study(doc: Document) -> None:
    """Section 6: 27 tasks -> one data row + loop."""
    t = doc.tables[1]
    hdr = find_row(t, "Mustaqil ta’lim topshiriqlari")
    task1 = hdr + 1
    set_cell(t, hdr, 10, "{{ hours.self_study }}")
    delete_rows(t, task1 + 1, len(t.rows))  # tasks 2-27
    set_cell(t, task1, 1, "{{ loop.index }}")
    set_cell(t, task1, 2, "{{ t.title }}")
    set_cell(t, task1, 10, "{{ t.hours }}")
    wrap_rows(t, task1, task1, "{%tr for t in self_study_tasks %}", "{%tr endfor %}")


# --------------------------------------------------------------------------


def main() -> int:
    if not SOURCE.exists():
        print(f"error: {SOURCE} not found", file=sys.stderr)
        return 1

    doc = Document(SOURCE)
    for step in (
        edit_cover,
        edit_fan_malumotlari,
        edit_mazmuni,
        edit_prerequisites,
        edit_outcomes,
        edit_topics,
        edit_self_study,
    ):
        step(doc)
        print(f"  {step.__name__}")

    TEMPLATE.parent.mkdir(parents=True, exist_ok=True)
    doc.save(TEMPLATE)
    print(f"\nwrote {TEMPLATE.relative_to(ROOT)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
