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

At this point in time not all are compatible with versions 4 of django CMS or above.
Please see those two lists:

Recommended with Version 4 of django CMS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

========================== ================================== ==========================
Package                    Description                        Status
========================== ================================== ==========================
djangocms-text-ckeditor    Text Plugin for django CMS using   supports v4.1 as of v5.1.2
                           CKEditor 4
djangocms-versioning       Adds versioning and publication    v4.x only
                           management features to v4
djangocms-moderation       Implements moderation process to   v4.x only
                           channel publications
djangocms-alias            Central management of recurring    v4.x only
                           plugin sequences - replaces static
                           placeholders
djangocms-url-manager      Central place to manage all link   v4.x only
                           urls for your project
djangocms-frontend         Plugin bundle for django CMS       supports v4.1
                           providing several components from
                           the popular Bootstrap 5 framework.
                           Themable and extensible
django-filer               Manager for assets like images     supports v4.1
djangocms-attributes-field An opinionated implementation to   no issues known
                           add attributes to any HTML element
djangocms-icons            Adds support for Fontawesome icons supports v4.1
                           attributes to any HTML element
djangocms-picture          Add images to your site            no issues known
djangocms-admin-style      django CMS design for Django's     supports v4.1 as of v3.2.1
                           admin backend
========================== ================================== ==========================

We welcome feedback, documentation, patches and any other help to maintain and improve
these valuable components.

Thrid-party opinionated packages
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

========================= ========================== ===================================
Package                   Description                Status
========================= ========================== ===================================
djangocms-version-locking Allows locking draft       v4.x only
                          versions to avoid
                          conflicts
djangocms-page-admin      New PageContent admin      supports v4.0, v4.1 support unclear
                          which doesn't include tree
                          functionality
djangocms-navigation      (undocumented)             supports v4.0, v4.1 support unclear
djangocms-references      Retrieve objects that are  supports v4.0, v4.1 support unclear
                          related to a selected
                          object and view to present
                          that data to the end user
========================= ========================== ===================================

Packages not (yet) supporting version 4
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

====================== =========================================== =================
Package                Description                                 Status
====================== =========================================== =================
djangocms-link         Add links on your site                      not yet supported
djangocms-blog         django CMS blog application - Support for   not yet supported
                       multilingual posts, placeholders, social
                       network meta tags and configurable apphooks
djangocms-history      Undo/redo functionality for django CMS      not yet supported
                       operations
djangocms-page-sitemap django CMS page extension to handle sitemap not yet supported
                       customization
djangocms-page-meta    Add SEO meta data to django CMS pages       not yet supported
djangocms-transfer     Export and import plugins as JSON           not yet supported
====================== =========================================== =================

Contributors are needed to add django CMS v4 support to the following packages:

Deprecated addons
-----------------

Some older plugins that you may have encountered are now deprecated and we advise
against incorporating them into new projects.

These are:

- `cmsplugin-filer <https://github.com/divio/cmsplugin-filer>`_
- `Aldryn Style <https://github.com/aldryn/aldryn-style>`_
- `Aldryn Locations <https://github.com/aldryn/aldryn-locations>`_
- `Aldryn Snippet <https://github.com/aldryn/aldryn-snippet>`_
- `Django CMS Bootstrap4 <https://github.com/django-cms/djangocms-bootstrap4>`_
  (djangocms-frontend offers an automated migration)
