.. _content_objects:

Content objects: the grouper / content pattern
==============================================

Suppose you are building a site that needs pages in three languages,
with draft/publish workflow, and a blog that inherits the same
behaviour. In a typical Django project you would model each concern
separately — translation tables, version fields, publish flags — and
wire them together by hand.

django CMS solves this once, at the architecture level. **Every
editable thing is a content object** — a page, an alias, a blog post,
a product listing. Each is stored as two cooperating objects: a
*grouper* that holds the long-lived identity (what it is, where it
lives in the tree), and one or more *content* rows that hold the
editable state (the title, the body, the template — per language, per
version). Versioning, translations, and permissions plug into this
split through contracts. Your model gets them without the CMS needing
to know what your model is.

If you have only ever used Django models that put everything in one
table, the pattern looks like one extra hop. It is. The hop is what
makes the CMS treat your blog post and a CMS page as the same kind of
thing — both get the draft/publish toolbar, both get translated through
the same mechanism, both participate in the same permission model.

The two parts
-------------

.. list-table::
   :header-rows: 1
   :widths: 18 38 44

   * - Part
     - What it holds
     - Example fields (for a Page)
   * - **Grouper**
     - The long-lived **identity** of the content object. One row
       per "thing". Survives translations, versions, and edits.
     - Site, tree position, ``is_home``, ``application_urls`` (the
       apphook binding), ``login_required``.
   * - **Content**
     - The **editable state** of the grouper, for one combination of
       *language × version × any other axis* a versioning package
       cares about. Many rows per grouper.
     - ``title``, ``template``, ``placeholders``, ``in_navigation``,
       ``soft_root``, ``meta_description``.

For a page that exists in English and German, there is **one**
``Page`` row and **two** ``PageContent`` rows — one per language. Add
``djangocms-versioning`` to the project and the same page now has *as
many* ``PageContent`` rows per language as there are draft, published,
unpublished, and archived versions.


Why split it
------------

Three concerns all push in the same direction:

- **Translations.** A page is not really *in* a single language — it
  has a translation for each language. Putting language fields on the
  grouper would force one row per language, with everything that
  shouldn't vary by language (site, parent in the tree, apphook
  binding) duplicated and kept in sync by hand.
- **Versions.** A versioning package wants to keep many flavours of
  the same content around (current draft, last published, an
  archived earlier draft). If versions lived on the grouper, the
  page tree would have to grow a new node for every draft — broken.
- **Stable identity.** A page's URL, its position in the tree, and
  the apphook attached to it should not change when an editor saves
  a new translation or publishes a new version. The grouper is what
  *stays the same*.

The grouper / content split keeps each concern in the right place.
The grouper is the *noun* (this page exists, here, in the tree). The
content is the *adjective* (in this language, this version, with this
title).


The concrete shape for pages
----------------------------

The two-part pattern is most visible on the page model:

.. code-block:: text

    Page                       (grouper)
     ├── site
     ├── parent / tree position
     ├── is_home
     ├── application_urls       ← the apphook binding
     │
     ├── PageContent rows       (content, per language × version)
     │    ├── language="en"
     │    │    ├── title="About us"
     │    │    ├── slug="about-us"
     │    │    ├── template="base.html"
     │    │    ├── placeholders → plugins
     │    │    └── in_navigation, soft_root, meta_description, …
     │    │
     │    └── language="de"
     │         └── …
     │
     └── PageUrl rows           (per-language routing table, derived
                                 from the published content)

The `Page <cms.models.pagemodel.Page>` docstring puts it plainly:

    A ``Page`` is an abstract entity. It does not have any content
    associated with it, nor does it provide any slugs to build a URL.


The pattern extends beyond pages
--------------------------------

Other content objects follow the same shape:

- **Aliases** (from ``djangocms-alias``): ``Alias`` is the grouper,
  ``AliasContent`` is the content. An alias survives across languages
  and versions in the same way a page does.
- **App-defined content objects.** Any add-on that needs versioning
  or translation on its own model is encouraged to use the
  grouper / content split. ``djangocms-versioning`` integrates with
  arbitrary grouper / content pairs through the
  ``CMSAppExtension`` contract.

The CMS provides scaffolding for the admin side of this pattern in
:class:`~cms.admin.utils.GrouperModelAdmin` — see
:doc:`/how_to/16-grouper-admin` for how to use it on your own
grouper / content pair.


Working with content in code
----------------------------

Two manager pairs come with every content model. They look the same
on the outside; they answer very different questions.

``objects``
    Filters down to "content the **public** should see right now."
    What that means depends on which packages are installed — a
    versioning package narrows it to the currently published version
    in the current language, for example. Use this in any code path
    that serves a request.

``admin_manager``
    Returns **every** content row attached to the grouper, regardless
    of visibility, language, or version state. Use this in admin code,
    management commands, and tools that need to reason about the full
    history of a content object.

.. code-block:: python

    # In a view: only what's currently visible to the public.
    PageContent.objects.filter(language="en", page=page)

    # In an admin tool: every version, every language.
    PageContent.admin_manager.filter(page=page)

Using ``objects`` in admin paths makes drafts and archived content
invisible to editors. Using ``admin_manager`` in public paths leaks
unpublished content. The split is intentional.


Implications and trade-offs
---------------------------

- **You always need to know which content row you mean.** "The
  page's title" is ambiguous — it's the title of *some* PageContent
  row. Most CMS APIs take a language argument (often defaulted from
  the request) to resolve this.
- **Foreign keys point at the grouper, not the content.** If your
  app's model needs to reference a page, the FK is to ``Page``, not
  to ``PageContent``. The reference survives translations and
  versions.
- **Custom admin work is more involved.** You are managing two
  models that should *feel* like one to the editor.
  :class:`~cms.admin.utils.GrouperModelAdmin` exists to keep that
  ergonomics work out of your code.
- **Placeholders belong to the content, not the grouper.** Every
  language version of a page has its own placeholders, with its own
  plugins. That is by design: a German translation rarely consists
  of the same plugins in the same order as the English one.


Where to go next
----------------

- :ref:`composition` — how content objects compose with plugins and
  apphooks to form a site.
- :ref:`publishing` — what "published" means for a content object,
  and what versioning packages add on top of the core split.
- :doc:`/how_to/16-grouper-admin` — building an admin for your own
  grouper / content pair.
- :doc:`/how_to/20-cms-config` — declaring that your app's content
  models participate in CMS contracts (e.g. versioning).
