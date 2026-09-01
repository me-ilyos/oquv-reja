"""Builds oquv_dastur.docx from code. Run manually after changing layout:

python -m plans.dastur.build_template
"""

from pathlib import Path

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.oxml.ns import qn
from docx.shared import Cm, Mm, Pt
from docxtpl import DocxTemplate

from plans.dastur.table_helpers import CellSpec, RowSpec, build_table_from_spec
from plans.dastur.template_text import TASDIQLAYMAN_BOX

OUTPUT_PATH = Path(__file__).resolve().parent / "oquv_dastur.docx"

TABLE0_COL_WIDTHS = [5495, 4081]

EXPECTED_TOP_LEVEL_VARS = {
    "university",
    "kafedra",
    "kafedra_council",
    "major",
    "education_form",
    "year",
    "course",
    "academic_years_str",
    "semesters_str",
    "credits_str",
    "weekly_hours_str",
    "plan_number",
    "total_hours",
    "classroom_total",
    "hours",
    "lectures",
    "practicals",
    "labs",
    "seminars",
}


def _set_page_setup(document: Document) -> None:
    section = document.sections[0]
    section.page_width = Mm(210)
    section.page_height = Mm(297)
    section.top_margin = Cm(2)
    section.bottom_margin = Cm(2.5)
    section.left_margin = Cm(2)
    section.right_margin = Cm(2)


def _set_rfonts(font, name: str) -> None:
    font.name = name
    rpr = font.element.get_or_add_rPr()
    rfonts = rpr.find(qn("w:rFonts"))
    if rfonts is None:
        rfonts = rpr.makeelement(qn("w:rFonts"), {})
        rpr.insert(0, rfonts)
    rfonts.set(qn("w:eastAsia"), name)
    rfonts.set(qn("w:cs"), name)


def _register_styles(document: Document) -> None:
    normal = document.styles["Normal"]
    normal.font.size = Pt(14)
    _set_rfonts(normal.font, "Times New Roman")
    normal.paragraph_format.line_spacing = 1.0

    styles = document.styles
    centered = styles.add_style("DasturCentered", WD_STYLE_TYPE.PARAGRAPH)
    centered.base_style = normal
    centered.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    heading = styles.add_style("DasturHeading", WD_STYLE_TYPE.PARAGRAPH)
    heading.base_style = normal
    heading.font.bold = True
    heading.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.CENTER

    italic = styles.add_style("DasturItalic", WD_STYLE_TYPE.PARAGRAPH)
    italic.base_style = normal
    italic.font.italic = True

    justify = styles.add_style("DasturJustify", WD_STYLE_TYPE.PARAGRAPH)
    justify.base_style = normal
    justify.paragraph_format.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY


def _add_run_paragraph(
    document: Document, runs: list[tuple[str, bool]], *, align, style=None
):
    """Adds a paragraph made of (text, bold) run pairs — used for cover-page
    lines that mix a bold label with a plain Jinja tag in one paragraph."""
    paragraph = document.add_paragraph(style=style)
    paragraph.alignment = align
    for text, bold in runs:
        run = paragraph.add_run(text)
        run.bold = bold
    return paragraph


def _add_bold_line(document: Document, text: str) -> None:
    paragraph = document.add_paragraph()
    run = paragraph.add_run(text)
    run.bold = True


def _build_approval_table(document: Document) -> None:
    rows = [RowSpec([CellSpec(""), CellSpec(TASDIQLAYMAN_BOX, align="left")])]
    build_table_from_spec(document, rows, TABLE0_COL_WIDTHS)


def _build_cover_page_title(document: Document) -> None:
    document.add_paragraph("TURAN INTERNATIONAL UNIVERSITY", style="DasturHeading")
    document.add_paragraph()
    _build_approval_table(document)
    document.add_paragraph()
    document.add_paragraph()

    _add_run_paragraph(
        document,
        [("{{ course.name|upper }}", True)],
        align=WD_ALIGN_PARAGRAPH.CENTER,
    )
    document.add_paragraph("FANINING O‘QUV DASTURI", style="DasturHeading")
    _add_run_paragraph(
        document,
        [("({{ education_form }} ta'lim uchun)", True)],
        align=WD_ALIGN_PARAGRAPH.CENTER,
        style="DasturItalic",
    )
    document.add_paragraph(style="DasturCentered")


def _build_cover_page_major_and_signoff(document: Document) -> None:
    _add_run_paragraph(
        document,
        [("Bilim sohasi:", True), ("  {{ major.bilim_sohasi }}", False)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    _add_run_paragraph(
        document,
        [("Ta’lim sohasi:", True), ("  {{ major.talim_sohasi }}", False)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    _add_run_paragraph(
        document,
        [("Ta’lim yo‘nalishi:", True), ("  {{ major.talim_yonalishi }}", False)],
        align=WD_ALIGN_PARAGRAPH.JUSTIFY,
    )
    for _ in range(5):
        document.add_paragraph(style="DasturCentered")

    _add_run_paragraph(
        document, [("Namangan – {{ year }}", True)], align=WD_ALIGN_PARAGRAPH.CENTER
    )
    document.add_paragraph(
        "Mazkur o‘quv dasturi {{ university }} {{ kafedra }} kafedrasi tomonidan "
        "taqdim etilgan (kafedraning {{ kafedra_council.year }}-yil"
        "{{ kafedra_council.date }}-sonli yig‘ilish bayoni).",
        style="DasturJustify",
    )
    _add_bold_line(document, "Tuzuvchi:")
    document.add_paragraph()
    _add_bold_line(document, "Taqrizchilar:")
    document.add_paragraph()
    document.add_paragraph()


def _build_cover_page(document: Document) -> None:
    _build_cover_page_title(document)
    _build_cover_page_major_and_signoff(document)


def _check_template_variables(path: Path) -> None:
    template = DocxTemplate(path)
    found = template.get_undeclared_template_variables()
    missing = EXPECTED_TOP_LEVEL_VARS - found
    unexpected = found - EXPECTED_TOP_LEVEL_VARS
    if missing:
        raise ValueError(f"Template is missing expected variables: {missing}")
    if unexpected:
        raise ValueError(f"Template has unexpected undeclared variables: {unexpected}")


def build() -> Document:
    document = Document()
    _set_page_setup(document)
    _register_styles(document)
    _build_cover_page(document)
    return document


def main() -> None:
    document = build()
    document.save(OUTPUT_PATH)
    _check_template_variables(OUTPUT_PATH)
    print(f"Wrote {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
