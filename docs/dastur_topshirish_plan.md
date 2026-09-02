# O'quv Dastur submission & AOH review

## Context

Per `PRD.md` §2.1/§2.3: after a department head delegates a course (`Yuklama`),
the teacher does not yet own it. The teacher must download the pre-filled
O'quv Dastur (already implemented: `plans/dastur/service.py:dastur_render`,
served via `men:dastur`), fill it in, and submit it back. The AOH then
reviews it — accept, decline (with feedback), or leave pending — and only an
accepted submission confirms course ownership. Today there is no submission
or review path at all: `men:dastur` is a one-way download, and no model,
view, or admin surface tracks a submitted file or its review state. This
plan adds that loop.

Multi-teacher courses: only the lecture owner may submit (PRD §2.3, "must be
submitted by the lecture owner"). That check already exists —
`plans/dastur/service.py:dastur_egasimi(variant, oqituvchi)` returns whether
`oqituvchi` holds the `MARUZA` `Yuklama` for a `FanVariant` — and this
feature reuses it unchanged as the submit-permission gate.

## Data model

New model in `plans/models.py`, alongside the existing `FanTuri`/`SoatTuri`
`TextChoices` pattern:

```python
class TopshirishHolati(models.TextChoices):
    KUTILMOQDA = "KUTILMOQDA", "Ko'rib chiqilmoqda"
    QABUL_QILINDI = "QABUL_QILINDI", "Qabul qilindi"
    RAD_ETILDI = "RAD_ETILDI", "Rad etildi"


class DasturTopshirish(models.Model):
    variant = models.OneToOneField(FanVariant, on_delete=models.CASCADE,
                                    related_name="dastur_topshirish")
    oqituvchi = models.ForeignKey(OqituvchiProfil, on_delete=models.PROTECT,
                                   related_name="dastur_topshirishlari")
    fayl = models.FileField(upload_to="dasturlar/%Y/")
    holat = models.CharField(max_length=20, choices=TopshirishHolati.choices,
                              default=TopshirishHolati.KUTILMOQDA)
    izoh = models.TextField(blank=True)          # AOH's decline reason
    yuborilgan_vaqt = models.DateTimeField()
    korib_chiqilgan_vaqt = models.DateTimeField(null=True, blank=True)
    korib_chiqqan = models.ForeignKey(Foydalanuvchi, null=True, blank=True,
                                       on_delete=models.SET_NULL, related_name="+")
```

Design decisions:

- **One row per `FanVariant` (`OneToOneField`), not a history table.**
  PRD says the teacher "revises and resubmits" — a single evolving record
  matches that and avoids an unrequested history feature. Resubmission
  overwrites the file and resets `holat` to `KUTILMOQDA`, clearing
  `izoh`/`korib_chiqilgan_vaqt`/`korib_chiqqan`.
- **`FileField`, not the `plans/uploads.py` manual-chunked-save pattern.**
  That existing pattern (`_faylni_saqlash`) exists because the Excel reja is
  parsed once and only the parsed data matters afterward — the file itself
  is never served again. Here the AOH must open/download the exact
  submitted file, which is what `FileField` + `MEDIA_ROOT` is for. This is
  the first model `FileField` in the codebase; `settings.py:138` already
  anticipated this ("Uploaded curriculum files (used from a later phase)").
- **No new "ownership" field/property anywhere.** `dastur_egasimi()` keeps
  meaning "is the lecture owner" (used to gate who may submit and
  re-download); "is the AOH-accepted owner" is simply
  `DasturTopshirish.holat == QABUL_QILINDI`. Nothing else in the app
  currently branches on ownership, so no wider rename/refactor is needed.

Migration: one `makemigrations plans` after adding the model.

## Service layer — `plans/dastur/topshirish.py` (new module)

Mirrors the existing `plans/dastur/service.py` (generation) as a sibling
module for submission/review, per CLAUDE.md's "one module = one
responsibility":

- `dastur_topshirish(variant, oqituvchi, fayl) -> DasturTopshirish` — checks
  `dastur_egasimi`, raising `ValidationError` if the caller isn't the
  lecture owner (same exception type/convention as `plans/services.py`,
  caught the same way in views); creates or overwrites the row, deletes the
  old file from storage on overwrite, sets `holat=KUTILMOQDA`,
  `yuborilgan_vaqt=now()`, clears review fields.
- `dastur_qabul_qilish(topshirish, admin) -> None` — sets
  `holat=QABUL_QILINDI`, stamps `korib_chiqilgan_vaqt`/`korib_chiqqan`.
- `dastur_rad_etish(topshirish, admin, izoh) -> None` — same, but
  `holat=RAD_ETILDI`; raises `ValidationError` if `izoh` is blank (AOH must
  give feedback per PRD).

## Forms — `web/forms/dastur.py` (new)

- `DasturTopshirishForm(forms.Form)` — single `fayl` `FileField`
  (`.docx` accept), with a `clean_fayl` extension check. Same shape as
  `web/forms/reja.py:RejaImportForm`.
- `DasturRadEtishForm(forms.Form)` — single required `izoh` `Textarea`.

## Views

**Teacher side** — `web/views/men.py`, next to the existing
`MenOquvDasturView`:

- `MenDasturTopshirishView(OqituvchiTalabMixin, View)` — `POST
  /men/kurs/<variant_id>/dastur/topshirish/`. Same ownership guard as
  `MenOquvDasturView` (`dastur_egasimi`), validates the form, calls
  `dastur_topshirish`, redirects back to `men:yuklamalar` with a
  `messages` success/error — matching the plain redirect+messages flow
  already used by `RejaImportView`/`semestrovka_saqlash`, not HTMX (no
  partial-refresh benefit here; the whole row's state changes).

**AOH side** — new `web/views/office/dastur.py`, registered under
`office:` (`OfficeAdminTalabMixin`, matching `RejaListView`'s pattern):

- `DasturTopshirishlarView(OfficeAdminTalabMixin, ListView)` — lists all
  `DasturTopshirish` rows, optional `?holat=` filter, newest first.
- `dastur_qabul(request, pk)` — `@require_POST @office_admin_talab`
  function view, redirect+messages (matches `semestrovka_saqlash`).
- `dastur_rad(request, pk)` — same shape, validates `DasturRadEtishForm`.
- `dastur_fayl(request, pk)` — `@office_admin_talab` GET view, streams the
  stored file back via `FileResponse` so the AOH can open/download what was
  submitted before deciding.

URLs: `web/urls_men.py` gets one new `path(...)`; `web/urls_office.py` gets
four new `dasturlar/...` paths, following the existing `rejalar/...` list.

## Templates

- `web/templates/web/men/yuklamalar.html` — in the existing per-row action
  cell (currently just the "Dasturni yaratish" download link, gated on
  `yuklama.tur == "MARUZA"`), add: a status tag (reusing the `.tag`/
  `.tag-mand`/`.tag-elec` CSS classes already in `app.css`, plus one new
  `.tag-rad` for declined) showing `KUTILMOQDA`/`QABUL_QILINDI`/
  `RAD_ETILDI`, the AOH's `izoh` when declined, and a small inline
  multipart upload form. The view's queryset adds
  `select_related("fan_semestr__variant__dastur_topshirish")` so the
  template can read `yuklama.fan_semestr.variant.dastur_topshirish` with no
  extra query (a missing reverse `OneToOne` renders as empty in Django
  templates — no `{% if %}` crash risk).
- New `web/templates/web/office/dasturlar/list.html` — table modeled on
  `web/templates/web/office/rejalar/list.html` (search/filter header,
  `table-wrap narrow cards`), columns: course, kafedra, teacher, submitted
  time, status, and per-row actions (open file, accept, decline-with-reason
  inline form) — same non-HTMX redirect style as the oqituvchilar delete
  button in `_jadval.html`.
- `web/templates/web/parts/_navbar.html` — add a "Dastur topshiriqlari"
  link in the `user.is_office_admin` block, next to the existing
  Kafedralar/O'qituvchilar links.

## Admin

Register `DasturTopshirishAdmin` in `plans/admin.py` (list/filter/search,
`autocomplete_fields` on `variant`/`oqituvchi`/`korib_chiqqan` — the
targets already expose `search_fields` for this), as a fallback/inspection
surface alongside the new web UI, matching how `YuklamaAdmin` coexists with
the `/kafedra/` delegation UI.

## Tests

- `plans/tests/test_dastur_topshirish.py` — service-level: only the lecture
  owner can submit (reuses the `DasturEgasimiTest` fixture pattern from
  `plans/tests/test_dastur.py`); resubmission overwrites the row and resets
  `holat`/clears review fields (and the old file is deleted from storage);
  accept/decline transitions and their stamped fields; decline requires a
  non-blank `izoh`.
- `web/tests/test_men_views.py` — submit view: 403 for a non-owner, success
  redirect + `DasturTopshirish` created for the owner, rejects non-`.docx`.
- New `web/tests/test_office_dastur_views.py` — list view role-gating
  (`OfficeAdminTalabMixin`), accept/decline POST endpoints change `holat`,
  file-download view streams the right content.

## Verification

- `python manage.py makemigrations plans` then `python manage.py migrate`.
- `python manage.py test plans web` — all green, including new tests above.
- `ruff format .` && `ruff check .`.
- Manual: as a teacher, submit a `.docx` on `/men/`, confirm the status tag
  updates; as AOH, open `/office/dasturlar/`, download the file, accept and
  decline (with/without a reason) and confirm the teacher's row reflects
  the new status and feedback.
