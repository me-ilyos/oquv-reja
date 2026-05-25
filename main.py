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


def find_cell_containing(ws, substring: str) -> str | None:
    for row in ws.iter_rows(max_row=15, values_only=True):
        for cell in row:
            if isinstance(cell, str) and substring in cell:
                return cell
    return None


def extract_direction(raw: str) -> tuple[str, str]:
    code = re.search(r"\d{6,9}", raw).group()
    name = raw.split(" - ", 1)[1].strip()
    return code, name


def to_camel_case(name: str) -> str:
    return "".join(re.sub(r"[^a-zA-Z0-9]", "", w).capitalize() for w in name.split())


def extract_start_year(raw: str) -> str:
    match = re.search(r"(\d{4})/\d{4}", raw)
    return match.group(1) if match else ""


def parse_core_courses(ws) -> list[dict]:
    courses = []
    in_core_section = False

    for row in ws.iter_rows(values_only=True):
        num = row[0] if len(row) > 0 else None
        code = row[1] if len(row) > 1 else None
        name = row[2] if len(row) > 2 else None

        num_str = str(num).strip() if num is not None else None
        name_str = str(name).strip() if name is not None else None

        if num_str == "1.00":
            in_core_section = True
            continue

        if num_str == "2.00":
            break

        if name_str == "Jami:":
            break

        if in_core_section and is_course_number(num) and section_prefix(num) == "1":
            courses.append({
                "num": num_str,
                "code": str(code).strip() if code else "",
                "name": name_str or "",
            })

    return courses


def build_markdown(title: str, start_year: str, core_courses: list[dict]) -> str:
    lines = [f"# Oquv Reja: {title}", ""]
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

    direction_raw = find_cell_containing(ws, "nalishi:")
    year_raw = find_cell_containing(ws, "quv yili")

    if direction_raw:
        code, name = extract_direction(direction_raw)
        stem = f"{to_camel_case(name)}_{code}"
        title = name
    else:
        stem = xlsx_path.stem
        title = xlsx_path.stem

    start_year = extract_start_year(year_raw) if year_raw else ""

    core_courses = parse_core_courses(ws)

    OUTPUT_DIR.mkdir(exist_ok=True)
    if start_year:
        stem = f"{stem}_{start_year}"
    out_path = OUTPUT_DIR / (stem + ".md")
    out_path.write_text(build_markdown(title, start_year, core_courses), encoding="utf-8")
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
