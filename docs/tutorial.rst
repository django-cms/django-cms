Django CMS Tutorial
===================

Installation
-------------

This guide assumes you have the following software installed:

* `Python`_ 2.5 or higher
* `Django`_ 1.2 or higher
* `pip`_ 0.8.2 or higher
* `South`_ 0.7.2 or higher
* `PIL`_ 1.1.6 or higher
* `django-classy-tags`_ 0.2.2 or higher

It also assumes you're on a Unix based system.

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _pip: http://pip.openplans.org/
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags

Installing Django CMS
*********************

While we strongly encourage you to install the Django CMS using `buildout`_ or
`virtualenv`_, for the sake of simplicity this guide will install Django CMS
system wide. For a proper installion procedure, please read the documentation of
those projects.

Install the latest Django CMS package::

    $ sudo pip install django-cms

Or install the latest revision from github::

    $ sudo pip install -e git+git://github.com/divio/django-cms.git#egg=django-cms

To check if you installed Django CMS properly, open a Python shell and type::

    import cms

If this does not return an error, you've successfully installed Django CMS.

.. _buildout: http://www.buildout.org/
.. _virtualenv: http://virtualenv.openplans.org/


Preparing the environment
*************************

Starting your Django project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

The following assumes your project is in ``~/workspace/myproject/``.

Set up your Django project::

	cd ~/workspace
	django-admin.py startproject myproject
	cd myproject
	python manage.py runserver

Open `127.0.0.1:8000 <http://127.0.0.1:8000>`_ in your browser. You should see a
nice "It Worked" message from Django.

|it-worked|

.. |it-worked| image:: images/it-worked.png


Installing and configuring Django CMS in Your Django Project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

You need to add the Django CMS middlewares to your ``MIDDLEWARE_CLASSES`` at the
right position::


	MIDDLEWARE_CLASSES = (
	    'django.middleware.cache.UpdateCacheMiddleware',
	    'django.contrib.sessions.middleware.SessionMiddleware',
	    'django.contrib.auth.middleware.AuthenticationMiddleware',
	    'django.middleware.common.CommonMiddleware',
	    'django.middleware.doc.XViewMiddleware',
	    'django.middleware.csrf.CsrfViewMiddleware',
	    'cms.middleware.page.CurrentPageMiddleware',
	    'cms.middleware.user.CurrentUserMiddleware',
	    'cms.middleware.toolbar.ToolbarMiddleware',
	    'cms.middleware.media.PlaceholderMediaMiddleware',
	    'django.middleware.cache.FetchFromCacheMiddleware',
	)

You need at least the following ``TEMPLATE_CONTEXT_PROCESSORS``::

	TEMPLATE_CONTEXT_PROCESSORS = (
	    'django.core.context_processors.auth',
	    'django.core.context_processors.i18n',
	    'django.core.context_processors.request',
	    'django.core.context_processors.media',
	    'cms.context_processors.media',
	)


Add at least one template to ``CMS_TEMPLATES``; for example::

	CMS_TEMPLATES = (
	    ('default.html', gettext('default')),
	)


.. note::

    The templates you define in ``CMS_TEMPLATES`` have to actually exist and
    contain at least one ``{% placeholder <name> %}`` template tag to be useful
    for Django CMS. For more details see `Templates`_


URL configuration
*****************

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
	        url(
	            r'^media/cms/(?P<path>.*)$',
	            'django.views.static.serve',
	            {'document_root': settings.MEDIA_ROOT, 'show_indexes': True}
	        )
	    ) + urlpatterns

To have access to app specific media files (javascript, stylesheets, images), we
recommend you use `django-appmedia`_. After you've installed it, use
``python manage.py symlinkmedia`` and it will do all the work for you.

.. _django-appmedia: http://pypi.python.org/pypi/django-appmedia


Initial database setup
**********************

This command depends on whether you **upgrade** your installation or do a
**fresh install**.

Fresh install
~~~~~~~~~~~~~

Run::

	python manage.py syncdb --all
	python manage.py migrate --fake

The first command will prompt you to create a super user; choose 'yes' and enter
appropriate values.

Upgrade
~~~~~~~

Run::

    python manage.py syncdb
    python manage.py migrate


Up and running!
***************

That should be it. Restart your development server and go to
`127.0.0.1:8000 <http://127.0.0.1:8000>`_ and you should get the Django
CMS "It Worked" screen.

|it-works-cms|

.. |it-works-cms| image:: images/it-works-cms.png

Head over to the `admin panel <http://127.0.0.1:8000/admin/>` and log in with
the user you created during the database setup.

To deploy your Django CMS project on a real webserver, please refer to the
`Django Documentation <http://docs.djangoproject.com/en/1.2/howto/deployment/>`_.


Templates
---------

Django CMS uses templates to define how a page should look and what parts of
it are editable. Editable areas are called *placeholders*. These templates are
standard Django templates and you may use them as described in the
`official documentation`_.

Templates you wish to use on your pages must be declared in the ``CMS_TEMPLATES``
setting::

  CMS_TEMPLATES = (
      ('template_1.html', 'Template One'),
      ('template_2.html', 'Template Two'),
      ...
  )

Here is a simple example for a base template called ``base.html``::

  {% load cms_tags %}
  <html>
    <body>
     {% placeholder base_content %}
     {% block base_content%}{% endblock %}
    </body>
  </html>

Now we can use this base template in our ``template_1.html`` template::

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

.. _official documentation: http://docs.djangoproject.com/en/1.2/topics/templates/

My First Plugin
---------------

There are a few plugins included with the CMS that let you put basic content
into a page's placeholders. To put custom content into a placeholder,
you need to write a CMS plugin. A plugin consists of two things: A model that
holds the actual data you want to store, and a plugin class that tells the CMS
how to render the plugin. Let's write a plugin that displays a title & some text.

Create a django application and install it in settings.py. If you want to save
data to the database, you must create a model in the plugin's ``models.py``. ::

  from cms.models import CMSPlugin
  from django.db import models

  class TextWithTitle(CMSPlugin):
      title = models.CharField(max_length=50)
      text =  models.TextField()

NB: the plugin model does not inherit from `django.db.models.Model` but from
`cms.models.CMSPlugin`.

Run syncdb to create the according database tables. ::

  python manage.py syncdb

Now you have a model that stores your plugin data, you need to tell the CMS
about your plugin. Create a plugin class that inherits
from `CMSPluginBase` in a file called **cms_plugins.py** in your
application folder. ::

  from cms.plugin_base import CMSPluginBase
  from cms.plugin_pool import plugin_pool
  from models import TextWithTitle
  from django.utils.translation import ugettext as _

  class TextWithTitlePlugin(CMSPluginBase):
      model = TextWithTitle
      name = _("Text with Title")
      render_template = "textwithtitle.html"

      def render(self, context, instance, placeholder):
          context.update({'instance':instance,
                          'placeholder':placeholder})
          return context

Note that the `TextWithTitlePlugin` class inherits from `CMSPluginBase`. It
holds information about its name, the model and the template to render.

Finaly you have to register this plugin (in cms_plugins.py) to actually tell
the CMS about your plugin. ::

  plugin_pool.register_plugin(TextWithTitlePlugin)

**Attributes**

These are the attributes you have to provide for the plugin to work.

:model:
  Specify the model this plugin uses to save data. You dont have to write a
  custom model if your plugin just wants to display some HTML. If
  so, just use the `CMSPlugin` class as this plugin's model.

:name:
  The name of this plugin in the admin.

:render_template:
  The template used to render this plugin on a page, not
  the template used for admin backend or frontend editing.

**The render Function**

The render Function is called when the plugin is rendered on a page. It modifies
the context given and sets any additional data you want while rendering the given
template. This function is only called when rendering the plugin on a page.

To provide a new change form for this plugin use the **change_form_template**
attribute. `CMSPluginBase` inherits from `ModelAdmin`, so you can change the
Plugin as you would a `ModelAdmin`. See
http://docs.djangoproject.com/en/1.2/ref/contrib/admin/

:context:
  The Context used to render the plugin.

:instance:
  The instance of the plugin specified by model.

:placeholder:
  The placeholder this plugin gets rendered in.

A template for this plugin could look like::

  <h1>{{ instance.title }}</h1>
  <p>{{ instance.text }}</p>

The context while rendering the plugin is the one returned in the render
function. In our example we passed `instance` and now can access all our
model's fields through this variable.

You should now be able to select this plugin under its name in any placeholder
on any page. The template is searched with normal django template lookup
mechanisms, so you may need to alter the `render_template` setting appropriately.

My First App
------------

My First Menu
-------------

My First Attach Menu
--------------------

My First Apphook
----------------

What is an apphook you might ask? "Apphooks" are a way to forward all URLs "under"
a CMS page to another Django app.
For the sake of the example, let's assume you have a very fancy "myapp" Django
application, which you want to use in your Django-CMS project, as the
"/myapp/<something>" pages.

#. Create a ``cms_app.py`` file in your app's module (usually next to ``models.py``)
#. Paste and adapt the following code to the newly created file, save, restart
   your server if needed::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool

    class MyApphook(CMSApp):
        name = "My Apphook's name" # Visible in the CMS admin page - make it readable!
        urls = ["myapp.blog.urls"] # Your app's ``urls.py`` file
    apphook_pool.register(MyAppHook) # As in ``admin.py`` file, you need to register your apphook with the CMS

#. Create a "blog" page in the Django-CMS admin interface.
#. Still in the admin interface, navigate to your newly created page, edit it,
   and expand the "Advanced Settings" group.
#. You should see your ``My Apphook's name`` apphook in the "Application"
   drop-down list.
#. Select your apphook & save the page. You must restart your Django server for
   the changes to take effect (Django caches urls).
#. Your application is now available at
   ``http://<your host>/myapp/<your apps urls>``!



