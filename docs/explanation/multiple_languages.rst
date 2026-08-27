#####################################
Serving content in multiple languages
#####################################

django CMS treats multilingual content as a first-class concern, not
as a feature bolted on top of single-language pages. This page
describes the underlying model, the configuration surface that
controls it, and the decisions every multilingual project has to
make.

For step-by-step setup, see :ref:`multilingual_support_how_to`. For
the authoritative list of settings, see
:doc:`/reference/configuration`.


********************
Content per language
********************

Every content object follows the grouper / content split described
in :ref:`content_objects`. The grouper (``Page``, ``Alias``) is
language-agnostic — it owns the identity, the tree position, the
apphook binding. The content row (``PageContent``, ``AliasContent``)
is **per language**.

That means:

* a page that exists in English and German is **one** ``Page`` with
  **two** ``PageContent`` rows,
* each translation has its **own placeholders** and its own
  plugins, *and* its own ``title``, ``meta_description``, ``template``
  choice, and ``in_navigation`` setting,
* slugs are also per language — they are authored on each
  ``PageContent`` and served from a ``PageUrl`` row keyed by
  ``(page, language)``, which is why the German URL
  ``/de/ueber-uns/`` and the English URL ``/en/about-us/`` can be
  completely independent words.

Translating a page is therefore not a content edit — it is **creating
a new PageContent row** for that page in the target language. The
grouper-side fields (apphook binding, tree position, login required)
are not duplicated.

********************************************
``CMS_LANGUAGES`` and Django's ``LANGUAGES``
********************************************

Django already has :setting:`django:LANGUAGES` and
:setting:`django:LANGUAGE_CODE`. django CMS adds its own
:setting:`CMS_LANGUAGES` setting on top. They do different jobs:

* :setting:`django:LANGUAGES` is the set of languages your *project*
  knows about — Django uses it for translation files, form labels,
  URL routing.
* :setting:`CMS_LANGUAGES` is how each of those languages should
  behave **as CMS content**: which sites it is offered on, what to
  do when a page is not translated into it, whether to show pages in
  it to anonymous visitors, and what to fall back to.

The per-language options that matter most are:

``fallbacks``
    Ordered list of language codes to try if a requested
    ``PageContent`` row does not exist in this language.

``redirect_on_fallback``
    When a fallback is served, whether to redirect the browser to
    the fallback's own URL (default ``True``) or to keep the URL of
    the originally requested language (and serve the fallback
    content under it).

``hide_untranslated``
    Whether pages without a ``PageContent`` row in this language are
    hidden from menus. Default ``True``.

``public``
    Whether this language is offered to anonymous visitors. Default
    ``True``. Setting this to ``False`` is useful for staging a
    translation before it goes live.

The setting can be configured per site (for multi-site projects),
with a ``default`` block providing fall-through values.


.. _determining_language_preference:

*************************************************
How django CMS determines which language to serve
*************************************************

Serving a multilingual page is two questions, asked in order:

1. **Which language does the visitor want?** (language *preference*)
2. **Does the requested page exist in that language?** (content
   *availability*)

Each question has its own resolution rules. Conflating them is a
common source of "why is it serving English?" bugs.

Language preference
===================

django CMS uses Django's standard language-discovery chain, in this
order:

* the language code prefix in the URL (e.g. ``/de/`` when using
  :func:`~django.conf.urls.i18n.i18n_patterns`),
* the language stored in the user's session,
* the language stored in a cookie from a previous visit (set by
  ``cms.middleware.language.LanguageCookieMiddleware`` — not on by
  default),
* the language requested by the browser in the ``Accept-Language``
  header,
* the project's :setting:`django:LANGUAGE_CODE` as a final fallback.

The first match wins. More detail is in the Django docs at
`How Django discovers language preference
<https://docs.djangoproject.com/en/dev/topics/i18n/translation/#how-django-discovers-language-preference>`_.

Content availability
====================

Once the preferred language is known, the CMS looks up the
``PageContent`` row for the requested page in that language.

* **Direct hit.** A ``PageContent`` row exists in the requested
  language — serve it.
* **Fallback hit.** No row in the requested language, but
  ``fallbacks`` lists another language that *does* have one. What
  happens next depends on ``redirect_on_fallback``:

  - ``True`` (default): redirect the browser to the URL of the
    fallback language. The address bar now shows the fallback's
    URL prefix.
  - ``False``: serve the fallback's content under the originally
    requested URL. The address bar keeps the requested language
    prefix but the content is in the fallback language.
* **No fallback.** No row exists in the requested language and no
  ``fallbacks`` entry produces a hit either — the CMS returns 404.

These three behaviours cover most real cases. Be deliberate about
which one each language gets; "serve English under the German URL"
is rarely what a German-speaking visitor wants.


**************
URL strategies
**************

A multilingual django CMS site picks one of three URL shapes. The
choice affects deployment, SEO, and the editor experience.

**Prefixed URLs** (``/en/``, ``/de/``)
    The most common. Wrap your CMS URL patterns in
    :func:`~django.conf.urls.i18n.i18n_patterns`. Django strips the
    prefix and activates the matching language; the CMS resolves
    the page in that language. One domain, all languages.

**Per-domain** (``example.com`` and ``example.de``)
    One Django ``Site`` per language. ``SITE_ID`` selects the active
    site per request (usually via host-header middleware); each
    site's :setting:`CMS_LANGUAGES` block defines what languages it
    serves. URLs do not carry a language prefix. Best when SEO or
    branding requires distinct domains.

**No URL marker**
    No prefix, no per-domain split. The language comes entirely
    from the cookie, session, or ``Accept-Language`` header. Rare in
    practice — most visitors and search engines expect a stable URL
    per language.

*********************************
Per-language menus and visibility
*********************************

Because content is per-language, navigation is too. The CMS menu
shows a page in language X if there is a ``PageContent`` row for it
in language X *and* that row's ``in_navigation`` flag is set.

If a page has no row in the requested language:

* with ``hide_untranslated = True`` (default), the page is omitted
  from menus in that language,
* with ``hide_untranslated = False``, the page is shown in menus
  even in languages it has not been translated into; clicking
  follows the fallback rules above.

The ``public`` per-language flag is independent: a language marked
``public = False`` is hidden from anonymous visitors entirely
(useful for staging translations before launch), regardless of which
pages are translated into it.

*****************
Where to go next
*****************

* :ref:`content_objects` — the grouper / content split that makes
  per-language content possible.
* :ref:`composition` — how content objects, plugins, and apphooks
  combine; placeholders being per-language is part of this story.
* :ref:`multilingual_support_how_to` — practical steps to enable
  multilingual support in a project (settings, middleware, URL
  patterns).
* :doc:`/reference/configuration` — the authoritative reference for
  :setting:`CMS_LANGUAGES` and related settings.
