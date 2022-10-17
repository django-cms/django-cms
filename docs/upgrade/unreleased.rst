.. _upgrade-to-enter-version-here:

*******************
4.X.X release notes
*******************

*October 31, 2022*

Welcome to django CMS 4.X.X!

These release notes cover the new features, as well as some backwards
incompatible changes you’ll want to be aware of when upgrading from
django CMS 4.0 or earlier. We’ve begun the deprecation process for some
features.

See the How to upgrade to 4.X.X to a newer version guide if you’re
updating an existing project.

Django and Python compatibility
===============================

django CMS supports **Django 3.2, 4.0, and 4.1**. We highly recommend and only
support the latest release of each series.

It supports **Python 3.7, 3.8, 3.9, and 3.10**. As for Django we highly recommend and only
support the latest release of each series.

*******************
What's new in 4.X.X
*******************

Integration of djangocms-versioning into the pagetree
=====================================================

Feature 2
=========

Feature 3
=========

Minor features
==============

Bug Fixes
=========

* In rare cases moving plugins from one placeholder to another could result in
  a server error and an inconsistent plugin tree.
* Empty page contents (e.g., due to a missing translation of a page) will now
  render correctly in the page tree.
* Adding a page will trigger the form in the language viewd not in the browser
  language
* The "Empty all" menus for placeholders now works.


**************************************
Backward incompatible changes in 4.X.X
**************************************

TitleExtension
==============

``TitleExtension`` in ``cms.extensions.models`` has been renamed to
``PageContentExtension`` to keep a consistent language in the page models.

Any packages using ``TitleExtension`` will need to adapt the name change in
their code base.

Miscellaneous
=============

Features deprecated in 4.X.X
============================

Empty sections are to be removed before release.

Removal of deprecated functionality
===================================

Empty sections are to be removed before release.

