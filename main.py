import argparse
from pathlib import Path

import openpyxl

from formatter import build_markdown
from parser import (
    detect_sheet_layout,
    extract_start_year,
    find_cell_containing,
    parse_core_courses,
    parse_selective_courses,
    resolve_direction,
    to_pascal_case,
    value_after_dash,
)

SOURCES_DIR = Path("sources")
OUTPUT_DIR = Path("output")


def read_metadata(ws) -> tuple[str, str, str]:
    """Return (degree, duration, edu_type) from the metadata region, each the
    text after the label's ' - ' or '' when its cell is absent."""
    degree_cell = find_cell_containing(ws, "Akademik daraja")
    duration_cell = find_cell_containing(ws, "muddati")
    edu_type_cell = find_cell_containing(ws, "shakli")
    degree = value_after_dash(degree_cell.value) if degree_cell else ""
    duration = value_after_dash(duration_cell.value) if duration_cell else ""
    edu_type = value_after_dash(edu_type_cell.value) if edu_type_cell else ""
    return degree, duration, edu_type


def output_stem(
    xlsx_path: Path, direction: tuple[str, str] | None, start_year: str
) -> str:
    """Build the output filename stem from the program direction (falling back
    to the source filename), suffixed with the start year when known."""
    if direction is not None:
        code, name = direction
        stem = f"{to_pascal_case(name)}_{code}" if code else to_pascal_case(name)
    else:
        stem = xlsx_path.stem
    return f"{stem}_{start_year}" if start_year else stem


def process_file(xlsx_path: Path) -> None:
    wb = openpyxl.load_workbook(xlsx_path, data_only=True)
    ws = wb.active

    direction = resolve_direction(ws)
    title = direction[1] if direction is not None else xlsx_path.stem

    year_cell = find_cell_containing(ws, "quv yili")
    year_raw = year_cell.value if year_cell else None
    start_year = extract_start_year(year_raw) if year_raw else ""

    degree, duration, edu_type = read_metadata(ws)

    layout, semester_map, weekly_map = detect_sheet_layout(ws)
    core_courses = parse_core_courses(ws, layout, semester_map, weekly_map)
    selective_slots = parse_selective_courses(ws, layout, semester_map, weekly_map)

    OUTPUT_DIR.mkdir(exist_ok=True)
    out_path = OUTPUT_DIR / (output_stem(xlsx_path, direction, start_year) + ".md")
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
