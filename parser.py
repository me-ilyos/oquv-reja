import re

from models import Alternative, ColumnLayout, Course, SelectiveSlot

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


def value_after_dash(raw: str) -> str:
    parts = raw.split(" - ", 1)
    return parts[1].strip() if len(parts) > 1 else raw.strip()


def split_direction(raw: str) -> tuple[str, str]:
    """Split a 'CODE - Name' direction string into (code, name)."""
    match = re.search(r"\d{6,9}", raw)
    code = match.group() if match else ""
    return code, value_after_dash(raw)


def resolve_direction(ws) -> tuple[str, str] | None:
    """Find and parse the program-direction cell into (code, name).

    Returns None when no direction cell is present (caller falls back to the
    filename). Handles the variant where the code and name are split across two
    vertically adjacent rows by reading the cell below when the primary cell has
    no digit code. Warns when a cell is found but yields no code.
    """
    cell = find_cell_containing(ws, "nalishi:")
    if cell is None:
        return None
    raw = cell.value or ""
    if not re.search(r"\d{6,9}", raw):
        below = ws.cell(row=cell.row + 1, column=cell.column)
        if below.value:
            raw = f"{raw} {below.value}"
    code, name = split_direction(raw)
    if not code:
        print(f"  WARNING: no direction code found in: {raw!r}")
    return code, name


def to_pascal_case(name: str) -> str:
    return "".join(re.sub(r"[^a-zA-Z0-9]", "", w).capitalize() for w in name.split())


def extract_start_year(raw: str) -> str:
    match = re.search(r"(\d{4})/\d{4}", raw)
    return match.group(1) if match else ""


def find_header_col(ws, keyword: str, max_row: int):
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
    """Locate the '1.00' marker cell. Returns (0-based num_col, 1-based row),
    or (None, None) if not found. Anchors all column/header detection."""
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


def detect_semester_columns(ws, years: int) -> dict[int, int]:
    """Return {0-based col index: semester number (1-N)} for credit columns.

    The credit columns are labeled (12+N) to (11+2N) in the header row, where
    N = total semesters (years * 2). For a 4-year program N=8: range [20,27],
    offset=19. For a 3-year program N=6: range [18,23], offset=17.
    """
    n = years * 2
    lo, hi, offset = 12 + n, 11 + 2 * n, 11 + n
    result = _detect_col_range(ws, lo, hi, offset)
    if not result:
        print("WARNING: semester (credit) header row not found")
        return {}
    return {col: sem for col, sem in result.items() if sem <= n}


def detect_weekly_hours_columns(ws, years: int) -> dict[int, int]:
    """Return {0-based col index: semester number (1-8)} for weekly-hours columns.

    Finds the header row with consecutive integers in [12, 19] (12→S1, …, 19→S8).
    """
    result = _detect_col_range(ws, 12, 19, 11)
    if not result:
        print("WARNING: semester (weekly hours) header row not found")
        return {}
    return {col: sem for col, sem in result.items() if sem <= years * 2}


def _find_code_name_cols(ws, num_col: int, start_row: int) -> tuple[int, int]:
    """Find code/name columns from the first course row below the anchor;
    fall back to num_col+1 / num_col+2 when the row can't be located."""
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


def find_total_hours_col(ws, start_row: int, name_col: int) -> int:
    """Locate the total-hours ('soat') column, falling back to name_col+1."""
    return find_header_col(ws, "soat", start_row) or (name_col + 1)


def _find_classroom_col(ws, start_row: int, hours_col: int) -> tuple[int, int | None]:
    """Find the classroom ('auditoriya') column and the header row it sits on,
    as (classroom_col, auditoriya_row). auditoriya_row is None (and classroom_col
    falls back to hours_col+2) when the header is absent."""
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


def detect_course_columns(ws) -> ColumnLayout:
    """Return the course ColumnLayout (ten 0-based indices) by orchestrating the
    focused detectors; defaults to 0..9 if no anchor is found."""
    num_col, start_row = _find_anchor(ws)
    if start_row is None:
        return ColumnLayout(0, 1, 2, 3, 4, 5, 6, 7, 8, 9)

    code_col, name_col = _find_code_name_cols(ws, num_col, start_row)
    hours_col = find_total_hours_col(ws, start_row, name_col)
    classroom_col, auditoriya_row = _find_classroom_col(ws, start_row, hours_col)
    lecture_col, practice_col, lab_col, seminar_col, course_proj_col = (
        _find_subcategory_cols(ws, auditoriya_row, classroom_col)
    )

    return ColumnLayout(
        num=num_col,
        code=code_col,
        name=name_col,
        hours=hours_col,
        classroom=classroom_col,
        lecture=lecture_col,
        practice=practice_col,
        lab=lab_col,
        seminar=seminar_col,
        course_proj=course_proj_col,
    )


def detect_sheet_layout(ws) -> tuple[ColumnLayout, dict[int, int], dict[int, int]]:
    """Detect everything position-dependent for a sheet in one place: returns
    (course layout, semester-credit map, weekly-hours map). Reads program
    duration once so the parse functions don't each re-scan the same anchors."""
    years = _extract_program_years(ws)
    layout = detect_course_columns(ws)
    semester_map = detect_semester_columns(ws, years)
    weekly_map = detect_weekly_hours_columns(ws, years)
    return layout, semester_map, weekly_map


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


def map_semester_values(row: tuple, semester_col_map: dict[int, int]) -> dict[int, int]:
    """Return {semester_number: value} for non-zero semester cells.

    Shared by credit and weekly-hours extraction — both read one value per
    semester off the same kind of column map.
    """
    result = {}
    for col_idx, sem_num in semester_col_map.items():
        val = _cell_int(row, col_idx)
        if val:
            result[sem_num] = val
    return result


def _warn_credit_mismatch(item) -> None:
    """Flag (don't correct) when an item's derived_credits (hours/30) disagrees
    with the sum of its per-semester credits. The sheet carries credits twice;
    surface a disagreement rather than trusting one. Accepts Course/SelectiveSlot."""
    derived = item.derived_credits
    if derived is None or not item.semester_credits:
        return
    s = sum(item.semester_credits.values())
    if derived != s:
        print(f"WARNING: {item.num} credit mismatch: hours/30={derived} vs sem-sum={s}")


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


BREAKDOWN_FIELDS = ("classroom", "lecture", "practice", "lab", "seminar", "course_proj")


def _iter_section_rows(ws, num_col: int, section: int):
    """Yield (num_str, row) for each row in the given top-level section (1 or 2).

    Enters when the section's '{section}.00' marker is seen and stops at the
    first 'Jami' total row or the next '\\d+.00' section marker. This is the
    single shared row-walk/stop skeleton for both parse functions.
    """
    start = f"{section}.00"
    in_section = False
    for row in ws.iter_rows(values_only=True):
        num = row[num_col] if len(row) > num_col else None
        num_str = str(num).strip().rstrip(".") if num is not None else None

        if not in_section:
            if num_str == start:
                in_section = True
            continue

        if any(
            cell is not None and str(cell).strip().rstrip(":").casefold() == "jami"
            for cell in row
        ):
            return
        if num_str is not None and re.match(r"^\d+\.00$", num_str):
            return

        yield num_str, row


def breakdown_from(row, cols: tuple, fill: int) -> dict:
    """Read the six hour-breakdown fields, defaulting every missing cell to `fill`.

    Used for a course row or a selective slot's own row, where an absent value
    means zero rather than 'inherit'.
    """
    return {f: _cell_int(row, c, fill) for f, c in zip(BREAKDOWN_FIELDS, cols)}


def breakdown_inheriting(row, cols: tuple, fallbacks: dict) -> dict:
    """Read the six hour-breakdown fields, inheriting per-field fallbacks.

    Used for a selective continuation row, whose numeric cells are vertically
    merged with the slot's first row: a None cell inherits the slot's value.
    """
    return {f: _cell_int(row, c, fallbacks[f]) for f, c in zip(BREAKDOWN_FIELDS, cols)}


def _append_alternative(
    slot: SelectiveSlot, code_str: str, name_str: str, breakdown: dict
) -> None:
    """Append an Alternative to the slot, skipping fully blank continuation rows."""
    if code_str or name_str:
        slot.alternatives.append(Alternative(code=code_str, name=name_str, **breakdown))


def parse_selective_courses(
    ws,
    layout: ColumnLayout,
    semester_map: dict[int, int],
    weekly_map: dict[int, int],
) -> list[SelectiveSlot]:
    """Parse section 2 (tanlov fanlar / selective courses) into SelectiveSlots.

    Each slot carries the shared hours/credits plus an `alternatives` list.
    Numeric columns are vertically merged in the spreadsheet, so their values
    appear only on the slot's first row; continuation rows carry only code and
    name and inherit the slot's breakdown for any merged (None) cell.
    """
    slots: list[SelectiveSlot] = []
    current: SelectiveSlot | None = None
    slot_breakdown: dict = {}

    for num_str, row in _iter_section_rows(ws, layout.num, 2):
        code = row[layout.code] if len(row) > layout.code else None
        name = row[layout.name] if len(row) > layout.name else None
        code_str = str(code).strip() if code is not None else ""
        name_str = _clean_name(name)

        if is_course_number(num_str) and section_prefix(num_str) == "2":
            hours_raw = row[layout.hours] if len(row) > layout.hours else None
            current = SelectiveSlot(
                num=num_str,
                hours=_to_int(hours_raw),
                semester_credits=map_semester_values(row, semester_map),
                semester_weekly_hours=map_semester_values(row, weekly_map),
            )
            slots.append(current)
            _warn_credit_mismatch(current)
            # The slot row's breakdown is the default every continuation row
            # inherits where its cells are merged (None).
            slot_breakdown = breakdown_from(row, layout.breakdown, 0)
            _append_alternative(current, code_str, name_str, slot_breakdown)

        elif current is not None and num_str is None:
            _append_alternative(
                current,
                code_str,
                name_str,
                breakdown_inheriting(row, layout.breakdown, slot_breakdown),
            )

    if not slots:
        print("WARNING: no selective courses found")

    return slots


def parse_core_courses(
    ws,
    layout: ColumnLayout,
    semester_map: dict[int, int],
    weekly_map: dict[int, int],
) -> list[Course]:
    """Parse section 1 (majburiy fanlar / core courses) into Courses."""
    courses: list[Course] = []

    for num_str, row in _iter_section_rows(ws, layout.num, 1):
        if not (is_course_number(num_str) and section_prefix(num_str) == "1"):
            continue
        code = row[layout.code] if len(row) > layout.code else None
        name = row[layout.name] if len(row) > layout.name else None
        hours_raw = row[layout.hours] if len(row) > layout.hours else None
        course = Course(
            num=num_str,
            code=str(code).strip() if code else "",
            name=_clean_name(name),
            hours=_to_int(hours_raw),
            **breakdown_from(row, layout.breakdown, 0),
            semester_credits=map_semester_values(row, semester_map),
            semester_weekly_hours=map_semester_values(row, weekly_map),
        )
        _warn_credit_mismatch(course)
        courses.append(course)

    return courses
