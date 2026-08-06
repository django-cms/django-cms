# Django 6.1 compatibility audit

Audit date: 2026-08-06

This note compares django CMS at `be0baa565` with Django 6.1, released on
2026-08-05, and records the compatibility work completed from that baseline.
It is an implementation audit, not a django CMS release note.

Primary sources:

- [Django 6.1 release notes](https://docs.djangoproject.com/en/6.1/releases/6.1/)
- [Django 6.1 mailers migration guide](https://docs.djangoproject.com/en/6.1/howto/mailers-migration/)
- [Django 6.1 fetch modes](https://docs.djangoproject.com/en/6.1/topics/db/fetch-modes/)
- [Django fixture signal guidance](https://docs.djangoproject.com/en/6.1/topics/db/fixtures/#how-fixtures-are-saved-to-the-database)

## Executive summary

The repository already declared Django 6.1 support and had mostly correct CI
coverage. No removed Django 6.1 API was used by production code. Four follow-up
changes were identified and completed:

1. Migrate django CMS's email calls away from deprecated `fail_silently`, and
   configure the test email backend through `MAILERS` on Django 6.1 while
   preserving Django 5.2/6.0 compatibility.
2. Remove the obsolete admin `wide` fieldset class, move the `object-tools`
   override in the custom page change form outside its `content` block, and
   visually test every custom admin change form with 6.1.
3. Make the permissions `m2m_changed` receiver explicitly accept and ignore
   `raw=True` fixture events, then cover that behavior with a fixture test.
4. Change the Django 6.1 test requirement from the prerelease floor
   `Django>=6.1a1` to the final-release floor `Django>=6.1`, and repair the
   generated-project matrix so it tests the three supported Django series.

These are compatibility and deprecation-cleanup changes. No django CMS model
migration is required by Django 6.1.

## Runtime and database floors

Django 6.1 supports Python 3.12, 3.13, and 3.14; PostgreSQL 15 or newer;
MySQL 8.4 or newer; MariaDB 10.11 or newer; and SQLite 3.37.0 or newer. See
[Python compatibility](https://docs.djangoproject.com/en/6.1/releases/6.1/#python-compatibility),
[dropped database support](https://docs.djangoproject.com/en/6.1/releases/6.1/#dropped-support-for-postgresql-14),
and [miscellaneous incompatibilities](https://docs.djangoproject.com/en/6.1/releases/6.1/#miscellaneous).

| Requirement | Repository state | Action |
| --- | --- | --- |
| Python 3.12-3.14 for Django 6.1 | `.github/workflows/test.yml` excludes Python 3.10 and 3.11 from the 6.1 jobs. `requires-python >=3.10` remains valid because django CMS also supports Django 5.2. | Do not raise the package-wide Python floor solely for 6.1. Clarify the per-Django Python combinations in the compatibility documentation. |
| PostgreSQL >=15 | CI uses PostgreSQL 16-18. | None. |
| MySQL >=8.4 | CI uses MySQL 8.4 and 9.5. | None. |
| MariaDB >=10.11 | MariaDB is documented as supported but has no dedicated CI service. | Document the 10.11 floor; add a MariaDB job if MariaDB compatibility is a release guarantee. |
| SQLite >=3.37.0 | The GitHub-hosted Python 3.12-3.14 builds satisfy this in practice. | Optionally assert `sqlite3.sqlite_version_info >= (3, 37)` in the 6.1 job to make the assumption explicit. |
| Final Django 6.1 | `test_requirements/django-6.1.txt` now says `Django>=6.1,<6.2`. | Complete; prereleases are no longer selected after the final release. |

The normal PostgreSQL, MySQL, and SQLite matrices already exercise Django 6.1.
At the audited baseline, `.github/workflows/test_startcmsproject.yml` listed
Django 4.2 through 5.2 and could silently upgrade the selected Django version.
It now installs django CMS and an explicit 5.2, 6.0, or 6.1 constraint together
and asserts the resolved Django version before and after project generation.

## New features relevant to django CMS

### ORM fetch modes

`QuerySet.fetch_mode()` can use `FETCH_ONE` (the old/default behavior),
`FETCH_PEERS` (batch deferred fields across queryset peers), or `FETCH_RAISE`
(reject accidental deferred-field queries). This can reduce N+1 queries or
enforce query budgets. See the [fetch mode documentation](https://docs.djangoproject.com/en/6.1/topics/db/fetch-modes/).

django CMS has deliberate `.only()` querysets in `cms/cms_menus.py`,
`cms/forms/utils.py`, and the optional materialized-path tree backend. No
change is required: their projected fields appear intentional. `FETCH_RAISE`
would be useful in performance tests around menu rendering to detect future
access to omitted fields; `FETCH_PEERS` should only be adopted after query-count
benchmarks.

### Database-level `on_delete`

`ForeignKey.on_delete` now accepts `DB_CASCADE`, `DB_SET_NULL`, and
`DB_SET_DEFAULT`. They avoid loading related objects in Python, but
`DB_CASCADE` deliberately does not send `pre_delete` or `post_delete` signals.
See [database-level delete options](https://docs.djangoproject.com/en/6.1/releases/6.1/#database-level-delete-options-for-foreignkey-on-delete).

django CMS relies on deletion behavior, signals, tree maintenance, plugin
cleanup, and cache invalidation. Do not mechanically replace existing
`CASCADE` declarations. Treat any use of `DB_CASCADE` as a separate design and
performance change with database-specific migration and signal tests.

### Mailers

`MAILERS`, `django.core.mail.mailers`, and the `using=` argument replace the
legacy `EMAIL_*` settings, `get_connection()`, connection arguments, and
several error-handling arguments. The old APIs are deprecated in 6.1 and are
scheduled for removal in 7.0. See the [mailers overview and migration guide](https://docs.djangoproject.com/en/6.1/howto/mailers-migration/).

This is directly relevant and needs the changes described under
[Implemented repository updates](#implemented-repository-updates).

### Admin, forms, and CSP

Relevant additions and behavior changes include:

- Admin actions can be exposed on the change form as well as the change list,
  and can have separate singular/plural descriptions.
- `ModelAdmin.list_select_related=False` now selects only foreign keys present
  in `list_display`, rather than every foreign key.
- Admin change-form fields, labels, help text, and errors have a new accessible
  vertical layout.
- `FilteredSelectMultiple` preserves grouped choices with `<optgroup>`.
- The default blank-choice label is more accessible and translatable.
- The new `csp_nonce_attr` tag can render nonce-bearing form assets, and Django
  admin/built-in templates add nonce attributes when the CSP context processor
  is enabled.

These are listed under the [Django 6.1 minor features](https://docs.djangoproject.com/en/6.1/releases/6.1/#minor-features).
The admin layout is the main immediate concern because django CMS overrides
admin templates and bundles admin-specific CSS/JavaScript. The CSP feature is a
useful future hardening option, not an upgrade requirement.

### Signals, JSON, responses, and validation

Potentially useful or observable additions are:

- `m2m_changed` now receives `raw`, and `loaddata` sends it with `raw=True`.
- `JSONNull` explicitly represents JSON scalar `null`.
- `HttpResponseRedirect` and `redirect()` accept a configurable URL
  `max_length`.
- `BinaryField`, multipart uploads, and database-cache decoding now reject
  invalid Base64 instead of accepting or ignoring it.
- Signed cookies use an unambiguous salt derivation by default.

See [model, request, and security features](https://docs.djangoproject.com/en/6.1/releases/6.1/#models)
and the [strict Base64 and signed-cookie incompatibilities](https://docs.djangoproject.com/en/6.1/releases/6.1/#miscellaneous).
django CMS has no `JSONField` or `BinaryField` model usage. Its permission
receiver does use `m2m_changed`, so fixture behavior needs attention below.

## Backwards-incompatible changes and repository exposure

The complete upstream list is in [Backwards incompatible changes in 6.1](https://docs.djangoproject.com/en/6.1/releases/6.1/#backwards-incompatible-changes-in-6-1).

| Django change | Baseline django CMS exposure | Assessment or response |
| --- | --- | --- |
| Admin removes the `wide` CSS class and hoists `object-tools` outside `content`. | `cms/test_utils/project/emailuserapp/admin.py` assigned `classes=("wide",)` to `add_fieldsets`. `cms/templates/admin/cms/page/change_form.html` declared `object-tools` inside `content`; `usersettings/change_form.html` already declared it at top level. | Removed `wide` and added a version-aware template fallback with rendered regression coverage. |
| `m2m_changed` is emitted by `loaddata` with `raw=True`. | `cms/signals/permissions.py:user_m2m_changed()` accepted `**kwargs`, so it did not crash, but it could clear caches and query users during raw fixture loading. Django's fixture guidance says receivers that access related data should return for `raw=True`. | Added an explicit `raw=False` parameter, an early return, and a zero-query regression test. |
| Supplying `fail_silently`, auth credentials, or a connection together has stricter errors; `EmailMessage` connection behavior changed. | No combined connection/auth usage was found, but deprecated `fail_silently` was used. | Migrated the calls to explicit exception handling. |
| `first()`/`last()` no longer add primary-key ordering after ordering was explicitly cleared with `order_by()`. | The only production bare `.order_by()` found builds a distinct field list and does not call `first()`/`last()`. | None. |
| ORM-generated aliases are consistently quoted; mixed-case `RawSQL` references may need quoting. | No `RawSQL` usage was found. | None. |
| `check` supplies every database when none is named. | django CMS provides checks and invokes `cms check`, but no code was found that assumes the old `databases=None` behavior. Multi-database projects may observe additional connections. | Run the check suite with two configured databases; no production edit is currently indicated. |
| PostgreSQL, MySQL, MariaDB, SQLite, GIS, and third-party database backend floors/APIs changed. | django CMS has no custom database backend or GIS code. Active PostgreSQL/MySQL CI meets the floors. | Documentation/CI changes only, as above. |
| Vary-aware page and fragment cache keys changed. | django CMS tests Django's update/fetch cache middleware and has its own plugin cache keys. The upstream change only means a one-time cache miss for old Django-generated vary-aware keys. | No migration or purge is required; note the expected cold miss in upgrade notes. |
| Signed-cookie salt fallback now defaults to false. | No direct signing API usage was found. Deployments using Django signed-cookie sessions or messages may invalidate legacy cookies at upgrade. | Document the possible logout/cookie invalidation. Use the transitional fallback only when continuity is essential. |
| Base `File` is always truthy, while common subclasses retain name-based truthiness. | No boolean checks of base `File` instances were found. | None. |
| `GenericForeignKey` now uses a private descriptor class. | django CMS uses public `GenericForeignKey` behavior but does not reference its private descriptor. | None. |
| Custom ASGI `RemoteUserMiddleware` headers changed. | No `RemoteUserMiddleware` subclass exists in the repository. | None. |
| Strict Base64 errors can surface from multipart input and corrupted database-cache values. | No custom multipart parser, `BinaryField`, or database-cache decoder exists. | No code change; malformed uploads/cache rows may now fail loudly by design. |

## Deprecations introduced in 6.1

The full list is in [Features deprecated in 6.1](https://docs.djangoproject.com/en/6.1/releases/6.1/#features-deprecated-in-6-1).
The baseline repository scan found these direct hits:

- `cms/utils/mail.py` passes `fail_silently` to
  `EmailMultiAlternatives.send()`.
- `cms/templatetags/cms_tags.py` calls
  `mail_managers(..., fail_silently=True)` while handling a missing page.
- `cms/tests/settings.py` and `testserver.py` configure `EMAIL_BACKEND`.

No affected usage was found for:

- argumentless `select_related()`;
- `ModelAdmin.list_select_related=True` or a method returning `True`;
- `values_list(flat=True)` without a field;
- top-level `JSONField` null queries;
- `BLANK_CHOICE_DASH` or either transitional setting;
- `salted_hmac()`/`base64_hmac()` without an explicit algorithm;
- `ModelAdmin.get_actions()` or `get_action_choices()` overrides;
- `transaction.savepoint()`;
- double-dot template lookups;
- deprecated field/compiler placeholder hooks; or
- PostgreSQL-specific bitwise aggregate imports.

## APIs removed in 6.1

Django 6.1 completes the 5.2 deprecation cycle. It removes:

- `staticfiles.finders.find(all=...)` in favor of `find_all=`;
- the `user=None` fallback in `login()`/`alogin()`;
- `ordering=` on PostgreSQL `ArrayAgg`, `JSONBAgg`, and `StringAgg` in favor
  of `order_by=`; and
- support for a `RemoteUserMiddleware` subclass that overrides only the sync
  `process_request()` method.

See [Features removed in 6.1](https://docs.djangoproject.com/en/6.1/releases/6.1/#features-removed-in-6-1).
No repository usage of these removed forms was found.

## Implemented repository updates

### 1. Migrate email behavior without dropping Django 5.2/6.0

The [official `fail_silently` guidance](https://docs.djangoproject.com/en/6.1/howto/mailers-migration/#replacing-fail-silently)
recommends intent-specific exception handling rather than the boolean argument.

- In the missing-page error path, `fail_silently` was omitted and transport
  errors represented by `OSError` are caught. This is an error reporter where
  mail failure must not replace the original response, while unexpected errors
  still propagate.
- `cms.utils.mail.send_mail()` preserves its public `fail_silently` argument
  for django CMS API compatibility but calls `message.send()` without the
  deprecated Django argument. It suppresses `OSError` when requested and
  re-raises it otherwise; other exceptions always propagate. Tests cover each
  branch and successful multipart delivery.
- On Django 6.1, the locmem backend is configured as:

  ```python
  MAILERS = {
      "default": {
          "BACKEND": "django.core.mail.backends.locmem.EmailBackend",
      },
  }
  ```

  `EMAIL_BACKEND` is retained for Django <6.1 through a shared feature-detection
  helper used by the test settings and standalone test server. Django explicitly
  recommends `hasattr(django.core.mail, "mailers")` or `django.VERSION >= (6, 1)`
  for multi-version libraries.

### 2. Align the custom admin change form with the 6.1 block layout

The obsolete `classes=("wide",)` was removed from the test email user's
`add_fieldsets`. The page change form now detects Django 6.1's hoisted
`object-tools` block and renders the nested fallback only on older Django
versions. Rendered regression tests verify that the tools appear exactly once
and in the appropriate location on Django 5.2 and 6.1. The custom email-user
admin configuration is also tested under its required custom-user setting.

### 3. Handle raw M2M fixture events

The permissions receiver now has the equivalent of:

```python
def user_m2m_changed(instance, action, reverse, pk_set, raw=False, **kwargs):
    if raw:
        return
    # Existing cache invalidation follows.
```

A test sends an M2M fixture event with `raw=True` and asserts that
permission-cache/user queries are skipped. This prevents unsafe fixture-time
work rather than fixing a signature crash.

### 4. Close release/test coverage gaps

- `test_requirements/django-6.1.txt` now uses `Django>=6.1,<6.2`.
- The unsupported 4.2/5.0/5.1 `test_startcmsproject` rows were replaced with
  5.2, 6.0, and 6.1. The workflow installs the editable package and Django
  constraint together and asserts `django.get_version()` before and after
  generation.
- The local Django 6.1 suite ran with deprecation warnings enabled, and the
  generated-project smoke tests verified the constrained 5.2 and 6.1 series.

## Validation evidence

Clean Python 3.14 SQLite runs passed all 1,704 tests on Django 5.2.17, 6.0.8,
and 6.1, with 57 expected skips in each environment. The Django 6.0 and 6.1
suites ran with Python warnings enabled; the 6.1 run emitted no deprecated
`fail_silently` or legacy email-backend warnings. Focused custom-user runs
verified the admin fieldset change on Django 5.2 and 6.1. Generated-project
smoke tests also completed on 5.2 and 6.1 without changing the constrained
Django series.

The remaining warnings are pre-existing django CMS deprecations, Python
resource/import deprecations, and Treebeard manager warnings; they are outside
the Django 6.1 compatibility work covered here.

## Optional adoption, not upgrade work

- Trial `FETCH_RAISE` in query-count tests and `FETCH_PEERS` only after
  benchmarking menu/admin workloads.
- Evaluate `csp_nonce_attr` and Django's CSP context processor as a separate
  security-hardening change.
- Consider `DB_CASCADE` only after identifying relations that do not depend on
  Django delete signals or Python-side cascade behavior.
- The new accessible blank-choice label may allow replacing the manual
  `("", "----")` label in `cms/forms/utils.py`, but that is a UX change and is
  not required for 6.1 compatibility.
