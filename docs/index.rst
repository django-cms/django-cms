.. |_| unicode:: 0xA0
   :trim:

|_|

.. image:: /images/django-cms-logo.png
   :alt: django CMS logo
   :align: right
   :height: 40px
   :class: doc-logo-no-margin

django CMS documentation
========================


Welcome to the **django CMS** developer documentation.

django CMS is a modern, open-source content management system built on Django,
designed to solve complex publishing requirements using simple, composable parts.

This documentation is organised using the **Diátaxis framework**, which separates
learning material, practical guides, conceptual explanations, and technical
reference — so you can quickly find the information you need.

If you are looking for editor or administrator documentation, see the
`django CMS User Guide <https://user-guide.django-cms.org/>`_.

🚀 Immediate pet project
------------------------

Create a fully configured django CMS project in minutes:

.. code-block:: bash

    python -m venv .venv
    source .venv/bin/activate  # On Windows: .venv\Scripts\activate
    pip install django-cms
    djangocms mysite

Already have a Django project? Run ``djangocms .`` in its root directory to
:ref:`add django CMS to it <add_to_existing_project>`. See the
:ref:`djangocms command <djangocms-command>` reference for all options.


🧭 Choose your path
------------------

.. grid:: 2
   :gutter: 3

   .. grid-item-card:: 🚀 Tutorials
      :link: tutorials
      :link-type: ref

      Step-by-step lessons that teach django CMS from installation
      through building your first project.

   .. grid-item-card:: 🛠 How-to guides
      :link: how-to
      :link-type: ref

      Practical, goal-oriented guides for solving specific problems
      in real projects.

   .. grid-item-card:: 🧠 Explanation
      :link: explanation
      :link-type: ref

      Background, concepts, and architectural decisions explained
      to help you understand how django CMS works.

   .. grid-item-card:: 📖 Reference
      :link: reference
      :link-type: ref

      Authoritative technical reference for APIs, settings,
      commands, and internals.


✨ Why django CMS?
-----------------

django CMS is a mature, open-source content management system built on
Django. It is designed for projects that require flexibility, long-term
stability, and close integration with custom Django applications.

Key features include:

- robust internationalisation (i18n) and multi-site support
- front-end (and inline) editing that allows editors to work directly on
  rendered pages
- a flexible placeholder and plugin system for composing reusable
  content components
- integration with multiple rich-text editors
- support for content versioning, editorial workflows, and headless setups through
  official add-on packages

Compared to other Django-based CMS platforms, django CMS stands out for:

- a small, stable core that integrates cleanly into existing Django
  projects
- non-monolithic architecture that allows incremental adoption
- thorough, structured documentation organised using the Diátaxis
  framework
- an active, long-running open-source community
- an emphasis on code quality, testing, and long-term support

🤝 Community & contribution
---------------------------

django CMS is developed and maintained by an open community.
Participation is welcome at every level, from asking questions
to improving documentation or contributing code.

.. grid:: 3
   :gutter: 2

   .. grid-item-card:: 💬 Community chat
      :link: https://discord-support-channel.django-cms.org
      :link-type: url

      Join the Discord server to ask questions and talk
      with other django CMS users and contributors.

   .. grid-item-card:: ✍️ Improve the docs
      :link: contributing/index
      :link-type: doc

      Documentation improvements — including small fixes —
      are one of the easiest ways to contribute.

   .. grid-item-card:: 🧩 About the project
      :link: whoisbehind/index
      :link-type: doc

      Learn more about the people and organisations
      behind django CMS.


📦 Versions, compatibility & support
------------------------------------

This documentation refers to django CMS version |release|.

django CMS follows Django’s
`long-term support (LTS) policy <https://www.djangoproject.com/download/#supported-versions>`_
and provides aligned LTS releases.

Current LTS versions
++++++++++++++++++++

.. include:: autogenerate/lts.include

After feature freeze, new features are developed for the next major
django CMS release.

Unsupported LTS versions
++++++++++++++++++++++++

The following LTS versions are **no longer supported**:

.. include:: autogenerate/past_lts.include

.. _requirements:

Django / Python compatibility
+++++++++++++++++++++++++++++

*LTS* indicates a Django and django CMS combination covered by long-term support.

*✓* means tested and supported. *×* means untested or incompatible.

.. include:: autogenerate/compatibility.include

For dependency details, see the project’s ``pyproject.toml`` or the
:ref:`release-notes`.

The :ref:`Commonly Used Plugin section <commonly-used-plugins>` lists
additional packages commonly used in django CMS projects.



.. toctree::
   :maxdepth: 2
   :hidden:

   tutorials/index
   explanation/index
   how_to/index
   reference/index
   upgrade/index
   contributing/index
   whoisbehind/index
