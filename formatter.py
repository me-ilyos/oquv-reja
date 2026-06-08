def build_markdown(
    title: str,
    start_year: str,
    degree: str,
    duration: str,
    edu_type: str,
    core_courses: list[dict],
    selective_slots: list[dict] | None = None,
) -> str:
    all_items = list(core_courses) + list(selective_slots or [])
    active_semesters = sorted(
        {sem for item in all_items for sem in item.get("semester_credits", {})}
        | {sem for item in all_items for sem in item.get("semester_weekly_hours", {})}
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
    lines.append(
        "| # | Code | Name | Hours | Credits | Classroom"
        " | Lecture | Practice | Lab | Seminar | Course Proj |" + sem_header
    )
    lines.append(
        f"|---|------|------|-------|---------|-----------|---------|----------|-----|---------|-------------|{sem_sep}"
    )

    for course in core_courses:
        sem_credits = course.get("semester_credits", {})
        sem_weekly = course.get("semester_weekly_hours", {})
        sem_cells = "".join(
            f" {sem_credits.get(s, '')} | {sem_weekly.get(s, '')} |"
            for s in active_semesters
        )
        lines.append(
            f"| {course['num']} | {course['code']} | {course['name']} "
            f"| {course['hours']} | {course['credits']} | {course['classroom']} "
            f"| {course['lecture']} | {course['practice']} | {course['lab']} "
            f"| {course['seminar']} | {course['course_proj']} |{sem_cells}"
        )

    if selective_slots:
        lines.append("")
        lines.append("## Tanlov Fanlar (Selective Courses)")
        lines.append("")
        lines.append(
            "| # | Code | Name | Hours | Credits | Classroom"
            " | Lecture | Practice | Lab | Seminar | Course Proj |" + sem_header
        )
        lines.append(
            f"|---|------|------|-------|---------|-----------|---------|----------|-----|---------|-------------|{sem_sep}"
        )
        for slot in selective_slots:
            sem_credits = slot.get("semester_credits", {})
            sem_weekly = slot.get("semester_weekly_hours", {})
            alts = slot.get("alternatives", [])
            sem_cells = "".join(
                f" {sem_credits.get(s, '')} | {sem_weekly.get(s, '')} |"
                for s in active_semesters
            )
            empty_sem = "".join("  |  |" for _ in active_semesters)
            first = alts[0] if alts else {}
            lines.append(
                f"| {slot['num']} | {first.get('code', '')} | {first.get('name', '')} "
                f"| {slot['hours']} | {slot['credits']} | {first.get('classroom', '')} "
                f"| {first.get('lecture', '')} | {first.get('practice', '')} | {first.get('lab', '')} "
                f"| {first.get('seminar', '')} | {first.get('course_proj', '')} |{sem_cells}"
            )
            for alt in alts[1:]:
                lines.append(
                    f"|  | {alt['code']} | {alt['name']} "
                    f"|  |  | {alt.get('classroom', '')} "
                    f"| {alt.get('lecture', '')} | {alt.get('practice', '')} | {alt.get('lab', '')} "
                    f"| {alt.get('seminar', '')} | {alt.get('course_proj', '')} |{empty_sem}"
                )

    lines.append("")
    if start_year:
        lines.append("---")
        lines.append(f"**O'quv yili:** {start_year}")
        lines.append("")
    return "\n".join(lines)
