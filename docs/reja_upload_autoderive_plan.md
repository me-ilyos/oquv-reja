# Auto-derive bilim/ta'lim sohasi on O'quv Reja upload

## Context

Today `RejaImportForm` (`web/forms/reja.py`) makes AOH type 9 fields by hand on every upload: `bilim_sohasi_kodi/nomi`, `talim_sohasi_kodi/nomi` (always required), plus optional "override if the file is wrong" fields for `yonalish_kodi/nomi`, `talim_shakli`, `daraja`, `boshlanish_yili`. The goal is to cut this down to exactly the 3 fields the task specifies: **major prefix** (`guruh_prefiksi`), **number of students** (`talabalar_soni`), **number of groups** (`guruhlar_soni`) — everything else derived automatically.

`daraja`, `talim_shakli`, `boshlanish_yili`, `yonalish_kodi` are already reliably parsed straight from the Excel file (`parser/parser.py`, confirmed against `docs/oquv_reja_map.md`) — the override fields exist only as a manual-correction escape hatch and can simply be dropped; the pipeline already fails fast (`ImportXato`) if the file is missing something it needs.

`bilim_sohasi`/`talim_sohasi` are the real problem: **nothing in the Excel file carries them** (confirmed against `docs/oquv_reja_map.md` and `docs/PRD.md` §7). PRD §3.1.1 already documents the intended design: *"once extracted, the platform can derive `Bilim sohasi` and `Ta'lim sohasi` from a pre-populated database"* and PRD §3 says *"the AOH maintains the Bilim sohasi and Ta'lim sohasi lookup tables in the platform's database, adding new entries as needed."* This lookup used to exist as a 3-model FK chain (`BilimSohasi` → `TalimSohasi` → `TalimYonalishi`, migrations `0002`–`0007`) and was deliberately flattened away into plain manual `CharField`s on `OquvReja` (migrations `0008`–`0010`) — this task reintroduces that lookup, this time keyed directly off the major code and populated by the AOH once per major via Django admin, not re-typed on every file upload.

The user confirmed via a screenshot of the official classifier table that the hierarchy is: **bilim sohasi → ta'lim sohasi → ta'lim yo'nalishi (major code) → yo'nalish nomi**, and that only the 8-digit major code is reliably read from the uploaded file — name and both sohasi levels come from this table. So the table becomes the authoritative source for `yonalish_nomi` too, not just the sohasi fields (removing the current fragile "extract title from free-text header cell" path from the storage side — the map documents several inconsistent formats for that text).

Confirmed with the user:
- Reference table shape: **flat**, one row per major code, carrying both sohasi levels directly (matches how `OquvReja` already stores them; consistent with the codebase's own earlier flattening decision).
- Maintained via **Django admin** (`plans/admin.py`) — no new UI screens.
- `guruh_prefiksi` stays **optional**, keeping its current fallback to `yonalish_kodi` when blank.

## Implementation

### 1. New reference model — `plans/models.py`

Add `TalimYonalishi`, keyed by the 8-digit major code:

```python
class TalimYonalishi(models.Model):
    """Official classifier row: major code -> field of study / knowledge.

    Maintained by AOH via admin, one row per major, independent of any
    single reja upload. `OquvReja.bilim_sohasi_*`/`talim_sohasi_*`/
    `yonalish_nomi` are populated from here at import time.
    """

    kodi = models.CharField(max_length=20, unique=True)
    nomi = models.CharField(max_length=255)
    bilim_sohasi_kodi = models.CharField(max_length=10)
    bilim_sohasi_nomi = models.CharField(max_length=255)
    talim_sohasi_kodi = models.CharField(max_length=10)
    talim_sohasi_nomi = models.CharField(max_length=255)

    class Meta:
        verbose_name = "Ta'lim yo'nalishi (klassifikator)"
        verbose_name_plural = "Ta'lim yo'nalishlari (klassifikator)"
        ordering = ["kodi"]

    def __str__(self) -> str:
        return f"{self.kodi} {self.nomi}"
```

New migration `plans/migrations/0011_talimyonalishi.py` — plain `CreateModel`, no backfill (table starts empty; AOH adds rows via admin, per PRD §3).

Register in `plans/admin.py`:

```python
@admin.register(TalimYonalishi)
class TalimYonalishiAdmin(admin.ModelAdmin):
    list_display = ("kodi", "nomi", "bilim_sohasi_kodi", "talim_sohasi_kodi")
    search_fields = ("kodi", "nomi")
```

### 2. Resolve the lookup in the importer — `plans/importer.py`

- `parse_xlsx`: drop the `yonalish_kodi`, `yonalish_nomi`, `talim_shakli`, `daraja` override kwargs entirely — always use the parsed values (`natija.direction_code`, etc). Keep `boshlanish_yili` as an optional positional param; it stays as the CLI's `--yil` escape hatch (`import_reja.py`), unrelated to the AOH web upload flow this task targets.
- `import_reja`: replace the `bilim_sohasi_kodi/nomi`, `talim_sohasi_kodi/nomi` kwargs with an internal lookup:
  ```python
  try:
      yonalish = TalimYonalishi.objects.get(kodi=parsed.yonalish_kodi)
  except TalimYonalishi.DoesNotExist as exc:
      raise ImportXato(
          f"{parsed.yonalish_kodi} yo'nalishi klassifikatorda topilmadi — "
          "avval admin panelda bilim/ta'lim sohasini qo'shing"
      ) from exc
  ```
  Use `yonalish.nomi`, `yonalish.bilim_sohasi_kodi/nomi`, `yonalish.talim_sohasi_kodi/nomi` in the `yangilanadigan` dict inside `_rejani_tayyorlash` (replacing `parsed.yonalish_nomi` and the old kwargs). This keeps the fail-fast pattern the codebase already uses (`c2e4c95`) — a missing classifier entry blocks the import with an actionable message instead of silently storing blanks.

### 3. Shrink the upload plumbing

- `plans/uploads.py`: `YuklashParametrlari` shrinks to `guruh_prefiksi: str`, `talabalar_soni: int`, `guruhlar_soni: int`, `replace: bool`. `fayldan_import_qilish` calls `parse_xlsx(yol)` (no overrides) and `import_reja(parsed, replace=parametrlar.replace)` (no sohasi kwargs).
- `web/forms/reja.py`: `RejaImportForm` shrinks to `fayl`, `talabalar_soni`, `guruhlar_soni`, `guruh_prefiksi` (unchanged, still optional), `replace`. Drop the other 9 fields and update `parametrlar()` accordingly. `RejaTahrirForm` (the post-import manual-correction screen) is untouched — it stays available as an escape hatch if the classifier data or parsed values ever need a manual fix on an existing reja.
- `web/templates/web/office/rejalar/yangi.html`: remove the "Bilim sohasi" section, "Ta'lim sohasi" section, "Fayldan boshqacha bo'lsa (ixtiyoriy)" section, and the standalone `boshlanish_yili` field. Keep `fayl`, `talabalar_soni`, `guruhlar_soni`, `guruh_prefiksi`, `replace`.
- `plans/management/commands/import_reja.py`: drop the four now-required `--bilim-sohasi-kodi/nomi`/`--talim-sohasi-kodi/nomi` CLI args; call `import_reja(parse_xlsx(path, boshlanish_yili=options["yil"]), replace=options["replace"])`.

### 4. Tests

- `plans/tests/test_importer.py`: the local `import_reja()` wrapper currently injects default sohasi kwargs for major code `60610100` (see `make_parsed`) — replace that with seeding one `TalimYonalishi(kodi="60610100", ...)` row per test (or a shared `setUp`/factory helper). Add a new test asserting `ImportXato` when `parsed.yonalish_kodi` has no matching `TalimYonalishi` row.
- `plans/tests/test_uploads.py`: `_parametrlar()` drops the sohasi kwargs; seed a `TalimYonalishi` row matching `sources/BHA.xlsx`'s actual major code before each test that expects success (find the code by running the parser against that file, or checking existing test expectations).
- `web/tests/test_office_rejalar.py`: update posted form data to the new field set; seed a matching `TalimYonalishi` row before posting to the upload view.
- `plans/tests/factories.py`: `make_reja` creates `OquvReja` directly (bypasses `import_reja`), so it needs no change; optionally add a `make_yonalish(**kwargs)` builder for the new tests above, following the file's existing plain-builder-function style.

### 5. Untouched, confirm no regressions

- `plans/dastur/kontekst.py` reads `reja.bilim_sohasi_kodi/nomi`, `reja.talim_sohasi_kodi/nomi`, `reja.yonalish_kodi/nomi` straight off the `OquvReja` instance — no change needed, since those fields are still populated at import time, just derived instead of hand-typed.
- `plans/services.guruhlarni_sinxronlash` (`guruh_prefiksi` fallback to `yonalish_kodi`) is unchanged per the user's decision.

## Verification

1. `ruff format .` / `ruff check .`.
2. `python manage.py makemigrations plans` (expect one migration adding `TalimYonalishi`), then `python manage.py migrate`.
3. `python manage.py test plans web` — update the tests listed above first so they seed `TalimYonalishi` rows; confirm the new "missing classifier entry" test fails fast with `ImportXato`.
4. Manual pass: in `/admin`, add a `TalimYonalishi` row for one sample file's major code (check `sources/*.xlsx` headers for the code), then upload that file through `office:reja_yangi` entering only prefix/students/groups — confirm the created `OquvReja` has correct `bilim_sohasi_*`/`talim_sohasi_*`/`yonalish_nomi`, and that uploading a file whose code has no classifier row produces a clear on-screen error instead of a 500 or blank data.
