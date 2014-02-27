##############################################
Installing django CMS into an existing project
##############################################


This document assumes you are familiar with Python and Django. It should
outline the steps necessary for you to follow the :doc:`tutorial`.

.. _requirements:

************
Requirements
************

* `Python`_ 2.6, 2.7 or 3.3.
* `Django`_ 1.4.5, 1.5.x or 1.6.x
* `South`_ 0.7.2 or higher
* `django-classy-tags`_ 0.3.4.1 or higher
* `django-mptt`_ 0.6 (strict due to API compatibility issues)
* `django-sekizai`_ 0.7 or higher
* `html5lib`_ 0.99 or higher
* `djangocms-admin-style`_
* An installed and working instance of one of the databases listed in the
  `Databases`_ section.

.. note:: When installing the django CMS using pip, Django, django-mptt
          django-classy-tags, django-sekizai, south and html5lib will be
          installed automatically.

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags
.. _django-mptt: https://github.com/django-mptt/django-mptt
.. _django-sekizai: https://github.com/ojii/django-sekizai
.. _html5lib: http://code.google.com/p/html5lib/
.. _django-i18nurls: https://github.com/brocaar/django-i18nurls
.. _djangocms-admin-style: https://github.com/divio/djangocms-admin-style

Recommended
===========

These packages are not *required*, but they provide useful functionality with
minimal additional configuration and are well-proven.

Text Editors
------------

* `Django CMS CKEditor`_ for a WYSIWYG editor 2.1.1 or higher

.. _Django CMS CKEditor: https://github.com/divio/djangocms-text-ckeditor

Other Plugins
-------------

* djangocms-link
* djangocms-snippet
* djangocms-style
* djangocms-column
* djangocms-grid
* djangocms-oembed
* djangocms-table


File and image handling
-----------------------

* `Django Filer`_ for file and image management
* `django-filer plugins for django CMS`_, required to use Django Filer with django CMS
* `Pillow`_ (fork of PIL) for image manipulation

.. _Django Filer: https://github.com/stefanfoulis/django-filer
.. _django-filer plugins for django CMS: https://github.com/stefanfoulis/cmsplugin-filer
.. _Pillow: https://github.com/python-imaging/Pillow

Revision management
-------------------

* `django-reversion`_ 1.6.6 (with Django 1.4.5), 1.7 (with Django 1.5)
  or 1.8 (with Django 1.6)  to support versions of your content (If using
  a different Django version it is a good idea to check the page
  `Compatible-Django-Versions`_ in the django-reversion wiki in order
  to make sure that the package versions are compatible.)

  .. note::

    As of django CMS 2.4, only the most recent 25 published revisions are
    saved. You can change this behaviour if required with
    :setting:`CMS_MAX_PAGE_PUBLISH_REVERSIONS`. Be aware that saved revisions
    will cause your database size to increase.

.. _django-reversion: https://github.com/etianen/django-reversion
.. _Compatible-Django-Versions: https://github.com/etianen/django-reversion/wiki/Compatible-Django-Versions


.. _installing-in-a-virtualenv-using-pip:

**********
Installing
**********

Installing in a virtualenv using pip
====================================

.. warning::

    As django CMS 3.0 is still unreleased, you need to pick it from the github repository.
    Use ::

        pip install https://github.com/divio/django-cms/archive/3.0.0.beta3.zip

    to install django CMS 3.0 beta3 or::

        pip install https://github.com/divio/django-cms/archive/develop.zip

    to target the development branch.

Installing inside a `virtualenv`_ is the preferred way to install any Django
installation. This should work on any platform where python in installed.
The first step is to create the virtualenv:

.. code-block:: bash

  #!/bin/sh
  sudo pip install --upgrade virtualenv
  virtualenv --distribute --no-site-packages env

.. note:: Since virtualenv v1.10 (2013-07-23) --distribute or --setuptools are
          the same because the new setuptools has been merged with Distribute.
          Since virtualenv v1.7 (2011-11-30) --no-site-packages was made the
          default behavior. By the way, we can create a virtualenv typing in our
          console only `virtualenv env`.

You can switch to your virtualenv at the command line by typing:

.. code-block:: bash

  source env/bin/activate
  
Next, you can install packages one at a time using `pip`_, but we recommend
using a `requirements.txt`_ file. The following is an example
requirements.txt file that can be used with pip to install django CMS and
its dependencies:

::

    # Bare minimum
    django-cms==3.0

    #These dependencies are brought in by django CMS, but if you want to
    # lock-in their version, specify them
    Django==1.6.1

    django-classy-tags==0.4
    South==0.8.4
    html5lib==1.0b1
    django-mptt==0.6
    django-sekizai==0.7
    six==1.3.0
    djangocms-admin-style==0.1.2
    
    #Optional, recommended packages
    Pillow==2.0.0
    django-filer==0.9.5
    cmsplugin-filer==0.9.5
    django-reversion==1.7

.. note::

    In the above list, packages are pinned to specific version as an example;
    those are not mandatory versions; refer to `requirements`_
    for any version-specific restriction

for Postgresql you would also add:

::

    psycopg2==2.5

and install libpq-dev (on Debian-based distro)

for MySQL you would also add:

::

    mysql-python==1.2.4

and install libmysqlclient-dev (on Debian-based distro)

One example of a script to create a virtualenv Python environment is as follows:

.. code-block:: bash

  #!/bin/sh
  env/bin/pip install --download-cache=~/.pip-cache -r requirements.txt

.. _virtualenv: http://www.virtualenv.org
.. _pip: http://www.pip-installer.org
.. _requirements.txt: http://www.pip-installer.org/en/latest/cookbook.html#requirements-files


Installing globally on Ubuntu
=============================

.. warning::

    The instructions here install certain packages, such as Django, South, Pillow
    and django CMS globally, which is not recommended. We recommend you use
    `virtualenv`_ instead (see above).

If you're using Ubuntu (tested with 10.10), the following should get you
started:

.. code-block:: bash

    sudo aptitude install python2.6 python-setuptools
    sudo easy_install pip
    sudo pip install Django==1.5 django-cms south Pillow

Additionally, you need the Python driver for your selected database:

.. code-block:: bash

    sudo aptitude python-psycopg2

or

.. code-block:: bash

    sudo aptitude install python-mysql

This will install Django, django CMS, South, Pillow, and your database's driver globally.

You have now everything that is needed for you to follow the :doc:`tutorial`.


On Mac OSX
==========

All you need to do is

.. code-block:: bash

    $ sudo easy_install pip

If you're using `Homebrew`_ you can install pip and virtualenv with the python
generic package:

.. code-block:: bash

    $ sudo brew install python

Then create an enviroment and work on it instead of install the packages in the
system path:

.. code-block:: bash

    $ virtualenv djangocms-env
    $ ./djangocms-env/bin/activate
    (djangocms-env)$ pip install Django==1.5 South Django-CMS

.. note:: You can see the general instructions on how to pip install packages
          after creating the virtualenv here: :ref:`Installing in a virtualenv using pip <installing-in-a-virtualenv-using-pip>`

.. _Homebrew: http://brew.sh/

*********
Databases
*********

We recommend using `PostgreSQL`_ or `MySQL`_ with django CMS. Installing and
maintaining database systems is outside the scope of this documentation, but
is very well documented on the systems' respective websites.

To use django CMS efficiently, we recommend:

* Creating a separate set of credentials for django CMS.
* Creating a separate database for django CMS to use.

.. _PostgreSQL: http://www.postgresql.org/
.. _MySQL: http://www.mysql.com

***********************
Configuration and setup
***********************


Preparing the environment
=========================

The following assumes your django project is in ``~/workspace/myproject/myproject``.


.. _configure-django-cms:

Installing and configuring django CMS in your django project
============================================================

Open the file ``~/workspace/myproject/myproject/settings.py``.

To make your life easier, add the following at the top of the file::

    # -*- coding: utf-8 -*-
    import os
    gettext = lambda s: s
    PROJECT_PATH = os.path.split(os.path.abspath(os.path.dirname(__file__)))[0]


Add the following apps to your :setting:`django:INSTALLED_APPS`.
This includes django CMS itself as well as its dependenices and
other highly recommended applications/libraries::

    'cms',  # django CMS itself
    'mptt',  # utilities for implementing a modified pre-order traversal tree
    'menus',  # helper for model independent hierarchical website navigation
    'south',  # intelligent schema and data migrations
    'sekizai',  # for javascript and css management
    'djangocms_admin_style',  # for the admin skin. You **must** add 'djangocms_admin_style' in the list before 'django.contrib.admin'.
    'django.contrib.messages',  # to enable messages framework (see :ref:`Enable messages <enable-messages>`)


Also add any (or all) of the following plugins, depending on your needs::

    'cms.plugins.file',
    'cms.plugins.flash',
    'cms.plugins.googlemap',
    'cms.plugins.picture',
    'cms.plugins.teaser',
    'djangocms_link',
    'djangocms_snippet',
    'djangocms_text_ckeditor',  # note this needs to be above the 'cms' entry
    'cms.plugins.video',

.. warning::

    Adding the ``'djangocms_snippet'`` plugin is a potential security hazard.
    For more information, refer to `snippet_plugin`_.

    In addition, ``'cms.plugins.text'`` and ``'cms.plugins.twitter'`` have
    been removed from the Django-CMS bundle. Read :ref:`upgrade-to-3.0` for
    detailed information.

The plugins are described in more detail in chapter :doc:`Plugins reference <../resources/plugin_reference>`.
There are even more plugins available on the django CMS `extensions page`_.

.. _snippet_plugin: https://github.com/divio/djangocms-snippet
.. _extensions page: http://www.django-cms.org/en/extensions/

In addition, make sure you uncomment (enable) ``'django.contrib.admin'``

You may also wish to use `django-filer`_ and its components with the `django CMS plugin`_
instead of the :mod:`cms.plugins.file`, :mod:`cms.plugins.picture`,
:mod:`cms.plugins.teaser` and :mod:`cms.plugins.video` core plugins.
In this case you should check the `django-filer documentation <django-filer:installation_and_configuration>`_
and `django CMS plugin documentation`_ for detailed installation information, and
then return to this tutorial.

.. _django-filer: https://github.com/stefanfoulis/django-filer
.. _django CMS plugin: https://github.com/stefanfoulis/cmsplugin-filer
.. _django CMS plugin documentation: https://github.com/stefanfoulis/cmsplugin-filer#installation

If you opt for the core plugins you should take care that directory to which
the :setting:`CMS_PAGE_MEDIA_PATH` setting points (by default ``cms_page_media/``
relative to :setting:`django:MEDIA_ROOT`) is writable by the user under which Django
will be running. If you have opted for django-filer there is a similar requirement
for its configuration.

If you want versioning of your content you should also install `django-reversion`_
and add it to :setting:`django:INSTALLED_APPS`:

* ``'reversion'``

.. _django-reversion: https://github.com/etianen/django-reversion

You need to add the django CMS middlewares to your :setting:`django:MIDDLEWARE_CLASSES`
at the right position::

    MIDDLEWARE_CLASSES = (
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.locale.LocaleMiddleware',
        'django.middleware.doc.XViewMiddleware',
        'django.middleware.common.CommonMiddleware',
        'cms.middleware.page.CurrentPageMiddleware',
        'cms.middleware.user.CurrentUserMiddleware',
        'cms.middleware.toolbar.ToolbarMiddleware',
        'cms.middleware.language.LanguageCookieMiddleware',
    )

You need at least the following :setting:`django:TEMPLATE_CONTEXT_PROCESSORS`::

    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.contrib.auth.context_processors.auth',
        'django.contrib.messages.context_processors.messages',
        'django.core.context_processors.i18n',
        'django.core.context_processors.request',
        'django.core.context_processors.media',
        'django.core.context_processors.static',
        'cms.context_processors.cms_settings',
        'sekizai.context_processors.sekizai',
    )

.. note::

    This setting will be missing from automatically generated Django settings
    files, so you will have to add it.

.. warning::

    Be sure to have ``'django.contrib.sites'`` in INSTALLED_APPS and set
    ``SITE_ID`` parameter in your ``settings``: they may be missing from the
    settings file generated by ``django-admin`` depending on your Django version
    and project template.

.. _enable-messages:

.. versionchanged:: 3.0.0

.. warning::

    Django ``messages`` framework is now required for the toolbar to work
    properly.

    To enable it you must be check the following settings:

        * ``INSTALLED_APPS``: must contain ``'django.contrib.messages'``
        * ``MIDDLEWARE_CLASSES``: must contain ``'django.contrib.messages.middleware.MessageMiddleware'``
        * ``TEMPLATE_CONTEXT_PROCESSORS``: must contain ``'django.contrib.messages.context_processors.messages'``


Point your :setting:`django:STATIC_ROOT` to where the static files should live
(that is, your images, CSS files, Javascript files, etc.)::

    STATIC_ROOT = os.path.join(PROJECT_PATH, "static")
    STATIC_URL = "/static/"

For uploaded files, you will need to set up the :setting:`django:MEDIA_ROOT`
setting::

    MEDIA_ROOT = os.path.join(PROJECT_PATH, "media")
    MEDIA_URL = "/media/"

.. note::

    Please make sure both the ``static`` and ``media`` subfolders exist in your
    project and are writable.

Now add a little magic to the :setting:`django:TEMPLATE_DIRS` section of the file::

    TEMPLATE_DIRS = (
        # The docs say it should be absolute path: PROJECT_PATH is precisely one.
        # Life is wonderful!
        os.path.join(PROJECT_PATH, "templates"),
    )

Add at least one template to :setting:`CMS_TEMPLATES`; for example::

    CMS_TEMPLATES = (
        ('template_1.html', 'Template One'),
        ('template_2.html', 'Template Two'),
    )

We will create the actual template files at a later step, don't worry about it for
now. Simply paste this code into your settings file.

.. note::

    The templates you define in :setting:`CMS_TEMPLATES` have to exist at runtime and
    contain at least one ``{% placeholder <name> %}`` template tag to be useful
    for django CMS. For more details see :doc:`../tutorial/templates`

The django CMS allows you to edit all languages for which Django has built in
translations. Since these are numerous, we'll limit it to English for now::

    LANGUAGES = [
        ('en', 'English'),
    ]

Finally, set up the :setting:`django:DATABASES` part of the file to reflect your
database deployment. If you just want to try out things locally, sqlite3 is the
easiest database to set up, however it should not be used in production. If you
still wish to use it for now, this is what your :setting:`django:DATABASES`
setting should look like::

    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': os.path.join(PROJECT_PATH, 'database.sqlite'),
        }
    }


URL configuration
=================

You need to include the ``'cms.urls'`` urlpatterns **at the end** of your
urlpatterns. We suggest starting with the following
``~/workspace/myproject/myproject/urls.py``::

    from django.conf.urls import include, patterns, url
    from django.conf.urls.i18n import i18n_patterns
    from django.contrib import admin
    from django.conf import settings

    admin.autodiscover()

    urlpatterns = i18n_patterns('',
        url(r'^admin/', include(admin.site.urls)),
        url(r'^', include('cms.urls')),
    )

    if settings.DEBUG:
        urlpatterns = patterns('',
        url(r'^media/(?P<path>.*)$', 'django.views.static.serve',
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}),
        url(r'', include('django.contrib.staticfiles.urls')),
    ) + urlpatterns



Awesome job!
============

That's it! You just set up django CMS! You can now start with an easy introduction into django CMS here:
:doc:`../tutorial/index`.

.. _mailinglist: https://groups.google.com/forum/#!forum/django-cms
