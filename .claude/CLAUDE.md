# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

Parses Uzbek university curriculum plans (*oquv reja*) issued in Excel by the Ministry of Higher Education and Science. Automates work departments previously did by hand: calculating total available teaching hours, distributing them across professors, and splitting multi-semester courses proportionally per semester.

**Users:** Department heads at Uzbek universities. The script is the backend of a planned UI — department heads will eventually run everything through an interface.

**Trigger:** On demand — whenever the department head needs to recalculate workloads or generate updated course templates.

**Output is used for:**
- Professor hour-load tables (who teaches what, and how many hours)
- Course document templates pre-filled with per-semester hour breakdowns for professors
- A future database powering the department management UI

**Scope:** Handles the standardized curriculum Excel format shared by all Uzbek universities.

## Glossary

**Oquv reja** — The official Excel document specifying the full curriculum for a degree program. Covers all courses, their hours, credits, and weekly schedule across every semester.

**Course categories**
| Uzbek term | English | Notes |
|---|---|---|
| Majburiy fanlar | Mandatory courses | Fixed required courses for the degree |
| Tanlov fanlar | Selective courses | Slots where one course is chosen from a sub-list; same hours/credits structure as mandatory |

**Hour structure (per course)**
| Uzbek term | English |
|---|---|
| Auditoriya mashg'ulotlari | Classroom hours (total contact time) |
| — Maruza | Lecture |
| — Amaliy / Amaliy mashg'ulot | Practice session |
| — Seminar | Seminar |
| — Laboratoriya | Lab work |
| — Kurs ishi | Course project |
| Mustaqil ta'lim | Individual / self-study hours |

**Credits:** 1 credit = 30 hours total (classroom + individual).

**Semester:** exactly 15 weeks. Each course states its weekly contact hours, from which per-semester totals are derived.

**Program metadata in the oquv reja**
| Field | Example values |
|---|---|
| Major code | 60110200 |
| Degree type | Bakalavr (Bachelor), Magistr (Master) |
| Program duration | 4 yil (4 years) |
| Study format | Kunduzgi (morning/full-time), Sirtqi (evening/part-time) |

## Commands

```bash
# Parse all files in sources/
python main.py

# Parse specific file(s)
python main.py sources/mmt_23.xlsx
python main.py sources/mmt_23.xlsx sources/60110100_ppd.xlsx

# Install dependencies
pip install -r requirements.txt

# Format code
ruff format main.py parser.py formatter.py

# Lint (check only)
ruff check main.py parser.py formatter.py

# Lint (auto-fix)
ruff check --fix main.py parser.py formatter.py
```

No test suite is configured yet. When adding tests, use **pytest**.

## Linting & Formatting

**Tool:** [ruff](https://docs.astral.sh/ruff/). Config lives in `pyproject.toml`.

```toml
[tool.ruff]
line-length = 88

[tool.ruff.lint]
select = ["E", "F", "W", "I"]
```

Rules enabled: pycodestyle errors and warnings (`E`, `W`), Pyflakes (`F`), import sorting (`I`).

**Always run `ruff format main.py` before committing.** If ruff and a hand-written style choice conflict, ruff wins — don't use `# fmt: skip` to preserve alignment. Consistent auto-formatting is more valuable than local aesthetics.

## Tech Stack

- **Python 3.10+** (uses lowercase `tuple[...]` type hints)
- **openpyxl** — reads `.xlsx` files with `data_only=True` (formulas resolve to cached values)
- **Standard library only** otherwise (`re`, `pathlib`)

## Architecture

Three-module ETL package that reads Uzbek academic plan spreadsheets from `sources/*.xlsx` and writes one Markdown file per spreadsheet to `output/`.

| Module | Role |
|---|---|
| `parser.py` | All Excel-reading logic: metadata extraction, column detection, course parsing |
| `formatter.py` | Renders parsed data to Markdown (`build_markdown`) |
| `main.py` | Entry point: CLI argument handling, file I/O, orchestrates parser + formatter |

### Data flow

```
sources/*.xlsx  →  main.py → parser.py  →  formatter.py  →  output/*.md
```

Each output filename is built from the extracted program name (CamelCase) + direction code + start year, e.g. `MaktabgachaTalim_60110200_2023.md`.

### Processing stages

`main.py` orchestrates four stages per file via `parser.py` and `formatter.py`. Read the code for function-level details — document here only what isn't obvious from reading it.

1. **Metadata extraction** — keyword-searches the first 15 rows for program info (direction, year, degree, duration, study format). Uses cell position, not fixed coordinates.
2. **Column detection** — dynamically locates all column indices by anchoring on the `"1.00"` marker cell and scanning header rows for keywords (see Excel Input Format for why this can't be hardcoded).
3. **Course parsing** — walks rows between section markers, collecting courses with full hour breakdowns.
4. **Output** — assembles and writes one Markdown file per spreadsheet.

### What is NOT implemented yet

- **Semester splitting** — per-semester weekly hours exist in the spreadsheet but are not extracted.
- **Individual hours (mustaqil ta'lim)** — not extracted per course.
- **Professor workload distribution** — mentioned in project goals but no code exists.
- **Database output** — only Markdown is generated.

## Excel Input Format

The parser expects the standardized Ministry curriculum `.xlsx` files. Key structural assumptions:

### Metadata region (rows 1–15)
- Metadata is found by keyword search, not by fixed cell position.
- `"Ta'lim yo'nalishi:"` (or the substring `"nalishi:"`) → direction cell containing `"CODE - Name"`. In some files, the code and name are split across two vertically adjacent rows; the parser checks the cell below if no digit code is found.
- `"quv yili"` → academic year in `"YYYY/YYYY"` format.
- `"Akademik daraja"` → degree type (value after `" - "`).
- `"muddati"` → program duration.
- `"shakli"` → study format.

### Course data region
- Section `1.00` marks the start of mandatory courses (majburiy fanlar).
- Section `2.00` or a row containing `"Jami:"` ends the section.
- Course rows have a dotted number (e.g. `1.01`, `1.02.1`) in the number column.
- **Column positions vary between files** due to merged cells. The parser detects them dynamically — never hardcode column indices.

### Header region for hour columns
- A row containing `"soat"` (hours) indicates the total-hours column.
- A row containing `"auditoriya"` indicates the classroom-hours column.
- The row immediately below the auditoriya header contains subcategory labels (`Ma'ruza`, `Amaliy`, `Laboratoriya`, `Seminar`, `Kurs ishi`), matched by normalized substrings (all non-alpha chars stripped).

## Known Edge Cases

These have already been encountered and handled — do not regress them:

| Issue | File | How it's handled |
|---|---|---|
| Trailing periods on course numbers (`"1.00."` instead of `"1.00"`) | `60110100_ppd.xlsx` | `num_str.rstrip(".")` before all comparisons |
| Direction metadata split across two rows | `mmt_23.xlsx` | Parser reads cell below if no digit code in primary cell |
| Column positions shifted by merged cells | `60110100_ppd.xlsx` | `detect_course_columns` skips `None` gaps instead of using hardcoded indices |
| Encoding variants in labels (`Ma'ruza` vs `Maruza`) | `mmt_23.xlsx` | Labels normalized by stripping all non-alpha chars |
| Typos in header labels (`Labaratoriya`) | `60110100_ppd.xlsx` | Substring match `"laborator"` and `"labarator"` |
| `"Jami:"` appearing in unexpected columns | multiple | Stop condition scans all cells in the row, not just the name column |
| Subcategory column order varies between files | `mmt_23.xlsx` | Columns matched by label text, not by position |

## Coding Conventions

Inferred from the existing codebase — follow these when modifying or extending:

- **Naming:** `snake_case` for functions and variables, `UPPER_CASE` for module-level constants.
- **Private helpers:** prefix with underscore (`_scan_col`, `_int_val`).
- **Type hints:** use on function signatures. Use lowercase generics (`tuple`, `list`, not `Tuple`, `List`).
- **Column detection:** always keyword-search or anchor-relative. Never hardcode column numbers — files vary.
- **Cell value access:** always guard against `None` and non-string types before `.strip()`, regex, or arithmetic.
- **String matching for Uzbek labels:** normalize by stripping non-alpha chars and lowering, to absorb encoding variants, apostrophes, and typos.
- **Logging:** `print()` statements for now. Prefix warnings with `WARNING:`.
- **No external dependencies** beyond openpyxl unless genuinely needed.

## Rules for Generating Code

These are derived from every bug in `.claude/DEVLOG.md`. Follow them or you will reintroduce solved problems.

### General discipline
Applies to any change, not just this project. Listed because these are the failure modes that matter, not generic style advice:
- **Understand before changing.** Read the actual code path you're about to edit. Do not pattern-match to what similar code usually looks like — this codebase's variant-handling is unusual.
- **Don't invent.** Only call functions, libraries, config keys, and file paths confirmed to exist in this repo. If unsure, check the code; never guess an API into existence.
- **Attempt, then ask.** Resolve ambiguity from the code and this file first. Ask only when a real decision genuinely can't be inferred — and when you must assume, state the assumption.
- **Smallest change that works.** Prefer a patch over a rewrite. A diff reviewable in 30 seconds beats a clever restructuring.
- **Don't claim it's done without tracing it.** Before saying a change works, run it (or mentally execute it) against a real input file.

### Scope — do exactly what's asked
- **Change only what the task requires.** Do not refactor, rename, or "tidy" unrelated code in the same edit. The DEVLOG shows surgical, single-purpose changes — match that.
- **The "What is NOT implemented yet" list is a boundary, not a backlog.** Do not opportunistically add semester splitting, professor workload distribution, etc. unless explicitly asked. Adding unrequested features is a defect, not a bonus.
- **Do not change function return shapes or the output format** without being asked. Other code (and the planned UI) depends on them.

### Input — never trust a single sample
- **Every spreadsheet is a different shape.** All five DEVLOG bugs came from assuming one file's layout was universal. Never generalize structure from one file.
- The concrete mechanics that follow from this — dynamic column detection, cell-access guards, label normalization — are in **Coding Conventions**. They are not optional; each maps to a real bug in the Known Edge Cases table.

### Failure — fail loud, never silent
- **Silent empty output is the worst outcome.** If parsing finds zero courses or a metadata field is missing, print a `WARNING:` — do not return empty data quietly. A visible warning beats a clean-looking but wrong result.
- **Keep graceful fallbacks observable.** Fallback column indices and default values are fine, but the degraded path should be detectable, not invisible.

### Verify — test against the known variants
- Before changing detection or parsing logic, mentally run it against **every row in the Known Edge Cases table** plus a normal file. A fix that helps one file but breaks another is a regression.
- After any change, the expected sanity check is: each source file still produces a non-empty course table with the same course count as before.

## Output Format

Each `.md` file contains:

```
# Oquv Reja: {program name}

**Akademik daraja:** {degree}
**O'qish muddati:** {duration}
**Ta'lim shakli:** {study format}

## Majburiy Fanlar (Core Courses)

| # | Code | Name | Hours | Credits | Classroom | Lecture | Practice | Lab | Seminar | Course Proj |
|---|------|------|-------|---------|-----------|---------|----------|-----|---------|-------------|
| ...rows... |

---
**O'quv yili:** {start year}
```

The structure is still evolving. Selective courses, per-semester breakdowns, and professor assignments will be added as new sections.

## Future Direction

The end goal is a department management tool, not a standalone script. Keep this in mind when making changes:

- **Functions should return data structures**, not print directly. `build_markdown` already follows this pattern (returns a string); new features should return dicts/lists that a future API layer can serialize.
- **Separate parsing from rendering.** Parsing functions (`parse_core_courses`, metadata extraction) should not know about Markdown. Output formatting lives in `build_markdown` and future equivalents.
- **Planned features** (in rough priority): selective course parsing → semester hour extraction → professor workload distribution → database/JSON output → UI integration.

## Dev Log

Task history is tracked in `.claude/DEVLOG.md`. Format for new entries:

```
---

**Task:** One-line description of what needed doing
**Solution:** What was changed and why. Name specific functions. Explain design choices when non-obvious.
**Date:** YYYY-MM-DD
```

Append new entries at the top (newest first).