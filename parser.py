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


def _extract_program_years(ws) -> int:
    """Return program duration in years (e.g. 3 for '3 yil'). Defaults to 4."""
    cell = find_cell_containing(ws, "muddati")
    match = re.search(r"(\d+)\s*yil", str(cell.value or "")) if cell else None
    if match is None:
        print("WARNING: program duration not parsed; defaulting to 4 years")
        return 4
    return int(match.group(1))


def _find_anchor(ws) -> tuple[int | None, int | None]:
    """Locate the '1.00' marker cell. Returns (0-based num_col, 1-based row).

    Returns (None, None) if no anchor is found. This cell anchors all column
    and header-row detection, so it is found once and reused.
    """
    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None and re.match(
                r"^1\.00\.?$", str(cell.value).strip()
            ):
                return cell.column - 1, cell.row
    return None, None


def _detect_col_range(ws, lo: int, hi: int, offset: int) -> dict[int, int]:
    """Scan header rows near the 1.00 anchor for consecutive ints in [lo, hi].

    Returns {0-based col index: int_val - offset} for the last matching row,
    or {} if no qualifying row is found. Used by detect_semester_columns and
    detect_weekly_hours_columns.
    """
    _, start_row_num = _find_anchor(ws)
    if start_row_num is None:
        return {}

    scan_start = max(1, start_row_num - 10)
    last_match = None
    for row in ws.iter_rows(
        min_row=scan_start, max_row=start_row_num, values_only=True
    ):
        candidates = []
        for col_idx, cell_val in enumerate(row):
            if cell_val is None:
                continue
            try:
                int_val = int(float(cell_val))
            except (ValueError, TypeError):
                continue
            if lo <= int_val <= hi:
                candidates.append((col_idx, int_val))

        if len(candidates) < 3:
            continue
        values = [v for _, v in candidates]
        if len(values) != len(set(values)):
            continue
        candidates.sort(key=lambda x: x[1])
        is_consecutive = all(
            candidates[i + 1][1] == candidates[i][1] + 1
            for i in range(len(candidates) - 1)
        )
        if not is_consecutive:
            continue

        last_match = {col_idx: int_val - offset for col_idx, int_val in candidates}

    return last_match or {}


def detect_semester_columns(ws) -> dict[int, int]:
    """Return {0-based col index: semester number (1-N)} for credit columns.

    The credit columns are labeled (12+N) to (11+2N) in the header row, where
    N = total semesters (program_years * 2). For a 4-year program N=8: range [20,27],
    offset=19. For a 3-year program N=6: range [18,23], offset=17.
    """
    n = _extract_program_years(ws) * 2
    lo, hi, offset = 12 + n, 11 + 2 * n, 11 + n
    result = _detect_col_range(ws, lo, hi, offset)
    if not result:
        print("WARNING: semester (credit) header row not found")
        return {}
    return {col: sem for col, sem in result.items() if sem <= n}


def detect_weekly_hours_columns(ws) -> dict[int, int]:
    """Return {0-based col index: semester number (1-8)} for weekly-hours columns.

    Finds the header row with consecutive integers in [12, 19] (12→S1, …, 19→S8).
    """
    result = _detect_col_range(ws, 12, 19, 11)
    if not result:
        print("WARNING: semester (weekly hours) header row not found")
        return {}
    max_semesters = _extract_program_years(ws) * 2
    return {col: sem for col, sem in result.items() if sem <= max_semesters}


def _find_code_name_cols(ws, num_col: int, start_row: int) -> tuple[int, int]:
    """Find the code and name columns from the first course row below the anchor.

    Falls back to num_col+1 / num_col+2 when the row can't be located.
    """
    code_col, name_col = None, None
    for data_row in ws.iter_rows(
        min_row=start_row + 1, max_row=start_row + 10, values_only=True
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
    return code_col, name_col


def _find_hours_col(ws, start_row: int, name_col: int) -> int:
    """Locate the total-hours ('soat') column, falling back to name_col+1."""
    return _scan_col(ws, "soat", start_row) or (name_col + 1)


def _find_classroom_col(ws, start_row: int, hours_col: int) -> tuple[int, int | None]:
    """Find the classroom ('auditoriya') column and the header row it sits on.

    Returns (classroom_col, auditoriya_row); auditoriya_row is None when the
    header is absent and classroom_col falls back to hours_col+2.
    """
    classroom_col = None
    auditoriya_row = None
    for hrow in ws.iter_rows(max_row=start_row):
        for cell in hrow:
            if isinstance(cell.value, str) and "auditoriya" in cell.value.lower():
                classroom_col = cell.column - 1
                auditoriya_row = cell.row
                break
        if classroom_col is not None:
            break
    if classroom_col is None:
        classroom_col = hours_col + 2
    return classroom_col, auditoriya_row


def _find_subcategory_cols(
    ws, auditoriya_row: int | None, classroom_col: int
) -> tuple[int, int, int, int, int]:
    """Map the label row below 'auditoriya' to the five subcategory columns.

    The label row holds "Ma'ruza", "Amaliy …", "Seminar", "Laboratoriya",
    "Kurs ishi". Labels are normalized to plain ASCII letters to absorb
    encoding variants and typos; unmatched columns fall back to fixed offsets
    from classroom_col.
    """
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
    return lecture_col, practice_col, lab_col, seminar_col, course_proj_col


def detect_course_columns(
    ws,
) -> tuple[int, int, int, int, int, int, int, int, int, int]:
    """Return the ten 0-based course column indices (num, code, name, hours,
    classroom, lecture, practice, lab, seminar, course_proj).

    Orchestrates the focused detectors; defaults to 0..9 if no anchor is found.
    """
    num_col, start_row = _find_anchor(ws)
    if start_row is None:
        return 0, 1, 2, 3, 4, 5, 6, 7, 8, 9

    code_col, name_col = _find_code_name_cols(ws, num_col, start_row)
    hours_col = _find_hours_col(ws, start_row, name_col)
    classroom_col, auditoriya_row = _find_classroom_col(ws, start_row, hours_col)
    lecture_col, practice_col, lab_col, seminar_col, course_proj_col = (
        _find_subcategory_cols(ws, auditoriya_row, classroom_col)
    )

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


def _to_int(value) -> int | None:
    """Coerce an Excel cell value to int, or None if absent/non-numeric."""
    if value is None:
        return None
    try:
        return int(float(value))
    except (ValueError, TypeError):
        return None


def _cell_int(row, col, default: int | None = None) -> int | None:
    """Read row[col] as int, falling back to default when absent/non-numeric."""
    val = _to_int(row[col]) if len(row) > col else None
    return val if val is not None else default


def _extract_semester_credits(
    row: tuple, semester_col_map: dict[int, int]
) -> dict[int, int]:
    """Return {semester_number: value} for non-zero semester cells."""
    result = {}
    for col_idx, sem_num in semester_col_map.items():
        val = _cell_int(row, col_idx)
        if val:
            result[sem_num] = val
    return result


def _warn_credit_mismatch(num, hours_raw, semester_credits: dict) -> None:
    """Flag (do not correct) when hours/30 disagrees with the per-semester sum.

    The sheet carries credits twice: as a total (hours / 30) and split across
    semester columns. When both are present and disagree, the parse or the
    source data is wrong; surface it rather than silently trusting one.
    """
    if hours_raw is None or not semester_credits:
        return
    try:
        derived = int(float(hours_raw) / 30)
    except (ValueError, TypeError):
        return
    s = sum(semester_credits.values())
    if derived != s:
        print(f"WARNING: {num} credit mismatch: hours/30={derived} vs sem-sum={s}")


def _clean_name(value) -> str:
    """Normalize a course/alternative name read from a cell.

    Ministry templates use hard line breaks (Alt+Enter) in cells; a stray
    newline or '|' inside a name would terminate a Markdown table row and
    corrupt every row below it. Collapse all internal whitespace to single
    spaces and replace '|' so the name is always row-safe.
    """
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value).replace("|", " ")).strip()


def parse_selective_courses(ws) -> list[dict]:
    """Parse section 2 (tanlov fanlar / selective courses).

    Returns a list of slot dicts. Each slot has the same numeric fields as a
    core course plus an 'alternatives' list of {code, name} dicts — one per
    alternative course offered in that slot.

    Numeric columns (hours, lecture, …, semester_credits) are vertically merged
    in the spreadsheet, so their values appear only on the first row of each
    slot; continuation rows carry only code and name.
    """
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
    semester_col_map = detect_semester_columns(ws)
    weekly_col_map = detect_weekly_hours_columns(ws)
    slots = []
    in_selective_section = False
    current_slot = None

    for row in ws.iter_rows(values_only=True):
        num = row[num_col] if len(row) > num_col else None
        code = row[code_col] if len(row) > code_col else None
        name = row[name_col] if len(row) > name_col else None
        hours_raw = row[hours_col] if len(row) > hours_col else None

        num_str = str(num).strip().rstrip(".") if num is not None else None

        if num_str == "2.00":
            in_selective_section = True
            continue

        if in_selective_section and any(
            cell is not None and str(cell).strip().rstrip(":").casefold() == "jami"
            for cell in row
        ):
            break

        if (
            in_selective_section
            and num_str is not None
            and re.match(r"^\d+\.00$", num_str)
        ):
            break

        if (
            in_selective_section
            and is_course_number(num_str)
            and section_prefix(num_str) == "2"
        ):
            if current_slot is not None:
                slots.append(current_slot)
            hours = _to_int(hours_raw)
            credits = hours // 30 if hours is not None else None
            # Breakdown values from the slot row are the defaults for all
            # alternatives. Continuation rows inherit these when their cells
            # are None (vertically merged); non-None values override them.
            slot_breakdown = {
                "classroom": _cell_int(row, classroom_col, 0),
                "lecture": _cell_int(row, lecture_col, 0),
                "practice": _cell_int(row, practice_col, 0),
                "lab": _cell_int(row, lab_col, 0),
                "seminar": _cell_int(row, seminar_col, 0),
                "course_proj": _cell_int(row, course_proj_col, 0),
            }
            sem_credits = _extract_semester_credits(row, semester_col_map)
            _warn_credit_mismatch(num_str, hours_raw, sem_credits)
            current_slot = {
                "num": num_str,
                "hours": hours,
                "credits": credits,
                "semester_credits": sem_credits,
                "semester_weekly_hours": _extract_semester_credits(row, weekly_col_map),
                "_breakdown_defaults": slot_breakdown,
                "alternatives": [],
            }
            code_str = str(code).strip() if code is not None else ""
            name_str = _clean_name(name)
            if code_str or name_str:
                current_slot["alternatives"].append(
                    {"code": code_str, "name": name_str, **slot_breakdown}
                )

        elif in_selective_section and current_slot is not None and num is None:
            code_str = str(code).strip() if code is not None else ""
            name_str = _clean_name(name)
            if code_str or name_str:
                d = current_slot["_breakdown_defaults"]
                current_slot["alternatives"].append(
                    {
                        "code": code_str,
                        "name": name_str,
                        "classroom": _cell_int(row, classroom_col, d["classroom"]),
                        "lecture": _cell_int(row, lecture_col, d["lecture"]),
                        "practice": _cell_int(row, practice_col, d["practice"]),
                        "lab": _cell_int(row, lab_col, d["lab"]),
                        "seminar": _cell_int(row, seminar_col, d["seminar"]),
                        "course_proj": _cell_int(
                            row, course_proj_col, d["course_proj"]
                        ),
                    }
                )

    if current_slot is not None:
        slots.append(current_slot)

    for slot in slots:
        slot.pop("_breakdown_defaults", None)

    if not slots:
        print("WARNING: no selective courses found")

    return slots


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
    semester_col_map = detect_semester_columns(ws)
    weekly_col_map = detect_weekly_hours_columns(ws)
    courses = []
    in_core_section = False

    for row in ws.iter_rows(values_only=True):
        num = row[num_col] if len(row) > num_col else None
        code = row[code_col] if len(row) > code_col else None
        name = row[name_col] if len(row) > name_col else None
        hours_raw = row[hours_col] if len(row) > hours_col else None

        num_str = str(num).strip().rstrip(".") if num is not None else None
        name_str = _clean_name(name)

        if num_str == "1.00":
            in_core_section = True
            continue

        if num_str == "2.00":
            break

        if in_core_section and any(
            cell is not None and str(cell).strip().rstrip(":").casefold() == "jami"
            for cell in row
        ):
            break

        if (
            in_core_section
            and is_course_number(num_str)
            and section_prefix(num_str) == "1"
        ):
            hours = _to_int(hours_raw)
            credits = hours // 30 if hours is not None else None
            sem_credits = _extract_semester_credits(row, semester_col_map)
            _warn_credit_mismatch(num_str, hours_raw, sem_credits)
            courses.append(
                {
                    "num": num_str,
                    "code": str(code).strip() if code else "",
                    "name": name_str or "",
                    "hours": hours,
                    "credits": credits,
                    "classroom": _cell_int(row, classroom_col, 0),
                    "lecture": _cell_int(row, lecture_col, 0),
                    "practice": _cell_int(row, practice_col, 0),
                    "lab": _cell_int(row, lab_col, 0),
                    "seminar": _cell_int(row, seminar_col, 0),
                    "course_proj": _cell_int(row, course_proj_col, 0),
                    "semester_credits": sem_credits,
                    "semester_weekly_hours": _extract_semester_credits(
                        row, weekly_col_map
                    ),
                }
            )

    return courses
