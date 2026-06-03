def build_markdown(
    title: str,
    start_year: str,
    degree: str,
    duration: str,
    edu_type: str,
    core_courses: list[dict],
) -> str:
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
    lines.append(
        "| # | Code | Name | Hours | Credits | Classroom | Lecture | Practice | Lab | Seminar | Course Proj |"
    )
    lines.append(
        "|---|------|------|-------|---------|-----------|---------|----------|-----|---------|-------------|"
    )
    for course in core_courses:
        lines.append(
            f"| {course['num']} | {course['code']} | {course['name']} "
            f"| {course['hours']} | {course['credits']} | {course['classroom']} "
            f"| {course['lecture']} | {course['practice']} | {course['lab']} "
            f"| {course['seminar']} | {course['course_proj']} |"
        )
    lines.append("")
    if start_year:
        lines.append("---")
        lines.append(f"**O'quv yili:** {start_year}")
        lines.append("")
    return "\n".join(lines)
