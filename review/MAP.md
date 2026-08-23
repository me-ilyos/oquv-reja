# Codebase Map

Django 5 + SQLite app for parsing ministry-format curriculum `.xlsx` files (o'quv reja) and distributing teaching load (yuklama) across departments and teachers. Uzbek domain naming throughout. Frontend: server-rendered templates with HTMX + Alpine.js (both vendored). ~5,270 lines of non-test Python (excluding `env/` venv and migrations), ~2,270 lines of tests, 45 templates (~1,550 lines).

## Apps & models

**`accounts`** — identity and org structure (`accounts/models.py`):
- `Foydalanuvchi` — custom phone-login user (`AUTH_USER_MODEL`), roles via `Rol` enum (superadmin / office admin / department admin / teacher).
- `OqituvchiProfil` 1:1→ `Foydalanuvchi`; FK→ `Department` (kafedra), FK→ `OqituvchiTuri` (position with `min_soat`).
- `Department.mudir` 1:1→ `OqituvchiProfil`; `Universitet` standalone singleton.
- Commands: `seed_departments` (dev seeding). Services in `accounts/services.py` (teacher CRUD, head assignment with role side-effects).

**`plans`** — core domain (`plans/models.py`):

```
OquvReja ──< Guruh
    └──< Fan ──< FanVariant ──< FanSemestr ──< Yuklama
          │(tanlangan_variant,     │              ├── FK Guruh (nullable)
          │ SET_NULL, cycle)       │              └── FK OqituvchiProfil
          └────────────────────────┘
        FanVariant ── FK accounts.Department
```

`OquvReja` = one intake (unique on yonalish_kodi + year + shakl); `Fan` = curriculum line (majburiy/tanlov); `FanVariant` = actual course content + hour columns; `FanSemestr` = materialized per-semester breakdown, the delegation anchor; `Yuklama` = one delegation row with a 3-shape check constraint (maruza / per-group / kurs ishi). Supporting modules: `importer.py`, `services.py`, `dashboard.py`, `delegation.py`, `split.py`, `managers.py`, `uploads.py`, `dastur/service.py` (.docx syllabus). Command: `import_reja`.

**`web`** — presentation only, no models. **`parser/`** — standalone non-Django openpyxl package (dataclasses in `parser/models.py`, heuristic layout detection in `parser/parser.py`, Markdown formatter, CLI `parser/main.py`); consumed one-way by `plans/importer.py`.

## Web layer

All HTTP handling lives in `web` (`accounts/views.py` and `plans/views.py` are empty stubs). Views split by role: `web/views/office/` (dashboard, rejalar, kafedralar, oqituvchilar), `web/views/kafedra/` (dashboard, yuklama — the HTMX delegation core via `PanelAsosView.panel_javobi()`, hisobot, oqituvchilar), `men.py` (teacher self-service), `auth.py`, `dev.py` (DEBUG-only role impersonation). URL modules mirror this: `urls_office/kafedra/men/dev.py`, all mounted from `web/urls.py`. Access control: `RolTalabMixin` family in `web/mixins.py` (`KafedraMudiriTalabMixin` sets `self.kafedra` — the only tenancy source) + `office_admin_talab` decorator for FBVs. Forms in `web/forms/` (auth, kafedra, oqituvchi, reja, yuklama — the yuklama forms surface model constraints as form errors via `_get_validation_exclusions`).

Templates: pure APP_DIRS, everything under `web/templates/web/` — `base.html` (CSRF `hx-headers` on body, vendored htmx/Alpine), `base_print.html`, per-area dirs, shared partials in `parts/`. Underscore-prefixed files are HTMX/include fragments (e.g. `office/_qator_va_statlar.html`, `kafedra/_panel_va_qator.html` — both use OOB swaps). Filters in `web/templatetags/ui.py`.

## Alpine.js & HTMX patterns

Alpine is inline-only — no `Alpine.data()` components. Three recurring patterns: **(1)** client-side table filter `x-data="{qidiruv: ''}"` + `x-model` + row `x-show` on `data-nomi`, repeated in ~7 templates; **(2)** popover pickers `{ochiq, q}` with `@click.outside` (variant/kafedra/teacher/mudir pickers); **(3)** tab and group toggles (`office/rejalar/detail.html` with nested state, `office/_fan_jadvali.html`). Heaviest files: `office/_fan_qatori.html`, `office/rejalar/detail.html`.

HTMX drives four screens: office dashboard year picker (conditional template via `HX-Request`), row-level variant/kafedra assignment (row swap + OOB stats), the kafedra delegation panel (panel + OOB row + OOB stats), and the dev role switcher. Everything else is plain POST-and-redirect.

## Complexity & duplication hotspots

Most complex files:
- `parser/parser.py` (508) — heuristic Excel reader: 9 regexes, anchor-hunting, consecutive-integer header detection, 6 silent-fallback points; merged-cell semantics split across `breakdown_from`/`breakdown_inheriting`; WARNINGs print to stdout, invisible in the Django import path.
- `plans/models.py` (361) — 131-line `Yuklama` with 3-branch check constraint + 4 private validators.
- `plans/importer.py` (328) — parse→persist plus snapshot/restore of manual state on re-import; `_rejani_tayyorlash` mixes 3 concerns.
- `plans/dashboard.py` (272) — 4 aggregation shapes each with its own grouping loop; O(n²) spot in `_effektiv_satrlar` (149–153).
- `plans/services.py` (267) — read-side demand math and write-side transactions in one module.
- Also: `plans/admin.py` (245, display columns duplicate services logic), `build_markdown` in `parser/formatter.py` (87-line function), `dastur_kontekst` in `plans/dastur/service.py` (45-key dict, half hardcoded blanks).

Duplication clusters:
1. Parser CLI vs Django importer run the same 6-step pipeline (`parser/main.py:34` vs `plans/importer.py:58`); the duration regex `r"(\d+)\s*yil"` is written twice.
2. `derived_credits` (hours // 30) exists in 3 places (`parser/models.py:58`, `:92`, `plans/models.py:131`).
3. The 3-line year-picker preamble (`yilni_tanlash`) is repeated in 6 view classes, all importing it from `web/views/office/dashboard.py` — kafedra/men views depend on an office module.
4. Office vs kafedra teacher CRUD are mirror views and forms (`web/views/office/oqituvchilar.py` vs `web/views/kafedra/oqituvchilar.py`; two subclass pairs in `web/forms/oqituvchi.py`).
5. Three near-identical queryset entrypoints in `plans/services.py` (91/105/114); the academic-year annotation is written twice in `plans/managers.py` with different join paths.
6. Templates: the teacher table is duplicated office vs kafedra; `_statlar.html` exists in both areas; the variant/kafedra popover is written twice (`_fan_qatori.html` HTMX vs `_semestrovka_qatori.html` plain forms); the year `<select>` is copy-pasted into 7 templates; teacher-chip markup is hand-written in 8 places (5 in `kafedra/_panel.html` alone).
