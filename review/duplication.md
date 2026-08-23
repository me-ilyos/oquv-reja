# Duplication Report

Findings from a codebase sweep for real duplicated logic — repeated queryset
filtering, copy-pasted view/form logic, and repeated template/Alpine blocks.
Superficial similarity (same shape, different business rule) is excluded;
each item below was spot-checked against the actual files. Ranked by impact
within each section.

## Python — views & querysets

### 1. Year-selection preamble copy-pasted into 6 views
`yilni_tanlash()` lives in `web/views/office/dashboard.py:16-24` and is
imported *into 5 other view modules* — a view module reaching into another
view module is itself a smell. Every call site repeats the same two lines
and the same two context keys:

```python
yillar, yil = yilni_tanlash(self.request.GET.get("yil"))
yil = yil or dashboard.joriy_akademik_yil()
```

- `web/views/office/oqituvchilar.py:21` (`import` at :13)
- `web/views/office/kafedralar.py:25` (`import` at :17)
- `web/views/kafedra/oqituvchilar.py:23` (`import` at :15)
- `web/views/kafedra/dashboard.py:15` (`import` at :7)
- `web/views/kafedra/hisobot.py:15` (`import` at :7)
- `web/views/men.py:26` (`import` at :14)

Each also repeats `"yillar": yillar, "yil": yil` in its `context.update(...)`.
`web/views/office/dashboard.py:47-50` is a deliberate 7th variant — it omits
the `or joriy_akademik_yil()` fallback so the dashboard can render an empty
state when no years exist. Keep that one separate.

**Fix:** add a `YilTanlovMixin` to `web/mixins.py` exposing `self.yil` /
`self.yillar` via `get_context_data`; move `yilni_tanlash` itself into
`plans/dashboard.py` next to `tanlanadigan_yillar()` / `joriy_akademik_yil()`
— it's pure domain logic with no request dependency, and moving it deletes
the 5 cross-package view→view imports.

### 2. Parallel office/kafedra teacher CRUD views — 3 near-identical pairs
`web/views/office/oqituvchilar.py` and `web/views/kafedra/oqituvchilar.py`
are structural clones (list/create/edit), each pair differing only in the
role mixin, the redirect namespace, and (for kafedra) one extra tenancy
predicate:

- **List**: `office/oqituvchilar.py:16` vs `kafedra/oqituvchilar.py:18` —
  both call `services.yuklama_kamomadi(yil, kafedra=...)`; kafedra sources
  the kafedra from `self.kafedra` (mixin), office from `?kafedra=`.
- **Create**: `office/oqituvchilar.py:42-49` vs `kafedra/oqituvchilar.py:36-48`
  — `form_valid` bodies are identical except the redirect name and (kafedra)
  passing `kafedra` into `get_form_kwargs`.
- **Edit**: `office/oqituvchilar.py:52-67` vs `kafedra/oqituvchilar.py:51-67`
  — `form_valid` is character-for-character identical apart from the
  redirect name; `get_form_kwargs` differs only by kafedra's extra
  `kafedra=self.kafedra` filter on the `get_object_or_404`.

The forms layer already solved this correctly by subclassing
(`web/forms/oqituvchi.py:57`, `:111`) — the views didn't follow suit.

**Fix:** a shared `web/views/oqituvchi_base.py` with
`OqituvchiYangiAsosView` / `OqituvchiTahrirAsosView` carrying
`success_url_name`, `template_name`, `form_class` as class attributes and a
`profil_olish()` hook the kafedra subclass overrides to add the tenancy
filter. Role mixins stay as the first base in each concrete subclass.

### 3. `taqsimlangan_soatlar` re-implemented inline in `plans/admin.py`
Canonical version: `plans/services.py:134-143`
(`Yuklama.objects.filter(...).values("fan_semestr_id", "tur").annotate(jami=Sum("soat"))`).
Reimplemented twice more, both in the same admin class:
- `plans/admin.py:192` — `obj.yuklamalar.values("tur").annotate(jami=Sum("soat"))`
- `plans/admin.py:198` — same, as `values_list(...)` cast to `dict`

Worse, `fan_semestr_talabi(obj, obj.variant.fan.reja)` is computed twice for
the same row (`admin.py:187` and `:197`) — `qoldiq` recomputes what `talab`
and `taqsimlangan` already produced. 3 queries + 2 demand computations per
changelist row.

**Fix:** one service function, e.g.
`services.fan_semestr_qoldigi(fs) -> dict[str, int | None]` returning
talab/taqsimlangan/qoldiq together; the three `@admin.display` methods read
from one cached call. `plans/delegation.py:120-128` (`fs_satri`) already
does the single-row rebuild this needs — reuse it.

### 4. Academic-year formula written 3 times
`reja.boshlanish_yili + (semestr - 1) // 2`:
- `plans/managers.py:41-46` — `FanSemestrQuerySet.akademik_yil_bilan` (ORM)
- `plans/managers.py:54-60` — `YuklamaQuerySet.akademik_yil_bilan` (ORM, only the FK prefix differs)
- `plans/models.py:216-217` — `FanSemestr.akademik_yil` (Python property)

**Fix:** a module-level `_akademik_yil_ifodasi(prefiks: str)` in
`plans/managers.py` returning the `ExpressionWrapper`, used by both
querysets; keep the Python property as the intentional mirror, ideally with
a test asserting the two agree. (`dashboard.joriy_akademik_yil` is a
*different* rule — calendar month ≥ 9 — do not merge it in.)

### 5. `SoatTuri` → hour-field-name mapping written 4 times
The ordered map of the four classroom-hour `SoatTuri` members to their model
fields:
- `plans/models.py:220-225` — `FanSemestr.tur_soat`
- `plans/services.py:188-193` — `_TAHRIR_MAYDONLARI`
- `plans/services.py:218-223` — `_semestrni_tahrirlash` (same keys, 30 lines from the copy above)
- `plans/split.py:11-16` — `BREAKDOWN_MAYDONLARI` (tuple form of the same 4 values)

The same order is also re-encoded *positionally* at `plans/importer.py:267-272`
and `plans/split.py:62` (`qiymatlar = (maruza, amaliyot, laboratoriya, seminar)`)
— a reorder bug here would silently swap hour types.

**Fix:** one constant in `plans/models.py` next to `PER_GURUH_TURLAR`, e.g.
`AUDITORIYA_MAYDONLARI: dict[SoatTuri, str]`; `FanSemestr.tur_soat` becomes
`getattr(self, AUDITORIYA_MAYDONLARI[tur])`, `split.BREAKDOWN_MAYDONLARI`
becomes `tuple(AUDITORIYA_MAYDONLARI.values())`.

### 6. `Department` has no `Meta.ordering` → `order_by("nomi")` written 6 times
- `web/views/office/dashboard.py:33`
- `web/views/office/oqituvchilar.py:28`
- `web/views/office/rejalar.py:71`
- `web/forms/oqituvchi.py:19`
- `plans/dashboard.py:261-263`
- `web/views/dev.py:106-108`

First four are the *entire* queryset and are literally identical.
`accounts/models.py:124-138` (`Department`) has no `Meta` class at all.

**Fix:** add `class Meta: ordering = ["nomi"]` to `Department` — removes 4
whole expressions outright.

### 7. `seed_departments` bypasses `accounts/services.py`
- `accounts/services.py:22-41` (`oqituvchi_yaratish`) is the canonical
  create-user-then-create-profile pair.
- `accounts/management/commands/seed_departments.py:99-108`
  (`_create_teacher_profil`) reimplements the same two calls verbatim after
  generating random name/phone/turi.
- Head assignment: `accounts/services.py:68-95` (`mudir_tayinlash`) does role
  sync, previous-head demotion, cross-kafedra validation, and a
  SUPERADMIN/OFFICE_ADMIN guard. `seed_departments.py:83-86` open-codes a
  stripped 2-line version with none of those safety checks — harmless today
  (fresh departments have no prior head) but a silent divergence risk if the
  rules in `services.py` change.

**Fix:** have the command call `accounts.services.oqituvchi_yaratish(...)`
and `accounts.services.mudir_tayinlash(...)`; `_create_teacher_profil`
shrinks to just the random-data generation.

### 8. Kafedra-scoped teacher queryset — duplicated and fetched twice per request
- `web/views/kafedra/yuklama.py:58-60` —
  `OqituvchiProfil.objects.filter(kafedra=self.kafedra).select_related("foydalanuvchi")`
- `web/forms/yuklama.py:28-30` — the identical filter, run again on the same
  panel render (the view and the form each fetch it independently).

Plus 3 more bare `OqituvchiProfil.objects.select_related("foydalanuvchi")`
lookups: `office/oqituvchilar.py:59`, `:74`, `kafedra/oqituvchilar.py:58`.
`OqituvchiProfil` has no custom manager at all
(`accounts/models.py:141-155`).

**Fix:** give `OqituvchiProfil` a manager with `.kafedrada(kafedra)` and a
`select_related("foydalanuvchi")` default.

### 9. Institution-name lookup duplicated
- `accounts/services.py:17-19` — `universitet_olish()` → `Universitet.objects.first()`
- `plans/dastur/service.py:90-92` — `_universitet_nomi()` re-queries
  `Universitet.objects.first()` directly, bypassing the service, then unwraps
  `.rasmiy_nomi if universitet else ""`
- `web/templatetags/ui.py:23-24` — calls the service, then repeats the same
  unwrap with a different fallback (`"—"`)

**Fix:** `accounts/services.py` gains `universitet_nomi(bosh: str = "") -> str`;
both callers pass their own placeholder. (Or a `Universitet.objects.yagona()`
manager method, since exactly-one-row is already documented at
`accounts/models.py:112`.)

### 10. Minor items
- **Effective-variant resolution** (`tanlangan_variant or <fallback>`) written
  3 ways: `plans/dashboard.py:117-119`, `:226-227`, and `plans/admin.py:128-134`
  (the admin version has no fallback, rendering `"—"` instead — a partial
  copy, not a full one). → belongs as a `Fan.effektiv_variant` property.
- **`qoldiq_soat`** identical in `plans/services.py:34-38` (`TalabSatri`) and
  `plans/delegation.py:41-45` (`TurHolati`); **`biriktirilmagan`** identical
  in `plans/dashboard.py:113-115` and `:215-217`.
- **`" ".join(xato.messages)`** ValidationError unwrapping, 4 copies:
  `web/views/office/dashboard.py:62-63`, `:76-77`,
  `web/views/office/kafedralar.py:88-89`, `web/views/office/rejalar.py:130-131`.
  → a small `xato_matni(exc)` helper in `web/mixins.py`.
- **Manager bypass**: `plans/admin.py:101` hand-rolls the exact complement of
  `FanQuerySet.tanlov_kutilmoqda()` (`plans/managers.py:17-20`) one line
  below a call site that correctly uses it (`admin.py:99`).
- **Raw type strings**: `web/views/office/rejalar.py:67-68` filters on
  `"MAJBURIY"` / `"TANLOV"` literals instead of `FanTuri.MAJBURIY` /
  `FanTuri.TANLOV`, which every other call site uses. Not duplication, but
  a latent bug source worth fixing alongside this pass.

## Python — forms

### 11. Kafedra-locked teacher forms — identical `clean()` override
- `web/forms/oqituvchi.py:57-68` (`KafedraOqituvchiYaratishForm`)
- `web/forms/oqituvchi.py:111-122` (`KafedraOqituvchiTahrirForm`)

Both `del self.fields["kafedra"]` and both override `clean()` identically:

```python
def clean(self) -> dict[str, object]:
    cleaned = super().clean()
    cleaned["kafedra"] = self.kafedra_qiymati
    return cleaned
```

They differ only in where `self.kafedra_qiymati` comes from (constructor arg
vs. `self.profil.kafedra`) — one line each.

**Fix:** a `KafedraQulflanganMixin` in `web/forms/oqituvchi.py` holding the
field removal + `clean()` override; subclasses set only `self.kafedra_qiymati`.

*(The rest of `web/forms/` is well-factored — phone normalization is
correctly single-sourced through `accounts/phone.py`, and no CSS-class
loops or other field boilerplate are duplicated.)*

## Templates & Alpine.js

### 12. Academic-year `<select>` filter — 6 byte-identical copies
- `web/templates/web/office/oqituvchilar/list.html:12-18`
- `web/templates/web/kafedra/oqituvchilar/list.html:11-19`
- `web/templates/web/office/kafedralar/list.html:11-19`
- `web/templates/web/kafedra/dashboard.html:10-18`
- `web/templates/web/men/yuklamalar.html:14-22`
- `web/templates/web/kafedra/hisobot.html:6-14`

`web/templates/web/office/dashboard.html:10-16` is a deliberately different
HTMX flavor (no wrapping `<form>`, `hx-get` instead of a GET submit).

**Fix:** `web/templates/web/parts/_yil_tanlov.html`, included everywhere,
with an optional `hx_url` param so the office dashboard's HTMX variant uses
the same partial.

### 13. Alpine search-box scaffold — 5 copies + duplicated filter predicate
`x-data="{ qidiruv: '' }"` plus a 24-byte magnifier `<svg>` path, copied in:
- `web/templates/web/office/oqituvchilar/_jadval.html:2-8`
- `web/templates/web/kafedra/oqituvchilar/list.html:23-29`
- `web/templates/web/office/kafedralar/list.html:23-29`
- `web/templates/web/office/rejalar/list.html:13-19`
- `web/templates/web/office/_fan_jadvali.html:1-9`

Differ only in the `placeholder` string. The paired row-filter expression
`x-show="qidiruv === '' || $el.dataset.nomi.includes(qidiruv.toLowerCase())"`
is duplicated across the same 5 files.

**Fix:** `parts/_qidiruv.html` taking `placeholder`; register an
`Alpine.data('jadvalQidiruv', ...)` component once in `base.html` so rows
use `x-show="mos($el)"` instead of re-inlining the expression.

### 14. Teacher table inlined instead of reusing the existing partial
`web/templates/web/office/oqituvchilar/_jadval.html:9-59` is already a
partial (included from `office/oqituvchilar/list.html:34`), but
`web/templates/web/kafedra/oqituvchilar/list.html:30-68` writes the same
table out inline instead of including it — both render the same
`services.yuklama_kamomadi(...)` result shape. Differences are fully
parameterizable: an extra "Kafedra" column, a "FAOL EMAS" tag, and the
actions cell (edit+delete vs. edit-only) — office has the tag, kafedra
silently doesn't.

**Fix:** promote `_jadval.html` to `parts/_oqituvchilar_jadvali.html`,
included from both list pages with `kafedra_ustuni`, `tahrir_url_nomi`,
`ochirish_url_nomi`, `bosh_matn` params.

### 15. Object-form page — 3 near-identical templates
- `web/templates/web/office/oqituvchilar/form.html` (22 lines)
- `web/templates/web/kafedra/oqituvchilar/form.html` (23 lines)
- `web/templates/web/office/kafedralar/form.html` (22 lines)

`diff` between the first two: 4 changed lines (two `{% url %}` names, one
added subtitle). Between the first and third: 6 lines (title text, display
field). Shared body — breadcrumb, `.card`, `{% include "_form_maydonlari.html" %}`,
save/cancel buttons — identical in all three.

**Fix:** a `parts/base_form.html` the three `{% extends %}`, overriding only
a `{% block sarlavha %}` / title.

### 16. Breadcrumb `<nav>` — 6 copies
`office/rejalar/yangi.html:4-8`, `tahrir.html:4-10`, `detail.html:5-9`,
`office/oqituvchilar/form.html:4-8`, `kafedra/oqituvchilar/form.html:4-8`,
`office/kafedralar/form.html:4-8`. Differ only in link URL/label.

**Fix:** an inclusion tag in `web/templatetags/ui.py` (already exists,
currently holds only filters) taking a list of `(url, label)` tuples — or
fold into #15's base_form.

### 17. `rejalar/yangi.html` vs `rejalar/tahrir.html` — identical form sections
`web/templates/web/office/rejalar/yangi.html:24-38` and
`web/templates/web/office/rejalar/tahrir.html:22-36` — verified `diff`
returns empty, 15 lines fully identical (the "Bilim sohasi" + "Ta'lim
sohasi" `form-section` blocks). `tahrir.html:38-44` adds a structurally
identical third "Yo'nalish" section.

**Fix:** `parts/_form_bolimi.html` taking `sarlavha` + a list of fields;
call it 2-3× per page.

### 18. Stat cards — existing partial bypassed
`web/templates/web/office/rejalar/detail.html:30-37` is byte-identical
(verified via `diff`) to `web/templates/web/office/_statlar.html:9-16` — the
warn/ok stat-card pair is re-inlined instead of included.

Separately, `office/_statlar.html:4-8` and `kafedra/_statlar.html:3-7`
share an identical 5-card `tur_soatlari` block (MARUZA/AMALIYOT/
LABORATORIYA/SEMINAR/KURS_ISHI) even though the rest of the two files
genuinely differ (different metrics per role) — don't merge the files, but
extract the 5 type-cards, ideally by having the view expose an ordered
`(nomi, soat)` list and rendering with `{% for %}`. The same hard-coded
5-type sequence also drives `kafedra/_fs_qatori.html:8-12`,
`office/_fan_qatori.html:14-18`, `office/_fan_jadvali.html:18-22`,
`kafedra/dashboard.html:32-36`, `office/_fan_semestrovka.html:14-18` — 6
places to update if a hour-type is ever added.

**Fix:** include `_statlar.html`'s warn/ok cards from `detail.html`;
extract the 5-type card loop into `parts/_tur_statlari.html`.

### 19. Kafedra-assignment popover — 2 copies, inconsistent transport
- `web/templates/web/office/_fan_qatori.html:21-60` (HTMX: `hx-post` + `hx-vals`)
- `web/templates/web/office/rejalar/_semestrovka_qatori.html:21-61` (plain
  `<form>` POST with hidden inputs)

Alpine shell and chip markup are identical
(`x-data="{ ochiq: false }" @click.outside="ochiq = false"`, the
`.popover`, the "+ Kafedra biriktirish" chip, "Biriktirishni bekor qilish").
The HTMX copy additionally has a search input the plain-POST copy lacks —
a real UX inconsistency caused by the fork.

**Fix:** `parts/_kafedra_biriktirish_katak.html` with a `usul="htmx"|"post"`
flag — or standardize both on HTMX and remove the divergence.

### 20. Read-only kafedra chip — 2 identical copies
`web/templates/web/office/_fan_semestrovka.html:41-47` and
`web/templates/web/office/rejalar/_semestrovka_breakdown_qatori.html:19-25`
are character-identical (verified). → tiny `parts/_kafedra_chip.html`.

### 21. Alpine popover shell duplicated 6× — real bug, not just duplication
`x-data="{ ochiq: false }" @click.outside="ochiq = false"` appears in
`office/_fan_qatori.html:21`, `kafedra/_panel.html:22`, `:41`,
`office/kafedralar/list.html:48`, `office/rejalar/_semestrovka_qatori.html:21`,
`parts/_rol_almashtirgich.html:1`. Only the last one adds
`@keydown.escape.window="ochiq = false"` — **the other 5 popovers can't be
closed with Esc**, directly because the copy-paste dropped that line.

**Fix:** register `Alpine.data('popover', () => ({ ochiq: false, ... }))`
once in `base.html` (Alpine is loaded there with zero components currently)
and use `x-data="popover"` everywhere — fixes the Esc-key gap in one place.

### 22. Repeated `hx-target`/`hx-post` clusters in `kafedra/_panel.html`
The "remove assignment ✕" button is copy-pasted 3× in the same file
(`:27-29`, `:47-49`, `:66-68`), identical apart from the yuklama pk passed
to the URL. `hx-target="#panel-{{ fs.pk }}" hx-swap="innerHTML"` repeats 5×
in this file alone, plus once each in `kafedra/_oqituvchi_popover.html:9`
and `kafedra/_fs_qatori.html:16`.

**Fix:** extract the remove-button to `parts/_yuklama_ochirish_tugma.html`;
move `hx-target`/`hx-swap` up to the outer `.card` at `_panel.html:2` so
children inherit it (htmx supports ancestor inheritance for both attrs).

### 23. Repeated inline styles that duplicate existing CSS classes
`app.css` already defines `.legend`, `.dot`, `.controls`, `.sem-fill`,
`.tag`, yet these are re-typed as inline `style="..."` repeatedly:
- `background:var(--unassigned-soft);color:var(--unassigned);"` — 5 copies
  (`kafedra/hisobot.html:53`, `kafedra/_tur_katak.html:6`, `:8`,
  `kafedra/_panel.html:18`, `office/_soat_katak.html:3`)
- the "Kafedraga biriktirilmagan" legend dot — 3 copies
  (`office/_dashboard_kontent.html:5`, `office/rejalar/detail.html:42`,
  `kafedra/dashboard.html:24`)
- `class="controls" style="margin-bottom:10px;"` — 6 copies (same files as
  #13 plus `office/oqituvchilar/list.html:30`)

**Fix:** promote each to a real class (`.sem-fill.qoldiq`,
`.dot.dot-unassigned`, `.controls.controls-filter`) — `kafedra/_panel.html`
alone carries 18 inline `style="..."` attributes and is the single worst
offender.

### 24. Existing partial bypassed in login form
`web/templates/web/auth/kirish.html:11-20` hand-writes two field blocks that
`web/templates/web/parts/_maydon.html:4-8` already renders identically.

**Fix:** `{% include "web/parts/_maydon.html" with field=form.username %}`
(×2), or `{% include "web/parts/_form_maydonlari.html" %}`.

## Not duplication (checked and ruled out)
- `plans/dashboard.py:133-158` vs `:161-184` (`_effektiv_satrlar` /
  `_tanlov_satrlari`) — similar shape, different business rules (selected
  vs. unselected tanlov handling).
- `plans/importer.py:199-213` vs `:216-223` — same shape, different rules
  (auto-select vs. leave unselected).
- `office/_statlar.html` vs `kafedra/_statlar.html` as whole files — real
  per-role metric differences; only the 5-card sub-block (#18) should merge.
- `office/_soat_katak.html` vs `kafedra/_tur_katak.html` vs
  `office/_soat_breakdown_hujayralari.html` — different structures (plain
  hour vs. taqsimlangan/talab pair vs. per-group tooltip); only one shared
  line is truly identical (covered in #23).
- `web/mixins.py` role-check usage — no view reimplements a permission
  check inline; `dev.py`'s `debug_talab` is a deliberately distinct guard
  (404 vs. redirect), documented in place.
