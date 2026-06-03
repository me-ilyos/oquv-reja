import re

COURSE_NUM_RE = re.compile(r"^\d+\.\d+(\.\d+)?$")


def is_course_number(value) -> bool:
    if value is None:
        return False
    return bool(COURSE_NUM_RE.match(str(value).strip()))


def section_prefix(course_num) -> str:
    return str(course_num).strip().split(".")[0]


def find_cell_containing(ws, substring: str):
    for row in ws.iter_rows(max_row=15):
        for cell in row:
            if isinstance(cell.value, str) and substring in cell.value:
                return cell
    return None


def parse_label_value(raw: str) -> str:
    parts = raw.split(" - ", 1)
    return parts[1].strip() if len(parts) > 1 else raw.strip()


def extract_direction(raw: str) -> tuple[str, str]:
    match = re.search(r"\d{6,9}", raw)
    code = match.group() if match else ""
    parts = raw.split(" - ", 1)
    name = parts[1].strip() if len(parts) > 1 else raw.strip()
    return code, name


def to_camel_case(name: str) -> str:
    return "".join(re.sub(r"[^a-zA-Z0-9]", "", w).capitalize() for w in name.split())


def extract_start_year(raw: str) -> str:
    match = re.search(r"(\d{4})/\d{4}", raw)
    return match.group(1) if match else ""


def _scan_col(ws, keyword: str, max_row: int):
    """Return 0-based column index of first header cell containing keyword, or None."""
    for row in ws.iter_rows(max_row=max_row):
        for cell in row:
            if isinstance(cell.value, str) and keyword in cell.value.lower():
                return cell.column - 1
    return None


def detect_course_columns(
    ws,
) -> tuple[int, int, int, int, int, int, int, int, int, int]:
    """Return (num_col, code_col, name_col, hours_col, classroom_col,
    lecture_col, practice_col, lab_col, seminar_col, course_proj_col) as 0-based indices."""
    num_col = 0
    start_row_num = None

    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None and re.match(
                r"^1\.00\.?$", str(cell.value).strip()
            ):
                num_col = cell.column - 1
                start_row_num = cell.row
                break
        if start_row_num is not None:
            break

    if start_row_num is None:
        return 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

    code_col, name_col = None, None
    for data_row in ws.iter_rows(
        min_row=start_row_num + 1, max_row=start_row_num + 10, values_only=True
    ):
        if not data_row or data_row[num_col] is None:
            continue
        if not re.match(r"^\d+\.\d+", str(data_row[num_col]).strip().rstrip(".")):
            continue
        found = []
        for i in range(num_col + 1, len(data_row)):
            if data_row[i] is not None and len(found) < 2:
                found.append(i)
        if len(found) >= 2:
            code_col, name_col = found[0], found[1]
        elif len(found) == 1:
            code_col = name_col = found[0]
        break

    if code_col is None:
        code_col = num_col + 1
    if name_col is None:
        name_col = num_col + 2

    hours_col = _scan_col(ws, "soat", start_row_num) or (name_col + 1)

    # Find classroom_col and capture which row it was on so we can read the label row below it.
    classroom_col = None
    auditoriya_row = None
    for hrow in ws.iter_rows(max_row=start_row_num):
        for cell in hrow:
            if isinstance(cell.value, str) and "auditoriya" in cell.value.lower():
                classroom_col = cell.column - 1
                auditoriya_row = cell.row
                break
        if classroom_col is not None:
            break
    if classroom_col is None:
        classroom_col = hours_col + 2

    # The label row (auditoriya_row + 1) holds text labels "Ma'ruza", "Amaliy ...",
    # "Seminar", "Laboratoriya", "Kurs ishi" for the subcategory columns.
    # Normalize to plain ASCII letters to handle encoding variants and typos.
    lecture_col = practice_col = lab_col = seminar_col = course_proj_col = None
    if auditoriya_row is not None:
        label_row = next(
            ws.iter_rows(
                min_row=auditoriya_row + 1, max_row=auditoriya_row + 1, values_only=True
            )
        )
        for i, v in enumerate(label_row):
            if i <= classroom_col or not isinstance(v, str):
                continue
            norm = re.sub(r"[^a-z]", "", v.lower())
            if "maruza" in norm and lecture_col is None:
                lecture_col = i
            elif "amaliy" in norm and practice_col is None:
                practice_col = i
            elif ("laborator" in norm or "labarator" in norm) and lab_col is None:
                lab_col = i
            elif "seminar" in norm and seminar_col is None:
                seminar_col = i
            elif "kursish" in norm and course_proj_col is None:
                course_proj_col = i

    lecture_col = lecture_col or classroom_col + 1
    practice_col = practice_col or classroom_col + 2
    lab_col = lab_col or classroom_col + 3
    seminar_col = seminar_col or classroom_col + 4
    course_proj_col = course_proj_col or classroom_col + 5

    return (
        num_col,
        code_col,
        name_col,
        hours_col,
        classroom_col,
        lecture_col,
        practice_col,
        lab_col,
        seminar_col,
        course_proj_col,
    )


def _int_val(row, col, default="0") -> str:
    v = row[col] if len(row) > col else None
    if v is None:
        return default
    try:
        return str(int(float(v)))
    except (ValueError, TypeError):
        return default


def parse_core_courses(ws) -> list[dict]:
    (
        num_col,
        code_col,
        name_col,
        hours_col,
        classroom_col,
        lecture_col,
        practice_col,
        lab_col,
        seminar_col,
        course_proj_col,
    ) = detect_course_columns(ws)
    courses = []
    in_core_section = False

    for row in ws.iter_rows(values_only=True):
        num = row[num_col] if len(row) > num_col else None
        code = row[code_col] if len(row) > code_col else None
        name = row[name_col] if len(row) > name_col else None
        hours_raw = row[hours_col] if len(row) > hours_col else None

        num_str = str(num).strip().rstrip(".") if num is not None else None
        name_str = str(name).strip() if name is not None else None

        if num_str == "1.00":
            in_core_section = True
            continue

        if num_str == "2.00":
            break

        if in_core_section and any(
            cell is not None and str(cell).strip() == "Jami:" for cell in row
        ):
            break

        if (
            in_core_section
            and is_course_number(num_str)
            and section_prefix(num_str) == "1"
        ):
            try:
                hours_str = str(int(float(hours_raw))) if hours_raw is not None else ""
            except (ValueError, TypeError):
                hours_str = str(hours_raw).strip() if hours_raw is not None else ""
            try:
                credits = (
                    str(int(float(hours_raw) / 30)) if hours_raw is not None else ""
                )
            except (ValueError, TypeError):
                credits = ""
            courses.append(
                {
                    "num": num_str,
                    "code": str(code).strip() if code else "",
                    "name": name_str or "",
                    "hours": hours_str,
                    "credits": credits,
                    "classroom": _int_val(row, classroom_col),
                    "lecture": _int_val(row, lecture_col),
                    "practice": _int_val(row, practice_col),
                    "lab": _int_val(row, lab_col),
                    "seminar": _int_val(row, seminar_col),
                    "course_proj": _int_val(row, course_proj_col),
                }
            )

    return courses
