.. _composition:

How django CMS is composed
==========================

A django CMS site is assembled from three building blocks: **content
objects** (of which the **page** is the most prominent), **plugins**,
and **apphooks**. Each has a single, well-defined job. Most decisions
you make while building a site are decisions about *which of the three
to reach for*.

This page describes the three building blocks side by side, the rules
that govern how they fit together, and the most common decision —
plugin vs apphook — that beginners ask about.

For the internals of each piece, follow the cross-links:

- :ref:`content_objects` — the grouper / content pattern every
  content object follows
- :ref:`plugins`
- :ref:`about_apphooks`
- :doc:`publishing`
- :doc:`menu_system`

The three building blocks
-------------------------

.. list-table::
   :header-rows: 1
   :widths: 18 32 50

   * - Block
     - What it is
     - What it owns
   * - **Content object**
     - A thing that holds editable content and exposes placeholders for
       editors to fill. **Pages** are the most common (and most powerful)
       kind — they live in the page tree, carry URLs, drive menus, and
       carry permissions. Other kinds include **aliases** (reusable
       content embedded via the Alias plugin) and content objects
       defined by add-on apps (e.g. blog posts, catalogue items).
     - Its placeholders, its translations, and — for pages — its slug,
       its template, and its position in the page tree.
   * - **Plugin**
     - A reusable content component an editor can drop into a
       placeholder.
     - The data the editor fills in (via its model) plus the template
       that renders it.
   * - **Apphook**
     - The standard way to mount a Django application onto the page
       tree. The application's URLs (and any content objects it
       defines) take their prefix from the CMS page that anchors them.
     - All URLs at and below the page it is attached to.

The content object is the **unit of editable content**. The plugin is
the **unit of composition inside it**. The apphook is **how other
content joins the page tree**.

How they fit together
---------------------

The relationships are simple, but easy to confuse if you only read
about each in isolation:

.. code-block:: text

    Page tree
     │
     └── Page  (a content object: owns placeholders, lives in the tree)
          │
          ├── Placeholder  (declared by the page's template)
          │    ├── Plugin
          │    │    └── Plugin (nested, if the parent allows it)
          │    └── Plugin
          │
          └── Apphook  (optional — attaches a Django app at this URL)
               │
               └── App-defined content objects
                    │   (e.g. blog posts, products, polls)
                    └── Placeholders
                         └── Plugins

    Outside the page tree:

    Alias  (a reusable content object embedded via the Alias plugin)
     └── Placeholders
          └── Plugins

A few rules govern the picture:

- **Content objects own placeholders. Placeholders contain plugins.
  Plugins compose.** This is true for every kind of content object —
  pages, aliases, and app-defined objects alike.
- **The page tree is what gives pages URLs**, what makes them appear
  in menus, and what carries the per-page permission model. Content
  objects that are *not* pages get their URLs by being mounted on the
  tree through an apphook, or by providing their URLs through their own
  ``get_absolute_url()`` method.
- **Plugins live in placeholders, never standalone.** Even when the
  same plugin appears on many content objects, each appearance is a
  separate plugin *instance* with its own configuration.
- **Plugins can contain other plugins** when the parent plugin
  declares ``allow_children = True``. This is how composite layouts
  (rows, columns, accordions) are built.
- **An apphook is meaningless without a page to attach it to.** It is
  not a setting; it is a binding made on a CMS page in *Advanced
  settings*. The page provides the URL prefix; the app provides
  everything below.


Plugin or apphook? A decision aid
---------------------------------

Reframed: the question is really *where does this content live?* If
it fits inside an existing placeholder on someone else's page, it is
a plugin. If it is its own kind of thing — with its own list view,
detail view, and URL — it is an app, mounted via an apphook.

.. list-table::
   :header-rows: 1
   :widths: 50 25 25

   * - You want…
     - Reach for…
     - Why
   * - A reusable content component the editor drops into any
       placeholder.
     - **Plugin**
     - Plugins are the unit of composition inside a placeholder.
   * - A whole sub-application (blog, catalogue, polls, search) with
       list and detail views.
     - **Apphook**
     - Apphooks own a URL prefix and bring their own content objects.
   * - A page where everything is editor-composed.
     - Page + plugins
     - The default flow for a page content object.
   * - A page whose body is driven by Django views (list, detail,
       search results).
     - Page + apphook
     - The page provides the URL, the app provides the views and (if
       it has them) its own content objects.
   * - Editors to choose *which records* show up in a list embedded
       on a page.
     - **Plugin** (with a model that references your records)
     - The component lives on a page; only its data lives in your
       app's models.
   * - Editors to *move* a sub-site to a different URL by moving a
       page.
     - **Apphook**
     - The views and content objects are yours; the URL belongs to
       the page.
   * - A teaser of upcoming events on the homepage *and* the full
       events sub-site at ``/events/``.
     - **Both** — plugin for the teaser, apphook for the sub-site
     - Common combination. The plugin renders a small summary; the
       apphook owns ``/events/`` and below.


When the line blurs
-------------------

A few real cases trip people up. None of them break the model; they
just look like edge cases.

**A plugin that needs its own detail URL.** A "product card" plugin
that links to ``/products/42/`` is still a plugin (it lives in a
placeholder), but the detail URL must come from somewhere. The
idiomatic answer is to **put the detail view in an apphook** mounted on
a CMS page, so the URL is editor-controllable. If you wire the view
into the project's root ``urls.py`` instead, the URL works but is
fixed in code and not controlled by the editor.

**Many copies of "the same" plugin on one page.** Each is an
independent plugin *instance* with its own configuration. They share
the same model and template; they do not share data.

**A page that has both placeholders and an apphook.** The page's own
URL (``/events/``) renders its placeholders normally; URLs *below*
(``/events/2026-summit/``) are handed to the apphook. Child CMS
pages under an apphooked page are *not* reliably reachable, because
the apphook owns that URL space. The URLs might resolve to the app hook
instead of a child page, and the child page might not be reached at all. 

**The same Django app mounted on several pages.** Each mount point is
independent. If editors should configure each mount differently
(different category, different feed), the app needs an
:ref:`apphook configuration <apphook_configurations>`.

**Reusing the same content across pages without copying it.** That's
what an **alias** is for: a content object that lives outside the
page tree and is embedded in placeholders via the Alias plugin. A
footer block, a promotional banner, or a "current opening hours"
strip are typical examples.


Where to go next
----------------

- :ref:`plugins` — what a plugin really is, what files it consists
  of, and how to think about plugin models.
- :ref:`about_apphooks` — what an apphook is, what it changes about
  URL handling, and the apphook configuration story.
- :doc:`publishing` — how the publishing model interacts with every
  content object on the page (an unpublished page hides its plugins
  *and* takes its apphook offline).
- :doc:`menu_system` — how pages, apphooks, and custom menu code
  combine to produce the navigation editors see.
