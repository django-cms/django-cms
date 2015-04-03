#######
Plugins
#######

In this tutorial we're going to take a Django poll app and integrate it into the CMS.

Install the polls app
#####################

Install the application from its GitHub repository using ``pip -e`` - this also places it in your virtualenv's ``src`` directory as a cloned Git repository::

    pip install -e git+http://git@github.com/divio/django-polls.git#egg=django-polls


You should end up with a folder structure similar to this::

    env/
        src/
            django-polls/
                polls/
                    __init__.py
                    admin.py
                    models.py
                    templates/
                    tests.py
                    urls.py
                    views.py

Let's add it this application to our project. Add ``'polls'`` to the end
of `INSTALLED_APPS` in your project's `settings.py`.

Add the following line to ``urlpatterns`` in the project's ``urls.py``::

    url(r'^polls/', include('polls.urls', namespace='polls')),

Make sure this line is included **before** the line for the django-cms urls::

    url(r'^', include('cms.urls')),

django CMS's URL pattern needs to be last, because it "swallows up" anything
that hasn't already been matched by a previous pattern.

Now run the application's migrations using ``south``::

    python manage.py migrate polls

At this point you should be able to create polls and choices in the Django
admin - localhost:8000/admin/ - and fill them in at ``/polls/``.

However, in pages of the polls application we only have minimal templates, and
no navigation or styling. Let's improve this by overriding the polls
application's base template.

add ``my_site/templates/polls/base.html``::


    {% extends 'base.html' %}

    {% block content %}
        {% block polls_content %}
        {% endblock %}
    {% endblock %}

Open the ``/polls/`` again. The navigation should be visible now.

So now we have integrated the standard polls app in our project. But we've not
done anything django CMS specific yet.

Creating a plugin
#################

If you've played around with the CMS for a little, you've probably already
encountered CMS Plugins. They are the objects you can place into placeholders on
your pages through the frontend: "Text", "Image" and so forth.

We're now going to extend the django poll app so we can embed a poll easily
into any CMS page. We'll put this integration code in a separate package in our
project.

This allows integrating 3rd party apps without having to fork them. It would
also be possible to add this code directly into the django-polls app to make it
integrate out of the box.

Create a new package at the project root called ``polls_plugin``:

    python manage.py startapp polls_plugin

So our workspace looks like this::

    env/
        src/  # the django polls application is in here
    polls_plugin/  # the newly-created application
        __init__.py
        admin.py
        models.py
        tests.py
        views.py
    my_site/
    static/
    project.db
    requirements.txt


The Plugin Model
================

In your poll application’s ``models.py`` add the following::

    from django.db import models
    from cms.models import CMSPlugin
    from polls.models import Poll


    class PollPlugin(CMSPlugin):
        poll = models.ForeignKey(Poll)

        def __unicode__(self):
            return self.poll.question

.. note::

    django CMS plugins inherit from :class:`cms.models.CMSPlugin` (or a
    subclass thereof) and not :class:`models.Model <django.db.models.Model>`.

The Plugin Class
================

Now create a file ``cms_plugins.py`` in the same folder your models.py is in.
The plugin class is responsible for providing django CMS with the necessary
information to render your plugin.

For our poll plugin, we're going to write the following plugin class::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from polls_plugin.models import PollPlugin
    from django.utils.translation import ugettext as _


    class CMSPollPlugin(CMSPluginBase):
        model = PollPlugin  # model where plugin data are saved
        module = _("Polls")
        name = _("Poll Plugin")  # name of the plugin in the interface
        render_template = "djangocms_polls/poll_plugin.html"

        def render(self, context, instance, placeholder):
            context.update({'instance': instance})
            return context

    plugin_pool.register_plugin(CMSPollPlugin)  # register the plugin

.. note::

    All plugin classes must inherit from :class:`cms.plugin_base.CMSPluginBase`
    and must register themselves with the :data:`cms.plugin_pool.plugin_pool`.

The convention for plugin naming is as follows:

* SomePlugin: the *model* class
* CMSSomePlugin: the *plugin* class

You don't need to follow this, but it's a sensible thing to do.

The template
============

The ``render_template`` attribute in the plugin class is required, and tells
the plugin which :attr:`render_template
<cms.plugin_base.CMSPluginBase.render_template>` to use when rendering.

In this case the template needs to be at
``polls_plugin/templates/djangocms_polls/poll_plugin.html`` and should look
something like this::

    <h1>{{ instance.poll.question }}</h1>

    <form action="{% url 'polls:vote' instance.poll.id %}" method="post">
        {% csrf_token %}
        {% for choice in instance.poll.choice_set.all %}
            <input type="radio" name="choice" id="choice{{ forloop.counter }}" value="{{ choice.id }}" />
            <label for="choice{{ forloop.counter }}">{{ choice.choice_text }}</label><br />
        {% endfor %}
        <input type="submit" value="Vote" />
    </form>

Now add ``polls_plugin`` to ``INSTALLED_APPS`` and create a database migration
to add the plugin table (using South)::

    python manage.py schemamigration polls_plugin --init
    python manage.py migrate polls_plugin

Finally, start the runserver and visit http://localhost:8000/.

You can now drop the ``Poll Plugin`` into any placeholder on any page, just as
you would any other plugin.

Next we'll integrate the Polls application more fully into our django CMS
project.
