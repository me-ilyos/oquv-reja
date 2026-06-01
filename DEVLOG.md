# Project Dev Log

---

**Task:** Fix crash when direction code regex finds no match in a cell  
**Solution:** `extract_direction` (main.py) called `.group()` directly on the result of `re.search`, which crashed with `AttributeError` when no 6–9 digit code was present in the cell. Fixed by assigning the match result first and guarding with `if match`. Also hardened the `" - "` name split to fall back to the full raw string when the separator is absent. A warning print was added so files without a parseable code are visible at runtime.  
**Date:** 2026-06-01

---

**Task:** Fix `mmt_23.xlsx` direction metadata not being extracted  
**Solution:** In `mmt_23.xlsx` the direction label (`Ta'lim yo'nalishi:`) and its value (`CODE - Name`) were in separate consecutive rows of the same column, while all other files contain both in a single cell. `find_cell_containing` (main.py) previously returned only the string value, so position was lost. Changed it to return the `Cell` object (dropped `values_only=True` from `iter_rows`). In `process_file`, after reading the direction cell's value, the code now checks whether a digit code is present; if not, it reads the cell directly below (`ws.cell(row+1, col)`) and concatenates the two strings before parsing. All callers updated to read `.value` from the returned Cell. Selected this approach (over a full column-scan) because real production files may have metadata spread across multiple columns, so the full-sheet keyword search must be preserved.  
**Date:** 2026-06-01

---

**Task:** Extract missing metadata fields — academic degree, duration, education type  
**Solution:** Three fields (`Akademik daraja`, `O'qish muddati`/`O'quv muddati`, `Ta'lim shakli`) were present in every source Excel file but never extracted or rendered. Added `parse_label_value` helper (main.py) to split a `LABEL - VALUE` cell and return the value half. Added three `find_cell_containing` calls in `process_file` using the substrings `"Akademik daraja"`, `"muddati"`, and `"shakli"`. Updated `build_markdown` to accept and render the three new fields under the title, skipping any that are empty. Kept the existing keyword-search approach rather than switching to an anchor-column scan, because production files may have metadata in multiple columns.  
**Date:** 2026-06-01

---

**Task:** Fix `60110100_ppd.xlsx` producing zero core courses  
**Solution:** Two structural differences in this file caused `parse_core_courses` to silently collect nothing. First, the section markers and course numbers all carry a trailing period (`"1.00."`, `"1.01."`) which the existing equality checks (`num_str == "1.00"`) and the course-number regex (`^\d+\.\d+(\.\d+)?$`) never matched. Fixed by normalising `num_str` with `.rstrip(".")` before every comparison and regex call. Second, the code and name data sat in different columns than the other files (code in col C, name in col F instead of cols B and C), caused by column-spanning merged cells that leave gap `None` entries between real values — the old hardcoded indices `row[1]` / `row[2]` therefore read `None`. Introduced `detect_course_columns(ws)`: it locates the `"1.00"` cell anywhere in the sheet to establish `num_col`, then scans the first real course row after it and picks the first two non-`None` values past `num_col` as `code_col` and `name_col`. Skipping `None` gaps handles merged cells without any explicit merge-aware API. `parse_core_courses` now calls `detect_course_columns` first and uses the returned indices throughout. The "Jami:" stop condition was also widened from checking only the name column to scanning all cells in the row.  
**Date:** 2026-06-01

---

**Task:** Extract total hours, credits, classroom hours, and subcategory hours per course  
**Solution:** Extended `detect_course_columns` (main.py) to locate five additional columns beyond course name/code: total hours (`soat`), total classroom hours (`auditoriya`), and the five classroom subcategories — Lecture (`Ma'ruza`), Practice (`Amaliy`), Lab (`Laboratoriya`), Seminar, and Course Project (`Kurs ishi`). Total hours and classroom are found by scanning header rows up to the `1.00` row for keyword matches using `_scan_col`. Credits are derived by dividing total hours by 30 at parse time. Subcategory columns are found by reading the label row immediately below the `auditoriya` header row and scanning only columns to the right of `classroom_col`; string values are normalised (all non-alpha characters stripped) before matching, which handles encoding variants (`Ma'ruza` in `mmt_23.xlsx`) and a typo (`Labaratoriya` in `60110100_ppd.xlsx`). This label-row approach was chosen over column-number scanning (values 5–10 in an adjacent header row) because the subcategory order is not consistent across files — `mmt_23.xlsx` places Seminar at position 8 and Lab at position 9, the reverse of other files. `parse_core_courses` now emits `hours`, `credits`, `classroom`, `lecture`, `practice`, `lab`, `seminar`, `course_proj` per course dict; `_int_val` helper handles `None` → `"0"` conversion with graceful fallback. `build_markdown` adds all fields as additional columns in the core courses table.  
**Date:** 2026-06-01

---
