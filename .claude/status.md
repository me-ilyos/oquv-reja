# Status

Living snapshot of current state — what's in progress, what just landed, and what to watch out for. For product/domain background see `PRD.md`; for coding rules see `CLAUDE.md`.

## Working on now

Nothing in progress. Next planned step (per `PRD.md` roadmap): semester hour extraction is partially done (per-course semester credits/weekly hours are extracted); professor workload distribution and database/JSON output are not started.

## Done recently

- Phase 2 structural refactor: introduced `models.py` (`ColumnLayout`, `Course`, `Alternative`, `SelectiveSlot`), unified numeric coercion (`_to_int`/`_cell_int`), split `detect_course_columns` into focused helpers, unified the core/selective parse loops behind `_iter_section_rows` + `_breakdown`, and moved direction resolution fully into `parser.py`.
- Phase 1 correctness fixes: fixed `"Jami"` (no colon) stop-condition bug that broke selective slot 2.04 in `60110100_ppd.xlsx`; added credit-mismatch warning (hours/30 vs. sum of per-semester credits); added a warning when program duration can't be parsed; added `_clean_name` to strip stray newlines/`|` from course names.
- Selective course (tanlov fanlar) parsing, weekly-hours columns, and per-alternative hour breakdowns added.
- Three-module split: `parser.py` (extraction), `formatter.py` (Markdown rendering), `main.py` (orchestration/CLI).

## Watch out

- **Every spreadsheet is a different shape.** All historical bugs came from assuming one sample file's layout was universal — never hardcode column indices; always keyword-search or anchor-relative (see `CLAUDE.md` Known Edge Cases).
- Course numbers sometimes carry trailing periods (`"1.00."`); already normalized via `.rstrip(".")`, but any new comparison against a raw course-number string needs the same treatment.
- The `"Jami"` stop-condition matches with or without a trailing colon, and scans all cells in the row — don't narrow it back to the name column only.
- Direction metadata can be split across two vertically adjacent rows (`mmt_23.xlsx`); `resolve_direction` already handles this.
- No test suite exists yet. When adding tests, use pytest (per `CLAUDE.md`).
- The `/ship` skill has been removed; there is no automated commit/push/log workflow currently wired up.
