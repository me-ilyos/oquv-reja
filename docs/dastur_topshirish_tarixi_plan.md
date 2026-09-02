# O'quv Dastur submission history & teacher viewing redesign

## Context

Teachers submit an O'quv Dastur, the AOH reviews it, and per the user it
typically takes **4–5 reject/resubmit rounds** before acceptance. Today's
implementation (`docs/dastur_topshirish_plan.md`, already built) deliberately
chose "one row per `FanVariant`, not a history table" — every resubmission
**overwrites** the previous file and **wipes** the prior rejection reason
(`izoh`), reviewer, and review timestamp. Confirmed in
`plans/models.py:395-433` (`DasturTopshirish`, `variant` is a `OneToOneField`)
and `plans/dastur/topshirish.py` (`dastur_topshirish()` does `get_or_create`
+ unconditional overwrite + `fayl.delete(save=False)` on the old file).

With 4–5 rounds being the norm, this loses exactly the information both
sides need most: the teacher can't see what was wrong in earlier rounds to
confirm they've fixed *all* of it, and the AOH (reviewing round 4) can't see
what they told the teacher in rounds 1–3, so they risk repeating feedback or
missing that an old issue crept back in.

Separately, the current "Mening yuklamam" table
(`web/templates/web/men/yuklamalar.html:77-96`) crams the create-link, status
tag, rejection reason, file input, and submit button into one narrow table
cell — workable for a single status, cluttered once there's a growing
history to show. This plan designs a submission-history data model plus a
decluttered way for both the teacher and the AOH to view it.

User-confirmed decisions:
- History view = **HTMX slide-out panel**, reusing the exact pattern already
  proven in `web/templates/web/kafedra/dashboard.html:40-47` +
  `_fs_qatori.html:13-18` (an empty `<div id="panel-{{ pk }}">` row per
  table row, toggled open via `hx-get`/`hx-target`/`hx-swap="innerHTML"`) —
  no new modal component needed.
- **AOH side is in scope too** — `web/templates/web/office/dasturlar/list.html`
  gets the same history visibility, since it's the same underlying model gap.

## Data model — `plans/models.py`

Change `DasturTopshirish` from a mutable "current state" row into an
**append-only attempt log**:

- `variant`: `OneToOneField` → `ForeignKey(FanVariant, related_name="dastur_topshirishlari")`
  (plural — a variant now has many attempts, not one).
- Add `urinish_raqami = models.PositiveSmallIntegerField()` — 1, 2, 3…,
  set at creation as `(latest attempt for this variant).urinish_raqami + 1`
  (or `1` if none exist). Stored rather than computed so templates/queries
  don't need a window function.
- Add `class Meta: ordering = ["-yuborilgan_vaqt"]` so `.first()` /
  `dastur_topshirishlari.all` is newest-first everywhere by default.
- Keep `holat`, `izoh`, `yuborilgan_vaqt`, `korib_chiqilgan_vaqt`,
  `korib_chiqqan`, `fayl` unchanged — these now describe **one attempt**,
  immutable once reviewed, instead of the whole submission's current state.

Migration: schema migration (`AlterField` variant + unique-constraint drop +
new field) followed by a data migration setting `urinish_raqami=1` on every
existing row (today there's at most one row per variant, so this is safe).

## Service layer — `plans/dastur/topshirish.py`

- `dastur_topshirish(variant, oqituvchi, fayl)`: stop overwriting. Look up
  the latest attempt for `variant` (if any); if its `holat == KUTILMOQDA`,
  raise `ValidationError` ("Joriy topshiriq hali ko'rib chiqilmoqda — javob
  kutilsin") — resubmitting over a pending review would otherwise create an
  ambiguous history entry. Otherwise **create a new row** (`urinish_raqami`
  = previous + 1, `holat=KUTILMOQDA`, fresh `yuborilgan_vaqt`). Do **not**
  delete the previous attempt's file — it's now part of the audit trail.
- `dastur_qabul_qilish` / `dastur_rad_etish`: unchanged in shape — they
  still take one `DasturTopshirish` instance (now: one *attempt*) and stamp
  `holat`/`korib_chiqilgan_vaqt`/`korib_chiqqan`. Since past attempts are
  never touched again, past `izoh` stays intact automatically.
- New `eng_songi_urinish(variant) -> DasturTopshirish | None` — thin
  `.dastur_topshirishlari.first()` wrapper (relies on the `Meta.ordering`
  above), used by views/templates instead of the old OneToOne accessor.
- New `joriy_topshirishlar(qs=None) -> list[DasturTopshirish]` for the AOH
  list page — one row **per variant** (its latest attempt only), not one
  row per historical attempt. Implemented by ordering
  `(variant_id, -yuborilgan_vaqt)` and taking the first row per variant in
  Python (`itertools.groupby`) rather than `QuerySet.distinct(*fields)`,
  which is Postgres-only and this project's DB backend isn't guaranteed to
  be Postgres.

## Views

**Teacher side** — `web/views/men.py`:

- `MenYuklamalarimView`: replace the `select_related(...dastur_topshirish)`
  with a `Prefetch("fan_semestr__variant__dastur_topshirishlari", queryset=DasturTopshirish.objects.select_related("korib_chiqqan"))`
  so `variant.dastur_topshirishlari.all` is cached and newest-first; the
  template reads `.0` for "current" and the full list for history — no N+1.
- New `MenDasturTarixiView` (`GET /men/kurs/<variant_id>/dastur/tarixi/`,
  name `men:dastur_tarixi`) — same ownership guard as
  `MenDasturTopshirishView`, renders `web/templates/web/men/_dastur_panel.html`
  with the full attempt list for that variant. This is the HTMX endpoint the
  new "Ko'rish" button targets.
- `MenDasturTopshirishView.post`: on success, instead of a redirect, return
  the same panel partial **plus** an `hx-swap-oob` update of the row's
  status badge — mirrors `web/templates/web/kafedra/_panel_va_qator.html`'s
  `<template>`-wrapped oob-row convention (`status.md`'s documented gotcha:
  raw `<tr>` fragments outside a `<table>` get dropped by the HTML parser,
  so the oob row must be wrapped in `<template>`). On validation failure
  (e.g. resubmitting while `KUTILMOQDA`), return the panel with an inline
  error instead of a `messages` redirect, since the user stays on the panel.

**AOH side** — `web/views/office/dastur.py`:

- `DasturTopshirishlarView`: queryset becomes `joriy_topshirishlar()` (one
  row per variant, latest attempt) instead of all `DasturTopshirish` rows —
  otherwise every past rejected attempt would permanently clutter the list.
- New `dastur_tarixi(request, variant_id)` (GET) — renders the same-style
  history panel for that variant (all attempts, newest first), reusing a
  shared partial with the teacher side (see Templates).
- `dastur_qabul` / `dastur_rad`: after acting, return the updated row +
  panel via HTMX (same oob-row pattern) instead of a redirect, so the list
  stays in sync without a full reload — matches the existing
  `kafedra:yuklama_ochirish` hx-post idiom (`hx-target="#panel-..."
  hx-swap="innerHTML"`).

URLs: one new path in `web/urls_men.py` (`men:dastur_tarixi`), one new path
in `web/urls_office.py` (`office:dastur_tarixi`).

## Templates

- `web/templates/web/men/yuklamalar.html`: per-row action cell shrinks to
  the "Dasturni yaratish" link, a compact status badge with attempt count
  (`RAD ETILDI · 3-urinish`), and one `Ko'rish` button
  (`hx-get="{% url 'men:dastur_tarixi' variant.pk %}" hx-target="#dastur-panel-{{ variant.pk }}" hx-swap="innerHTML"`).
  Add a sibling `<tr><td colspan="7"><div id="dastur-panel-{{ variant.pk }}"></div></td></tr>`
  row per `MARUZA` yuklama, exactly mirroring
  `web/templates/web/kafedra/dashboard.html:42-47`.
- New shared partial `web/templates/web/dastur/_tarix_royxati.html` — just
  the timeline list (per attempt: `urinish_raqami`, `yuborilgan_vaqt`,
  status tag, `izoh` if rejected, a file-download link) — included by both
  sides so the rendering of "the history" only lives in one place (CLAUDE.md:
  one module = one responsibility).
- New `web/templates/web/men/_dastur_panel.html` — course name/current
  status header, `{% include ".../_tarix_royxati.html" %}`, and the upload
  form (hidden/disabled if the latest attempt is `KUTILMOQDA`).
- New `web/templates/web/men/_dastur_qator_va_panel.html` — the HTMX submit
  response: panel + `<template>`-wrapped oob row update, mirroring
  `_panel_va_qator.html`.
- `web/templates/web/office/dasturlar/list.html`: add a `Tarixni ko'rish`
  button per row (same `hx-get`/panel-row idiom) and a
  `web/templates/web/office/dasturlar/_tarix_panel.html` that includes the
  shared `_tarix_royxati.html` plus the existing accept/decline forms
  (now acting on the latest attempt's pk).

## Tests

- `plans/tests/test_dastur_topshirish.py`: resubmission creates a **new**
  row (old row's `izoh`/reviewer/file untouched); `urinish_raqami`
  increments correctly; resubmitting while the latest attempt is
  `KUTILMOQDA` raises `ValidationError`; old files are not deleted from
  storage; `joriy_topshirishlar()` returns exactly one row per variant even
  with several rejected attempts, and it's the latest one.
- `web/tests/test_men_views.py`: `men:dastur_tarixi` renders all attempts
  newest-first for the owner, 403 for a non-owner; submit view rejects
  (with the panel re-rendered, not a 500) when a pending attempt exists.
- `web/tests/test_office_dastur_views.py`: list view row count stays at one
  per variant after multiple rejection rounds; `office:dastur_tarixi` shows
  the full history; accept/decline still operate correctly against the
  latest attempt.

## Verification

1. `python manage.py makemigrations plans` (schema + data migration) then
   `python manage.py migrate`.
2. `python manage.py test plans web` — all green, including the new/updated
   tests above.
3. `ruff format .` && `ruff check .`.
4. Manual: as a teacher, submit → have AOH reject → resubmit, repeated 3–4
   times; confirm the "Ko'rish" panel shows every past rejection reason
   intact with correct attempt numbers, and the AOH's panel shows the same
   history when reviewing round 4.
