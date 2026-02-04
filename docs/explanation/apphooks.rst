.. _about_apphooks:

Application hooks ("apphooks")
==============================

An *Application Hook* (usually simply *apphook*) attaches a Django application's URL tree to a
django CMS page.

Conceptually, an apphook turns a CMS page into a **mount point** for another application's URLs.
Once attached, requests to that page (and to everything below it) are **routed into the hooked
application**, rather than being served as normal CMS page content.

Think of it like including a URLconf in your project's ``urls.py``, except that the *base path*
is defined by content editors through the page tree.

.. code-block::

  /records/            -> handled by the attached application's URLs
  /records/1984/       -> handled by the attached application's URLs
  /records/...         -> handled by the attached application's URLs

In other words: the CMS page provides the **base path** (``/records``), and the application
provides the **remainder of the URL space** (``/1984/``).

For example, suppose you have an application that maintains and publishes information about
Olympic records. You could add this application to your project's ``urls.py`` (before the
django CMS URL patterns), so that users will find it at ``/records``.

That would integrate the application into your *project*, but it would not be fully integrated
into django CMS. For example:

- django CMS would not be aware of it and could allow editors to create a CMS page with the same
  ``/records`` slug, which could then never be reached.
- The application's pages won't automatically appear in your site's menus.
- The application's pages won't be able to take advantage of the CMS's publishing
  workflow, permissions or other functionality.

Apphooks offer a more complete integration by making the CMS aware of that URL space.

What changes in request handling
--------------------------------

Without an apphook, a request like ``/records/1984/`` is resolved by Django's URLconf first, and
then (if it falls through to the CMS) by django CMS.

With an apphook in place, django CMS treats the apphooked page as a routing entry:

- It resolves the CMS page for the base path (``/records/``).
- If that page has an apphook attached (and is published), it delegates URL resolution for the
  remainder of the path (``1984/``) to the application's URLconf.

This delegation is why apphooks are sometimes described as "swallowing" the URL space below a
page: the application becomes responsible for everything underneath that base path.

What changes with an apphook
----------------------------

When you attach an application to a CMS page:

- The CMS page's URL becomes the **base path** for the application (e.g. ``/records``).
- The application takes over **all URLs below that base path** (e.g. ``/records/1984``).
- django CMS can treat the application as part of the site's structure (for example, preventing
  unreachable slug conflicts and supporting menu integration).

In practice this means the CMS page behaves like a routing entry in your project's URLconf.

This also means the application can be served at a URL defined by content managers, and moved
around in the site structure by moving the page.

An apphook only becomes active when an editor attaches it to a page (see :ref:`apphooks_how_to`
for the mechanics).

.. important::

  Apphooks are part of the CMS *publishing* model.

  - An apphook does not serve any public traffic until the page is **published**.
  - This also implies that parent pages on the path need to be published.

Implications and trade-offs
---------------------------

Apphooks trade "page renders its own content" for "page becomes a mount point". That has a few
practical consequences:

- **Slug conflicts become CMS-visible**. Because django CMS owns that base path, it can prevent
  editors from creating pages that would make the mounted application unreachable.
- **Menu integration becomes possible**. Mounted application pages can participate in the site's
  navigation (depending on the menu integration the application/apphook provides).
- **CMS workflow and permissions can apply**. At minimum, publishing controls whether the mount
  point is public; additional integration varies by application.

.. warning::

  An apphook "swallows" all URLs below the apphooked page.

  As a result, child pages under an apphooked page are not reliably reachable, because requests
  under that path are routed to the application.

  Workarounds exist for advanced cases, but they require explicit routing back into the CMS; see
  the discussion in :ref:`apphooks_how_to`.

Multiple apphooks per application
---------------------------------

The same application can be attached multiple times, to different pages. Each attachment creates a
different mount point (for example ``/records`` and ``/results`` could both route into the same
application).

See :ref:`multi_apphook` for details.

In addition, an application can support multiple configurations so that each mount point can
behave differently.

Apphook configurations
----------------------

You may require the same application to behave differently in different locations on
your site. For example, the Olympic Records application may be required to publish
athletics results at one location, but cycling results at another, and so on.

An :ref:`apphook configuration <apphook_configurations>` class allows site editors to create
multiple configuration *instances* that specify this behaviour.

Terminology (and how the pieces relate)
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

Apphooks involve three related concepts that are easy to blur together:

.. list-table::
   :header-rows: 1
   :widths: 22 18 60

   * - Concept
     - Defined by
     - Meaning
   * - Apphook class
     - Developer
     - Code that connects a CMS page to an application's URLconf ("mount this application here").
   * - Apphook configuration class
     - Developer
     - Describes which configuration options exist ("what can editors choose?").
   * - Apphook configuration instance
     - Editor
     - Concrete configuration data selected for one mount point ("use cycling mode here").

The available configuration options are presented in an admin form and are determined by the
application developer.

.. important::

  An apphook (and therefore also an apphook configuration) serves no function until it is
  attached to a page. Also, until that page is **published**, the application will not be
  reachable for the public at that location.

  An apphook also "swallows" all URLs below that of the page, handing them over to the
  attached application. If you add child pages under an apphooked page, django CMS cannot serve
  them reliably because requests under that path are routed to the application instead.
