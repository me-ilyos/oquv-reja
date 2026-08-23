# Django best-practice review

Scope: N+1 queries, fat views, business logic in templates, raw SQL, missing
indexes, signals, missing transactions around multi-step writes, and
SQLite→PostgreSQL portability. Method: full read of `models.py`/`managers.py`
per app, all `views.py`/`services.py`/`dashboard.py` modules, templates and
templatetags, plus `manage.py check --deploy`.

## `manage.py check --deploy` output

```
System check identified some issues:

WARNINGS:
?: (security.W004) You have not set a value for the SECURE_HSTS_SECONDS setting. If your entire site is served only over SSL, you may want to consider setting a value and enabling HTTP Strict Transport Security. Be sure to read the documentation first; enabling HSTS carelessly can cause serious, irreversible problems.
?: (security.W008) Your SECURE_SSL_REDIRECT setting is not set to True. Unless your site should be available over both SSL and non-SSL connections, you may want to either set this setting True or configure a load balancer or reverse-proxy server to redirect all connections to HTTPS.
?: (security.W009) Your SECRET_KEY has less than 50 characters, less than 5 unique characters, or it's prefixed with 'django-insecure-' indicating that it was generated automatically by Django. Please generate a long and random value, otherwise many of Django's security-critical features will be vulnerable to attack.
?: (security.W012) SESSION_COOKIE_SECURE is not set to True. Using a secure-only session cookie makes it more difficult for network traffic sniffers to hijack user sessions.
?: (security.W016) You have 'django.middleware.csrf.CsrfViewMiddleware' in your MIDDLEWARE, but you have not set CSRF_COOKIE_SECURE to True. Using a secure-only CSRF cookie makes it more difficult for network traffic sniffers to steal the CSRF token.
?: (security.W018) You should not have DEBUG set to True in deployment.

System check identified 6 issues (0 silenced).
```

Note: W009 flags the *current local* `SECRET_KEY` value, not the mechanism —
`oquv_reja/settings.py:28` correctly reads it from the environment with no
fallback. The other five are real gaps: none of the `SECURE_*`/cookie-security
settings are set anywhere in the file.

## High severity

- **`plans/dashboard.py:161-184`** (`_tanlov_satrlari`) — N+1 query, and a
  nested N+1 on top of it. `yildagi.filter(variant__fan=fan)` runs once per
  pending elective (`tanlov`) course inside the `for fan in fanlar:` loop, with
  no `select_related`. The result then feeds `_tur_yigindisi`, which accesses
  `fs.variant.fan.reja` per `FanSemestr` row — 2-3 more queries each, since
  nothing was preloaded. This is the most severe query-scaling issue in the
  codebase: cost grows with (pending electives × their semesters).
  Fix: mirror `_effektiv_satrlar` (`plans/dashboard.py:133-158`) — fetch all
  relevant `FanSemestr` rows once with
  `select_related("variant__fan__reja")` and group by `fan_id` in Python via
  `defaultdict`, instead of re-querying per `fan`.

- **`plans/services.py:54-69`** (`guruhlarni_sinxronlash`) — not wrapped in
  `transaction.atomic`. Loops `Guruh.objects.get_or_create(...)` once per group
  (N+1 writes), then runs a separate `.filter(...).delete()`. Both call sites —
  `web/views/office/rejalar.py:83-87` (`RejaTahrirView.form_valid`) and
  `plans/admin.py:52-56` (`OquvRejaAdmin.save_model`) — call this *after* the
  `OquvReja` save has already committed in its own transaction, so a failure
  partway through the loop leaves the reja update committed with stale/partial
  groups. (The one safe caller, `plans/uploads.py:44-58`, happens to already be
  inside its own `transaction.atomic()` block — safe by accident of call site,
  not by design of the function.)
  Fix: put `@transaction.atomic` on `guruhlarni_sinxronlash` itself so it's
  self-contained regardless of caller; consider replacing the `get_or_create`
  loop with a single batched insert since groups have no FK dependency on each
  other.

- **`oquv_reja/settings.py`** — no `SECURE_HSTS_SECONDS`, `SECURE_SSL_REDIRECT`,
  `SESSION_COOKIE_SECURE`, or `CSRF_COOKIE_SECURE` set anywhere (confirmed by
  the deploy check above: W004, W008, W012, W016). Combined with W018
  (`DEBUG`) and W009 (`SECRET_KEY` strength in the current local env), this is
  a real gap for a production deployment.
  Fix: set these for production, gated behind an env-driven flag (e.g.
  `env.bool("SECURE", default=not DEBUG)`) so local dev is unaffected.

## Medium severity

- **`plans/services.py:159`** (`yuklama_kamomadi`) — `select_related` chain
  is `"foydalanuvchi", "turi"` only; `"kafedra"` is missing. Triggers a real
  N+1 on the institution-wide teacher list: `OqituvchiListView`
  (`web/views/office/oqituvchilar.py:19-33`) → template
  `web/templates/web/office/oqituvchilar/_jadval.html:35`
  (`{{ holat.oqituvchi.kafedra.nomi }}`) — one extra query per teacher. (The
  kafedra-scoped teacher list calls the same function but never renders
  `.kafedra`, so it's unaffected today — the bug is latent until the
  office-wide page is hit.)
  Fix: add `"kafedra"` to the `select_related(...)` call.

- **`plans/dashboard.py:261-263`** (`kafedra_qamrovi`) — no
  `select_related`/`prefetch_related` at all beyond the `annotate(Count(...))`.
  Template `web/templates/web/office/kafedralar/list.html` then accesses
  `q.kafedra.mudir` (1 query) → `str(mudir.foydalanuvchi)` (1 more query,
  since `mudir__foydalanuvchi` isn't preloaded) and iterates
  `q.kafedra.oqituvchilar.all` (1 more query) per department row — roughly 3
  extra queries × N departments per page load.
  Fix: `Department.objects.select_related("mudir__foydalanuvchi").prefetch_related("oqituvchilar").annotate(...)`.

- **`plans/admin.py:190-203`** (`FanSemestrAdmin.taqsimlangan` / `qoldiq`) —
  each admin changelist column independently runs
  `obj.yuklamalar.values("tur").annotate(jami=Sum("soat"))` per rendered row —
  2 extra queries × N rows in the Django admin. `get_queryset` only does
  `select_related("variant__fan__reja")` (line 176-177), which doesn't help
  per-object aggregates.
  Fix: precompute the aggregates once in `get_queryset` (e.g. via annotated
  `Sum(Case(When(...)))` per type) instead of per-column instance methods.

- **`plans/services.py:228-230`** (inside `_semestrni_tahrirlash`) — loops
  `yuklama.save(update_fields=["soat"])` per delegated `Yuklama` row instead of
  a single `bulk_update`. Necessary today because `Yuklama.save()` recomputes
  `hisoblangan_soat()` (`plans/models.py:304-311`), which branches on `tur`
  and isn't a trivial bulk SQL expression. Low request frequency (an admin
  edit action, not a page render) — worth a footnote, not urgent.

- **Missing pagination** on four list views that render the full queryset and
  rely on client-side Alpine `x-model` filtering instead of server-side
  paging/search:
  - `RejaListView` — `web/views/office/rejalar.py:23-26`
  - `OqituvchiListView` (institution-wide) — `web/views/office/oqituvchilar.py:16-33`
  - `KafedraListView` — `web/views/office/kafedralar.py:20-34`
  - `KafedraOqituvchiListView` (per-department, naturally bounded, lower risk)
    — `web/views/kafedra/oqituvchilar.py:18-33`
  Fine at current institutional scale; will not scale gracefully as
  plan/teacher counts grow. Fix: add `paginate_by` and a real `?q=` server-side
  filter before that happens.

- **`oquv_reja/settings.py:92-97`** — `DATABASES` is hardcoded to
  `django.db.backends.sqlite3` with no environment-based engine switch. This
  is the actual blocker for a future Postgres move — the whole `DATABASES`
  dict needs rewriting (host/port/user/password via `env()`, plus
  `CONN_MAX_AGE`/`OPTIONS`), not a code-portability issue per se.

- **`plans/models.py:309-311` and `:313-361`** (`Yuklama.save` / `clean`) —
  the derived `soat` field is recomputed in `save()`, and real validation
  (`_clean_effektiv_variant`, `_clean_soat_mavjud`, `_clean_guruh_rejasi`,
  `_clean_kurs_ishi_sigimi`) lives in `clean()`, which Django does **not**
  auto-invoke on `.save()` — it only runs via `full_clean()`. Today every
  `Yuklama` is created/edited through `web/forms/yuklama.py`, which correctly
  calls `full_clean()`, and no code path uses `.update()`/`bulk_create()` on
  `Yuklama`. Not a live bug, but a landmine: any future direct-write path
  (management command, bulk import) would silently skip both the recompute
  and the validation.

## Low severity

- **`plans/models.py:47-52`** (`Foydalanuvchi.telefon`) — `unique=True,
  db_index=True` together; `unique=True` already creates the index, so
  `db_index=True` is redundant (harmless, just noise).

- **`web/templatetags/ui.py:11-19`** (`rasmiy_matn`) and
  `plans/dastur/service.py:90-92` — both call `Universitet.objects.first()`
  uncached. `rasmiy_matn` isn't currently referenced in any template (grep
  confirmed), and the `dastur/service.py` call fires once per document
  render, so there's no live N+1 today. Flagging as a caching opportunity
  (`Universitet` is a documented singleton, `accounts/models.py:112`) in case
  `rasmiy_matn` ever gets wired into a per-row template loop.

- **Clean fronts, stated explicitly so they don't need re-checking**: no
  Django signals anywhere in the codebase (no `signals.py`, no `@receiver`,
  no non-default `AppConfig.ready()`); no raw SQL (`.raw()`, `cursor.execute`,
  `RawSQL`, `.extra()`); no legacy `unique_together` (everything uses modern
  `Meta.constraints` / `UniqueConstraint`); no `JSONField` usage anywhere.

- **`Yuklama.Meta.constraints`** (`plans/models.py:261-297`) — conditional
  `UniqueConstraint(condition=Q(...))` and a compound `CheckConstraint`. Both
  patterns are portable to Postgres (partial indexes and CHECK constraints
  are supported on both engines), but recommend running migrations against a
  real Postgres instance at least once before cutover — SQLite's
  table-rebuild migration path can mask FK/constraint-ordering issues that
  only surface as real `ALTER TABLE` statements on Postgres.

- **No `assertNumQueries` tests exist** anywhere in `plans/tests/` or
  `web/tests/`. Recommend adding a few once the N+1 fixes above land, to pin
  the query count on the dashboard/list views the templates depend on
  (several templates do 4-hop dotted lookups like
  `satr.fan_semestr.variant.fan.reja.yonalish_kodi` that are silently reliant
  on upstream `select_related` chains — a regression there wouldn't show up
  as a template error, only as a query-count regression).

## What's already good (for calibration)

- Views are consistently thin (`web/views/**`, longest module is 135 lines of
  mostly form-parsing); business logic lives in `plans/services.py`,
  `plans/dashboard.py`, `plans/delegation.py`, and `plans/managers.py`, not in
  views or templates. `accounts/views.py` / `plans/views.py` are unused
  Django boilerplate stubs — all real views are under `web/views/`.
- `_effektiv_satrlar` (`plans/dashboard.py:133-158`), `reja_semestrovkasi`
  (`plans/dashboard.py:219-238`), `_talab_satrlari`
  (`plans/services.py:119-131`), and the kafedra delegation panel
  (`plans/delegation.py:48-55`) all use correct `select_related`/
  `prefetch_related` and group in Python instead of querying per row.
- Every multi-step write in `plans/importer.py` (`import_reja`,
  `@transaction.atomic`) and `plans/uploads.py`
  (`fayldan_import_qilish`) is correctly wrapped in `transaction.atomic`.
- `plans/managers.py:39-47`'s academic-year integer-division handling
  (`ExpressionWrapper(... , output_field=IntegerField())`) is a deliberate,
  correctly-reasoned fix for SQLite/Postgres division-semantics portability —
  the developer's own comment at `plans/managers.py:40` shows this was
  anticipated, not accidental.
- Consistent `get_object_or_404` usage across every view, always scoped by
  the correct tenancy filter (kafedra, reja, etc.) — no manual
  `.get()`/`DoesNotExist` patterns anywhere.
- No duplicated business logic between forms and models:
  `web/forms/yuklama.py`'s `_get_validation_exclusions` deliberately routes
  validation into `Yuklama.full_clean()` (model-level rules) instead of
  re-implementing them in the form.
- `DEFAULT_AUTO_FIELD = BigAutoField`, `USE_TZ = True` with
  `TIME_ZONE = "Asia/Tashkent"`, and `SECRET_KEY`/`ALLOWED_HOSTS`/
  `CSRF_TRUSTED_ORIGINS` all sourced from environment with no hardcoded
  fallback — all good defaults for a future multi-environment/Postgres setup.
