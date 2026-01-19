Philosophy
==========

django CMS is designed around a simple guiding idea: **complex publishing
requirements are best addressed through small, composable building
blocks**.

In django CMS, those building blocks are primarily **Django applications**
and **content plugins**. Rather than introducing a separate abstraction
layer, the CMS builds directly on Django’s application model and extends
it with tools for structured, editable content.

This approach allows projects to remain recognisably Django projects
while gaining powerful content management capabilities.

----

A small, stable core
-------------------

The core of django CMS has a deliberately limited scope. Its main
responsibilities are to:

- manage pages and their hierarchical structure
- provide placeholders where content can be edited
- integrate editing capabilities into rendered pages
- coordinate plugins and application integration

By keeping the core focused, django CMS remains stable and predictable.
Most project-specific functionality lives outside the core, in Django
apps and plugins.

----

Applications as building blocks
--------------------------------

django CMS treats **Django applications** as first-class building blocks
for structuring a site.

They can provide front-end editable models that contain CMS content.

Through the use of *apphooks*, applications can be attached to parts of
the page tree, allowing them to:

- define their own URL structures
- handle requests using standard Django views
- coexist alongside CMS-managed pages

This makes it possible to combine traditional Django applications with
CMS-managed content in a single, coherent site, without forcing either
into an unnatural role.

----

Plugins for content composition
-------------------------------

While applications provide functionality and behaviour, **plugins are
used to compose content**.

Plugins represent small, focused pieces of content or presentation that
can be placed inside placeholders on a page. They can be:

- combined and nested to build complex layouts
- reused across pages
- extended or customised by developers

This plugin-based approach allows editors to assemble pages visually,
while developers retain control over structure, data, and behaviour.

----

Advanced functionality through CMS extensions
---------------------------------------------

More advanced publishing requirements — such as content versioning,
editorial or moderation workflows — are addressed through **CMS
extensions** rather than by expanding the core system.

This ensures that projects can adopt additional capabilities when
needed, without imposing unnecessary complexity on simpler use cases.

CMS extensions advertise their capabilities. Other Django applications
or plugin packages can sign up to use them.

----

Alignment with Django
---------------------

django CMS is designed to integrate naturally into Django projects,
rather than replacing or abstracting away Django itself.

It builds directly on Django concepts such as:

- applications and URL routing
- authentication and permissions
- models, migrations, and views
- the Django admin

As a result, CMS-managed content and custom application logic can
coexist cleanly, and developers can apply familiar Django patterns and
tooling throughout a project.

----

Implications for projects
-------------------------

This design philosophy leads to several practical outcomes:

- django CMS can be introduced incrementally into existing Django
  projects
- applications and CMS pages can evolve independently
- long-term maintenance and upgrades are easier to manage
- editors gain flexible content tools without being exposed to
  unneccessary application complexity

The rest of the Explanation section explores how these principles are
applied in areas such as plugins, apphooks, publishing, permissions, and
multilingual content.
