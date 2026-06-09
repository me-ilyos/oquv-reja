from models import Course, SelectiveSlot


def _cell(value) -> str:
    """Render a numeric field for Markdown: None becomes an empty cell."""
    return "" if value is None else str(value)


def _row(cells: list[str], suffix: str = "") -> str:
    """Assemble a Markdown table row from cell strings, plus an optional suffix."""
    return "| " + " | ".join(cells) + " |" + suffix


def _breakdown(obj) -> list[str]:
    """The six hour-breakdown cells of a Course/Alternative, or blanks if None."""
    if obj is None:
        return ["", "", "", "", "", ""]
    return [
        _cell(obj.classroom),
        _cell(obj.lecture),
        _cell(obj.practice),
        _cell(obj.lab),
        _cell(obj.seminar),
        _cell(obj.course_proj),
    ]


def build_markdown(
    title: str,
    start_year: str,
    degree: str,
    duration: str,
    edu_type: str,
    core_courses: list[Course],
    selective_slots: list[SelectiveSlot] | None = None,
) -> str:
    all_items = list(core_courses) + list(selective_slots or [])
    active_semesters = sorted(
        {sem for item in all_items for sem in item.semester_credits}
        | {sem for item in all_items for sem in item.semester_weekly_hours}
    )

    lines = [f"# Oquv Reja: {title}", ""]
    if degree:
        lines.append(f"**Akademik daraja:** {degree}")
    if duration:
        lines.append(f"**O'qish muddati:** {duration}")
    if edu_type:
        lines.append(f"**Ta'lim shakli:** {edu_type}")
    if degree or duration or edu_type:
        lines.append("")
    lines.append("## Majburiy Fanlar (Core Courses)")
    lines.append("")

    # Interleaved S{n} (credits) and W{n} (weekly hours) per active semester
    sem_header = "".join(f" S{s} | W{s} |" for s in active_semesters)
    sem_sep = "".join(" --- | --- |" for _ in active_semesters)
    header = (
        "| # | Code | Name | Hours | Credits | Classroom"
        " | Lecture | Practice | Lab | Seminar | Course Proj |" + sem_header
    )
    separator = (
        "|---|------|------|-------|---------|-----------|---------|"
        "----------|-----|---------|-------------|" + sem_sep
    )
    lines.append(header)
    lines.append(separator)

    def sem_cells(item) -> str:
        return "".join(
            f" {_cell(item.semester_credits.get(s))} |"
            f" {_cell(item.semester_weekly_hours.get(s))} |"
            for s in active_semesters
        )

    for course in core_courses:
        cells = [
            course.num,
            course.code,
            course.name,
            _cell(course.hours),
            _cell(course.derived_credits),
            *_breakdown(course),
        ]
        lines.append(_row(cells, sem_cells(course)))

    if selective_slots:
        lines.append("")
        lines.append("## Tanlov Fanlar (Selective Courses)")
        lines.append("")
        lines.append(header)
        lines.append(separator)
        empty_sem = "".join("  |  |" for _ in active_semesters)
        for slot in selective_slots:
            first = slot.alternatives[0] if slot.alternatives else None
            cells = [
                slot.num,
                first.code if first else "",
                first.name if first else "",
                _cell(slot.hours),
                _cell(slot.derived_credits),
                *_breakdown(first),
            ]
            lines.append(_row(cells, sem_cells(slot)))
            for alt in slot.alternatives[1:]:
                cells = ["", alt.code, alt.name, "", "", *_breakdown(alt)]
                lines.append(_row(cells, empty_sem))

    lines.append("")
    if start_year:
        lines.append("---")
        lines.append(f"**O'quv yili:** {start_year}")
        lines.append("")
    return "\n".join(lines)
