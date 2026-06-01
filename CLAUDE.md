# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
# Run the parser
python main.py

# Install dependencies
pip install -r requirements.txt
```

No test suite or linter is configured.

## Architecture

This is a single-file ETL script (`main.py`) that reads Uzbek academic plan spreadsheets from `sources/*.xlsx` and writes one Markdown file per spreadsheet to `output/`.

### Data flow

```
sources/*.xlsx  →  main.py  →  output/*.md
```

Each output filename is built from the extracted program name (CamelCase) + direction code + start year, e.g. `MaktabgachaTalim_60110200_2023.md`.

### Excel structure assumptions

All source files share this layout:
- **Metadata block** (rows 1–15, column varies per file): 5 consecutive cells in one column hold the program header. Keywords used to locate each cell via full-sheet scan:
  - `"nalishi:"` → direction line: `Ta'lim yo'nalishi: CODE - Name`
  - `"quv yili"` → academic year: `2022/2023 o'quv yili`
  - `"Akademik daraja"` → degree: `Akademik daraja - BAKALAVR`
  - `"muddati"` → duration: `O'qish muddati - 4 yil`
  - `"shakli"` → education type: `Ta'lim shakli - kunduzgi`

  One known variant (`mmt_23.xlsx`): the direction label and its `CODE - Name` value are split across two consecutive rows. `process_file` handles this by peeking at the row below when no digit code is found in the label cell.

- **Course table**: scanned across the entire sheet. Section `1.xx` (core/mandatory courses) starts at the row where column A equals `1.00` and ends at `2.00` or a `Jami:` row.

### Key functions (`main.py`)

| Function | Role |
|---|---|
| `find_cell_containing(ws, substring)` | Scans rows 1–15 of the full sheet, returns the first `Cell` whose value contains the substring. Returns `Cell` (not string) so position is available for split-cell handling. |
| `extract_direction(raw)` | Extracts 6–9 digit code via regex and splits on `" - "` to get program name. Gracefully returns empty strings on no-match. |
| `parse_label_value(raw)` | Splits a `LABEL - VALUE` string on `" - "` and returns the value half. |
| `parse_core_courses(ws)` | Iterates all rows; collects courses where column A matches `^\d+\.\d+` and the section prefix is `"1"`. |
| `build_markdown(...)` | Assembles the output `.md` from all extracted fields. |
| `process_file(xlsx_path)` | Orchestrates extraction for one file: metadata → courses → write output. |

## Known edge cases

- Files where the direction label and value are in separate rows (e.g. `mmt_23.xlsx`) are handled by the "peek below" logic in `process_file`.
- The metadata column varies between files (Z, AK, AL, AM, AP have been observed). The keyword scan covers the full sheet width, so column position is irrelevant.
- `~$`-prefixed files (Excel lock files) are skipped automatically.

## Dev log

Task history is tracked in `DEVLOG.md`.
