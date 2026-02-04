.. _install-django-cms-by-hand:

#############################
Install django CMS manually
#############################

This how-to guide walks you through manually installing django CMS into a new or
existing Django project. For a quick start, see :doc:`/introduction/01-install`.

This guide assumes you have basic familiarity with Python and Django.


****************************************
Create a new project with djangocms
****************************************

This section explains how to create a brand new django CMS project using the
``djangocms`` command. If you're adding django CMS to an existing project, skip to
:ref:`minimal-required-configuration`.

Install the django CMS package
==============================

Check the :ref:`Python/Django requirements <requirements>` for this version of django
CMS.

.. important::

    We strongly recommend doing all of the following steps in a `virtual environment
    <https://docs.python.org/3/library/venv.html>`_.

    .. code-block:: bash

        python3 -m venv .venv  # create a virtualenv
        source .venv/bin/activate  # activate it
        pip install --upgrade pip  # Upgrade pip

Then install django CMS:

.. code-block::

    pip install django-cms


What the djangocms command does
===============================

You can create a new django CMS project using:

.. code-block::

    djangocms myproject

This shortcut command performs the following five steps:

1. Creates a new Django project using a template:

   .. code-block::

       django-admin startproject myproject --template https://github.com/django-cms/cms-template/archive/5.1.tar.gz

2. Installs additional *optional packages* used in the template project:

   - `djangocms-text <https://github.com/django-cms/djangocms-text>`_ for rich text input
   - `djangocms-frontend <https://github.com/django-cms/djangocms-frontend>`_ for Bootstrap5 support
   - `django-filer <https://github.com/django-cms/django-filer>`_ for media file management
   - `djangocms-versioning <https://github.com/django-cms/djangocms-versioning>`_ for publishing and version management
   - `djangocms-alias <https://github.com/django-cms/djangocms-alias>`_ for managing common content parts
   - `djangocms-simple-admin-style <https://github.com/fsbraun/djangocms-simple-admin-style>`_ for consistent admin styling

3. Runs the ``migrate`` command to create the database:

   .. code-block::

       python -m manage migrate

4. Prompts for creating a superuser:

   .. code-block::

       python -m manage createsuperuser

5. Runs the django CMS check command:

   .. code-block::

       python -m manage cms check


Project structure
=================

After running ``djangocms myproject``, your project looks like this:

.. code-block::

    myproject/
        LICENSE
        README.md
        db.sqlite3
        myproject/
            static/
            templates/
                base.html
            __init__.py
            asgi.py
            settings.py
            urls.py
            wsgi.py
        manage.py
        requirements.in

The ``LICENSE`` and ``README.md`` files can be deleted or replaced. The
``requirements.in`` contains dependencies for the project.


.. _minimal-required-configuration:

****************************************
Add django CMS to an existing project
****************************************

To add django CMS to an existing Django project, you need to install dependencies
and modify ``settings.py`` and ``urls.py``.

Install required packages
=========================

Add django CMS and its dependencies to your requirements file:

.. code-block::

    django-cms>=4.1
    django-sekizai
    django-treebeard

Or install directly:

.. code-block:: bash

    pip install django-cms

For a fully-featured setup, also install recommended plugins:

.. code-block:: bash

    pip install djangocms-text djangocms-frontend django-filer djangocms-versioning djangocms-alias

INSTALLED_APPS
==============

Add to ``INSTALLED_APPS`` (order matters):

.. code-block:: python

    INSTALLED_APPS = [
        # Add before django.contrib.admin for admin styling (optional)
        # "djangocms_admin_style",

        "django.contrib.admin",
        "django.contrib.auth",
        "django.contrib.contenttypes",
        "django.contrib.sessions",
        "django.contrib.messages",
        "django.contrib.staticfiles",
        "django.contrib.sites",  # Required by django CMS

        # django CMS core
        "cms",
        "menus",
        "treebeard",
        "sekizai",

        # Recommended plugins (if installed)
        "filer",
        "easy_thumbnails",
        "djangocms_text",
        "djangocms_frontend",
        "djangocms_frontend.contrib.grid",
        "djangocms_frontend.contrib.image",
        "djangocms_frontend.contrib.link",
        "djangocms_versioning",
        "djangocms_alias",

        # Your existing apps
        # ...
    ]

- django CMS needs Django's :mod:`django:django.contrib.sites` framework
- ``cms`` and ``menus`` are the core django CMS modules
- `django-treebeard <http://django-treebeard.readthedocs.io>`_ manages the page tree
- `django-sekizai <https://django-sekizai.readthedocs.io>`_ handles CSS/JS blocks in templates

Required settings
=================

Add to ``settings.py``:

.. code-block:: python

    SITE_ID = 1

    CMS_CONFIRM_VERSION4 = True

    X_FRAME_OPTIONS = "SAMEORIGIN"

``CMS_CONFIRM_VERSION4`` ensures you do not accidentally run migrations on a django CMS
version 3 database.

.. warning::

    Do not add ``CMS_CONFIRM_VERSION4 = True`` to a django CMS version 3 project unless
    you know what you are doing.

Language settings
=================

django CMS requires the :setting:`django:LANGUAGES` setting:

.. code-block:: python

    LANGUAGES = [
        ("en", "English"),
        ("de", "German"),
        ("it", "Italian"),
    ]
    LANGUAGE_CODE = "en"

Database
========

django CMS requires a relational database. SQLite works for development:

.. code-block:: python

    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

For production, use PostgreSQL, MySQL, or MariaDB:

.. code-block:: bash

    pip install psycopg2     # for PostgreSQL
    pip install mysqlclient  # for MySQL or MariaDB

MIDDLEWARE
==========

Add to :setting:`django:MIDDLEWARE` (order matters):

.. code-block:: python

    MIDDLEWARE = [
        "cms.middleware.utils.ApphookReloadMiddleware",  # Optional, must be first
        "django.middleware.security.SecurityMiddleware",
        # ... existing middleware ...
        "django.middleware.locale.LocaleMiddleware",  # After SessionMiddleware
        # ... existing middleware ...
        "cms.middleware.user.CurrentUserMiddleware",
        "cms.middleware.page.CurrentPageMiddleware",
        "cms.middleware.toolbar.ToolbarMiddleware",
        "cms.middleware.language.LanguageCookieMiddleware",
    ]

``ApphookReloadMiddleware`` is optional but recommended for :ref:`apphook reloading
<reloading_apphooks>`.

TEMPLATES
=========

Add ``sekizai`` to ``INSTALLED_APPS`` and configure context processors:

.. code-block:: python

    TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [BASE_DIR / "templates"],
            "APP_DIRS": True,
            "OPTIONS": {
                "context_processors": [
                    # ... existing context processors ...
                    "django.template.context_processors.i18n",
                    "sekizai.context_processors.sekizai",
                    "cms.context_processors.cms_settings",
                ],
            },
        },
    ]

CMS_TEMPLATES
=============

django CMS requires at least one template. Add :setting:`CMS_TEMPLATES` to settings:

.. code-block:: python

    CMS_TEMPLATES = [
        ("home.html", "Home page template"),
    ]

Create a ``templates`` directory and add ``home.html``:

.. code-block:: html+django

    {% load cms_tags sekizai_tags %}
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>{% page_attribute "page_title" %}</title>
        {% render_block "css" %}
    </head>
    <body>
        {% cms_toolbar %}
        <main>
            {% placeholder "content" %}
        </main>
        {% render_block "js" %}
    </body>
    </html>

Key template tags:

- ``{% load cms_tags sekizai_tags %}`` loads required template tag libraries
- ``{% page_attribute "page_title" %}`` extracts the page's title
- ``{% render_block "css" %}`` and ``{% render_block "js" %}`` load CSS and JavaScript
- ``{% cms_toolbar %}`` renders the django CMS toolbar
- ``{% placeholder "content" %}`` defines where plugins can be inserted

If using django-filer, add thumbnail configuration:

.. code-block:: python

    THUMBNAIL_HIGH_RESOLUTION = True
    THUMBNAIL_PROCESSORS = (
        "easy_thumbnails.processors.colorspace",
        "easy_thumbnails.processors.autocrop",
        "filer.thumbnail_processors.scale_and_crop_with_subject_location",
        "easy_thumbnails.processors.filters",
    )

urls.py
=======

Add CMS URLs using ``i18n_patterns``:

.. code-block:: python

    from django.conf import settings
    from django.conf.urls.i18n import i18n_patterns
    from django.conf.urls.static import static
    from django.contrib import admin
    from django.urls import include, path

    urlpatterns = [
        # Non-i18n URLs (if any)
    ]

    urlpatterns += i18n_patterns(
        path("admin/", admin.site.urls),
        # Your existing app URLs
        # path("myapp/", include("myapp.urls")),
        # CMS URLs - must be last (catch-all)
        path("", include("cms.urls")),
    )

    # For development only
    if settings.DEBUG:
        urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

Media files
===========

Configure media file handling in ``settings.py``:

.. code-block:: python

    MEDIA_URL = "/media/"
    MEDIA_ROOT = BASE_DIR / "media"

For production, configure proper media file serving per
:doc:`Django's documentation <django:howto/static-files/index>`.

Run migrations
==============

Create database tables and verify configuration:

.. code-block:: bash

    python manage.py migrate
    python manage.py createsuperuser  # If you don't have one
    python manage.py cms check
    python manage.py runserver

Visit http://127.0.0.1:8000 and log in to start creating pages.


****************************************
Optional plugins
****************************************

django CMS uses plugins to handle content. The ``djangocms`` command installs
recommended plugins automatically. If you installed manually, consider adding these.

Django Filer
============

`Django Filer <https://github.com/django-cms/django-filer>`_ provides file and image
management.

.. code-block:: bash

    pip install django-filer>=3.0

Add to ``INSTALLED_APPS``:

.. code-block:: python

    "filer",
    "easy_thumbnails",

djangocms-text
==============

`djangocms-text <https://github.com/django-cms/djangocms-text>`_ provides rich text
editing.

.. code-block:: bash

    pip install djangocms-text

Add ``djangocms_text`` to ``INSTALLED_APPS``.

djangocms-frontend
==================

`djangocms-frontend <https://github.com/django-cms/djangocms-frontend>`_ adds Bootstrap 5
support.

.. code-block:: bash

    pip install djangocms-frontend

Add to ``INSTALLED_APPS``:

.. code-block:: python

    "djangocms_frontend",
    "djangocms_frontend.contrib.accordion",
    "djangocms_frontend.contrib.alert",
    "djangocms_frontend.contrib.badge",
    "djangocms_frontend.contrib.card",
    "djangocms_frontend.contrib.carousel",
    "djangocms_frontend.contrib.collapse",
    "djangocms_frontend.contrib.content",
    "djangocms_frontend.contrib.grid",
    "djangocms_frontend.contrib.image",
    "djangocms_frontend.contrib.jumbotron",
    "djangocms_frontend.contrib.link",
    "djangocms_frontend.contrib.listgroup",
    "djangocms_frontend.contrib.media",
    "djangocms_frontend.contrib.tabs",
    "djangocms_frontend.contrib.utilities",

djangocms-versioning and djangocms-alias
========================================

Install for publishing workflow and reusable content blocks:

.. code-block:: bash

    pip install djangocms-versioning djangocms-alias

Add to ``INSTALLED_APPS``:

.. code-block:: python

    "djangocms_versioning",
    "djangocms_alias",

Run migrations
==============

After installing plugins:

.. code-block:: bash

    python manage.py migrate


****************************************
Verify your installation
****************************************

Use django CMS's built-in check command to verify your configuration:

.. code-block:: bash

    python manage.py cms check

This checks your configuration, applications, and database, reporting any problems.
Run it after each configuration step to verify progress.


****************************************
Next steps
****************************************

- Read the `user guide <https://user-guide.django-cms.org>`_ for a walk-through of basics
- Follow the :ref:`tutorials for developers <tutorials>`
- See :doc:`Django deployment documentation <django:howto/deployment/index>` for production
