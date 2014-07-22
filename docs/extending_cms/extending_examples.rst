###########################
Extending the CMS: Examples
###########################

From this point onwards, this tutorial assumes you have done the `Django
Tutorial`_ (for Django 1.6) and will show you how to integrate the tutorial's
poll app into the django CMS. Hereafter, if a poll app is mentioned, we are
referring to the one you get after completing the `Django Tutorial`_.  Also,
make sure the poll app is in your :setting:`django:INSTALLED_APPS`.

We assume your main ``urls.py`` looks something like this::

    # -*- coding: utf-8 -*-

    from django.conf.urls import *

    from django.contrib import admin

    admin.autodiscover()

    urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        (r'^polls/', include('polls.urls', namespace='polls')),
        (r'^', include('cms.urls')),
    )

***************
My First Plugin
***************

A Plugin is a small bit of content that you can place on your pages.

The Model
=========

For our polling app we would like to have a small poll plugin which shows a
poll and lets the user vote.

In your poll application's ``models.py`` add the following::

    # -*- coding: utf-8 -*-

    from django.db import models

    from cms.models import CMSPlugin

    # existing Poll and Choice models...
    ....
    
    class PollPluginModel(CMSPlugin):
        poll = models.ForeignKey('polls.Poll', related_name='plugins')
        
        def __unicode__(self):
          return self.poll.question


.. note::

    django CMS plugins must inherit from :class:`cms.models.CMSPlugin`
    (or a subclass thereof) and not
    :class:`models.Model <django.db.models.Model>`.

Run ``manage.py syncdb`` to create the database tables for this model or see
:doc:`../../basic_reference/using_south` to see how to do it using `South`_.


The Plugin Class
================

Now create a file ``cms_plugins.py`` in the same folder your ``models.py`` is
in. After having followed the `Django Tutorial`_ and adding this file your polls
app folder should look like this::

    polls/
        templates/
            polls/
                detail.html
                index.html
                results.html
        __init__.py
        admin.py
        cms_plugins.py
        models.py
        tests.py
        urls.py
        views.py


The plugin class is responsible for providing the django CMS with the necessary
information to render your Plugin.

For our poll plugin, write the following plugin class::

    # -*- coding: utf-8 -*-

    from django.utils.translation import ugettext as _

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool

    from .models import PollPluginModel
    
    class PollPlugin(CMSPluginBase):
        model = PollPluginModel                 # Model where data about this plugin is saved
        name = _("Poll Plugin")                 # Name of the plugin
        render_template = "polls/plugin.html"   # template to render the plugin with
    
        def render(self, context, instance, placeholder):
            context.update({'instance':instance})
            return context
    
    plugin_pool.register_plugin(PollPlugin) # register the plugin

.. note::

    All plugin classes must inherit from 
    :class:`cms.plugin_base.CMSPluginBase` and must register themselves
    with the :data:`cms.plugin_pool.plugin_pool`.


The Template
============

You probably noticed the
:attr:`render_template <cms.plugin_base.CMSPluginBase.render_template>`
attribute in the above plugin class. In order for our plugin to work, that
template must exist and is responsible for rendering the plugin. You should
create a new file in your poll-app’s templates folder under ``polls``
called ``plugin.html``.


The template should look something like this:

.. code-block:: html+django

    <h1>{{ instance.poll.question }}</h1>
    
    <form action="{% url 'polls:vote' instance.poll.id %}" method="post">
    {% csrf_token %}
    {% for choice in instance.poll.choice_set.all %}
        <input type="radio" name="choice" id="choice{{ forloop.counter }}" value="{{ choice.id }}" />
        <label for="choice{{ forloop.counter }}">{{ choice.choice }}</label><br />
    {% endfor %}
    <input type="submit" value="Vote" />
    </form>


.. note::

    We don't show the errors here, because when submitting the form you're
    taken off this page to the actual voting page.

**********************
My First App (apphook)
**********************

Right now, external apps are statically hooked into the main ``urls.py``. This
is not the preferred approach in the django CMS. Ideally you attach your apps
to CMS pages. This will allow the editors to move your page, and the attached
application to different parts of the page tree, without breaking anything.

For that purpose you write a :class:`CMSApp <cms.app_base.CMSApp>`. That is
just a small class telling the CMS how to include that app.

CMS Apps live in a file called ``cms_app.py``, so go ahead and create it to
make your polls app look like this::

    polls/
        templates/
            polls/
                detail.html
                index.html
                plugin.html
                results.html
        __init__.py
        admin.py
        cms_app.py
        cms_plugins.py
        models.py
        tests.py
        urls.py
        views.py


In this file, write::

    # -*- coding: utf-8 -*- 

    from django.utils.translation import ugettext_lazy as _

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool
    
    class PollsApp(CMSApp):
        name = _("Poll App")        # give your app a name, this is required
        urls = ["polls.urls"]       # link your app to url configuration(s)
        app_name = "polls"          # this is the application namespace
        
    apphook_pool.register(PollsApp) # register your app
    

NOTE: If your polls module is not in the root of your project folder, then you
may need to adjust the line above ``urls = ["polls.urls"]`` accordingly.

Now remove the inclusion of the polls urls in your main ``urls.py`` so it looks
like this::

    # -*- coding: utf-8 -*- 

    from django.conf.urls import *
    from django.contrib import admin

    admin.autodiscover()

    urlpatterns = patterns('',
        (r'^admin/', include(admin.site.urls)),
        # delete the polls entry that was here, no longer needed!
        (r'^', include('cms.urls')),
    )


Restart your server so that the PollsApp will now register.

Now open your Django Admin in your browser and navigate to the CMS app, then
choose Pages. This should display the "page tree". From this page, create a
page called "Polls". Save the page with the button: "Save and continue
editing". Next, press "Advanced Settings" and choose "Poll App" in the drop-
down menu labeled "Application". Finally, in the field named "Application
instance name", enter "polls" and "Save".


|apphooks|

.. |apphooks| image:: ../images/cmsapphook.png

Unfortunately, for these changes to take effect, you will have to restart your
server (this is automatic when using runserver, but not other servers). So do
that and afterwards if you navigate to that CMS Page, you will see your polls
application.

*************
My First Menu
*************

Now you might have noticed that the menu tree stops at the CMS Page you created
in the last step. So let's create a menu that shows a node for each poll you
have active.

For this we need a file called ``menu.py``. Create it and ensure your polls app
directory looks like this::

    polls/
        templates/
            polls/
                detail.html
                index.html
                plugin.html
                results.html
        __init__.py
        admin.py
        cms_app.py
        cms_plugins.py
        menu.py
        models.py
        tests.py
        urls.py
        views.py


In your ``menu.py`` write::

    # -*- coding: utf-8 -*-

    from django.core.urlresolvers import reverse
    from django.utils.translation import ugettext_lazy as _

    from cms.menu_bases import CMSAttachMenu
    from menus.base import Menu, NavigationNode
    from menus.menu_pool import menu_pool

    from .models import Poll
    
    class PollsMenu(CMSAttachMenu):
        name = _("Polls Menu") # give the menu a name, this is required.
        
        def get_nodes(self, request):
            """
            This method is used to build the menu tree.
            """
            nodes = []
            for poll in Poll.objects.all():
                # the menu tree consists of NavigationNode instances
                # Each NavigationNode takes a label as its first argument, a URL as
                # its second argument and a (for this tree) unique id as its third
                # argument.
                node = NavigationNode(
                    poll.question,
                    reverse('polls:detail', args=(poll.pk,)),
                    poll.pk
                )
                nodes.append(node)
            return nodes

    menu_pool.register_menu(PollsMenu) # register the menu.


At this point this menu alone doesn't do a whole lot. We have to attach it to the
Apphook first.

So open your ``cms_app.py`` and write::

    # -*- coding: utf-8 -*- 

    from django.utils.translation import ugettext_lazy as _

    from cms.app_base import CMSApp
    from cms.apphook_pool import apphook_pool

    from .menu import PollsMenu

    class PollsApp(CMSApp):
        name = _("Poll App")        # give your app a name, this is required
        urls = ["polls.urls"]       # link your app to url configuration(s)
        app_name = "polls"          # this is the application namespace
        menus = [PollsMenu]         # attach a CMSAttachMenu to this apphook.
        
    apphook_pool.register(PollsApp) # register your app


Alternatively, you can attach it to any page directly using the "Attached
Menu" field in the Advances Settings of the page’s admin. This is useful if
you need to modify the menu independent of a CMS App.


.. _Django Tutorial: http://docs.djangoproject.com/en/1.6/intro/tutorial01/

.. _Python: http://www.python.org
.. _Django: http://www.djangoproject.com
.. _pip: http://pip.openplans.org/
.. _PIL: http://www.pythonware.com/products/pil/
.. _South: http://south.aeracode.org/
.. _django-classy-tags: https://github.com/ojii/django-classy-tags
