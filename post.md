# django CMS 5.0.13 and 5.1.3 released with security fixes

*September 24, 2026*

We have released **django CMS 5.0.13** and **django CMS 5.1.3**. Together, the
two releases fix seven security advisories.

**We recommend that all users of django CMS 5.0.x and 5.1.x upgrade as soon as
possible.**

```bash
# django CMS 5.1.x
python -m pip install --upgrade "django-cms==5.1.3"

# django CMS 5.0.x
python -m pip install --upgrade "django-cms==5.0.13"
```

Neither release adds migrations.

## Security fixes

All of these issues require an authenticated staff account, and none can be
exploited anonymously. django CMS 5.0.13 fixes the first one. The other six
were fixed in 5.0.12 last week, and 5.1.3 is the first 5.1 release to include
them.

- [GHSA-mgv8-5r6j-2gjq](https://github.com/django-cms/django-cms/security/advisories/GHSA-mgv8-5r6j-2gjq)
  (5.0.13 and 5.1.3): a staff user who could change a page could store markup
  in its **Overwrite URL**. The page delete confirmation screen then ran that
  markup in the browser of whoever opened it, which let an editor become an
  administrator.
- [GHSA-976q-w6ch-6w82](https://github.com/django-cms/django-cms/security/advisories/GHSA-976q-w6ch-6w82)
  (5.0.12 and 5.1.3): copying, duplicating or moving pages in the page tree
  could drop view restrictions and expose restricted pages to anonymous
  visitors.
- [GHSA-g52p-phr3-hvx9](https://github.com/django-cms/django-cms/security/advisories/GHSA-g52p-phr3-hvx9)
  (5.0.12 and 5.1.3): the add-page form checked permissions against the parent
  page named in the query string instead of the parent the page was created
  under.
- [GHSA-ppqv-h89f-6q9p](https://github.com/django-cms/django-cms/security/advisories/GHSA-ppqv-h89f-6q9p)
  (5.0.12 and 5.1.3): the page wizard allowed creating pages below a parent
  page on another site.
- [GHSA-7fqg-chmv-c89g](https://github.com/django-cms/django-cms/security/advisories/GHSA-7fqg-chmv-c89g)
  (5.0.12 and 5.1.3, low severity): adding a page from a page type exposed
  restricted page types and page types from other sites.
- [GHSA-79vf-xh44-8cpm](https://github.com/django-cms/django-cms/security/advisories/GHSA-79vf-xh44-8cpm)
  (5.0.12 and 5.1.3): the move-plugin endpoint exposed plugin content through
  `plugin_parent`.
- [GHSA-cx9c-3cc5-gg94](https://github.com/django-cms/django-cms/security/advisories/GHSA-cx9c-3cc5-gg94)
  (5.0.12 and 5.1.3): users who could manage permissions could grant
  themselves page rights they did not have.

Some of these fixes are backward incompatible. Page paths containing `<` or
`>` are now rejected. Permissions behave differently when pages are copied,
duplicated or moved, and non-superusers can grant fewer global page
permissions. Please read the backward-incompatible changes in the
[5.1.3](https://docs.django-cms.org/en/latest/upgrade/5.1.3.html) and
[5.0.13](https://docs.django-cms.org/en/latest/upgrade/5.0.13.html) release
notes before you upgrade.

## Other fixes in 5.1.3

- Migration `cms.0045_pageurl_site_unique_path` no longer fails on PostgreSQL
  for databases with duplicate page paths. If the migration failed for you,
  run `python manage.py migrate` again after upgrading.
- Placeholders restricted by `CMS_PLACEHOLDER_CONF` show explicitly declared
  child plugins again. This fixes a regression introduced in django CMS 5.0.0.
- `CurrentUserMiddleware` no longer makes requests hang under ASGI.
- `GrouperAdmin` no longer writes to the wrong content object when one is
  selected by primary key.
- Slug uniqueness checks now take the site into account.
- The apphook resolver's `get_app_patterns` has been fixed.
- Inline editing modals now include the `_popup=1` query parameter Django
  expects.
- Best-effort CMS mail delivery has been restored.

The full list is in the
[changelog](https://github.com/django-cms/django-cms/blob/develop-4/CHANGELOG.rst).

## Release notes

- [django CMS 5.1.3 release notes](https://docs.django-cms.org/en/latest/upgrade/5.1.3.html)
- [django CMS 5.0.13 release notes](https://docs.django-cms.org/en/latest/upgrade/5.0.13.html)

## Reporting security issues

Thank you to everyone who reported issues responsibly and helped review the
fixes. If you think you have found a security issue in django CMS, please do
not open a public issue. Instead, follow our
[security policy](https://github.com/django-cms/django-cms/security/policy)
and report it privately.

## Thank you

Thanks to Venelin Stoykov and Vinit Kumar for their contributions and reviews,
and to the whole django CMS community.
