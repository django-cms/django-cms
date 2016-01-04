#####################################
Integrating a third-party application
#####################################

We've already written our own django CMS plugins and apps, but now we want to
extend our CMS with a third-party application,
`Aldryn News & Blog <https://github.com/aldryn/aldryn-newsblog>`_.


******************
Basic installation
******************

First, we need to install the app into our virtual environment from
`PyPI <http://pypi.python.org>`_::

    pip install aldryn-newsblog


***************
Django settings
***************

``INSTALLED_APPS``
==================

Add the application and any of its requirements that are not there already to
``INSTALLED_APPS`` in ``settings.py``. Some *will* be already present; it's up
to you to check them because you need to avoid duplication:

.. code-block:: python

    # you will probably need to add:
    'aldryn_apphooks_config',
    'aldryn_boilerplates',
    'aldryn_categories',
    'aldryn_common',
    'aldryn_newsblog',
    'aldryn_people',
    'aldryn_reversion',
    'djangocms_text_ckeditor',
    'parler',
    'sortedm2m',
    'taggit',

    # and you will probably find the following already listed:
    'easy_thumbnails',
    'filer',
    'reversion',


``THUMBNAIL_PROCESSORS``
========================

One of the dependencies is Django Filer. It provides a special feature that allows more
sophisticated image cropping. For this to work it needs its own thumbnail processor
(``filer.thumbnail_processors.scale_and_crop_with_subject_location``) to be listed in
``settings.py`` in place of ``easy_thumbnails.processors.scale_and_crop``:

.. code-block:: python
   :emphasize-lines: 4,5

    THUMBNAIL_PROCESSORS = (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        # 'easy_thumbnails.processors.scale_and_crop',  # disable this one
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    )


``ALDRYN_BOILERPLATE_NAME``
===========================

Aldryn News & Blog uses aldryn-boilerplates_ to provide multiple sets of templates and static files
for different CSS frameworks. We're using the Bootstrap 3 in this tutorial, so let's choose
``bootstrap3`` by adding the setting:

.. code-block:: python

    ALDRYN_BOILERPLATE_NAME='bootstrap3'


``STATICFILES_FINDERS``
=======================

Add the boilerplates static files finder to ``STATICFILES_FINDERS``, *immediately before*
``django.contrib.staticfiles.finders.AppDirectoriesFinder``:

.. code-block:: python
   :emphasize-lines: 3

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        'aldryn_boilerplates.staticfile_finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]

If ``STATICFILES_FINDERS`` is not defined in your ``settings.py`` just copy and paste the code
above.


``TEMPLATES``
=============

.. important::

    In Django 1.8, the ``TEMPLATE_LOADERS`` and ``TEMPLATE_CONTEXT_PROCESSORS`` settings are
    rolled into the ``TEMPLATES`` setting. We're assuming you're using Django 1.8 here.


.. code-block:: python
   :emphasize-lines: 7,11

    TEMPLATES = [
        {
            # ...
            'OPTIONS': {
                'context_processors': [
                    # ...
                    'aldryn_boilerplates.context_processors.boilerplate',
                    ],
                'loaders': [
                    # ...
                    'aldryn_boilerplates.template_loaders.AppDirectoriesLoader',
                    ],
                },
            },
        ]


********************
Migrate the database
********************

We've added a new application so we need to update our database::

    python manage.py migrate

Start the server again.


***************************
Create a new apphooked page
***************************

The News & Blog application comes with a django CMS apphook, so add a new django CMS page (call it
*News*), and add the News & Blog application to it :ref:`just as you did for Polls
<apply_apphook>`.

For this application we also need to create and select an *Application configuration*.

Give this application configuration some settings:

* ``Instance namespace``: *news* (this is used for reversing URLs)
* ``Application title``: *News* (the name that will represent the application configuration in the
  admin)
* ``Permalink type``: choose a format you prefer for news article URLs

Save this application configuration, and make sure it's selected in ``Application configurations``.

Publish the new page, and you should find the News & Blog application at work there. (Until you
actually create any articles, it will simply inform you that there are *No items available*.)


****************************
Add new News & Blog articles
****************************

You can add new articles using the admin or the new *News* menu that now appears in the toolbar when you are on a page belonging to News & Blog.

You can also insert a *Latest articles* plugin into another page - like all good
django CMS applications, Aldryn News & Blog comes with plugins.

In the next tutorial, we're going to integrate our Polls application into the toolbar too.

.. _aldryn-boilerplates: https://github.com/aldryn/aldryn-boilerplates
