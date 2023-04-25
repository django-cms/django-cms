:sequential_nav: prev

.. _third_party:

#####################################
Integrating a third-party application
#####################################

We've already written our own django CMS plugins and apps, but now we want to
extend our CMS with a third-party application,
`Djangocms-Blog <https://github.com/nephila/djangocms-blog>`_.


******************
Basic installation
******************

First, we need to install the app into our virtual environment from
`PyPI <https://pypi.python.org>`_::

    pip install djangocms-blog


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
    'filer',
    'easy_thumbnails',
    'aldryn_apphooks_config',
    'parler',
    'taggit',
    'taggit_autosuggest',
    'meta',
    'sortedm2m',
    'djangocms_blog',


``THUMBNAIL_PROCESSORS``
========================

One of the dependencies is Django Filer. It provides a special feature that allows more
sophisticated image cropping.

.. code-block:: python

    THUMBNAIL_PROCESSORS = (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    )
    
    META_SITE_PROTOCOL = 'https'  # set 'http' for non ssl enabled websites
    META_USE_SITES = True


``URL Patterns``
=======================

Add the following url pattern to the main urls.py:

.. code-block:: python

    urlpatterns += [
        url(r'^taggit_autosuggest/', include('taggit_autosuggest.urls')),
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
*Blog*), and add the Blog application to it :ref:`just as you did for Polls
<apply_apphook>`.

For this application we also need to create and select an *Application configuration*.

Give this application configuration some settings:

* ``Instance namespace``: *article* (this is used for reversing URLs)
* ``Application title``: *Blog* (the name that will represent the application configuration in the
  admin)
* ``Permalink type``: choose a format you prefer for news article URLs

Save this application configuration, and make sure it's selected in ``Application configurations``.

Publish the new page, and you should find the Blog application at work there. (Until you
actually create any articles, it will simply inform you that there are *No items available*.)


****************************
Add new News & Blog articles
****************************

You can add new articles using the admin or the new *Blog* menu that now appears in the toolbar when you are on a page belonging to Blog.

