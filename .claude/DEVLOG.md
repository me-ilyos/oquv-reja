# Project Dev Log

---

**Task:** Parse selective courses (tanlov fanlar), add weekly hours columns, fix semester range for sub-8-semester programs, and handle per-alternative hour breakdowns
**Solution:** Added `parse_selective_courses(ws)` to `parser.py` — walks section 2 rows, reads numeric slot data from the merged top-left row per slot, and collects alternatives by inheriting slot defaults when continuation rows are `None` (merged case) or using their own values when non-`None` (non-merged, e.g. `mt_23.xlsx` slot 2.01 where SITQ2 has 0 lecture but MTSTE204 has 60). Breakdown fields (classroom, lecture, practice, lab, seminar, course_proj) were moved from slot-level into each alternative dict with `_breakdown_defaults` as a private slot-level fallback. Extracted a shared `_detect_col_range(ws, lo, hi, offset)` helper so both `detect_semester_columns` and the new `detect_weekly_hours_columns` reuse the same scan logic. Credit columns (20–27 for 4-year, 18–23 for 3-year) are now derived dynamically as `lo=12+N, hi=11+2N, offset=11+N` so programs shorter than 4 years map correctly. `build_markdown` extended with `selective_slots` parameter, interleaved `S{n}|W{n}` semester columns, and a new "## Tanlov Fanlar" table section.
**Date:** 2026-06-08

---

**Task:** Fix semester detection bleeding into "Kredit taqsimoti" section on sub-8-semester programs
**Solution:** For a 3-year (6-semester) program like `mt_23.xlsx`, the column-numbering row places the "Semestrdagi auditoriya" section at global columns 12–17 and the "Kredit taqsimoti" section at 18+. The previous detector looked for unique consecutive values in [12, 19], so columns 18–19 of the Kredit section were incorrectly captured as semesters 7–8. Fixed by adding `_extract_program_years(ws)` (reuses existing `find_cell_containing(ws, "muddati")`, parses `"N yil"`, defaults to 4) and filtering the detected map to `sem_num <= years * 2` at the end of `detect_semester_columns`.
**Date:** 2026-06-08

---

**Task:** Extract per-semester classroom hours for each course and render as S1–SN columns
**Solution:** Added `detect_semester_columns(ws)` to `parser.py`, which locates the column-numbering row (values 12–19 unique and consecutive) in the 10-row window immediately above the `1.00` marker, and returns `{col_idx: semester_num}`. Uses bottom-up scan (`last_match`) to avoid an earlier false-positive metadata row present in some files. Added `_extract_semester_credits(row, map)` to pull non-zero values from semester columns per course row, stored as `semester_credits: dict[int, str]` in each course dict. `build_markdown` in `formatter.py` now computes `active_semesters` from the union of all courses' semester keys and appends S1…SN columns dynamically; if detection fails the table renders unchanged.
**Date:** 2026-06-08

---

**Task:** Add CLI argument support for parsing specific files and update CLAUDE.md architecture docs
**Solution:** Added `argparse` to `main()` in `main.py` — accepts zero or more positional `files` arguments; when none are given it falls back to globbing `sources/*.xlsx` (existing behaviour). Missing files emit a `WARNING:` rather than crashing. Updated `CLAUDE.md` Commands section to show the specific-file invocation forms, and updated the Architecture section to reflect the three-module structure (`parser.py`, `formatter.py`, `main.py`) that replaced the original single-file description.
**Date:** 2026-06-03

---

**Task:** Repo cleanup — gitignore, untrack sources, reorganize docs into .claude/
**Solution:** Added `sources/`, `__pycache__/`, and `.ruff_cache/` to `.gitignore`; ran `git rm --cached` to stop tracking the six source `.xlsx` files (kept locally). Moved `CLAUDE.md` and `DEVLOG.md` from the project root into `.claude/` using `git mv` so the root stays clean. Updated path references to `DEVLOG.md` in `.claude/CLAUDE.md` and `.claude/skills/ship/SKILL.md`. Deleted `inspect_columns.py` and `inspect_detailed.py` — one-off debug scripts no longer needed now that column detection is stable.
**Date:** 2026-06-03

---

**Task:** Refactor main.py into parser.py, formatter.py, and a slim orchestration entry point
**Solution:** Split the 346-line `main.py` into three focused modules. `parser.py` contains all parsing and extraction logic: string helpers (`is_course_number`, `section_prefix`, `parse_label_value`, `extract_direction`, `to_camel_case`, `extract_start_year`), worksheet helpers (`find_cell_containing`, `_scan_col`, `_int_val`), and the two main parsing functions (`detect_course_columns`, `parse_core_courses`). `formatter.py` contains `build_markdown`. `main.py` is reduced to ~65 lines covering only `process_file` and `main`. No function signatures, logic, or output changed — verified by running against all six source files and confirming identical course counts.
**Date:** 2026-06-03

---

**Task:** Create /ship custom skill for the log → commit → push workflow
**Solution:** Created `.claude/skills/ship/SKILL.md` — a project-level Claude Code skill that automates the post-task workflow: infer the task and solution from conversation context, append a DEVLOG entry at the top of `.claude/DEVLOG.md`, stage and commit all changed files, and push to `main`. Chosen as a skill (over a slash command) for the richer frontmatter and auto-invocation support.
**Date:** 2026-06-03

---

**Task:** Expand CLAUDE.md with full project documentation and set up ruff formatter  
**Solution:** `CLAUDE.md` was significantly expanded beyond the original architecture stub. Added: Tech Stack section, Processing Stages breakdown (4 stages per file), "What is NOT implemented yet" list (selective courses, semester splitting, individual hours, workload distribution, DB output), Excel Input Format section covering all three sheet regions (metadata, course data, header rows), Known Edge Cases table derived from DEVLOG, Coding Conventions, Rules for Generating Code, Output Format sample, and Future Direction guidance. Also added `Laboratoriya` (lab work) to the Glossary hour-structure table which was previously missing. Set up `ruff` (v0.15.15) as the project formatter/linter: added `pyproject.toml` with `line-length = 88` and rules `E, F, W, I`; ran `ruff format main.py` which reformatted long lines and removed manual alignment padding — no logic changes. Added ruff to `requirements.txt`.  
**Date:** 2026-06-03

---

**Task:** Document project purpose, users, and domain terminology in CLAUDE.md  
**Solution:** Added two new sections to `CLAUDE.md`. **Project Overview** explains why the project exists (automate department hour calculation and professor workload distribution), who uses it (department heads via a future UI), when it runs (on demand), and where output goes (hour-load tables, course document templates, future database). **Glossary** defines key Uzbek domain terms: *oquv reja*, course categories (majburiy fanlar / tanlov fanlar), the classroom vs. individual hours split with all subcategory names (maruza, amaliy, seminar, kurs ishi, mustaqil ta'lim), the 1-credit = 30-hour rule, the fixed 15-week semester, and program metadata fields. Also removed the *Excel structure assumptions*, *Key functions*, and *Known edge cases* subsections from `CLAUDE.md` as they are derivable from the code itself.  
**Date:** 2026-06-03

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
