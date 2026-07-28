:sequential_nav: prev

.. _tutorial_next_steps:

Where to go next
================

The tutorial is over. You can publish CMS pages, write your own
plugins, and mount Django apps via apphooks. This page is a map of
where to look when you need more.

If you have a *task* in mind
----------------------------

Reach for :doc:`/how_to/index`. The how-to guides are short, focused
recipes:

- :doc:`/how_to/05-caching` — page and plugin caching.
- :doc:`/how_to/02-languages` — serve content in multiple languages.
- :doc:`/how_to/03-multi-site` — run multiple sites from one project.
- :doc:`/how_to/13-toolbar` — add custom buttons and menus to the
  toolbar.
- :doc:`/how_to/15-wizards` — create content-creation wizards for the
  toolbar's *Create* button.
- :doc:`/how_to/18-extending_page_contents` — add custom fields to
  pages.
- :doc:`/how_to/21-headless` — use django CMS as a headless backend.
- :doc:`/how_to/22-docker-installation` and
  :doc:`/how_to/23-manual-installation` — deployment-shaped setups.

If you want to understand *why*
-------------------------------

Reach for :doc:`/explanation/index`:

- :doc:`/explanation/philosophy` — design principles behind the CMS.
- :doc:`/explanation/plugins` — the model/view/template split for
  plugins, and how plugins compose with placeholders.
- :doc:`/explanation/apphooks` — what an apphook really is.
- :doc:`/explanation/publishing` — drafts, versions, and the
  publishing model.
- :doc:`/explanation/permissions` — the permission system.

If you need the authoritative *API*
-----------------------------------

Reach for :doc:`/reference/index`:

- :doc:`/reference/configuration` — every ``CMS_*`` setting.
- :doc:`/reference/plugins` — ``CMSPluginBase`` and the plugin pool.
- :doc:`/reference/app_base` — ``CMSApp``.
- :doc:`/reference/templatetags` — every template tag the CMS exposes.
- :doc:`/reference/cli` — ``manage.py cms`` subcommands.

Three topics worth exploring next
---------------------------------

Most production sites need at least these three things. None of them
are part of django CMS core, but each has an official package and a
how-to.

**Versioning.** The core publishing flow has draft/published states.
For richer editorial workflows (multiple draft versions, scheduled
publishing) add `djangocms-versioning <https://github.com/django-cms/djangocms-versioning>`_.

**A rich-text editor that suits your team.** The CMS works with several
editors; pick one and install it as a frontend integration.
See :doc:`/explanation/commonly_used_plugins`.

**A frontend admin you're happy with.** ``djangocms-simple-admin-style``
provides a polished admin skin that pairs with the toolbar. The
quickstart project includes it; you can adopt it in a manual install
too.

Community
---------

The friendliest place to ask questions is the django CMS
`Discord server <https://discord-support-channel.django-cms.org>`_.

If you find a bug, file it on
`GitHub <https://github.com/django-cms/django-cms/issues>`_. If you
want to help, see :doc:`/contributing/index` — documentation fixes are
some of the most valuable contributions and one of the easiest places
to start.
