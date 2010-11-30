Django CMS Tutorial
===================

Installation
-------------

This guide has been tested with Ubuntu 9.10 and Mac OS X Snow Leopard.

<--I am working on Ubuntu 9.10 here, not windows or mac...sorry, although I don't
expect things will be much different for mac at least...if I get a chance i'll
run through this process on windows too and update the article but no
promises.

I'm assuming that Python, Django and sqlite3 are installed already. For
reference, I am currently using Python 2.6.4 and Django (trunk version) 1.2.-->

Installing Django CMS
*********************
Django CMS can be installed in different ways.

You can use PIP::

    $ pip install django-cms

You can use easy_install::

    $ easy_install django-cms

Or you can download a tarball or check out a specific version from github::

    http://github.com/divio/django-cms/downloads

If you opt for this method, then you then need to run the `setup.py` file in the root folder of the downloaded package::

    $ python setup.py install

Alternatively, you can do everything by hand:

If you don't know your Python location, issue the following command::

    $ which python

(my path is "/usr/local/lib/python2.6" for example)

Go to your Python dist-packages directory "your-python-path/dist-packages"

Download the latest and greatest Django CMS from here: http://www.django-cms.org/en/downloads/

Unzip the downloaded file into the "dist-packages" directory...you will need to do this as the superuser.

Make copies of the following directories like so::

	sudo cp -R divio-django-cms-c0288a1/cms/ cms
	sudo cp -R divio-django-cms-c0288a1/mptt/ mptt
	sudo cp -R divio-django-cms-c0288a1/publisher/ publisher

Do a bit of house cleaning to get rid of all the files you don't need::

	sudo rm -rf divio-django-cms-c0288a1.zip
	sudo rm -rf divio-django-cms-c0288a1/
	
To ensure the cms is properly installed, invoke a Python shell (just type ``python`` at the prompt), and ensure the following command returns without errors:
    
    import cms

If this works, then you’re ready to create and configure a new project!

Make a set of basic project files
*********************************

Preparing the environment
*************************

If you don't already have one, create a new folder for your code to live in. My
folder lives in my home directory and is named "django_apps". This will pop up
throughout this guide so if you're following along and you call yours
something else, remember to replace "django_apps" with the name of your own
folder when the time comes.

In a terminal, move into your code directory::

	CD ~/django_apps

Create a new Django project (call this whatever you like but remember to
change it if you're following along and have called it something else)::

	django-admin.py startproject project-name

No harm in making sure that all is indeed well with Django at this early stage so::

	CD project-name

And... ::

	python manage.py runserver

Head on over to http://127.0.0.1:8000 and if you should see the "It worked!" page:

|it-worked|

.. |it-worked| image:: images/it-worked.png

Head back to the project you created previously::

	cd ~/django_apps/project-name

To use Django CMS as part of the project, you need to edit the "settings.py" file.

Insert the following before anything else in the file::

	import os
	gettext = lambda s: s
	PROJECT_PATH = os.path.realpath(os.path.dirname(__file__))

The gettext line allows us to use translatable strings in the settings.py file (see below).
	
The PROJECT_PATH line instructs Django to consider the location of your settings.py file to be the root of the project. 

Set up the remainder of the file with the following changes/additions::

    DATABASES = {
        # There are more fields in the generated settings.py, but they are not used
        # if one chooses sqlite3. Feel free to keep them.
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': '/path/to/your/data/your-db-name.db/',
        }
    }


	MEDIA_ROOT = os.path.join(PROJECT_PATH, 'media')
	MEDIA_URL = '/media/'

	ADMIN_MEDIA_PREFIX = '/media/admin/'

	INSTALLED_APPS = (
	    'django.contrib.auth',
	    'django.contrib.admin', # Make sure you uncomment this line
	    'django.contrib.contenttypes',
	    'django.contrib.sessions',
	    'django.contrib.sites',
	    'django.contrib.messages',
	    'cms',
	    'cms.plugins.text',
	    'cms.plugins.picture',
	    'cms.plugins.link',
	    'cms.plugins.file',
	    'cms.plugins.snippet',
	    'cms.plugins.googlemap',
	    'mptt',
	    'publisher',
	    'menus',
	)


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

	TEMPLATE_DIRS = os.path.join(PROJECT_PATH, 'templates')
	# (templates being the name of my template dir within project-name)

	TEMPLATE_CONTEXT_PROCESSORS = (
	    'django.core.context_processors.auth',
	    'django.core.context_processors.i18n',
	    'django.core.context_processors.request',
	    'django.core.context_processors.media',
	    'cms.context_processors.media',
	)

(I didn't have a ``TEMPLATE_CONTEXT_PROCESSORS`` specified so had to add all of the above anew.)

Set up your available templates (don't worry that they don't actually exist yet)::

	CMS_TEMPLATES = (
	    ('base.html', gettext('default')),
	    ('2col.html', gettext('2 Column')),
	    ('3col.html', gettext('3 Column')),
	    ('extra.html', gettext('Some extra fancy template')),
	)

The CMS_MEDIA_URL setting
*************************

Although the Django CMS media is located in the same folder as the rest of your media, you should set up a specific URL for just the Django CMS media. Then add a CMS_MEDIA_URL variable to settings.py, eg:: 
    
    CMS_MEDIA_URL = 'http://127.0.0.1:8000/static_media/cms/'

This configuration is necessary to overcome cross-site security issues relating to wymeditor, the Javascript utility used by Django CMS for the WYSIWYM text editor plugin. Although it is common to serve static files from a different domain, the Django CMS media must be served by the same domain that serves the dynamic Python files. 

In a development / test setting, the Django development server should be used to serve the Django CMS media files (see the "URLs configuration" section).

In a production environment, a server alias should be created which sends requests for the Django CMS media files to a folder on the main server.


URLs configuration
******************

Next, Edit your ``urls.py`` file like this::

	from django.conf.urls.defaults import *
	from django.contrib import admin
	from django.conf import settings

	admin.autodiscover()

	urlpatterns = patterns('',
	    (r'^admin/', include(admin.site.urls)),
	)

	if settings.DEBUG:
	    urlpatterns += patterns('',
	        url(r'^static_media/cms/(?P<path>.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT, 'show_indexes': True})
	    )

	urlpatterns += patterns('',
	    url(r'^', include('cms.urls')),
	)

It is necessary to include the Django CMS media folder in the media folder of your Django project:

1. Create a folder called 'media' in your project root (that's "project-name" for me).
 
2. Create a symbolic link from the "cms/media/cms" folder in "dist-packages" to your new "media" folder, for example::

    ln -s /usr/local/lib/python2.6/dist-packages/cms/media/cms cms

Make sure that read permissions are set on this folder. Now all of the static media files used by Django CMS can be served to your site.


Loading up on supplies: preparing the database
**********************************************

Now for the magic...if you're not already there::

	cd ~/django_apps/project-name

and... ::

	python manage.py syncdb

If all goes well, you'll be asked if you want to set up your superuser account...which of course you do so just follow the instructions in the terminal.

Up and running!
***************

That should hopefully be that. If your development server is still running in your terminal stop it, then restart it again just to be sure. ::

	cmd c
	python manage.py runserver

Visit http://127.0.0.1:8000/ to make sure all is well, you'll be greeted with
appropriate text and if you can see the django-cms logo then your media folder
is cool also.

|it-works-cms|

.. |it-works-cms| image:: images/it-works-cms.png

Now log in via the admin link (http://127.0.0.1:8000/admin/) and enjoy :)

This is your development enviroment. On how to deploy django projects on real
webservers you may want to head over to http://www.django-project.com/


Templates
---------

In django-cms you set one template per page. After you have set a template for
a page you can put plugins into the defined placeholders. Templates in django-cms
are just django templates. See official documentation `django template language <http://docs.djangoproject.com/en/1.2/topics/templates/>`_

You have to define the templates in ``settings.CMS_TEMPLATES``. ::

  CMS_TEMPLATES = (
      ('template_1.html', 'Template One'),
      ('template_2.html', 'Template Two'),
      ...
  )

Each of these templates is now available to be set on a given page in the admin
backend. When you set a template for a certain page, django-cms will search
for the placeholders defined in that template and update the page form so you
can put plugins into them. You can even have a placeholder for all your page
templates in a base template that the template for a page extends.

For example you have a ``base.html`` like this: ::

  {% load cms_tags %}
  <html>
    <body>
     {% placeholder base_content %}
     {% block base_content%}{% endblock %}
    </body>
  </html>

And have set ``template_1.html`` to: ::

  {% extends "base.html" %}
  {% load cms_tags %}

  {% block base_content %}
    {% placeholder template_1_content %}
  {% endblock %}

When you set ``template_1.html`` as a template on a page you will get two
placeholders to put plugins in. One is **template_1_content** from the page
template ``template_1.html`` and another is **base_content** from extended
``base.html``.

When working with alot of placeholders, you want to make sure to set proper names
for your placeholders. These are just spitted out on the page form and it
can get messy if you have lots of them. Have a look at ``settings.CMS_PLACEHOLDER_CONF``
to further configure the placeholders.

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



