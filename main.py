import re
from pathlib import Path

import openpyxl

from formatter import build_markdown
from parser import (
    extract_direction,
    extract_start_year,
    find_cell_containing,
    parse_core_courses,
    parse_label_value,
    to_camel_case,
)

SOURCES_DIR = Path("sources")
OUTPUT_DIR = Path("output")


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

    degree_cell = find_cell_containing(ws, "Akademik daraja")
    duration_cell = find_cell_containing(ws, "muddati")
    edu_type_cell = find_cell_containing(ws, "shakli")

    degree = parse_label_value(degree_cell.value) if degree_cell else ""
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
    xlsx_files = sorted(
        f for f in SOURCES_DIR.glob("*.xlsx") if not f.name.startswith("~$")
    )
    if not xlsx_files:
        print("No .xlsx files found in sources/")
        return
    for xlsx_path in xlsx_files:
        process_file(xlsx_path)


if __name__ == "__main__":
    main()
