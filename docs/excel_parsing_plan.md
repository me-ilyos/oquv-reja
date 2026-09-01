# Excel Parsing Correctness Plan

Plan for fixing the two unreliable areas of `parser/parser.py`: program metadata ("general
info") and per-course credits/hours. For the document layout this plan repeatedly cites, see
`oquv_reja_map.md`. For the domain rules, see `PRD.md`. For current state, see `status.md`.

Findings below are grounded in the 18 real 2024-25 files now in `sources/`.

---

## 1. Context

`parser/parser.py` reads the ministry O'quv Reja `.xlsx` files entirely by heuristic text search.
Two areas are unreliable:

1. **General info (metadata)** — direction code/name, degree, duration, education form, start
   year. Every field independently degrades to `""` or a hardcoded default, with at most a
   `print()`. `status.md` already records this as an open bug.
2. **Credits and hours** — the most important data in the document. The per-semester credit and
   weekly-hour columns are located via a header row of logical column numbers that
   `oquv_reja_map.md` §4.4 says is **not present in all files**; when it is missing, every course
   silently gets zero credits and zero weekly hours.

The failure mode throughout is *silent plausibility*: a wrong column produces numbers that look
like real hours, and the warnings that would flag it are `print()` calls, invisible in the Django
import path.

**Intended outcome:** structural detection either succeeds or raises a specific, actionable
error; per-row data problems become a structured warning list visible in both the CLI and the web
upload result; and the sheet's own redundancy (section totals, `hours == credits × 30`,
`classroom == lecture + practice + lab + seminar`) is used to verify that detection landed on the
right columns.

### Decisions

| Decision | Choice |
|---|---|
| Sheet selection | **Always the first sheet.** Never `wb.active` — see W1 |
| Fractional credits | Keep integer storage. Normalize `"1,5"` so it parses, then **warn** on any non-integral value instead of silently truncating. No model migration |
| Failure policy | **Fail fast on structure, warn on data** |

---

## 2. Workbook-level defect

| # | Defect | Fix |
|---|---|---|
| W1 | Both entry points open `wb.active` (`parser/main.py:37`, `plans/importer.py:67`). All 18 files in `sources/` carry 2–3 sheets — one per education form (`kunduzgi` / `sirtqi` / `kechki`) — and in **6 of 18 the active sheet is not the first one**, so the tool silently imports a different education form than intended | Use `wb.worksheets[0]`, per the map's standing rule. Warn, naming the sheet, when the workbook has more than one sheet so the discarded forms are visible |

> `oquv_reja_map.md` states **"always parse the first sheet only"**. `wb.active` is the sheet that
> happened to be selected when the file was last saved — it is not the first sheet, and nothing
> in the format guarantees the two agree.

Two workbooks also carry an empty junk sheet (`Sheet1`, `Лист1`); reading only the first sheet
avoids them.

---

## 3. General info (metadata)

All in `parser/parser.py` unless noted. Reference: `oquv_reja_map.md` §2.

| # | Defect | Fix |
|---|---|---|
| M1 | `find_cell_containing` (`:18`) is **case-sensitive** — a sheet writing `AKADEMIK DARAJA` yields `""` | Casefold both sides. Also normalize the apostrophe family (`'` `'` `‘` `ʻ` `` ` ``) to `'` before matching — the `sources/` filenames alone use three different apostrophes |
| M2 | `resolve_direction` (`:46`) requires the literal `"nalishi:"`, so the **colon is mandatory**; the map's split label/value format (label in one cell, value in a neighbouring cell) is missed entirely | Search `"nalishi"`; take the value from, in order: the same cell → the cell to the right → the cell below. Accept the first that contains a 6–9 digit code |
| M3 | `value_after_dash` (`:26`) splits only on `" - "`, with surrounding spaces required | Split on `\s*[-–—:]\s*`. Covers the map's `-4 yil` (no space) and the en-dash `–` that produces the garbled program-name blob |
| M4 | `extract_start_year` (`:64`) matches only `2023/2024`; map §2.2 documents `2025-2026` as equally common. In the Django path this is a **hard failure** (`importer.py:92`) | Regex `(\d{4})\s*[-/–]\s*\d{4}` |
| M5 | `_extract_program_years` (`:90`) silently defaults to 4 — and duration drives the credit-column window, so this quietly corrupts every credit on a 3- or 5-year program | Raise `ParseError`. Also accept `4,5 yil` / `4.5 yil` via `(\d+(?:[.,]\d+)?)\s*yil`; semesters = `round(years * 2)` (map §4.3 lists 9-semester programs) |
| M6 | The duration regex is duplicated in `plans/importer.py:99` (`_davomiylik_yillari`) with its **own** silent default of 4 | Delete it; call the parser's function. `OquvReja.davomiylik_yil` stays an int — store `ceil` for the 4.5 case and note it in a warning |
| M7 | `_bir_qatorga(direction[1], 255)` (`importer.py:77`) truncates the garbled blob rather than fixing it | Keep as a safety net; M2 + M3 remove the cause |

`read_metadata` (`:69`) keeps its `""`-on-absent behaviour for degree and education form — those
are informational, not structural — but each now emits a warning.

---

## 4. Credits and hours

### 4.1. Anchor and course columns

| # | Defect | Fix |
|---|---|---|
| H1 | `_find_anchor` (`:100`) matches only `^1\.00\.?$`. Map §5.1 lists `1.0`, `1`, `1,00`, `1,0`; and a cell stored as the **number** `1.00` stringifies to `"1.0"`, which never matches | Normalize comma→dot, strip trailing dots, compare against the documented set. Disambiguate a stray numeric `1.0` by preferring a matching row that also contains `majburiy`; fall back to the bare marker with a warning |
| H2 | An anchor miss returns `ColumnLayout(0,1,2,…,9)` with **no warning** (`:281`) — the sheet is then parsed against columns A–J and yields pure garbage | Raise `ParseError` |
| H3 | `find_total_hours_col` (`:213`) scans **rows 1..start_row, every column** for the substring `soat`. That window spans the metadata block and the whole academic-calendar zone, so any earlier `soat`-stemmed cell hijacks the column | Restrict the search to the header band (`auditoriya_row - 2 … start_row`); match `umumiy yuklama` first (map §4.3 label table), falling back to `soat` **within that band only** |
| H4 | The `or` fallback idiom (`:215`, `:269-273`) treats a legitimately detected **column index 0** as "not found" | Explicit `is None` checks |
| H5 | `_find_subcategory_cols` (`:266`) tests `"kursish" in norm`, but `Kurs loyihasi (ishi)` normalizes to `kursloyihasiishi` — no match, so the column falls back to a wrong offset. Map §8 records this exact file (Turizm, layout C) | Test `"kurs" in norm`, ordered after the other four labels so it cannot shadow them |
| H6 | Unmatched subcategory labels fall back to `classroom_col + 1…5` — wrong under the 2-apart (Turizm) and 5-apart (Boshlangich) spacings the map documents. Map: **always search by label, never by offset** | Raise `ParseError` when `ma'ruza` or `amaliy` is absent (map: always present). For `laboratoriya` / `seminar` / `kurs ishi`, an absent header means 0 hours **and a warning** — never a guessed offset |
| H7 | `_find_classroom_col` (`:232`) falls back to `hours_col + 2` silently | Same treatment — raise |

### 4.2. Semester credit and weekly-hour columns

The largest source of wrong credit data.

| # | Defect | Fix |
|---|---|---|
| S1 | `detect_weekly_hours_columns` (`:178`) hardcodes the range `[12, 19]` regardless of `years` — a 4-year assumption. On a 3-year program the weekly block is logical 12–17 and credits 18–23, so `[12,19]` straddles both blocks and the consecutive-run test makes the outcome depend on which cells happen to be populated. On a 5-year program it can never match | Derive both windows from `n = semesters`: weekly `lo=12, hi=11+n, offset=11`; credits `lo=12+n, hi=11+2n, offset=11+n` (the credit formula at `:165` is already correct) |
| S2 | Both maps depend on the logical column-number row (`1,2,…,29`), which map §4.4 states is **not present in all files**. Absent → both maps come back `{}` → **every course gets zero credits and zero weekly hours**, reported only as a `print()` | Add a label-driven primary strategy per map §4.3: locate the weekly group header (`haftalar soni` / `Kurslardagi haftalar`) and the credit group header (`kredit`), then read the consecutive `1..N` sub-number row beneath each. Keep the logical-number-row scan as a fallback. Raise `ParseError` when both strategies fail |
| S3 | No sanity check on the detected maps | Cross-validate: each map holds exactly `n` entries; the two are disjoint; every credit column sits to the right of every weekly column. Violation → `ParseError` naming the detected indices |
| S4 | `_detect_col_range` (`:119`) re-runs the full-sheet `_find_anchor` on every call | Pass the anchor in from `detect_sheet_layout` (`:305`), which already computes it |

### 4.3. Value coercion

| # | Defect | Fix |
|---|---|---|
| V1 | `_to_int` (`:316`): `float("1,5")` raises → `None`. In a semester column that **drops the semester from the dict entirely** — silent data loss | Normalize `,`→`.` and strip spaces/NBSP before `float()` |
| V2 | `int(float(v))` truncates toward zero — a 1.5-credit course silently becomes 1 | Warn, naming the raw cell value, then round half-up. Integer storage is retained; the warning is what makes the sheet's own inconsistency visible |
| V3 | A semester present in `semester_credits` but absent from `semester_weekly_hours` gets **no `FanSemestr` row at all**, because `semester_weights` (`plans/split.py:41`) returns weekly whenever it is non-empty. Those credits vanish | Build rows for the **union** of the two semester sets; use weekly as the split weight where present, falling back to credits for a semester weekly omits |
| V4 | `_cell_int` cannot distinguish "merged/blank" from "unparseable", so `breakdown_inheriting` (`:412`) makes an alternative row with a genuinely bad cell inherit the slot's value | Use a distinct sentinel for "unparseable" and warn; inherit only on a true `None` |
| V5 | The workbook is opened `data_only=True` (`main.py:36`, `importer.py:67`). A file never recalculated by Excel has `None` cached values, so every hour reads as absent with no error | When the hours column is entirely `None` across all course rows, re-open with `data_only=False`; if formulas are present, raise `ParseError` telling the user to open and re-save the file in Excel |

---

## 5. Validation against the sheet's own redundancy

The document states its numbers several times over. Use that as proof that column detection
landed on the right columns. These produce warnings (data-level), not errors.

1. **Section totals** — map §5.1: the `1.00` / `2.00` marker row carries the section aggregate in
   the hours columns. Compare it against the sum of the parsed course rows. This is the strongest
   available signal that the hours columns were detected correctly, and is currently unused.
2. **Classroom decomposition** — `classroom == lecture + practice + lab + seminar`. Not checked
   anywhere today.
3. **Credits ↔ hours** — replace `_warn_credit_mismatch`'s floor division (`hours // 30`,
   `models.py:64`) with an exact `hours == credits × 30` test that reports the remainder. Also
   fire when `semester_credits` is empty while `hours` is not: the check currently returns early
   (`:351`) at exactly the moment detection failed.
4. **Skip rows** — map §5.4 documents `Jami:`, `Malakaviy amaliyot`, `Yakuniy davlat
   attestatsiyasi`, `Hammasi`. `parse_core_courses` (`:491`) silently `continue`s **any**
   non-course-number row, violating `CLAUDE.md`'s "never silently skip malformed rows". Recognize
   the documented rows explicitly; warn on anything else skipped.
5. Deduplicate `derived_credits`, which exists three times (`parser/models.py:58`, `:92`,
   `plans/models.py:131`).

---

## 6. Execution order

Each phase is independently committable, tests green before moving on.

| Phase | Content | Why first |
|---|---|---|
| 1 | Error + warning plumbing: `ParseError` and a `ParseResult` carrying `warnings: list[str]` in `parser/models.py`; replace every `print("WARNING: …")` (`:56`, `:95`, `:168`, `:180`, `:355`, `:476`) with a collected warning; `parser/main.py` prints them; `plans/importer.py` folds them into `ImportNatija.ogohlantirishlar` | Every later phase reports through it, and it makes existing failures visible in the web upload path for the first time |
| 2 | W1 (first sheet) + §3 metadata | Smallest, highest-confidence wins; W1 alone changes which reja 6 files import |
| 3 | §4 credits and hours | The core fix; depends on M5 for the semester count |
| 4 | §5 validation | Needs phases 2–3 in place to be meaningful |

### Files touched

| File | Change |
|---|---|
| `parser/parser.py` | Bulk of the work — every phase |
| `parser/models.py` | `ParseError`, `ParseResult`, shared `derived_credits` |
| `parser/main.py` | First sheet; print collected warnings |
| `plans/importer.py` | First sheet; drop the duplicate duration regex (`:99`); plumb warnings; semester union |
| `plans/split.py` | `semester_weights` — union of weekly ∪ credits |
| `plans/tests/test_parser.py` | **New** — first tests for `parser/` (none exist today) |
| `plans/tests/test_split.py` | Add the union-of-semesters case |
| `oquv_reja_map.md` | Amend only where a real file contradicts the map |

Not touched: the `plans/models.py` schema (no migration — integer credits retained), and
`parser/formatter.py`.

---

## 7. Verification

1. **Regression baseline, before any edit.** Run `python -m parser.main` over `sources/` and
   archive `output/*.md`. Every later diff is read against this.
2. **Real files.** Verify against at least 2 sheets per `CLAUDE.md`, and specifically these, which
   cover the documented variants:
   - a 4-year `kunduzgi` file — output must be *unchanged* apart from new warnings;
   - a file where `active != first` (Tarix, Psixologiya, Biologiya, Buxgalteriya, Maktabgacha,
     MMT) — proves W1, and the imported `talim_shakli` must change to the first sheet's form;
   - the 3-year program — proves the S1 weekly-column fix;
   - a `Kurs loyihasi (ishi)` file — proves H5.
3. **Per-file assertions.** Direction code is 6–9 digits and the name is a course-title string
   rather than a label blob; start year is a plausible 4-digit year; the credit and weekly maps
   each hold exactly `years × 2` entries; no course has an empty `semester_credits` while having
   a non-null `hours`.
4. **Unit tests** — `python manage.py test plans`. `test_parser.py` covers, using small in-test
   openpyxl workbooks: comma decimals (`"1,5"`), dash vs. slash year, en-dash direction,
   `Kurs loyihasi (ishi)`, a 3-year semester window, a missing column-number row (must find
   columns by label, not raise), and a workbook whose active sheet is not the first.
5. **Failure paths.** Assert `ParseError` is raised — not a silent default — for: no `1.00`
   anchor, missing duration, and undetectable semester columns.
6. **End-to-end Django import.** `python manage.py import_reja "sources/<file>.xlsx" --replace`
   against a scratch DB. Confirm warnings reach the command output, then spot-check one known
   course in the DB (`Fan.jami_soat`, `FanVariant.*_soat`, `FanSemestr.kredit` per semester)
   against the cell values read directly from the sheet.
7. **Web upload path.** Upload the same file through the UI and confirm the warning list renders —
   the point of phase 1, since these were previously invisible there.
8. `ruff format .` and `ruff check .`
