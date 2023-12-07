.. _installation:

#################################
How to install django CMS by hand
#################################

The easiest way to install django CMS is by using the automated `django CMS quckstart
<https://github.com/django-cms/django-cms-quickstart>`_ project. This is the
recommended way to start with (docker-based) new projects, and it's
what we use in the :ref:`tutorial section of this documentation <tutorials>`.

If you prefer to do things manually, this how-to guide will take you through the process.

..  note::

    You can also use this guide to help you install django CMS as part of an existing project. However, the guide
    assumes that you are starting with a blank project, so you will need to adapt the steps below appropriately as
    required.

This document assumes you have some basic familiarity with Python and Django. After you've integrated django CMS into
your project, you should be able to follow the :doc:`/introduction/index` for an introduction to developing with django
CMS.


******************************
Install the django CMS package
******************************

Check the :ref:`Python/Django requirements <requirements>` for this version of django CMS.

django CMS also has other requirements, which it lists as dependencies in its ``setup.py``.

..  important::

    We strongly recommend doing all of the following steps in a virtual environment. You ought to know how to create,
    activate and dispose of virtual environments using `venv <https://docs.python.org/3.9/library/venv.html>`_. If you don't, you
    can use the steps below to get started, but you are advised to take a few minutes to learn the basics of using
    virtualenv before proceeding further.

    ..  code-block:: bash

        python3 -m venv venv # create a virtualenv
        source venv/bin/activate  # activate it

In an activated virtualenv, run::

	pip install --upgrade pip

to make sure ``pip`` is up-to-date, as earlier versions can be less reliable.

Then::

    pip install django-cms

to install the latest stable version of django CMS.


************************************
Create a new project from a template
************************************

Create a new project::

    django-admin startproject myproject  --template https://github.com/django-cms/cms-template/archive/3.11.tar.gz

If this is new to you, you ought to read the `official Django tutorial
<https://docs.djangoproject.com/en/3.2/intro/tutorial01/>`_, which covers starting a new project.

It installs additional optional packages which are used in the template project. Those are

* `djangocms-text-ckeditor <https://github.com/django-cms/djangocms-text-ckeditor>`_ for rich text input.
* `djangocms-frontend <https://github.com/django-cms/djangocms-frontend>`_ for `Bootstrap5 <https://getbootstrap.com>`_ support.
* `django-filer <https://github.com/django-cms/django-filer>`_ for managing media files like images.
* `djangocms_admin_style <https://github.com/django-cms/djangocms-admin-style>`_ for a consistent user experience with django CMS and Django admin.

Your new project will look like this::

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

The ``LICENSE`` and ``README.md`` files are not needed and can be deleted or replaced by appropriate files for your project.

``requirements.in`` contains dependencies for the project. Add your dependencies here. We suggest to use `pip-compile <https://github.com/jazzband/pip-tools>`_  to freeze your requirements as, for example, discussed in `this blog post <https://blog.typodrive.com/2020/02/04/always-freeze-requirements-with-pip-compile-to-avoid-unpleasant-surprises/>`_.

Now, enter the project directory and create the database::

    cd myproject
    python -m manage migrate

To run the project, you at least need a superuser to log in::

    python -m manage createsuperuser

Finally, run the ``cms check`` command to see if everything worked fine::

    python -m manage cms check

Fix any errors that are displayed. Once done, you are ready to spin up Django's development server by running::

    python -m manage runserver

You can visit your project's web site by pointing your browser to ``localhost:8000``.

Use the newly created superuser's credentials to authenticate and create your first page!

|it-works-cms|

.. |it-works-cms| image:: ../images/it-works-cms.png


***********************************************
Adding django CMS to an existing Django project
***********************************************

django CMS is nothing more than a powerful set of Django apps. Hence you can add django CMS to any Django project. It might require some settings and URLs to be modified, however. The template project comes with suitable settings. When adding django CMS to your existing project, you need to adjust the settings yourself.

Open the your project's ``settings.py`` file in your text editor.


INSTALLED_APPS
==============

You will need to add the following to its list of ``INSTALLED_APPS``::

    'django.contrib.sites',
    'cms',
    'menus',
    'treebeard',

* django CMS needs to use Django's :mod:`django:django.contrib.sites` framework. You'll need to set a ``SITE_ID``   in the settings - ``SITE_ID = 1`` will suffice.
* ``cms`` and ``menus`` are the core django CMS modules.
* `django-treebeard <http://django-treebeard.readthedocs.io>`_ is used to manage django CMS's page and plugin tree structures.

django CMS installs `django CMS admin style <https://github.com/django-cms/djangocms-admin-style>`_.
This provides some styling that helps make django CMS administration components easier to work with.
Technically it's an optional component and does not need to be enabled in your project,
but it's strongly recommended.

In the ``INSTALLED_APPS``, **before** ``django.contrib.admin``, add::

    'djangocms_admin_style',


Language settings
=================

django CMS requires you to set the :setting:`django:LANGUAGES` setting. This should list all the languages you want
your project to serve, and must include the language in :setting:`django:LANGUAGE_CODE`.

For example::

    LANGUAGES = [
        ('en', 'English'),
        ('de', 'German'),
    ]

(For simplicity's sake, at this stage it is worth changing the default ``en-us`` in that you'll find in the
``LANGUAGE_CODE`` setting to ``en``.)


Database settings
=================

django CMS requires a relational database backend. Each django CMS installation should have its own database. If you're adding django CMS to an existing project, you will most likely already have your database configured.

If not, you can use SQLite, which is included in Python and doesn't need to be installed separately or configured further. You
are unlikely to be using that for a project in production, but it's ideal for development and exploration, especially
as it is configured by default in a new Django project's :setting:`django:DATABASES`::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

..  note::

    For deployment, you'll need to use a :doc:`production-ready database with Django <django:ref/databases>`. We
    recommend using `PostgreSQL`_ or `MySQL`_.

    Installing and maintaining database systems is far beyond the scope of this documentation, but is very well
    documented on the systems' respective websites.

    .. _PostgreSQL: http://www.postgresql.org/
    .. _MySQL: http://www.mysql.com

    Whichever database you use, it will also require the appropriate Python adaptor to be installed::

        pip install psycopg2     # for Postgres
        pip install mysqlclient  # for MySQL

    Refer to :setting:`Django's DATABASES setting documentation <django:DATABASES>` for the appropriate configuration
    for your chosen database backend.


Migrating database tables
=========================

Now run migrations to create database tables for the new applications::

    python -m manage migrate


Sekizai
=======

`Django Sekizai <https://github.com/ojii/django-sekizai>`_ is required by the CMS for static files management. You need
to have ``'sekizai'`` listed in ``INSTALLED_APPS``,

.. code-block:: python

    INSTALLED_APPS = [
        ...,
        'sekizai',
        ...,
    ]


and ``'sekizai.context_processors.sekizai'`` in the ``TEMPLATES['OPTIONS']['context_processors']``:

..  code-block:: python

    TEMPLATES = [
        {
            ...
            'OPTIONS': {
                'context_processors': [
                    ...
                    'django.template.context_processors.i18n',
                    'sekizai.context_processors.sekizai',
                ],
            },
        },
    ]

.. note::

    ``django.template.context_processors.i18n`` is needed for the
    wizards to work properly.


Middleware
==========

in your :setting:`django:MIDDLEWARE` you'll need :class:`django:django.middleware.locale.LocaleMiddleware` -
it's **not** installed in Django projects by default.

Also add::

    'cms.middleware.user.CurrentUserMiddleware',
    'cms.middleware.page.CurrentPageMiddleware',
    'cms.middleware.toolbar.ToolbarMiddleware',
    'cms.middleware.language.LanguageCookieMiddleware',

to the list.

You can also add ``'cms.middleware.utils.ApphookReloadMiddleware'``. It's not absolutely necessary, but it's
:ref:`useful <reloading_apphooks>`. If included, should be at the start of the list.

add the following configuration to your ``settings.py``::

    X_FRAME_OPTIONS = 'SAMEORIGIN'

Context processors
==================

Add ``'cms.context_processors.cms_settings'`` to ``TEMPLATES['OPTIONS']['context_processors']``.

Also add ``'django.template.context_processors.i18n'`` if it's not already present.

``cms check`` should now be unable to identify any further issues with your project. Some additional configuration is
required however.


Adding django CMS' URLs
=======================

In the project's ``urls.py``, add ``re_path(r'^', include('cms.urls'))`` to the ``urlpatterns`` list. It should come after
other patterns, so that specific URLs for other applications can be detected first.

You'll also need to have an import for ``django.urls.include``. For example:

..  code-block:: python

    from django.urls import re_path, include

    urlpatterns = [
        re_path(r'^admin/', admin.site.urls),
        re_path(r'^', include('cms.urls')),
    ]

The django CMS project will now run, as you'll see if you launch it with

..  code-block:: bash

    python -m manage runserver


You'll be able to reach it at http://localhost:8000/, and the admin at http://localhost:8000/admin/. You won't yet actually be able to
do anything very useful with it though.


.. _basic_template:

Templates
=========

django CMS requires at least one template for its pages, so you'll need to add :setting:`CMS_TEMPLATES` to your
settings. The first template in the :setting:`CMS_TEMPLATES` list will be the project's default template.

::

    CMS_TEMPLATES = [
        ('home.html', 'Home page template'),
    ]

In the root of the project, create a ``templates`` directory, and in that, ``home.html``, a minimal django CMS
template:


..  code-block:: html+django

    {% load cms_tags sekizai_tags %}
    <html>
        <head>
            <title>{% page_attribute "page_title" %}</title>
            {% render_block "css" %}
        </head>
        <body>
            {% cms_toolbar %}
            {% placeholder "content" %}
            {% render_block "js" %}
        </body>
    </html>

This is worth explaining in a little detail:

* ``{% load cms_tags sekizai_tags %}`` loads the template tag libraries we use in the template.
* ``{% page_attribute "page_title" %}`` extracts the page's ``page_title`` :ttag:`attribute <page_attribute>`.
* ``{% render_block "css" %}`` and ``{% render_block "js" %}`` are Sekizai template tags that load blocks of HTML
  defined by Django applications. django CMS defines blocks for CSS and JavaScript, and requires these two tags. We
  recommended placing ``{% render_block "css" %}`` just before the ``</head>`` tag, and and ``{% render_block "js" %}``
  tag just before the ``</body>``.
* ``{% cms_toolbar %}`` renders the :ttag:`django CMS toolbar <cms_toolbar>`.
* ``{% placeholder "content" %}`` defines a :ttag:`placeholder`, where plugins can be inserted. A template needs at
  least one ``{% placeholder %}`` template tag to be useful for django CMS. The name of the placeholder is simply a
  descriptive one, for your reference.

Django needs to be know where to look for its templates, so add ``templates`` to the ``TEMPLATES['DIRS']`` list:

..  code-block:: python

    TEMPLATES = [
        {
            ...
            'DIRS': ['templates'],
            ...
        },
    ]

..  note::

    The way we have set up the template here is just for illustration. In a real project, we'd recommend creating a
    ``base.html`` template, shared by all the applications in the project, that your django CMS templates can extend.

    See Django's :ref:`template language documentation <django:template-inheritance>` for more on how template
    inheritance works.


Media and static file handling
==============================

A django CMS site will need to handle:

* *static files*, that are a core part of an application or project, such as its necessary images, CSS or
  JavaScript
* *media files*, that are uploaded by the site's users or applications.

:setting:`django:STATIC_URL` is defined (as ``"/static/"``) in a new project's settings by default.
:setting:`django:STATIC_ROOT`, the location that static files will be copied to and served from, is not required for
development - :doc:`only for production <django:howto/deployment/checklist>`.

For now, using the runserver and with ``DEBUG = True`` in your settings, you don't need to worry about either of these.

However, :setting:`django:MEDIA_URL` (where media files will be served) and :setting:`django:MEDIA_ROOT` (where they
will be stored) need to be added to your settings::

    MEDIA_URL = "/media/"
    MEDIA_ROOT = os.path.join(BASE_DIR, "media")

For deployment, you need to configure suitable media file serving. **For development purposes only**, the following will
work in your ``urls.py``:

..  code-block:: python

    from django.conf import settings
    from django.conf.urls.static import static

    urlpatterns = [
        ...
    ] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

(See the Django documentation for guidance on :doc:`serving media files in production
<django:howto/static-files/index>`.)

Using ``cms check`` for configuration
=====================================

Once you have completed the minimum required set-up described above, you can use django CMS's built-in ``cms check``
command to help you identify and install other components. Run::

    python -m manage cms check

This will check your configuration, your applications and your database, and report on any problems.

..  note::

    If key components are be missing, django CMS will be unable to run the ``cms check command`` and will simply raise
    an error instead.

After each of the steps below run ``cms check`` to verify that you have resolved that item in its checklist.


*************************************
Adding content-handling functionality
*************************************

You now have the basics set up for a django CMS site, which is able to manage and serve up pages. However the project
so far has no plugins installed, which means it has no way of handling content in those pages. All content in django
CMS is managed via plugins. So, we now need to install some additional addon applications to provide plugins and other
functionality.

You don't actually **need** to install any of these. django CMS doesn't commit you to any particular applications for
content handling. The ones listed here however provide key functionality and are strongly recommended.

Django Filer
============

`Django Filer`_ provides file and image management. Many other applications also rely on Django Filer - it's very
unusual to have a django CMS site that does *not* run Django Filer. The configuration in this section will get you
started, but you should refer to the `Django Filer documentation <https://django-filer.readthedocs.io>`_ for more
comprehensive configuration information.

.. _Django Filer: https://github.com/divio/django-filer

To install::

    pip install django-filer

A number of applications will be installed as dependencies. `Easy Thumbnails
<https://github.com/SmileyChris/easy-thumbnails>`_ is required to create new versions of images in different sizes; in older versions of Django Filer
`Django MPTT <https://github.com/django-mptt/django-mptt/>`_ manages the tree structure of the folders in Django Filer - you will not need it if you use Django Filer version 3 and above.

Pillow, the Python imaging library, will be installed. `Pillow <https://github.com/python-pillow/Pillow>`_ needs some
system-level libraries - the `Pillow documentation <https://pillow.readthedocs.io>`_ describes in detail what is
required to get this running on various operating systems.

Add::

    'filer',
    'easy_thumbnails',

to ``INSTALLED_APPS``.

You also need to add::

    THUMBNAIL_HIGH_RESOLUTION = True

    THUMBNAIL_PROCESSORS = (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters'
    )

New database tables will need to be created for Django Filer and Easy Thumbnails, so run migrations::

    python -m manage migrate filer
    python -m manage migrate easy_thumbnails

(or simply, ``python -m manage migrate``).


Django CMS CKEditor
===================

`Django CMS CKEditor`_ is the default text editor for django CMS.

.. _Django CMS CKEditor: https://github.com/django-cms/djangocms-text-ckeditor

Install: ``pip install djangocms-text-ckeditor``.

Add ``djangocms_text_ckeditor`` to your ``INSTALLED_APPS``.

Run migrations::

    python -m manage migrate djangocms_text_ckeditor


Miscellaneous plugins
=====================

There are plugins for django CMS that cover a vast range of functionality. To get started, it's useful to be able to
rely on a set of well-maintained plugins that cover some general content management needs.

* `djangocms-link <https://github.com/django-cms/djangocms-link>`_
* `djangocms-file <https://github.com/django-cms/djangocms-file>`_
* `djangocms-picture <https://github.com/django-cms/djangocms-picture>`_
* `djangocms-video <https://github.com/django-cms/djangocms-video>`_
* `djangocms-googlemap <https://github.com/django-cms/djangocms-googlemap>`_
* `djangocms-snippet <https://github.com/django-cms/djangocms-snippet>`_
* `djangocms-style <https://github.com/django-cms/djangocms-style>`_

To install::

    pip install djangocms-link djangocms-file djangocms-picture djangocms-video djangocms-googlemap djangocms-snippet djangocms-style

and add::

    'djangocms_link',
    'djangocms_file',
    'djangocms_picture',
    'djangocms_video',
    'djangocms_googlemap',
    'djangocms_snippet',
    'djangocms_style',

to ``INSTALLED_APPS``.

Then run migrations::

    python -m manage migrate

These and other plugins are described in more detail in :ref:`commonly-used-plugins`. More are listed
plugins available on the `django CMS Marketplace <https://marketplace.django-cms.org/en/addons/>`_.


**********
Next steps
**********

The :ref:`tutorials for developers <tutorials>` will help you understand how to approach django CMS as a developer.
Note that the tutorials assume you have installed the CMS using the django CMS Quistart project, but with a little
adaptation you'll be able to use it as a basis.

To deploy your django CMS project on a production web server, please refer to the :doc:`Django deployment documentation
<django:howto/deployment/index>`.
