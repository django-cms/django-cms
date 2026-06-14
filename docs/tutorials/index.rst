.. _tutorials:
.. _tutorial:

Tutorial
========

A guided walkthrough that builds a small, real-looking django CMS site
from an empty project. You will end up with a marketing site for a
fictional coffee roaster — a few editable pages, a custom plugin, and a
catalogue mounted via an apphook.

The tutorial is structured for someone who:

- has used Django at the level of the
  `official Django tutorial <https://docs.djangoproject.com/en/stable/intro/tutorial01/>`_,
- has never (or barely) used django CMS,
- wants to feel productive within an hour.

Plan to spend roughly **30 minutes reading and 60 minutes typing** for the
whole sequence. Each chapter ends with something you can see in the
browser.

Conventions
-----------

- The :doc:`/explanation/index` section answers *why*. This tutorial does
  not.
- The :doc:`/reference/index` section is the authoritative API. This
  tutorial cites it but never reproduces it.
- The :doc:`/how_to/index` section covers production concerns (caching,
  multi-language, deployment, headless). This tutorial does not.

When something in the tutorial feels too small, that is on purpose. The
goal is to finish a working site, not to enumerate every option.

The chapters
------------

.. toctree::
    :maxdepth: 1

    00-installing-django-cms
    01-first-page
    02-templates-placeholders
    03-custom-plugin
    04-apphook
    05-frontend
    06-next-steps

What you will build
-------------------

By the end of chapter 5 your project will contain:

- an ``About`` page and a ``Home`` page authored in django CMS' frontend editing 
  interface,
- a custom plugin called *Coffee card* that editors can drop into any
  placeholder,
- a ``coffeeshop`` Django app exposing a catalogue at ``/menu/``, mounted
  on a CMS page through an apphook,
- a navigation menu and minimal styling so the site reads as a site
  rather than an admin demo.

If you get stuck, the django CMS community is on
`Discord <https://discord-support-channel.django-cms.org>`_.
