import re
import openpyxl
from pathlib import Path

SOURCES_DIR = Path("sources")
OUTPUT_DIR = Path("output")

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


def detect_course_columns(ws) -> tuple[int, int, int]:
    """Return (num_col, code_col, name_col) as 0-based indices."""
    num_col = 0
    start_row_num = None

    for row in ws.iter_rows():
        for cell in row:
            if cell.value is not None and re.match(r"^1\.00\.?$", str(cell.value).strip()):
                num_col = cell.column - 1
                start_row_num = cell.row
                break
        if start_row_num is not None:
            break

    if start_row_num is None:
        return 0, 1, 2

    code_col, name_col = None, None
    for data_row in ws.iter_rows(min_row=start_row_num + 1, max_row=start_row_num + 10, values_only=True):
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

    return num_col, code_col, name_col


def parse_core_courses(ws) -> list[dict]:
    num_col, code_col, name_col = detect_course_columns(ws)
    courses = []
    in_core_section = False

    for row in ws.iter_rows(values_only=True):
        num = row[num_col] if len(row) > num_col else None
        code = row[code_col] if len(row) > code_col else None
        name = row[name_col] if len(row) > name_col else None

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

        if in_core_section and is_course_number(num_str) and section_prefix(num_str) == "1":
            courses.append({
                "num": num_str,
                "code": str(code).strip() if code else "",
                "name": name_str or "",
            })

    return courses


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
    lines.append("| # | Code | Name |")
    lines.append("|---|------|------|")
    for course in core_courses:
        lines.append(f"| {course['num']} | {course['code']} | {course['name']} |")
    lines.append("")
    if start_year:
        lines.append("---")
        lines.append(f"**O'quv yili:** {start_year}")
        lines.append("")
    return "\n".join(lines)


def process_file(xlsx_path: Path) -> None:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    direction_cell = find_cell_containing(ws, "nalishi:")
    year_cell = find_cell_containing(ws, "quv yili")

    if direction_cell:
        direction_raw = direction_cell.value or ""
        if not re.search(r"\d{6,9}", direction_raw):
            below = ws.cell(row=direction_cell.row + 1, column=direction_cell.column)
            if below.value:
                direction_raw = direction_raw + " " + str(below.value)
        code, name = extract_direction(direction_raw)
        if not code:
            print(f"  WARNING: no direction code found in: {direction_raw!r}")
        stem = f"{to_camel_case(name)}_{code}" if code else to_camel_case(name)
        title = name
    else:
        stem = xlsx_path.stem
        title = xlsx_path.stem

    year_raw = year_cell.value if year_cell else None
    start_year = extract_start_year(year_raw) if year_raw else ""

    degree_cell   = find_cell_containing(ws, "Akademik daraja")
    duration_cell = find_cell_containing(ws, "muddati")
    edu_type_cell = find_cell_containing(ws, "shakli")

    degree   = parse_label_value(degree_cell.value)   if degree_cell   else ""
    duration = parse_label_value(duration_cell.value) if duration_cell else ""
    edu_type = parse_label_value(edu_type_cell.value) if edu_type_cell else ""

    core_courses = parse_core_courses(ws)

    OUTPUT_DIR.mkdir(exist_ok=True)
    if start_year:
        stem = f"{stem}_{start_year}"
    out_path = OUTPUT_DIR / (stem + ".md")
    out_path.write_text(
        build_markdown(title, start_year, degree, duration, edu_type, core_courses),
        encoding="utf-8",
    )
    print(f"  {xlsx_path.name} -> {out_path}  ({len(core_courses)} core courses)")


def main() -> None:
    xlsx_files = sorted(f for f in SOURCES_DIR.glob("*.xlsx") if not f.name.startswith("~$"))
    if not xlsx_files:
        print("No .xlsx files found in sources/")
        return
    for xlsx_path in xlsx_files:
        process_file(xlsx_path)


if __name__ == "__main__":
    main()
