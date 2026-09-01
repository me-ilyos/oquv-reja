"""Row data for Table 1 — the 58-row main content table (sections 1-6)."""

from plans.dastur.table_helpers import CellSpec, RowSpec, RunSpec

TABLE1_COL_WIDTHS = [715, 184, 958, 997, 997, 997, 997, 1243, 1240, 336, 1268]


def _label_tag_cell(
    label: str, tag: str, *, span: int = 1, shaded: bool = True
) -> CellSpec:
    return CellSpec(
        runs=(RunSpec(label, bold=True), RunSpec(tag)),
        align="center",
        span=span,
        shaded=shaded,
    )


def _header_cell(text: str, *, span: int = 1, shaded: bool = True) -> CellSpec:
    return CellSpec(text=text, bold=True, align="center", span=span, shaded=shaded)


def _section1_rows() -> list[RowSpec]:
    return [
        RowSpec(
            [
                _header_cell("1.", span=2),
                _header_cell("Fan ma’lumotlari", span=8),
            ]
        ),
        RowSpec(
            [
                _label_tag_cell("Fan/modul kodi", "{{ course.code }}", span=3),
                _label_tag_cell("O‘quv yili", "{{ academic_years_str }}"),
                _label_tag_cell("Semestr", "{{ semesters_str }}", span=3),
                _label_tag_cell("ECTS - Kreditlar", "{{ credits_str }}", span=3),
            ]
        ),
        RowSpec(
            [
                _label_tag_cell("Fan/modul turi", "{{ course.module_type }}", span=3),
                CellSpec(
                    runs=(RunSpec("Ta'lim tili", bold=True),),
                    align="center",
                    shaded=True,
                ),
                _label_tag_cell(
                    "O‘quv rejadagi tartib raqami", "{{ plan_number }}", span=3
                ),
                _label_tag_cell(
                    "Haftadagi dars soatlari", "{{ weekly_hours_str }}", span=3
                ),
            ]
        ),
        *_section1_hours_rows(),
    ]


def _hours_header_row() -> RowSpec:
    return RowSpec(
        [
            CellSpec(
                runs=(
                    RunSpec("Fanning nomi", bold=True),
                    RunSpec("{{ course.name }}"),
                ),
                align="center",
                span=3,
                vmerge="restart",
                shaded=True,
            ),
            CellSpec(
                runs=(
                    RunSpec("Jami yuklama", bold=True),
                    RunSpec("(soat)", bold=True),
                ),
                align="center",
                vmerge="restart",
                shaded=True,
            ),
            _header_cell(
                "Auditoriya mashg‘ulotlari jami - {{ classroom_total }} soat, shundan:",
                span=4,
            ),
            CellSpec(
                runs=(
                    RunSpec("Mustaqil ta'lim", bold=True),
                    RunSpec("(soat)", bold=True),
                ),
                align="center",
                vmerge="restart",
                shaded=True,
            ),
            _header_cell("Kurs ishi", span=2),
        ]
    )


def _hours_subheader_row() -> RowSpec:
    return RowSpec(
        [
            CellSpec(vmerge="continue", span=3, shaded=True),
            CellSpec(vmerge="continue", shaded=True),
            _header_cell("Ma'ruza"),
            _header_cell("Amaliy"),
            _header_cell("Laboratoriya"),
            _header_cell("Seminar"),
            CellSpec(vmerge="continue", shaded=True),
            _header_cell("", span=2),
        ]
    )


def _hours_value_row() -> RowSpec:
    return RowSpec(
        [
            CellSpec(vmerge="continue", span=3),
            CellSpec(jinja_run="{{ total_hours }}", align="center"),
            CellSpec(jinja_run="{{ hours.lecture }}", align="center"),
            CellSpec(jinja_run="{{ hours.practice }}", align="center"),
            CellSpec(jinja_run="{{ hours.lab }}", align="center"),
            CellSpec(jinja_run="{{ hours.seminar }}", align="center"),
            CellSpec(jinja_run="{{ hours.self_study }}", align="center"),
            CellSpec(jinja_run="{{ hours.coursework }}", align="center", span=2),
        ]
    )


def _section1_hours_rows() -> list[RowSpec]:
    return [_hours_header_row(), _hours_subheader_row(), _hours_value_row()]


def _section_header_row(number: str, title: str, *, span: int = 8) -> RowSpec:
    return RowSpec([_header_cell(number, span=2), _header_cell(title, span=span)])


def _teacher_fill_row(label: CellSpec) -> RowSpec:
    return RowSpec([label, CellSpec(align="justify", span=9)])


def _section2_rows() -> list[RowSpec]:
    return [
        _section_header_row("2.", "Fanning mazmuni"),
        RowSpec([CellSpec(align="justify", span=10)]),
    ]


def _section3_rows() -> list[RowSpec]:
    return [
        RowSpec(
            [
                _header_cell("3.", span=1),
                _header_cell(
                    "Fanni o‘zlashtirish uchun zarur boshlang‘ich bilimlar", span=9
                ),
            ]
        ),
        _teacher_fill_row(CellSpec(text="1.", align="center")),
        _teacher_fill_row(CellSpec(text="2.", align="center")),
        _teacher_fill_row(CellSpec(align="center")),
    ]


def _subtitle_row(text: str) -> RowSpec:
    return RowSpec([CellSpec(), CellSpec(text=text, bold=True, span=9)])


def _learning_outcomes_block(subtitle: str) -> list[RowSpec]:
    rows = [_subtitle_row(subtitle)]
    for i in range(1, 9):
        rows.append(_teacher_fill_row(CellSpec(text=f"TN{i}", align="center")))
    return rows


def _section4_rows() -> list[RowSpec]:
    return [
        RowSpec(
            [
                _header_cell("4.", span=1),
                _header_cell("Ta'lim natijalari (TN)", span=9),
            ]
        ),
        *_learning_outcomes_block("Kasbiy kompetensiyalar:"),
        *_learning_outcomes_block("Ko‘nikmalar:"),
    ]


def _tag_row(tag: str) -> RowSpec:
    return RowSpec(
        [
            CellSpec(jinja_run=tag),
            _header_cell("", span=8, shaded=False),
            CellSpec(),
        ]
    )


def _lesson_subheader_row(title: str, hours_tag: str) -> RowSpec:
    return RowSpec(
        [
            CellSpec(),
            _header_cell(title, span=8, shaded=False),
            CellSpec(jinja_run=hours_tag, align="center"),
        ]
    )


def _lesson_data_row() -> RowSpec:
    return RowSpec(
        [
            CellSpec(jinja_run="{{ t.code }}", align="center"),
            CellSpec(jinja_run="{{ t.title }}", span=8),
            CellSpec(jinja_run="{{ t.hours }}", align="center"),
        ]
    )


def _lesson_loop_rows(label: str, var_name: str, hours_tag: str) -> list[RowSpec]:
    """The repeated 5-row `{%tr if%}` / `{%tr for%}` / data row / `{%tr
    endfor%}` / `{%tr endif%}` block, reused for lectures/practicals/labs/
    seminars — each conditionally rendered only when that hour type has
    topics."""
    return [
        _lesson_subheader_row(label, hours_tag),
        _tag_row(f"{{%tr if {var_name} %}}"),
        _tag_row(f"{{%tr for t in {var_name} %}}"),
        _lesson_data_row(),
        _tag_row("{%tr endfor %}"),
        _tag_row("{%tr endif %}"),
    ]


def _blank_row() -> RowSpec:
    return RowSpec([CellSpec(), _header_cell("", span=8, shaded=False), CellSpec()])


def _section5_rows() -> list[RowSpec]:
    return [
        RowSpec(
            [
                _header_cell("5.", span=1),
                _header_cell("Fan mazmuni va mashg‘ulotlar shakli:", span=8),
                _header_cell("Soat"),
            ]
        ),
        *_lesson_loop_rows("Ma'ruza (M)", "lectures", "{{ hours.lecture }}"),
        _blank_row(),  # spacing quirk in the original template; row count is pinned
        *_lesson_loop_rows("Amaliy (A)", "practicals", "{{ hours.practice }}"),
        *_lesson_loop_rows("Laboratoriya (L)", "labs", "{{ hours.lab }}"),
        *_lesson_loop_rows("Seminar (S)", "seminars", "{{ hours.seminar }}"),
    ]


def _section6_rows() -> list[RowSpec]:
    return [
        RowSpec(
            [
                _header_cell("6.", span=1, shaded=True),
                _header_cell("Mustaqil ta'lim topshiriqlari*", span=8, shaded=True),
                CellSpec(
                    jinja_run="{{ hours.self_study }}", align="center", shaded=True
                ),
            ]
        ),
    ]


def table1_rows() -> list[RowSpec]:
    return [
        *_section1_rows(),
        *_section2_rows(),
        *_section3_rows(),
        *_section4_rows(),
        *_section5_rows(),
        *_section6_rows(),
    ]
