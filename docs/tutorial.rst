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

It also assumes you're on a Unix based system.

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _pip: http://pip.openplans.org/
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/

Installing Django CMS
*********************

While we strongly encourage you to install the Django CMS using `buildout`_ or
`virtualenv`_, for the sake of simplicity this guide will install the Django CMS
system wide. For the proper way to install it, please read the documentation of
those projects.

Install the latest package of the Django CMS::

    $ sudo pip install django-cms

Or install the latest revision from github::

    $ sudo pip install -e git+git://github.com/divio/django-cms.git#egg=django-cms

To check if you installed the Django CMS properly, open a python shell and do::
    
    import cms
    
If this does not give you an error, you've successfully installed the Django CMS.

.. _buildout: http://www.buildout.org/
.. _virtualenv: http://virtualenv.openplans.org/


Preparing the environment
*************************

Starting your Django project
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

We assume you develop your project in ``~/workspace/myproject/``.

Set up your Django project::

	cd ~/workspace
	django-admin.py startproject myproject
	cd myproject
	python manage.py runserver

Open `127.0.0.1:8000 <http://127.0.0.1:8000>`_ in your browser which should give
you a nice "It Worked" message from Django.

|it-worked|

.. |it-worked| image:: images/it-worked.png


Adding and configuring the Django CMS
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

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

Also add any (or all) of the following plugins depending on your needs:

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
right position, we suggest::


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


Add at least one template to ``CMS_TEMPLATES``, for example::

	CMS_TEMPLATES = (
	    ('default.html', gettext('default')),
	)


.. note::

    The templates you define in ``CMS_TEMPLATES`` have to actually exist and contain
    at least one ``{% placeholder <name> %}`` template tag to be useful for the
    Django CMS. For more details see `Templates`_ 


URL configuration
*****************

You need to include the ``'cms.urls'`` urlpatterns **as the end** of your
urlpatterns. We suggest the following urls.py for a start::

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
recommend you use `django-appmedia`_. After you installed it, use
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
	
The first command will prompt you to create a super user, chose 'yes' and enter
appropriate values.

Upgrade
~~~~~~~

Run::

    python manage.py syncdb
    python manage.py migrate


Up and running!
***************

That should hopefully be that. Restart your development server and go to
`127.0.0.1:8000 <http://127.0.0.1:8000>`_ again and you should get the Django
CMS "It Worked" screen.

|it-works-cms|

.. |it-works-cms| image:: images/it-works-cms.png

Head over to the `admin panel <http://127.0.0.1:8000/admin/>` and log in with
the user you created during the database setup.

To deploy your Django CMS project on a real webserver, please refer to the
`Django Documentation <http://docs.djangoproject.com/en/1.2/howto/deployment/>`_.


Templates
---------

The Django CMS uses templates to define how a page should look and what parts of
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

Here is a simple example for a base template we call ``base.html``::

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
template ``template_1.html`` and another is ``base_content`` from extended
``base.html``.

When working with a lot of placeholders, you want to make sure to set proper
names for your placeholders so it easier to identify them in the admin panel.

.. _official documentation: http://docs.djangoproject.com/en/1.2/topics/templates/

My First Plugin
---------------

There are a few plugins within the CMS that let you put basic content into the
placeholders of a page. To be able to put custom content into a placeholder,
you need to write a CMS plugin. A plugin consists of two things. A model that
holds the actual data you want to store and a plugin class that tells the CMS
how to render it. Lets write a plugin that displays a title and some text.

Create a django application and install it in settings.py. As you want to save
data to the database you need to write a model in your models.py. ::

  from cms.models import CMSPlugin
  from django.db import models
  
  class TextWithTitle(CMSPlugin):
      title = models.CharField(max_length=50)
      text =  models.TextField()

Note that the model does not inherit from `django.db.models.Model` but from
`cms.models.CMSPlugin`.

Run syncdb to create the according database tables. ::

  python manage.py syncdb

Now that you have a model that stores your plugin data, you need to tell the CMS
about your plugin. For that you need to write the plugin class that inherits
from `CMSPluginBase`. Do this in a file called **cms_plugins.py** in your
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

Note that the `TextWithTitlePlugin` class inherits from `CMSPluginBase`. It holds 
information about its name, the model and the template to render with.

Finaly you have to register this plugin (in cms_plugins.py) to actually tell
the CMS about your plugin. ::

  plugin_pool.register_plugin(TextWithTitlePlugin)

**Attributes**

These are the attributes you have to provide for the plugin to work.

:model:
  Specify the model this plugin uses to save data. You dont have to write a
  custom model if your plugin just wants to display some HTML for example. If
  doing so you should just Provide the `CMSPlugin` class as this plugins model.

:name:
  The name of this plugin in the admin.

:render_template:
  The template that is being use to render this plugin on a page. This is not 
  the template beeing used to render the plugin in the admin backend or frontend
  editing parts.

**The render Function**

The render Function is called when the plugin is rendered on a page. Modify the
context given and set the additional data you want while rendering the given
template. This function is only called when rendering the plugin on a page.

To provide a new change form for this plugin use the **change_form_template**
attribute. `CMSPluginBase` inherits from `ModelAdmin`. So you can change the
Plugin as you would with a `ModelAdmin`. See http://docs.djangoproject.com/en/1.2/ref/contrib/admin/

:context:
  The Context with which the plugin gets rendered.

:instance:
  The instance of the model specified by model.

:placeholder:
  The placeholder this plugin gets rendered in.

The template for this plugin could look like this: ::

  <h1>{{ instance.title }}</h1>
  <p>{{ instance.text }}</p>

The context while rendering the plugin is the one you returned in the render
function. In our example we passed 'instance' and now can access all our
model's fields through this variable.

You should now be able to select this plugin under its name in any placeholder
on any page. The template is searched with normal django template lookup 
mechanisms so you may need to alter the setting of render_template appropriatly
to meet your needs.

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
For the sake of the example, let's assume you have a very fancy "myapp" django application, 
that you would like to use in your django-CMS project, as the "/myapp/<something>" pages.

#. Create a ``cms_app.py`` file in your app's module (usually next to ``models.py``)
#. Paste and adapt the following code to the newly created file, save, restart your server if needed::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool

    class MyApphook(CMSApp):
        name = "My Apphook's name" # This is visible in the CMS admin page - make it readable!
        urls = ["myapp.blog.urls"] # Your app's urls.py file
    apphook_pool.register(MyAppHook) # Like in admin.py file, you need to register your apphook with the CMS
    
#. Create a "blog" page in the Django-CMS admin interface.
#. Still in the admin interface, navigate to your newly create page, edit it, and expand the "Advanced Settings" group
#. You should see your ``My Apphook's name`` apphook in the "Application" drop-down list.
#. Once selected, you unfortunately need to restart your django server for the changes to take effect.
#. Your application is now available at ``http://<your host>/myapp/<your apps urls.py>``!



