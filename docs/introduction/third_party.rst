#####################################
Integrating a third-party application
#####################################

We've already written our own django CMS plugins and apps, but now we want to
extend our CMS with a third party app,
`Aldryn News & Blog <https://github.com/aldryn/aldryn-newsblog>`_.

First, we need to install the app into our virtual environment from
`PyPI <http://pypi.python.org>`_::

    pip install aldryn-newsblog

Add the app and any of its requirements that are not there already to
``INSTALLED_APPS`` in ``settings.py``. Some *will* be already present; it's up
to you to check them:

.. code-block:: python

    'aldryn_apphooks_config',
    'aldryn_boilerplates',
    'aldryn_categories',
    'aldryn_newsblog',
    'aldryn_people',
    'aldryn_reversion',
    'djangocms_text_ckeditor',
    'easy_thumbnails',
    'filer',
    'parler',
    'reversion',
    'sortedm2m',
    'taggit',

One of the dependencies is django-filer. It provides a special feature that
allows nicer image cropping. For this to work it needs it's own
thumbnail processor (easy-thumbnails) to be inserted in ``settings.py``:

.. code-block:: python

    THUMBNAIL_PROCESSORS = (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        # 'easy_thumbnails.processors.scale_and_crop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    )

aldryn-newsblog uses aldryn-boilerplates_ to provide multiple sets of templates
and staticfiles for different css frameworks. We're using
bootstrap3 in this tutorial, so lets choose `bootstrap3`.:

.. code-block:: python

    ALDRYN_BOILERPLATE_NAME='bootstrap3'

Add boilerplates finder to ``STATICFILES_FINDERS``:

.. code-block:: python

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        # important! place right before django.contrib.staticfiles.finders.AppDirectoriesFinder
        'aldryn_boilerplates.staticfile_finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]

Add the boilerplate template loader to ``TEMPLATE_LOADERS``:

.. code-block:: python

    TEMPLATE_LOADERS = (
        'django.template.loaders.filesystem.Loader',
        'aldryn_boilerplates.template_loaders.AppDirectoriesLoader',
        'django.template.loaders.app_directories.Loader',
        'django.template.loaders.eggs.Loader'
    )

Add the boilerplates context processor to ``TEMPLATE_CONTEXT_PROCESSORS``:

.. code-block:: python

    TEMPLATE_CONTEXT_PROCESSORS = [
        # ...
        'aldryn_boilerplates.context_processors.boilerplate',
    ]


Since we added a new app, we need to update our database::

    python manage.py migrate

Start the server again.

The newsblog application comes with a django CMS apphook, so add a new django
CMS page (let's call it 'Blog'), and add the blog application to it as you did
for Polls in the previous tutorial step.
In this case we also have to add an "Application configuration" (see the
field right under the apphook field). You can configure some settings here,
like the url format. It's also possible to add multiple instances of the
application, if you like.
The *Instance namespace* should be ``blog`` (this is used for reversing urls).
Choose ``Blog`` as the *Application title* and choose whatever *Permalink type*
you prefer.

Publish the new page, and you should find the blog application at work there.

*You may need to restart your server at this point.*


You can add new blog posts using the admin, but also have a look at the
toolbar. When you're within the urls of the blog, you should see an extra menu
item called "Blog".
You can now select "Blog" > "Add new article..." from it and add a new blog
post directly from there.

Try also inserting a "Latest articles" plugin into another page - as a good
django CMS application, *Aldryn News & Blog* comes with plugins.

In the next tutorial, we're going to integrate our Polls app into the toolbar
in, just like the blog application has been.

.. _aldryn-boilerplates: https://github.com/aldryn/aldryn-boilerplates
