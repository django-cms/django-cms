Installing A Blog App
=====================

We've already written our own django CMS plugins and apps, but now we
want to extend our CMS with a third party app,
`aldryn-blog <https://github.com/aldryn/aldryn-blog>`__.

At first, we need to install the app from the Cheese Shop
(`pypi.python.org <http://pypi.python.org>`__) (remember, always in the
virtual environment!):

.. code:: bash

    $ source env/bin/activate
    (env) $ pip install aldryn-blog

Add the app and its requirements below to ``INSTALLED_APPS`` in
``settings.py``:

.. code:: python

    INSTALLED_APPS += (
        'aldryn_blog',
        'django_select2',
        'djangocms_text_ckeditor',
        'easy_thumbnails',
        'filer',
        'taggit',
    )

Since we added a new app, we need to update our database:

.. code:: bash

    (env) $ python manage.py syncdb
    (env) $ python manage.py migrate

We can now run our server again

.. code:: bash

    (env) $ python manage.py runserver

Run your server, add a new page for the blog and edit it. Go to
‘Advanced Settings’ and choose ‘Blog App’ for ‘Application’. This will
hook the blog app into the page. For these changes to take effect, you
will have to restart your server once again. If you reload your page
now, you should be presented with the blog app!

Furthermore, check the toolbar. You can now select "Blog" > "Add Blog
Post..." from it and add a new blog post directly from there (you should
totally do that!)

Since the toolbar integration is totally awesome, we're going to
integrate our poll app into the toolbar in :doc:`toolbar`.
