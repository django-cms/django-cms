.. _commonly-used-plugins:

Some commonly-used plugins
==========================

Please note that dozens if not hundreds of different django CMS plugins have been made
available under open-source licences. Some, like the ones on this page, are likely to be
of general interest, while others are highly specialised.

This page only lists those that fall under the responsibility of the django CMS project.
Please see the `Django Packages <https://djangopackages.org/search/?q=django+cms>`_ site
for some more, or just do a web search for the functionality you seek - you'll be
surprised at the range of plugins that has been created.

django CMS Core Addons
----------------------

We maintain a set of *Core Addons* for django CMS.

You don't need to use them, and for many of them alternatives exist, but they represent
a good way to get started with a reliable project set-up. We recommend them for new
users of django CMS in particular.

You will always find a complete list of the officially endorsed core addons in the
`django CMS ecosystem <https://github.com/django-cms/djangocms-ecosystem>`_ github
repository.

Here's a brief overview of the current status of the core addons:

.. include :: ../autogenerate/plugins.include

We welcome feedback, documentation, patches and any other help to maintain and improve
these valuable components.

Thrid-party opinionated packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

========================= ========================== ===================================
Package                   Description                Status
========================= ========================== ===================================
djangocms-page-admin      New PageContent admin      supports v4.0, v4.1 support unclear
                          which doesn't include tree
                          functionality
djangocms-navigation      (undocumented)             supports v4.0, v4.1 support unclear
djangocms-references      Retrieve objects that are  supports v4.0, v4.1 support unclear
                          related to a selected
                          object and view to present
                          that data to the end user
========================= ========================== ===================================

Deprecated addons
-----------------

Some older plugins that you may have encountered are now deprecated and we advise
against incorporating them into new projects.

.. include :: ../autogenerate/deprecated_plugins.include

Also, all `Aldryn plugins <https://github.com/aldryn/>`_ are deprecated and archived.