def build_markdown(
    title: str,
    start_year: str,
    degree: str,
    duration: str,
    edu_type: str,
    core_courses: list[dict],
) -> str:
    active_semesters = sorted(
        {sem for course in core_courses for sem in course.get("semester_credits", {})}
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

    sem_header = "".join(f" S{s} |" for s in active_semesters)
    lines.append(
        "| # | Code | Name | Hours | Credits | Classroom"
        " | Lecture | Practice | Lab | Seminar | Course Proj |" + sem_header
    )
    sem_sep = "".join(" --- |" for _ in active_semesters)
    lines.append(
        f"|---|------|------|-------|---------|-----------|---------|----------|-----|---------|-------------|{sem_sep}"
    )

    for course in core_courses:
        sem_credits = course.get("semester_credits", {})
        sem_cells = "".join(f" {sem_credits.get(s, '')} |" for s in active_semesters)
        lines.append(
            f"| {course['num']} | {course['code']} | {course['name']} "
            f"| {course['hours']} | {course['credits']} | {course['classroom']} "
            f"| {course['lecture']} | {course['practice']} | {course['lab']} "
            f"| {course['seminar']} | {course['course_proj']} |{sem_cells}"
        )

    lines.append("")
    if start_year:
        lines.append("---")
        lines.append(f"**O'quv yili:** {start_year}")
        lines.append("")
    return "\n".join(lines)
