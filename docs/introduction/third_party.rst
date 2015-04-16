#####################################
Integrating a third-party application
#####################################

We've already written our own django CMS plugins and apps, but now we want to
extend our CMS with a third party app,
`Aldryn blog <https://github.com/aldryn/aldryn-blog>`_.

First, we need to install the app into our virtual environment from
`PyPI <http://pypi.python.org>`_::

    pip install aldryn-blog

Add the app and any of its requirements that are not there already to
``INSTALLED_APPS`` in ``settings.py``. Some *will* be already present; it's up
to you to check them::

    'aldryn_blog',
    'aldryn_common',
    'aldryn_boilerplates',
    'django_select2',
    'djangocms_text_ckeditor',
    'easy_thumbnails',
    'filer',
    'taggit',
    'hvad',

One of the dependencies is ``easy_thumbnails``. It has already switched to
Django-1.7-style migrations and needs some extra configuration to work with
South. In ``settings.py``::

    SOUTH_MIGRATION_MODULES = {
        'easy_thumbnails': 'easy_thumbnails.south_migrations',
    }

Configure the image thumbnail processors in ``settings.py``::

    THUMBNAIL_PROCESSORS = (
        'easy_thumbnails.processors.colorspace',
        'easy_thumbnails.processors.autocrop',
        # 'easy_thumbnails.processors.scale_and_crop',
        'filer.thumbnail_processors.scale_and_crop_with_subject_location',
        'easy_thumbnails.processors.filters',
    )

Configure the templates that will be used by Aldryn Blog (if you configured
django CMS to use Bootstrap templates, choose `bootstrap3` instead)::

    ALDRYN_BOILERPLATE_NAME='legacy'

Add boilerplates finder to ``STATICFILES_FINDERS``::

    STATICFILES_FINDERS = [
        'django.contrib.staticfiles.finders.FileSystemFinder',
        # important! place right before django.contrib.staticfiles.finders.AppDirectoriesFinder
        'aldryn_boilerplates.staticfile_finders.AppDirectoriesFinder',
        'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    ]

Add the boilerplates loader to ``TEMPLATE_CONTEXT_PROCESSORS``::

    TEMPLATE_CONTEXT_PROCESSORS = [
        # ...
        'aldryn_boilerplates.context_processors.boilerplate',
    ]

Add the boilerplates context processor to ``TEMPLATE_CONTEXT_PROCESSORS``::

    TEMPLATE_CONTEXT_PROCESSORS = [
        # ...
        'aldryn_boilerplates.context_processors.boilerplate',
    ]


Since we added a new app, we need to update our database::

    python manage.py migrate

Start the server again.

The blog application comes with a django CMS apphook, so add a new django CMS
page, and add the blog application to it as you did for Polls in the previous
tutorial. *You may need to restart your server at this point.*

Publish the new page, and you should find the blog application at work there.

You can add new blog posts using the admin, but also have a look at the toolbar.
You can now select "Blog" > "Add Blog Post..." from it and add a new blog post
directly from there.

Try also inserting a "Latest blog entries" plugin into another page - as a good
django CMS application, Aldryn Blog comes with plugins.

In the next tutorial, we're going to integrate our Polls app into the toolbar
in, just like the blog application has been.
