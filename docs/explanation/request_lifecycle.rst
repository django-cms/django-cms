.. _request_lifecycle:

How a request becomes a page
============================

django CMS builds on Django's request-to-response cycle — URL routing, middleware,
template rendering, and the cache framework are all standard Django. This page
explains how the CMS extends that cycle: which Django parts it hooks into, what it
adds on top, and how the two layers interact when a request for a CMS-managed page
arrives. Read it when you need to debug a page that is not showing, understand why
a cache is not invalidating, or build a mental model of how all the pieces fit
together.

If you have not yet read :ref:`composition` and :ref:`content_objects`,
do that first. The concepts introduced there — pages, content objects,
placeholders, plugins, apphooks, and the grouper / content split — are
the vocabulary this page assumes.

The big picture
---------------

.. code-block:: text

    Browser:  GET /de/events/2026-summit/
                    │
                    ▼
    1. Middleware preamble
       ApphookReload → CurrentPage → Language → Toolbar
                    │
                    ▼
    2. URL resolution
       slug → PageUrl table → Page object  (or 404 / welcome)
                    │
                    ▼
    3. Language determination
       URL prefix → session → cookie → Accept-Language → LANGUAGE_CODE
                    │
                    ▼
    4. Content resolution
       Page + language → which PageContent row?  (published? fallback?)
                    │
                    ▼
    5. Page cache gate
       Hit? → return cached response immediately
       Miss? → proceed to render, cache result for next time
                    │
                    ▼
    6. Template selection
       PageContent.template → "base.html"
                    │
                    ▼
    7. Placeholder rendering (per {% placeholder %} tag)
       Cache check → load plugin tree → render plugins
                    │
                    ▼
    8. Menu building (if template uses {% show_menu %})
                    │
                    ▼
    9. Response


1. The middleware preamble
--------------------------

Before the CMS view runs, Django's middleware stack fires in order.

``ApphookReloadMiddleware``
    Ensures the URL configuration is up-to-date when apphooks have been
    added or removed. A stale URLconf would cause ``NoReverseMatch``
    errors in menu templates.

``CurrentPageMiddleware``
    Attaches ``request.current_page`` as a lazy object. The page is
    resolved once on first access and stored on the request as
    ``request._current_page_cache`` — an in-process attribute that
    prevents resolving the same page twice during a single request.

``LanguageCookieMiddleware`` (optional — add it to
:setting:`django:MIDDLEWARE` to enable)
    Persists the user's language preference in a cookie so that
    subsequent visits default to the same language.

``ToolbarMiddleware``
    Attaches the toolbar if the user is staff and the request is in
    edit mode (``?edit`` or ``?toolbar_on``). The toolbar's presence
    disables CMS-level caching for the request.


2. URL resolution
-----------------

The request arrives at :func:`cms.views.details` via the CMS URLconf.
The view calls :func:`~cms.utils.page.get_page_from_request`, which
matches the URL slug against the ``PageUrl`` table.

The ``PageUrl`` model stores one row per ``(page, language)`` pair,
each with its own ``path`` field. This means the German URL
``/de/ueber-uns/`` and the English URL ``/en/about-us/`` are stored
independently and resolve to the same ``Page`` through different
``PageContent`` rows.

If no page is found:

* The CMS checks whether the request falls inside an apphook's URL
  space (via ``applications_page_check``). If it does, the apphook's
  parent page is treated as ``request.current_page``.
* If the URL is ``/`` and no pages exist at all, the welcome screen is
  rendered.
* Otherwise, a 404 is raised.

A ``PageUrl`` lookup happens on most requests. To avoid hitting the
database every time, the result is cached in Django's cache backend —
keyed by ``(page_lookup, language, site_id)``, with a duration set by
:setting:`CMS_CACHE_DURATIONS` ``['content']`` (default 60 seconds).
The cache is invalidated alongside the global page cache when a page's
slug changes or the page is moved in the tree.


3. Language determination
-------------------------

By the time the CMS view runs, Django's ``LocaleMiddleware`` has
already resolved the active language. The resolution chain, in order:

1. language prefix in the URL (``/de/`` when using
   :func:`~django.conf.urls.i18n.i18n_patterns`)
2. language stored in the user's session
3. language stored in a cookie (from ``LanguageCookieMiddleware``)
4. browser's ``Accept-Language`` header
5. the project's :setting:`django:LANGUAGE_CODE`

The resolved language is available as ``request.LANGUAGE_CODE``.

:setting:`CMS_LANGUAGES` overlays additional policy per language:
``fallbacks``, ``redirect_on_fallback``, ``hide_untranslated``, and
``public``. These are consulted in the next step, not here. Language
*preference* (this step) and content *availability* (the next step)
are separate concerns.


4. Content resolution
---------------------

With the ``Page`` and the language known, the CMS needs to determine
*which* ``PageContent`` row to serve.

A ``Page`` instance carries a ``page_content_cache`` dictionary —
mapping ``language → PageContent`` — that is populated once per
request by ``_get_page_content_cache()``. It loads all available
``PageContent`` rows for the page in a single query, so subsequent
lookups during the same request (including those from template tags
and the toolbar) hit this dictionary rather than the database.

The lookup logic:

* **Direct hit.** A ``PageContent`` row exists in the requested
  language. Serve it.
* **Fallback hit.** No row in the requested language, but the
  language's ``fallbacks`` list (in :setting:`CMS_LANGUAGES`) names a
  language that does have one. If ``redirect_on_fallback`` is
  ``True`` (the default), the browser is redirected to the fallback
  language's URL. If ``False``, the fallback's content is served under
  the original URL.
* **No fallback.** 404.

When ``djangocms-versioning`` is installed, ``PageContent.objects``
(the default manager) filters to the *published* row per language.
``PageContent.admin_manager`` returns every row and is used in admin
code paths only. See :ref:`publishing` for the full version-state
model.


5. The page cache gate
----------------------

Before any rendering begins, the CMS checks whether a cached copy of
the entire page already exists. This is the most impactful cache in
the system: a hit avoids template loading, placeholder rendering,
plugin rendering, and menu building entirely.

The check runs only when :setting:`CMS_PAGE_CACHE` is ``True``
(default), the user is anonymous, the toolbar is not in edit mode, and
no placeholder on the page uses the legacy ``cache = False`` flag (see
`Step 7`_).

If the conditions are met, ``get_page_cache(request)`` queries
Django's cache backend for a key composed from the site ID, language,
and a hash of the request path. A hit returns ``(content, headers,
expires_datetime)`` — the CMS reconstructs an ``HttpResponse``,
recalculates a ``max-age`` header from the stored expiry, and returns
immediately. No further processing.

The page cache uses a versioning strategy: a global integer is stored
under ``CMS_PAGE_CACHE_VERSION_KEY``. Each cache write includes the
current version. ``invalidate_cms_page_cache()`` increments the
version — all previous entries become unreachable and expire
naturally. The version key is re-written with a fresh timeout on every
cache write, ensuring it always outlives the entries it protects.

The cache duration is the shortest of ``CMS_CACHE_DURATIONS['content']``
and the TTL returned by each rendered placeholder's
:meth:`~cms.models.placeholdermodel.Placeholder.get_cache_expiration`.
If any placeholder returns ``EXPIRE_NOW`` (0), the page is not cached
at all.

When the page cache is skipped — for authenticated users, toolbar
edit mode, or plugins that opt out — the remaining cache layers
(placeholder, menu) are also skipped for that request.

**On a cache miss,** the CMS proceeds to render the page (Steps 6–8).
After rendering, ``set_page_cache()`` stores the result: it gathers
all placeholders that were rendered, computes the effective TTL as the
shortest across all placeholders, collects the union of Vary headers,
and writes ``(content, headers, expires_datetime)`` to the cache. The
absolute expiry timestamp is stored so that future reads can
recalculate ``max-age`` without recomputing each placeholder's TTL.


6. Template selection
---------------------

The ``PageContent.template`` field names the Django template to use
(e.g. ``"base.html"``). Template resolution follows Django's standard
loader chain: the CMS template directory, then the project's template
directories, then any additional loaders configured in
:setting:`django:TEMPLATES`.

The template defines which placeholders exist through ``{% placeholder
"name" %}`` tags. These are the rendering anchor points for the next
step.


7. Placeholder rendering
------------------------

For each ``{% placeholder %}`` tag in the template, the CMS resolves
the corresponding :class:`~cms.models.placeholdermodel.Placeholder`
object — scoped to the current ``PageContent`` — and renders it.

Before loading plugins, the CMS checks the placeholder cache. This
cache stores the fully rendered HTML for a single placeholder, keyed
by placeholder ID, language, site, timezone, and any Vary headers the
placeholder's plugins declare. It uses its own per-placeholder version
integer — separate from the global page cache version — so
invalidating one placeholder does not affect others. The check runs
when :setting:`CMS_PLACEHOLDER_CACHE` is ``True`` (default), the
toolbar is not in edit mode, and caching is enabled on the placeholder
and in the template tag (both defaults).

A cache hit returns the pre-rendered HTML directly. On a miss, the CMS
loads the plugin tree and renders it.

**Plugin tree loading.** Plugins form a tree through a self-referential
foreign key: each ``CMSPlugin`` row has a ``parent`` field pointing to
its container plugin (or ``NULL`` for plugins placed directly into a
placeholder). The tree is assembled by querying children at each
level, ordered by a ``position`` field.

The root plugins (those inserted directly into the placeholder) are
determined by the template and slot; valid root plugin classes for a
given ``(template, slot)`` are cached in-process in
``PluginPool.root_plugin_cache``, avoiding recomputation on every
render.

**Plugin rendering.** The tree is walked depth-first. For each plugin,
:meth:`CMSPluginBase.render() <cms.plugin_base.CMSPluginBase.render>`
returns an HTML fragment. Context flows from parent to child through
the :setting:`CMS_PLUGIN_CONTEXT_PROCESSORS` pipeline.

**Plugin-level cache control.** Each plugin class can influence the
placeholder cache through two methods:

``get_cache_expiration(request, instance, placeholder)``
    Returns a TTL in seconds for this plugin instance. The placeholder
    uses the shortest TTL across all its plugins. Override this to
    vary cache duration by content type — a shorter TTL for a "latest
    news" plugin than for static footer content.

``get_vary_cache_on(request, instance, placeholder)``
    Returns a list of HTTP header names to vary on — for example
    ``['User-Agent']`` for a plugin that renders differently on mobile.

The legacy ``cache = False`` attribute on a ``CMSPluginBase`` subclass
causes the plugin to return ``EXPIRE_NOW``, which disables the page
cache for any page containing that plugin. Prefer overriding
``get_cache_expiration()`` with a short TTL instead.

After rendering, the result is stored in the placeholder cache with a
duration of ``min(CMS_CACHE_DURATIONS['content'], placeholder_ttl)``.
The cache is invalidated — by incrementing the per-placeholder
version — whenever any plugin inside it is saved, moved, or deleted.

During rendering, plugins may also perform permission checks — for
example, whether the current user can see a restricted plugin. These
checks use the permission cache, which stores allowed page IDs per
user and per action (``change_page``, ``publish_page``, etc.) in
Django's cache backend. It is invalidated when the user's groups
change or when any ``PagePermission`` or ``GlobalPagePermission`` is
saved or deleted. See :doc:`permissions` for the full model.


8. Menu building
----------------

If the template uses ``{% show_menu %}`` or related tags, the menu
system assembles the navigation tree.

The menu is cached independently of the page and its placeholders. A
cached page response does *not* imply a cached menu — the menu is
still built or retrieved on every request, because it depends on the
page tree state, which can change independently of individual page
content.

The menu cache is keyed by ``(site_id, language)``, stored in Django's
cache backend, with a duration set by :setting:`CMS_CACHE_DURATIONS`
``['menus']`` (default one hour). On a cache miss, the system runs
menu generators (``CMSMenu`` walks the page tree) and modifiers (soft
root cutting, auth visibility filtering, level marking), then
serializes the result. The cache is invalidated by
``menu_pool.clear()`` whenever a page is saved, moved, published, or
deleted — selectively by site and language or globally.

Menu building and toolbar authorization also consult the permission
cache (see `Step 7`_) to determine which pages are visible to the
current user based on ``hide_untranslated``, login-required, and
view-restriction settings.

For the full menu system, see :doc:`menu_system`.


9. Response
-----------

The rendered page — whether from cache or freshly built — is returned
as a Django ``HttpResponse``. If the page cache layer wrote the
response, the headers include ``Cache-Control: max-age=...``,
``Expires``, and ``Vary``, set from the values computed during the
cache write in Step 5.

The toolbar, if active, wraps each plugin in edit markers and injects
structure-board data and admin URLs. This happens after rendering and
does not affect the cache — edit-mode requests bypass all CMS-level
caching and are never cached themselves.


Cache layers at a glance
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 22 16 14 18 30

   * - Layer
     - Storage
     - Keyed by
     - Duration
     - Invalidated by
   * - ``request._current_page_cache``
     - Process memory
     - —
     - Request lifetime
     - —
   * - ``page.page_content_cache``
     - Process memory
     - language
     - Request lifetime
     - —
   * - Page URL cache
     - Django cache
     - (page, lang, site)
     - ``content`` TTL
     - Version bump on slug/move
   * - **Page cache**
     - Django cache
     - (site, lang, path hash)
     - ``min(content, min ph TTL)``
     - ``invalidate_cms_page_cache()``
   * - **Placeholder cache**
     - Django cache
     - (ph, lang, site, tz, vary)
     - ``min(content, ph TTL)``
     - ``clear_placeholder_cache()``
   * - **Permission cache**
     - Django cache
     - (user, action)
     - ``permissions`` TTL
     - Version bump on group/perm change
   * - **Menu cache**
     - Django cache
     - (site, lang)
     - ``menus`` TTL
     - ``menu_pool.clear()``
   * - Plugin pool cache
     - Process memory
     - (template, slot)
     - Process lifetime
     - —


Where to go next
----------------

- :ref:`composition` — the three building blocks (content objects,
  plugins, apphooks) that the lifecycle orchestrates.
- :ref:`content_objects` — the grouper / content split that underpins
  content resolution (Step 4).
- :ref:`publishing` — how version states affect which content rows are
  visible and what "published" means for caching.
- :doc:`multiple_languages` — the language-determination and fallback
  rules that drive Steps 3 and 4.
- :doc:`menu_system` — the generators and modifiers behind Step 8.
- :doc:`permissions` — the permission model that the permission cache
  protects.
- :doc:`/reference/configuration` — the authoritative reference for
  :setting:`CMS_PAGE_CACHE`, :setting:`CMS_PLACEHOLDER_CACHE`,
  :setting:`CMS_CACHE_DURATIONS`, and related settings.
- :doc:`/reference/plugins` — the ``CMSPluginBase`` API, including
  ``get_cache_expiration()`` and ``get_vary_cache_on()``.
