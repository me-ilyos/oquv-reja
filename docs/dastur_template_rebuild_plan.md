# Rebuild the O'quv Dastur DOCX template

> **Superseded (cover page only):** the cover page is no longer generated
> from scratch by this rebuild's python-docx code. See
> `docs/dastur_cover_page_from_source_plan.md` — the cover page is now
> loaded verbatim from `sources/Kiberxavfsizlik_asoslari_fan_dasturi_ATDT.docx`,
> which reverts the cover page (only) to Letter page size. Table 1/Table 2
> below are unaffected and still built the way this doc describes.

## Context

Teachers report that the generated O'quv Dastur (course syllabus) document has formatting that's "a bit off." Investigation found the generation pipeline itself (`plans/dastur/service.py`, `kontekst.py`, `mavzular.py`) is correct and already covered by tests — the bug lives entirely in the Jinja template file `plans/dastur/oquv_dastur.docx`, which `docxtpl` renders. That file was exported from Google Docs rather than authored natively in Word (`docProps/core.xml` shows `creator="Un-named"`, all-zero RSIDs, a `GrammarlyDocumentId` property). This export left it with real, verifiable defects:

- Page size is **US Letter** (12240×15840 twips) — Uzbek official documents use A4.
- Only **72 of ~584** sized text runs carry an explicit `Times New Roman` font; the rest fall back to the document theme's default font (Word 365's "Aptos"), so the rendered doc mixes fonts even though the visible intent is Times New Roman 14pt throughout.
- The `Normal` style is completely empty — every paragraph uses hand-applied direct formatting, no named styles are actually used anywhere in the body. This makes the file fragile: any future manual edit (in Google Docs, the likely original editing tool) risks re-splitting `{{ }}`/`{%tr %}` Jinja tags across runs or reintroducing inconsistent formatting.
- 1.15 line spacing (a Google Docs default) is baked into nearly every paragraph as direct formatting rather than inherited from a style.
- Two of the four hyperlinks in the grading-rubric prose point to Uzbek Wikipedia pages — confirmed present, look like an accidental leftover from drafting, not an intentional citation.

**Decision:** rebuild `oquv_dastur.docx` from scratch as a maintained Python builder script using `python-docx`, rather than patching the existing binary. The script becomes the checked-in source of truth — formatting is "saved" as reviewable code, and regenerating the file becomes a one-command, deterministic operation instead of hand-editing a binary. Confirmed sub-decisions:

- Switch page size to **A4** (was Letter).
- Use clean, standard Word formatting — do not preserve Google-Docs-specific artifacts (e.g. its 1.15 line-spacing default). Use single (1.0) line spacing via the named style.
- **Drop the two Wikipedia hyperlinks** from the grading-rubric prose during the rebuild (keep the surrounding text, just remove the links); keep the two legitimate links (pedagogika.uz, ziyonet.uz).
- Content/wording, table structure, row counts, and all `{{ }}`/`{%tr %}` Jinja tags stay identical — `kontekst.py`, `mavzular.py`, `service.py`, and the existing test suite in `plans/tests/test_dastur.py` must keep working unmodified.

## File layout

```
plans/dastur/
    build_template.py      # new — builds the .docx from code; run manually
    template_text.py       # new — static Uzbek prose as string constants
    oquv_dastur.docx        # regenerated output, committed to git
    kontekst.py              # unchanged
    mavzular.py              # unchanged
    service.py                # unchanged
```

`template_text.py` is split out from `build_template.py` so the ~2 pages of static Uzbek prose (grading rubric, teaching-methods bullets, reference citations) are plain data, not buried in table-construction code, keeping every function in `build_template.py` under the CLAUDE.md ~40-line limit and making text-only fixes a one-line diff.

`requirements.txt` currently pins `docxtpl==0.20.2` but not `python-docx` directly (it's a transitive dependency of docxtpl). Since `build_template.py` will `import docx` directly, add an explicit `python-docx` pin to `requirements.txt`.

## Step 0 — Extract exact static text (read-only pass)

Write a throwaway script `scripts/extract_dastur_text.py` that opens the *current* `oquv_dastur.docx` with `python-docx` and dumps, per paragraph/cell, exact run text plus bold/italic/hyperlink info. Use this to hand-verify and copy the exact wording for: the "Izoh:" comment paragraph, the Table-2 teaching-methods bullets, the credit-requirements paragraph, the full grading-policy prose (locating the two Wikipedia hyperlinks to drop and the two legitimate links to keep), and the 4 reference citations — never retype ~2 pages of Uzbek prose by eye. Delete this script once its output is copied into `template_text.py` (dead code once done, per CLAUDE.md).

## Step 1 — Page setup and named styles

`_set_page_setup(document)`: A4 (`Mm(210) x Mm(297)`), margins matching the original's intent — top `Cm(2)`, bottom `Cm(2.5)`, left/right `Cm(2)` (these reproduce the current 1134/1418/1134/1134 dxa margins almost exactly on the new page size).

`_register_styles(document)`: set `Normal.font.name = "Times New Roman"`, `Normal.font.size = Pt(14)`, `Normal.paragraph_format.line_spacing = 1.0`. Also explicitly set `w:rFonts/@eastAsia` and `@cs` via oxml (python-docx's `font.name` alone only sets `@ascii`/`@hAnsi`) — this is the actual fix for the font-fallback bug, since it makes Times New Roman inherited by every paragraph rather than needing a per-run override. Add derived paragraph styles: `DasturCentered`, `DasturHeading` (bold+centered), `DasturItalic`, `DasturJustify`.

## Step 2 — Table-building helpers

Small, focused helpers (each under ~40 lines) instead of one large imperative function:

- `CellSpec` (frozen dataclass): `text`, `bold`, `italic`, `align`, `span` (gridSpan), `vmerge` (`None`/`"restart"`/`"continue"`), `jinja_run` (for tag cells).
- `RowSpec` (frozen dataclass): `cells: list[CellSpec]`, `shaded: bool`.
- `_merge_row(table, row_idx, spans) -> list[_Cell]` — horizontally merges a row's grid cells per a span list, returns the visible cells in order.
- `_vmerge_cell(cell, mode)` — vertical merge via oxml (`w:vMerge`), which python-docx has no built-in helper for.
- `_shade_row(row, color="D9D9D9")` — cell shading via oxml `w:shd`.
- `_set_cell_text(cell, text, *, bold, italic, align)` — single `add_run()` call per cell.
- `_add_tag_run(cell, tag, *, align)` — writes a Jinja `{{ }}`/`{%tr %}` tag as **one** unsplit run via a single `add_run()` call. This is the critical correctness point: python-docx's `add_run()` never splits text on its own, but the tag string must always be passed whole to one call — never built by concatenating multiple `add_run()`s, which would break docxtpl's tag parser.
- `_build_table_from_spec(document, rows: list[RowSpec], col_widths: list[int]) -> Table` — iterates the declarative row list and applies merges/shading/text, so the 58-row and 17-row tables read as data (a list of `RowSpec`) rather than a wall of imperative calls.
- `_lesson_loop_rows(label, var_name)` — factory for the repeated 5-row `{%tr if%}` / `{%tr for%}` / data row / `{%tr endfor%}` / `{%tr endif%}` block, reused for `lectures`/`practicals`/`labs`/`seminars`.
- `_add_hyperlink(paragraph, text, url)` — python-docx has no hyperlink API; build `<w:hyperlink r:id=...>` manually via `part.relate_to()`, styled blue/underlined (`0563C1`) to match the two links being kept.

Reconstruct, in order: cover paragraphs 1–15 (title, Table 0 approval box, bilim/talim sohasi lines, blank spacers, "Tuzuvchi:"/"Taqrizchilar:"), Table 1 (58×11, all merges/shading/loop blocks per the confirmed row map), the "Izoh:" paragraph, Table 2 (17×2, with hyperlinks), trailing paragraphs, and the A4 footer (centered Times New Roman 12pt page-number field).

Column widths for Table 1: `715, 184, 958, 997, 997, 997, 997, 1243, 1240, 336, 1268` dxa (sum 9932, confirmed against the current file) — keep as-is on A4 since it already fits well within the new page width.

## Step 3 — Build-time self-check

After saving, reopen the file with `docxtpl.DocxTemplate` and call `.get_undeclared_template_variables()`, diff against the known set of top-level context keys `dastur_kontekst()` returns (`university`, `kafedra`, `kafedra_council`, `major`, `education_form`, `year`, `course`, `academic_years_str`, `semesters_str`, `credits_str`, `weekly_hours_str`, `plan_number`, `total_hours`, `classroom_total`, `hours`, `lectures`, `practicals`, `labs`, `seminars`). Raise if any are missing — that means a tag got corrupted (run-split or misspelled) during construction. Wire this into `build_template.py`'s `main()` so it fails loudly before a broken template gets saved/committed.

## Step 4 — Regeneration and regression tests

Run via `python -m plans.dastur.build_template`, which writes `plans/dastur/oquv_dastur.docx` (committed to git as before). Add a new `DasturFormatlashTest` to `plans/tests/test_dastur.py`, following the file's existing pattern of rendering through `dastur_render()` and reopening with `docx.Document`:

- `test_sahifa_olchami_a4` — asserts `section.page_width == Mm(210)` and `page_height == Mm(297)`.
- `test_shrift_times_new_roman` — asserts `Normal` style's font name is Times New Roman.
- `test_sarlavha_qatori_kulrang_fon` — asserts a known header row (e.g. Table 1 row 1) carries `w:shd fill="D9D9D9"`.
- `test_jadval_tuzilishi_saqlanadi` — asserts table count (3) and row counts (58, 17) are unchanged.

All existing tests in `test_dastur.py` (context building, ownership checks, topic-row rendering) must keep passing unmodified, since `kontekst.py`/`mavzular.py`/`service.py` aren't touched.

## Step order / commits

Branch: `feat/dastur-template-rebuild`.

1. `refactor(dastur): extract static template prose into template_text.py` — Step 0, then delete the extraction script.
2. `feat(dastur): scaffold A4 page setup and base styles for template rebuild` — Step 1, manually verify in Word.
3. `feat(dastur): rebuild cover page and approval box` — cover paragraphs + Table 0.
4. `feat(dastur): rebuild main 58-row content table` — Table 1, run the self-check, fix any tag issues.
5. `feat(dastur): rebuild references table and drop stray Wikipedia links` — Table 2 + hyperlinks.
6. `feat(dastur): add A4 footer with page numbering`.
7. `chore(dastur): regenerate oquv_dastur.docx from rebuilt template` — run the builder, commit the output, run `python manage.py test plans.tests.test_dastur` (must stay green).
8. `test(dastur): add formatting regression tests for rebuilt template` — Step 4 tests, then `ruff format .` + `ruff check .`.
9. Update `docs/oquv_dastur_map.md` only if any field mapping actually changed (none should — only underlying formatting changes).

Each checkpoint should be a working, test-green state before moving to the next.

## Verification

- Automated: `python manage.py test plans.tests.test_dastur` — existing tests plus the new `DasturFormatlashTest` all green.
- `ruff format .` and `ruff check .` clean.
- Manual: render a real `FanVariant` through `men:dastur` (or a one-off `dastur_render()` call) and open the resulting `.docx` in actual Microsoft Word — confirm A4 layout, consistent Times New Roman throughout, correct merged cells in Table 1 rows 3–5, gray header shading, and that the two Wikipedia links are gone while pedagogika.uz/ziyonet.uz links still work — since automated tests can't fully catch visual regressions.
