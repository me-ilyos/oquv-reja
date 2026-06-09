import argparse
import re
from pathlib import Path

import openpyxl

from formatter import build_markdown
from parser import (
    detect_columns,
    extract_direction,
    extract_start_year,
    find_cell_containing,
    parse_core_courses,
    parse_label_value,
    parse_selective_courses,
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

    layout, semester_map, weekly_map = detect_columns(ws)
    core_courses = parse_core_courses(ws, layout, semester_map, weekly_map)
    selective_slots = parse_selective_courses(ws, layout, semester_map, weekly_map)

    OUTPUT_DIR.mkdir(exist_ok=True)
    if start_year:
        stem = f"{stem}_{start_year}"
    out_path = OUTPUT_DIR / (stem + ".md")
    out_path.write_text(
        build_markdown(
            title, start_year, degree, duration, edu_type, core_courses, selective_slots
        ),
        encoding="utf-8",
    )
    print(
        f"  {xlsx_path.name} -> {out_path}"
        f"  ({len(core_courses)} core, {len(selective_slots)} selective slots)"
    )


def main() -> None:
    arg_parser = argparse.ArgumentParser(description="Parse oquv reja Excel files.")
    arg_parser.add_argument(
        "files",
        nargs="*",
        type=Path,
        help="One or more .xlsx files to parse. Defaults to all files in sources/.",
    )
    args = arg_parser.parse_args()

    if args.files:
        xlsx_files = []
        for p in args.files:
            if not p.exists():
                print(f"WARNING: file not found: {p}")
            else:
                xlsx_files.append(p)
    else:
        xlsx_files = sorted(
            f for f in SOURCES_DIR.glob("*.xlsx") if not f.name.startswith("~$")
        )

    if not xlsx_files:
        print("No .xlsx files found.")
        return
    for xlsx_path in xlsx_files:
        process_file(xlsx_path)


if __name__ == "__main__":
    main()
