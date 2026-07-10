# Status

Living snapshot of current state — what's in progress, what just landed, and what to watch out for. For product/domain background see `PRD.md`; for coding rules see `CLAUDE.md`.

## Working on now

Nothing in progress. `feat/plans-db` (DB schema + import + workload services, see below) awaits merge. Next planned step: HTMX/Alpine views for study-year course browsing, tanlov selection, delegation, and the teacher-deficit report — the service functions in `plans/services.py` are the ready-made backend for these.

## Done recently

- **`plans` app: full DB layer for curricula and teacher workload** (branch `feat/plans-db`). Models: `OquvReja` (intake; manual `talabalar_soni`/`guruhlar_soni`), `Guruh` (named groups synced from the count), `Fan` + `FanVariant` (every curriculum line is a slot with 1+ variants; majburiy auto-selects its single variant, tanlov stays pending until the office head selects — only the selected variant counts in demand), `FanSemestr` (materialized per-semester hours via largest-remainder split of course totals weighted by weekly hours), `Yuklama` (delegation rows; partial unique indexes forbid double-assigning a group / second lecture teacher). Hour demand: lecture ×1, amaliyot/laboratoriya/seminar × group count, kurs ishi 2h × student (owner policy; lands on the course's last semester).
- `import_reja` management command (`--replace` preserves kafedra links + tanlov selections and refuses when yuklamalar exist; `--yil` covers sheets missing the o'quv yili cell — `sources/BHA.xlsx` needs it). `plans/services.py`: demand/allocated/qoldiq reports per reja/kurs/kafedra, per-teacher annual hours, `yuklama_kamomadi` deficit report vs `min_soat`. Django admin is the interim UI (selection form, talab/taqsimlangan/qoldiq columns, autocompletes). 68 Django tests in `plans/tests/`.
- `parser/` converted to a package (CLI is now `python -m parser.main`; `read_metadata` moved into `parser/parser.py`) so Django imports its functions directly.
- Phase 2 structural refactor: introduced `models.py` (`ColumnLayout`, `Course`, `Alternative`, `SelectiveSlot`), unified numeric coercion (`_to_int`/`_cell_int`), split `detect_course_columns` into focused helpers, unified the core/selective parse loops behind `_iter_section_rows` + `_breakdown`, and moved direction resolution fully into `parser.py`.
- Phase 1 correctness fixes: fixed `"Jami"` (no colon) stop-condition bug that broke selective slot 2.04 in `60110100_ppd.xlsx`; added credit-mismatch warning (hours/30 vs. sum of per-semester credits); added a warning when program duration can't be parsed; added `_clean_name` to strip stray newlines/`|` from course names.
- Selective course (tanlov fanlar) parsing, weekly-hours columns, and per-alternative hour breakdowns added.
- Three-module split: `parser.py` (extraction), `formatter.py` (Markdown rendering), `main.py` (orchestration/CLI).

## Watch out

- **Every spreadsheet is a different shape.** All historical bugs came from assuming one sample file's layout was universal — never hardcode column indices; always keyword-search or anchor-relative (see `CLAUDE.md` Known Edge Cases).
- Course numbers sometimes carry trailing periods (`"1.00."`); already normalized via `.rstrip(".")`, but any new comparison against a raw course-number string needs the same treatment.
- The `"Jami"` stop-condition matches with or without a trailing colon, and scans all cells in the row — don't narrow it back to the name column only.
- Direction metadata can be split across two vertically adjacent rows (`mmt_23.xlsx`); `resolve_direction` already handles this.
- `sources/BHA.xlsx` has garbled merged metadata cells (program name imports as the whole blob) and no o'quv yili cell — parser hardening for the metadata region is still open; the importer stores a single-line, length-capped version and requires `--yil`.
- `Yuklama.soat` is denormalized (computed in `save()`); re-import is blocked while yuklamalar exist, so it can't go stale today — but any future "edit hours in place" feature must recompute it. The kurs-ishi over-allocation check is `clean()`-level only (not a DB constraint).
- Tests use Django's built-in runner (`python manage.py test plans`), not pytest — pytest isn't in `requirements.txt`.
- The `/ship` skill has been removed; there is no automated commit/push/log workflow currently wired up.
