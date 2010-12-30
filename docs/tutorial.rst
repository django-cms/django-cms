###################
django CMS Tutorial
###################

************
Installation
************

This guide assumes you have the following software installed:

* `Python`_ 2.5 or higher
* `Django`_ 1.2 or higher
* `pip`_ 0.8.2 or higher
* `South`_ 0.7.2 or higher
* `PIL`_ 1.1.6 or higher
* `django-classy-tags`_ 0.2.2 or higher

It also assumes you're on a Unix-based system.

Installing django CMS
=====================

While we strongly encourage you to install the django CMS using `buildout`_ or
`virtualenv`_, for the sake of simplicity this guide will install django CMS
system wide. For a proper installation procedure, please read the documentation
of those projects.

Install the latest django CMS package::

    $ sudo pip install django-cms

Or install the latest revision from github::

    $ sudo pip install -e git+git://github.com/divio/django-cms.git#egg=django-cms

To check if you installed django CMS properly, open a Python shell and type::

    import cms

If this does not return an error, you've successfully installed django CMS.

.. _buildout: http://www.buildout.org/
.. _virtualenv: http://virtualenv.openplans.org/


Preparing the environment
=========================

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

.. |it-worked| image:: images/it-worked.png


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
    for django CMS. For more details see `Templates`_


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

	if settings.DEBUG: # these lines are just to serve media on local machines.
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
======================

This command depends on whether you **upgrade** your installation or do a
**fresh install**.

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

That should be it. Restart your development server and go to
`127.0.0.1:8000 <http://127.0.0.1:8000>`_ and you should get the Django
CMS "It Worked" screen.

|it-works-cms|

.. |it-works-cms| image:: images/it-works-cms.png

Head over to the `admin panel <http://127.0.0.1:8000/admin/>` and log in with
the user you created during the database setup.

To deploy your django CMS project on a real webserver, please refer to the
`Django Documentation <http://docs.djangoproject.com/en/1.2/howto/deployment/>`_.


*********
Templates
*********

django CMS uses templates to define how a page should look and what parts of
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

Here is a simple example for a base template called ``base.html``:

.. code-block:: html+django

  {% load cms_tags %}
  <html>
    <body>
     {% placeholder base_content %}
     {% block base_content%}{% endblock %}
    </body>
  </html>

Now we can use this base template in our ``template_1.html`` template:

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

.. _official documentation: http://docs.djangoproject.com/en/1.2/topics/templates/


**************************
Integrating custom content
**************************

From this part onwards, this tutorial assumes you have done the
`Django Tutorial`_ and we will show you how to integrate that poll app into the
django CMS. If a poll app is mentioned here, we mean the one you get when
finishing the `Django Tutorial`_.

We assume your main ``urls.py`` looks somewhat like this::

    from django.conf.urls.defaults import *

    from django.contrib import admin
    admin.autodiscover()

    urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        (r'^polls/', include('polls.urls')),
        (r'^', include('cms.urls')),
    )


My First Plugin
===============

A Plugin is a small bit of content you can place on your pages.

The Model
---------

For our polling app we would like to have a small poll plugin, that shows one
poll and let's the user vote.

In your poll application's ``models.py`` add the following model::

    from cms.models import CMSPlugin
    
    class PollPlugin(CMSPlugin):
        poll = models.ForeignKey('polls.Poll', related_name='plugins')
        
        def __unicode__(self):
          return self.poll.question


.. note:: django CMS Plugins must inherit from ``cms.models.CMSPlugin`` (or a
          subclass thereof) and not ``django.db.models.Model``.

Run ``syncdb`` to create the database tables for this model or see
:doc:`using_south` to see how to do it using `South`_


The Plugin Class
----------------

Now create a file ``cms_plugins.py`` in the same folder your ``models.py`` is
in, so following the `Django Tutorial`_, your polls app folder should look like
this now::

    polls/
        __init__.py
        cms_plugins.py
        models.py
        tests.py
        views.py 


The plugin class is responsible to provide the django CMS with the necessary
information to render your Plugin.

For our poll plugin, write following plugin class::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from polls.models import PollPlugin as PollPluginModel
    from django.utils.translation import ugettext as _
    
    class PollPlugin(CMSPluginBase):
        model = PollPluginModel # Model where data about this plugin is saved
        name = _("Poll Plugin") # Name of the plugin
        render_template = "polls/plugin.html" # template to render the plugin with
    
        def render(self, context, instance, placeholder):
            context.update({'instance':instance})
            return context
    
    plugin_pool.register_plugin(PollPlugin) # register the plugin

.. note:: All plugin classes must inherit from ``cms.plugin_base.CMSPluginBase``
          and must register themselves with the ``cms.plugin_pool.plugin_pool``.


The Template
------------

You probably noticed the ``render_template`` attribute on that plugin class, for
our plugin to work, that template must exist and is responsible for rendering
the plugin.


The template could look like this:

.. code-block:: html+django

    <h1>{{ poll.question }}</h1>
    
    <form action="{% url polls.views.vote poll.id %}" method="post">
    {% csrf_token %}
    {% for choice in poll.choice_set.all %}
        <input type="radio" name="choice" id="choice{{ forloop.counter }}" value="{{ choice.id }}" />
        <label for="choice{{ forloop.counter }}">{{ choice.choice }}</label><br />
    {% endfor %}
    <input type="submit" value="Vote" />
    </form>


.. note:: We don't show the errors here, because when submitting the form you're
          taken off this page to the actual voting page.


My First App
============

Right now, your app is statically hooked into the main ``urls.py``, that is not
the preferred way in the django CMS. Ideally you attach your apps to CMS Pages.

For that purpose you write CMS Apps. That is just a small class telling the CMS
how to include that app.

CMS Apps live in a file called ``cms_app.py``, so go ahead and create that to
make your polls app look like this::

    polls/
        __init__.py
        cms_app.py
        cms_plugins.py
        models.py
        tests.py
        views.py 

In this file, write::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from django.utils.translation import ugettext_lazy as _
    
    class PollsApp(CMSApp):
        name = _("Poll App") # give your app a name, this is required
        urls = ["polls.urls"] # link your app to url configuration(s)
        
    apphook_pool.register(PollsApp) # register your app
    
Now remove the inclusion of the polls urls in your main ``urls.py`` so it looks
like this::

    from django.conf.urls.defaults import *

    from django.contrib import admin
    admin.autodiscover()

    urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        (r'^', include('cms.urls')),
    )


Now open your admin in your browser and edit a CMS Page. Open the 'Advanced
Settings' tab and choose 'Polls App' for your 'Application'.

|apphooks|

.. |apphooks| image:: images/cmsapphook.png

Now for those changes to take effect, unfortunately you will have to restart
your server. So do that and now if you navigate to that CMS Page, you will see
your polls application.


My First Menu
=============

Now you might have noticed that the menu tree stops at the CMS Page you created
in the last step, so let's create a menu that shows a node for each poll you
have active.

For this we need a file called ``menu.py``, create it and check your polls app
looks like this::

    polls/
        __init__.py
        cms_app.py
        cms_plugins.py
        menu.py
        models.py
        tests.py
        views.py


In your ``menu.py`` write::

    from cms.menu_bases import CMSAttachMenu
    from menus.base import Menu, NavigationNode
    from menus.menu_pool import menu_pool
    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _
    from polls.models import Poll
    
    class PollsMenu(CMSAttachMenu):
        name = _("Polls Menu") # give the menu a name, this is required.
        
        def get_nodes(self, request):
            """
            This method is used to build the menu tree.
            """
            nodes = []
            for poll in Poll.objects.all():
                # the menu tree consists of NavigationNode instances
                # Each NavigationNode takes a label as first argument, a URL as
                # second argument and a (for this tree) unique id as third
                # argument.
                node = NavigationNode(
                    poll.question,
                    reverse('polls.views.detail', args=(poll.pk,)),
                    poll.pk
                )
                nodes.append(node)
            return nodes
    menu_pool.register_menu(PollsMenu) # register the menu.


Now this menu alone doesn't do a whole lot yet, we have to attach it to the
Apphook first.

So open your ``cms_apps.py`` and write::

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    from polls.menu import PollsMenu
    from django.utils.translation import ugettext_lazy as _
    
    class PollsApp(CMSApp):
        name = _("Poll App")
        urls = ["polls.urls"]
        menu = [PollsMenu] # attach a CMSAttachMenu to this apphook.
        
    apphook_pool.register(PollsApp)


.. _Django Tutorial: http://docs.djangoproject.com/en/1.2/intro/tutorial01/

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _pip: http://pip.openplans.org/
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags