CMS Plugins
===========

In this part of the tutorial we're going to take the django poll app and
modify it in a way to use it in the CMS.

You can either complete the tutorial here
https://docs.djangoproject.com/en/dev/intro/tutorial01/ or copy the
folder ``polls`` from
`Chive/django-poll-app <https://github.com/Chive/django-poll-app>`__ to
your project root.

You should end up with a folder structure similar to this:

::

    demo/
        env/
        manage.py
        my_demo/
        polls/
            __init__.py
            admin.py
            models.py
            templates/
            tests.py
            urls.py
            views.py
        project.db
        requirements.txt

Our first plugin
----------------

If you've played around with the CMS for a little, you've probably
already encountered CMS Plugins. They are the objects you can fill into
placeholders on your pages through the frontend (e.g. "Text", "Image"
and so forth).

We're now going to modify the django poll app so we can embed a poll
easily into a CMS page.

The Plugin Model
~~~~~~~~~~~~~~~~

In your poll application’s ``models.py`` add the following:

.. code:: python

    from cms.models import CMSPlugin

    class PollPlugin(CMSPlugin):
        poll = models.ForeignKey(Poll)

        def __unicode__(self):
          return self.poll.question

.. note:: django CMS plugin models must inherit from ``cms.models.CMSPlugin``
    (or a subclass thereof) and not ``models.Model``.

The Plugin Class
~~~~~~~~~~~~~~~~

Now create a file ``cms_plugins.py`` in the same folder your models.py
is in. The plugin class is responsible for providing django CMS with the
necessary information to render your plugin.

For our poll plugin, we're going to write the following plugin class:

.. code:: python

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from polls.models import PollPlugin
    from django.utils.translation import ugettext as _

    class CMSPollPlugin(CMSPluginBase):
        model = PollPlugin  # Model where data about this plugin is saved
        name = _("Poll Plugin")  # Name of the plugin
        render_template = "polls/plugin.html"  # template to render the plugin with

        def render(self, context, instance, placeholder):
            context.update({'instance': instance})
            return context

    plugin_pool.register_plugin(PollPlugin)  # register the plugin

.. note:: All plugin classes must inherit from
    ``cms.plugin_base.CMSPluginBase`` and must register themselves with
    the ``cms.plugin_pool.plugin_pool``.

The Template
~~~~~~~~~~~~

You probably noticed the render\_template attribute in the above plugin
class. In order for our plugin to work, we need to set it up first.

The template is located at ``polls/templates/polls/plugin.html`` and
should look something like this:

.. code:: html

    <h1>{{ instance.poll.question }}</h1>

    <form action="{% url polls.views.vote instance.poll.id %}" method="post">
        {% csrf_token %}
        {% for choice in instance.poll.choice_set.all %}
            <input type="radio" name="choice" id="choice{{ forloop.counter }}" value="{{ choice.id }}" />
            <label for="choice{{ forloop.counter }}">{{ choice.choice }}</label><br />
        {% endfor %}
        <input type="submit" value="Vote" />
    </form>

    **Note**: We don’t show the errors here, because when submitting the
    form you’re taken off this page to the actual voting page.

Quite some work done by now, let's add it to our project. Add your polls
plugin to the ``INSTALLED_APPS`` in your projects ``settings.py``:

.. code:: python

    INSTALLED_APPS += ['polls']

Secondly, add the following line to the project's ``urls.py``:

.. code:: python

    url(r'^polls/', include('polls.urls')),

    **Note**: CMS Patterns (``url(r'^', include('cms.urls')),``) must
    always be last entry in the urls.py!

Now to create the initial migrations for our app and migrate them into
the database (using South):

.. code:: bash

    (env) $ python manage.py schemamigration polls --initial
    (env) $ python manage.py migrate polls

Finally, run the server and go visit http://localhost:8000/polls/. Yay!

Next up are :doc:`apps`.