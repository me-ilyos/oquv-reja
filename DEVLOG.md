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
