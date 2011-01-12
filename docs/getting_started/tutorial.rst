#####################
Introductory Tutorial
#####################

************
Installation
************

This guide assumes your machine meets the requirements outlined in the
:doc:`installation` section of this documentation. Please refer to this section for
more information.

Installing Django CMS
=====================

While we strongly encourage you to install the django CMS using `buildout`_ or
`virtualenv`_, for the sake of simplicity this guide will install Django CMS
system wide. For more details about how either of theses projects work please 
refer to their respective documentation.

Install the latest django CMS package::

    $ sudo pip install django-cms south django-appmedia

Or install the latest revision from github::

    $ sudo pip install -e git+git://github.com/divio/django-cms.git#egg=django-cms
    $ sudo pip install south django-appmedia

To check if you installed django CMS properly, open a Python shell and type::

    import cms

If this does not return an error, you've successfully installed django CMS.

.. _buildout: http://www.buildout.org/
.. _virtualenv: http://virtualenv.openplans.org/


Preparing the environment
=========================

Gathering the requirements is a good start, but we now need to give the CMS a 
Django project to live in, and configure it.


Starting your Django project
----------------------------

The following assumes your project will be in ``~/workspace/myproject/``.

Set up your Django project::

    cd ~/workspace
    django-admin.py startproject myproject
    cd myproject
    python manage.py runserver

Open `127.0.0.1:8000 <http://127.0.0.1:8000>`_ in your browser. You should see a
nice "It Worked" message from Django.

|it-worked|

.. |it-worked| image:: ../images/it-worked.png


Installing and configuring django CMS in your Django project
------------------------------------------------------------

Open the file ``~/workspace/myproject/settings.py``.

To make your life easier, add the following at the top of the file::

    # -*- coding: utf-8 -*-
    import os
    gettext = lambda s: s
    PROJECT_PATH = os.path.abspath(os.path.dirname(__file__))


Add the following apps to your ``INSTALLED_APPS``:

* ``'cms'``
* ``'mptt'``
* ``'menus'``
* ``'south'``
* ``'appmedia'``

Also add any (or all) of the following plugins, depending on your needs:

* ``'cms.plugins.text'``
* ``'cms.plugins.picture'``
* ``'cms.plugins.link'``
* ``'cms.plugins.file'``
* ``'cms.plugins.snippet'``
* ``'cms.plugins.googlemap'``

If you wish to use the moderation workflow, also add:

* ``'publisher'``

Further, make sure you uncomment ``'django.contrib.admin'``

You need to add the django CMS middlewares to your ``MIDDLEWARE_CLASSES`` at the
right position::


    MIDDLEWARE_CLASSES = (
        'django.middleware.common.CommonMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'cms.middleware.page.CurrentPageMiddleware',
        'cms.middleware.user.CurrentUserMiddleware',
        'cms.middleware.toolbar.ToolbarMiddleware',
        'cms.middleware.media.PlaceholderMediaMiddleware',
    )

You need at least the following ``TEMPLATE_CONTEXT_PROCESSORS`` (a default Django
settings file will not have any)::

    TEMPLATE_CONTEXT_PROCESSORS = (
        'django.core.context_processors.auth',
        'django.core.context_processors.i18n',
        'django.core.context_processors.request',
        'django.core.context_processors.media',
        'cms.context_processors.media',
    )

Almost there!
Point your ``MEDIA_ROOT`` to where the static media should live (that is, your images, 
CSS files, Javascript files...)::

    MEDIA_ROOT = os.path.join(PROJECT_PATH, "media")
    MEDIA_URL = "/media/"
    ADMIN_MEDIA_PREFIX="/media/admin/"

Now add a little magic to the ``TEMPLATE_DIRS`` section of the file::

    TEMPLATE_DIRS = (
        # The docs say it should be absolute path: PROJECT_PATH is precisely one.
        # Life is wonderful!
        os.path.join(PROJECT_PATH, "templates")
    )

Add at least one template to ``CMS_TEMPLATES``; for example::

    CMS_TEMPLATES = (
        ('template_1.html', 'Template One'),
        ('template_2.html', 'Template Two'),
    )

We will create the actual template files at a later step, don't worry about it for 
now, and simply paste this code in your settings file.

.. note::

    The templates you define in ``CMS_TEMPLATES`` have to exist at runtime and
    contain at least one ``{% placeholder <name> %}`` template tag to be useful
    for django CMS. For more details see `Creating templates`_

Finally, setup the ``DATABASES`` part of the file to reflect your database deployement.


URL configuration
=================

You need to include the ``'cms.urls'`` urlpatterns **at the end** of your
urlpatterns. We suggest starting with the following ``urls.py``::

    from django.conf.urls.defaults import *
    from django.contrib import admin
    from django.conf import settings

    admin.autodiscover()

    urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        url(r'^', include('cms.urls')),
    )

    if settings.DEBUG:
        urlpatterns = patterns('',
            (r'^' + settings.MEDIA_URL.lstrip('/'), include('appmedia.urls')),
        ) + urlpatterns

To have access to app specific media files, use ``python manage.py symlinkmedia`` 
and `django-appmedia`_ will do all the work for you.

.. _django-appmedia: http://pypi.python.org/pypi/django-appmedia

Initial database setup
======================

This command depends on whether you **upgrade** your installation or do a
**fresh install**. We recommend that you get familiar with the way `South`_ works, 
as it is a very powerful, easy and convenient tool. Django CMS uses it extensively.

Fresh install
-------------

Run::

    python manage.py syncdb --all
    python manage.py migrate --fake

The first command will prompt you to create a super user; choose 'yes' and enter
appropriate values.

Upgrade
-------

Run::

    python manage.py syncdb
    python manage.py migrate

Up and running!
===============

That should be it. Restart your development server using ``python manage.py runserver`` 
and point a web browser to `127.0.0.1:8000 <http://127.0.0.1:8000>`_ :you should get 
the Django CMS "It Worked" screen.

|it-works-cms|

.. |it-works-cms| image:: ../images/it-works-cms.png

Head over to the `admin panel <http://127.0.0.1:8000/admin/>` and log in with
the user you created during the database setup.

To deploy your django CMS project on a production webserver, please refer to the
`Django Documentation <http://docs.djangoproject.com/en/1.2/howto/deployment/>`_.


******************
Creating templates
******************

Django CMS uses templates to define how a page should look and what parts of
it are editable. Editable areas are called *placeholders*. These templates are
standard Django templates and you may use them as described in the
`official documentation`_.

Templates you wish to use on your pages must be declared in the ``CMS_TEMPLATES``
setting::

  CMS_TEMPLATES = (
      ('template_1.html', 'Template One'),
      ('template_2.html', 'Template Two'),
  )

If you followed this tutorial from the beginning, we already put this code in your settings file.

Now, on with the actual template files!

Fire up your favorite editor and create a file called ``base.html`` in a folder called ``templates``
in your myproject directory.

Here is a simple example for a base template called ``base.html``:

.. code-block:: html+django

  {% load cms_tags %}
  <html>
    <body>
     {% placeholder base_content %}
     {% block base_content%}{% endblock %}
    </body>
  </html>

Now, create a file called ``template_1.html`` in the same directory. This will use 
your base template, and add extra content to it:

.. code-block:: html+django

  {% extends "base.html" %}
  {% load cms_tags %}

  {% block base_content %}
    {% placeholder template_1_content %}
  {% endblock %}

When you set ``template_1.html`` as a template on a page you will get two
placeholders to put plugins in. One is ``template_1_content`` from the page
template ``template_1.html`` and another is ``base_content`` from the extended
``base.html``.

When working with a lot of placeholders, make sure to give descriptive
names for your placeholders, to more easily identify them in the admin panel.

Now, feel free to experiment and make a ``template_2.html`` file! If you don't feel creative, 
just copy template_1 and name the second placeholder something like "template_2_content".

.. _official documentation: http://docs.djangoproject.com/en/1.2/topics/templates/

*****************************
Creating your first CMS page!
*****************************

That's it, now the best part: you can start using the CMS!
Run your server with ``python manage.py runserver``, then point a web browser to 
`127.0.0.1:8000/admin/ <http://127.0.0.1:8000/admin/>`_ , and log in using the super 
user credentials you defined when you ran ``syncdb`` earlier.

Once in the admin part of your site, you should see something like the following:

|first-admin| 

.. |first-admin| image:: ../images/first-admin.png

Adding a page
=============

Adding a page is as simple as clicking "Pages" in the admin view, then the "add page" button
on the top right-hand corner of the screen.

This is where you select which template to use (remember, we created two), as well as
pretty obvious things like which language the page is in (used for internationalisation),
the page's title, and the url slug it will use.

Hitting the "Save" button, well, saves the page. It will now display in the list of
pages.

|my-first-page|

.. |my-first-page| image:: ../images/my-first-page.png

Congratulations! You now have a fully functional Django CMS installation!

Publishing a page
=================

The list of pages available is a handy way to change a few parameters about your pages:

Visibility
----------
By default, pages are "invisible". To let people access them you should mark them as "published".

Menus 
-----
Another option this view lets you tweak is wether or not the page should appear in
your site's navigation (that is, wether there should be a menu entry to reach it
or not)

Adding content to a page
========================

So far, our page doesn't do much. Make sure it's marked as "published", the click on the page's 
"edit" button.

Ignore most of the interface for now, and click the "view on site" button on the 
top right-hand corner of the screen. As expected, your page is blank for the time being,
since our template is really a minimal one.

Let's get to it now then!

Press your browser's back button, so as to see the page's admin interface. If you followed 
the tutorial so far, your template (``template_1.html``) defines two placeholders.
The admin interfaces shows you theses placeholders as sub menus:

|first-placeholders|

.. |first-placeholders| image:: ../images/first-placeholders.png

Scroll down the "Available plugins" drop-down list. This displays the plugins you
added to your INSTALLED_APPS settings. Choose the "text" plugin in the drop-down,
then press the "Add" button.

The right part of the plugin area displays a rich text editor (`TinyMCE`_).

Type in whatever you please there, then press the "Save" button.

Go back to your website using the top right-hand "View on site" button. That's it!

|hello-cms-world|

.. |hello-cms-world| image:: ../images/hello-cms-world.png


Where to go from here
=====================

Congratulations, you now have a fully functional CMS! Feel free to play around 
with the different plugins provided out of the box, and build great websites!

***************
Troubleshooting
***************

If you've created a page & you don't see it in the cms list of the Django admin:

- Be sure you copied all the media files. Check with firebug and its "net" panel
  to see if you have any 404s.

If you're editing a Page in the Django admin, but don't see an "Add Plugin"
button with a dropdown-list of plugins:

- Be sure your ``CMS_TEMPLATES`` setting is correct, the templates specified
  exist, and they contain at least one ``{% placeholder %}`` templatetag.


Template errors
===============

If your placeholder content isn't displayed when you view a CMS page: change the
CMS_MODERATOR variable in settings.py to False. This bug has been recently
fixed, so upgrade to the latest version of Django CMS. See:
https://github.com/divio/django-cms/issues/issue/430


Javascript errors
=================

If plugins don't work (e.g.: you add a text plugin, but don't see the Javascript
text editor in the plugin window), you should use a Javascript inspector in your
browser to investigate the issue (e.g.: Firebug for Firefox, Web Inspector for
Safari or Chrome). The Javascript inspector may report the following errors:

- **TypeError: Result of expression 'jQuery' [undefined] is not a function.**

If you see this, check the ``MEDIA_URL`` variable in your settings.py file. Your
webserver (e.g.: Apache) should be configured to serve static media files from
this URL.

- **Unsafe JavaScript attempt to access frame with URL
  http://localhost/media/cms/wymeditor/iframe/default/wymiframe.html from frame
  with URL http://127.0.0.1:8000/admin/cms/page/1/edit-plugin/2/. Domains,
  protocols and ports must match.**

This error is due to the Django test server running on a different port and URL
than the main webserver. In your test environment, you can overcome this issue
by adding a CMS_MEDIA_URL variable to your settings.py file, and adding a url
rule in urls.py to make the Django development serve the Django CMS files from
this location.

.. _South: http://south.aeracode.org/
.. _TinyMCE: http://tinymce.moxiecode.com/

