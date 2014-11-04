.. django cms documentation master file, created by
   sphinx-quickstart on Tue Sep 15 10:47:03 2009.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

########################
django CMS documentation
########################

********
Overview
********

django CMS is a modern CMS platform built with the popular Django web
framework.
django CMS offers out of the box support for the common features you'd expect
from a CMS but can also be easily customized by developers to create a site
that is tailored to your unique needs.

If you are a content editor looking for documentation on how to use the editing
interface, see our :doc:`/user/editing_basics` guide.

If you are a developer looking to learn more about django CMS as well as how to
install, configure and customize it for your project, this guide is for you.

***************
Why django CMS?
***************

django CMS is a battle-tested CMS platform that powers sites both large and small.
Here are a few of the key features:

* Robust internationalization (i18n) support for creating multilingual sites.
* Virtually unlimited undo history, allowing editors to revert to a previous
  version.
* Front-end editing: Create and edit content using the same interface as your users.
  Found a typo? Fixing it is as simple as double-clicking the content to switch
  to edit mode.
* Easy to use WYSIWYG editor which allows for advanced text editing features.
* Flexible plugins system: developers and designers can create custom snippets
  of content (e.g. an image carousel, etc.) to let editors focus on data entry
  rather than layout.
* ...and much more

There are other capable Django-based CMS platforms but here's why you should
consider django CMS:

* Thorough documentation.
* Integrates easily into existing projects; django CMS isn't a monolithic application
* Active and responsive developer community on Github.
* Heavily tested code.

*************
Release Notes
*************

This document refers to version |release|

.. warning::
    Version 3.0 introduces some significant changes that **require** action if
    you are upgrading from a previous version. Please refer to
    :ref:`Upgrading from previous versions <upgrade-to-3.0>`


*****************
Table of contents
*****************

.. toctree::
    :maxdepth: 2

    introduction/index
    how_to/index
    topics/index
    reference/index
    contributing/index
    user/index
    upgrade/index


Indices and tables
==================

* :ref:`genindex`
* :ref:`modindex`
* :ref:`search`
