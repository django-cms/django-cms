##########
django CMS
##########

|PyPiVersion| |PyVersion| |DjVersion| |License| |Coverage|

Lean, open-source enterprise content management powered by Django.
Backed by the non-profit django CMS Association (`Sponsor us <https://www.django-cms.org/en/memberships/>`_).

This repository contains the core package published as ``django-cms`` on PyPI.

Quick links
===========

* Start here: `Documentation (stable) <https://docs.django-cms.org/>`_
* Developing on ``main``: `Documentation (latest) <https://docs.django-cms.org/en/latest/>`_
* Planning an upgrade: `Release notes / Upgrade guide <https://docs.django-cms.org/en/latest/upgrade/index.html>`_
* Project info: `Website <https://www.django-cms.org/>`_ · `Changelog <CHANGELOG.rst>`_
* Contribute safely: `Contributing <CONTRIBUTING.rst>`_ · `Code of Conduct <CODE_OF_CONDUCT.rst>`_ · `Security <SECURITY.md>`_


********
Features
********

Build complex publishing workflows with simple, composable parts:

* robust internationalisation (i18n) and multi-site support
* front-end (inline) editing so editors can work directly on rendered pages
* a flexible placeholder and plugin system for reusable content components
* integration with multiple rich-text editors
* content versioning, editorial workflows, and headless setups via official add-on packages
* a hierarchical page tree with SEO-friendly URLs
* extensible navigation and application integration (apphooks)

Developing applications that integrate with and take advantage of django CMS features is easy and well-documented.

More information on `our website <https://www.django-cms.org>`_.


*************************
Installation & Quickstart
*************************

Get a working setup by following the official guide (recommended). If you already have a Django project, you can still
use the same steps and integrate django CMS incrementally.

.. code-block:: console

    python -m pip install django-cms

Next, follow the official installation guide and tutorials:

* `Installation (How-to) <https://docs.django-cms.org/en/latest/introduction/01-install.html>`_
* `Tutorials <https://docs.django-cms.org/en/latest/introduction/>`_


*************
Documentation
*************

Find tutorials, how-to guides, explanation, and reference material here:

* `Current stable version <https://docs.django-cms.org/>`_ (current release)
* `Latest development version <https://docs.django-cms.org/en/latest/>`_ (main branch)
* Sources in this repo: `docs/ <docs/>`_

Branch policy details: `Development policies <https://docs.django-cms.org/en/latest/contributing/development-policies.html>`_.


***************************
Test django CMS in our demo
***************************

The demo platform is kindly provided by Divio, platinum member of the django CMS Association.

.. image:: docs/images/try-with-divio.png
   :target: https://www.django-cms.org/en/django-cms-demo/
   :alt: Try demo with Divio Cloud

Want to get a feel for the editing experience before you install anything? Start with the demo link above.


Development
***********

If you want to contribute code, start here (you'll be productive quickly):

* `CONTRIBUTING.rst <CONTRIBUTING.rst>`_ (workflow, PR process)
* `Contributing docs <https://docs.django-cms.org/en/latest/contributing/>`_

************
Getting Help
************

Need help choosing an approach, debugging an issue, or reviewing an implementation idea?
Head over to our `Discord Server <https://discord-support-channel.django-cms.org>`_ or Stackoverflow.

********************
Professional support
********************

Choose from a list of `trusted tech partner <https://www.django-cms.org/en/tech-partners/>`_ of the django CMS Association to get your website project delivered successfully.

Choose a `trusted web host <https://www.django-cms.org/en/hosting-services/>`_ for your django CMS project and get your website online today.


**************************
The django CMS Association
**************************

The django CMS Association is a non-profit founded in 2020 to drive the success of django CMS by providing guidance,
infrastructure and funding for core development and community projects.

If your business depends on django CMS, consider supporting its long-term health:
`Join the django CMS Association <https://www.django-cms.org/en/contribute/>`_ or `become a member <https://www.django-cms.org/en/memberships/>`_.


*******
Credits
*******

* Includes icons and adapted icons from `Bootstrap <https://icons.getbootstrap.com>`_.
* Includes icons from `FamFamFam <http://www.famfamfam.com>`_.
* Python tree engine powered by
  `django-treebeard <https://tabo.pe/projects/django-treebeard/>`_.
* JavaScript tree in admin uses `jsTree <https://www.jstree.com>`_.
* Many thanks to
  `all the contributors <https://github.com/django-cms/django-cms/graphs/contributors>`_
  to django CMS!

.. |PyPiVersion| image:: https://img.shields.io/pypi/v/django-cms.svg
    :target: https://pypi.python.org/pypi/django-cms/
.. |PyVersion| image:: https://img.shields.io/pypi/pyversions/django-cms
    :target: https://pypi.python.org/pypi/django-cms/
    :alt: PyPI - Python Version
.. |DjVersion| image:: https://img.shields.io/pypi/frameworkversions/django/django-cms
    :alt: PyPI - Versions from Framework Classifiers
.. |License| image:: https://img.shields.io/badge/License-BSD_3_clause-green
    :target: https://pypi.python.org/pypi/django-cms/
    :alt: License
.. |Coverage| image:: https://codecov.io/gh/django-cms/django-cms/graph/badge.svg?token=Jyx7Ilpibf
 :target: https://codecov.io/gh/django-cms/django-cms
