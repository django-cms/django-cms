Philosophy
==========

django CMS gives **editors** a toolbar on the live site where they
compose pages from reusable components — drag a hero image into place,
drop in a card grid, reorder the sections. It gives **developers**
standard Django — models, views, templates, URL patterns — and plugs
their work into that editing surface. And it gives **designers** full
control over templates and CSS, unconstrained by an admin theme or a
fixed set of layout options. Each role owns its surface; the CMS
connects them without any one needing to understand the internals of
the others.

Think of it as a box of LEGO bricks rather than a model-car kit: the
kit gives you one car, while the bricks give you the parts and the
rules for combining them. A few of those parts ship in the box; the
rest you bring yourself or pick from a wide ecosystem of add-ons.

Everything else on this page follows from that single idea.

Three disciplines, three surfaces
---------------------------------

django CMS treats **design, code, and content** as three distinct
disciplines, owned by three different roles. The CMS is shaped around
keeping those concerns separate:

- **Designers** work in templates and CSS. They define which drag-and-drop
  layout tools are available in the front end; the layout vocabulary is whatever
  the templates and CSS provide.
- **Developers** work in Django: in apps, models, plugins, apphooks,
  and configuration. The CMS's extensibility is exposed as Python
  APIs, not as a no-code builder.
- **Editors** work in the toolbar and the structure board. They
  compose pages by adding plugins to placeholders, never by editing
  templates or writing code.

Tools that blur the three roles trade flexibility and
maintainability for short-term convenience; django CMS deliberately
sides with the former.


A small, stable core
--------------------

The core of django CMS does a deliberately limited set of things:

- manage **pages** and their hierarchical structure,
- expose **placeholders** that content objects can publish into,
- coordinate **plugins** and **apphooks** so that other Django apps
  can plug into the CMS,
- integrate editing into rendered pages.

Almost everything else — versioning, alias content, headless rendering,
the rich-text editor, the frontend admin theme — lives in separate
packages. The core stays small and stable; the surface area you adopt
is the surface area you need.

For *how* pages, plugins, apphooks, and other content objects fit
together, see :ref:`composition`.


Content-agnostic
----------------

django CMS does not assume what kind of site you are building. It does
not ship a Blog model, a Product model, a News model, or a Team
model. It provides the **framework** — pages, content
objects, placeholders, plugins, the apphook mechanism — and leaves
the domain modelling to your apps.

This is a common source of "why doesn't it just…" questions, and the
answer is always the same: because every project's notion of a blog,
a product, or a team is slightly different, and the CMS would rather
host *your* model cleanly than impose *its* model in a way not optimal 
for you.

Having said that, the django CMS ecosystem includes many reusable add-ons
such as djangocms-stories for blogs and news.

Alignment with Django
---------------------

django CMS is designed to integrate naturally into a Django project,
not to replace or wrap Django. It builds on:

- apps and URL routing,
- authentication and permissions,
- models, migrations, and views,
- the Django admin.

The result is that custom application logic and CMS-managed content
coexist cleanly, and familiar Django patterns and tooling apply
throughout the project. A django CMS project is a Django project
first.


When django CMS may not be the right fit
----------------------------------------

A philosophy page should be honest about the shape of its own
tradeoffs. django CMS is not the right tool for every site:

- **It is a developer's CMS.** Reaching a working site requires some
  Django code (settings, templates, sometimes a small app). If
  nobody on the project is comfortable doing that, a no-code site
  builder will be a faster path.
- **It is overkill for very small or static sites.** A two-page
  brochure does not benefit from the publishing model, the page
  tree, or the plugin system. A static site generator is lighter.
- **It does not ship ready-made themes.** Where WordPress and
  similar platforms offer thousands of drop-in themes, django CMS
  expects you to bring your own frontend. Add-ons such as
  ``djangocms-frontend`` provide building blocks for established CSS
  frameworks (especially Bootstrap), and you are free to integrate
  any third-party theme or design system you like, but the
  templating and styling work is yours to do. On the other hand:
  there are no limits to design creativity or frontend frameworks.
- **Major upgrades take work.** django CMS follows Django's LTS
  cadence, which limits surprises, but moving a project across a
  major CMS version still requires planning — especially if you
  rely on add-ons that lag behind.
- **The surface area is large.** Versioning, multilingual content,
  multi-site, headless mode, the permission model — each is powerful
  and each takes time to learn. Small teams should adopt them
  incrementally rather than all at once. We believe it to be an exciting
  learning curve, but it is a curve nonetheless.

If your project's centre of gravity is a Django application that
happens to need a few editable pages, or if you want editors to
compose pages from reusable components without being exposed to
your application's internals, django CMS is squarely in its element.


Implications for projects
-------------------------

The philosophy above leads to several practical outcomes:

- django CMS can be introduced **incrementally** into an existing
  Django project — you do not have to rebuild around the CMS.
- Apps and CMS content can **evolve independently**, because the
  integration points (plugins, apphooks, content objects) are
  narrow and explicit.
- Long-term maintenance and upgrades are easier to manage, because
  the small core changes slowly and add-ons can usually be swapped.
- Editors gain flexible content tools **without being exposed to
  application complexity** they do not need.

The rest of the Explanation section explores how these principles
play out in practice — see :ref:`composition` next, then
:doc:`publishing`, :doc:`permissions`, and :doc:`multiple_languages`
for the cross-cutting concerns.
