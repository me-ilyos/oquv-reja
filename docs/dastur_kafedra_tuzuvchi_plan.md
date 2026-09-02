# Cover page: kafedra prefill + blank Tuzuvchi/Taqrizchilar

## Context

Requirement: on page 2 of the O'quv Dastur cover page (the "Mazkur o'quv
dasturi ... kafedrasi tomonidan taqdim etilgan..." paragraph), the platform
must prefill the department (kafedra) name. The Tuzuvchi (author) and
Taqrizchilar (reviewer) lines must be left empty for the teacher to fill in
themselves.

A reference screenshot showed "Filologiya kafedrasi" hardcoded and
"S.Komilov"/"S.Xashimov" filled in on those lines — but that screenshot was
confirmed (by the user) to be from a manually created reference document, not
actual platform output.

Investigation (reading `plans/dastur/build_template.py`,
`plans/dastur/kontekst.py`, and the compiled `plans/dastur/oquv_dastur.docx`
directly) shows **this requirement is already implemented**, landed in
commit `ce58be2` ("feat(dastur): load cover page verbatim from reference
source docx"), merged to `main` via `050051b`:

- `plans/dastur/kontekst.py:20` sets
  `"kafedra": variant.kafedra.nomi if variant.kafedra else ""`, sourced from
  the real `FanVariant.kafedra` FK (`plans/models.py:167-179`), which is
  populated when an office head delegates the course to a department via
  `kafedraga_biriktirish()` (`plans/services.py:258-267`) — this happens
  before a teacher can access the dastur download, so `variant.kafedra` is
  guaranteed set by then.
- `plans/dastur/build_template.py:181` replaces the reference doc's
  hardcoded `"Filologiya"` run with the `{{ kafedra }}` Jinja tag inside the
  department-attribution paragraph.
- `plans/dastur/build_template.py:185-186` calls
  `_blank_paragraph_after(document, "Tuzuvchi:")` and
  `_blank_paragraph_after(document, "Taqrizchilar:")`, which strip the
  reference doc's sample names ("Komilov", "Xashimov") from the paragraphs
  immediately following those labels.
- Verified directly in the compiled `plans/dastur/oquv_dastur.docx`
  (`word/document.xml`): the attribution paragraph contains
  `{{ university }} {{ kafedra }} kafedrasi tomonidan taqdim etilgan...`, and
  neither "Komilov" nor "Xashimov" appears anywhere in the document.
- `plans/dastur/service.py` `dastur_render()` always renders live from this
  template with no caching, so any current teacher download already
  reflects this behavior.

**Remaining gap**: no test renders a real document and asserts the kafedra
name actually appears in the department-attribution sentence, or that the
Tuzuvchi/Taqrizchilar paragraphs come out empty. `test_muqova_teglari_toldiriladi`
(`plans/tests/test_dastur.py:178-187`) checks course name / bilim_sohasi /
year but not this. This exact class of bug — leftover sample content leaking
through the verbatim-loaded reference file — is easy to silently reintroduce
(e.g. if the reference source docx is ever swapped, or
`_blank_paragraph_after`'s label-matching breaks). Closing this gap is the
concrete follow-up work.

## Approach

Add assertions to `plans/tests/test_dastur.py`, in the existing
`DasturKontekstTest` class (same class as `test_muqova_teglari_toldiriladi`,
which already renders via `dastur_render()` and inspects `hujjat.paragraphs`
— follow that exact pattern, no new fixtures needed).

### 1. Extend `test_muqova_teglari_toldiriladi` (or add a sibling test)

Using the already-rendered `muqova_matni` (joined paragraph text) in that
test:

- Assert the kafedra name from `self.kafedra` (`"Matematika"`, set up in
  `setUp` at line 91-93) appears in the attribution sentence, e.g.
  `self.assertIn("Matematika kafedrasi", muqova_matni)` — pins the literal
  `"{{ kafedra }} kafedrasi"` phrasing from the template so a broken tag
  substitution or reordered sentence fails the test.

### 2. Add a new test asserting the author/reviewer lines are blank

- Render via `dastur_render(self.variant)` (same as `test_render_hujjat_yaratadi`).
- Assert the known leftover sample names from the reference source docx never
  appear: `self.assertNotIn("Komilov", muqova_matni)` and
  `self.assertNotIn("Xashimov", muqova_matni)`.
- Optionally also assert the paragraphs immediately following the
  "Tuzuvchi:" and "Taqrizchilar:" label paragraphs are empty strings, by
  locating those labels in `hujjat.paragraphs` and checking the next
  paragraph's `.text == ""` — catches the case where blanking removes the
  *wrong* paragraph, or a future reference-doc swap adds different sample
  text that isn't literally "Komilov"/"Xashimov".

### 3. `docs/oquv_dastur_map.md`

No change needed — Section 2 (row 10, "Department attribution") and rows
11-12 (Author/Reviewers marked "Teacher fills") already document the correct
target behavior.

## Verification

1. `python manage.py test plans.tests.test_dastur` — new/extended tests
   green, all existing 20 tests still pass.
2. `ruff format .` && `ruff check .`.
3. Manual sanity check (already done during investigation): unzip
   `plans/dastur/oquv_dastur.docx`, inspect `word/document.xml` for
   `{{ kafedra }}` in the attribution sentence and absence of
   "Komilov"/"Xashimov".
