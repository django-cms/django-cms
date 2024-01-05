:sequential_nav: both

.. _plugins_tutorial:

Plugins
=======

In this tutorial we're going to take a basic Django opinion poll application and
integrate it into the CMS.

Create a plugin model
---------------------

In the ``models.py`` of ``polls_cms_integration`` add the following:

.. code-block:: python

    from django.db import models
    from cms.models import CMSPlugin
    from polls.models import Poll


    class PollPluginModel(CMSPlugin):
        poll = models.ForeignKey(Poll, on_delete=models.CASCADE)

        def __str__(self):
            return self.poll.question

This creates a plugin model class; these all inherit from the
:class:`cms.models.pluginmodel.CMSPlugin` base class.

.. note::

    django CMS plugins inherit from :class:`cms.models.pluginmodel.CMSPlugin` (or a
    sub-class thereof) and not :class:`models.Model <django.db.models.Model>`.

Create and run migrations:

.. code-block:: bash

    python manage.py makemigrations polls_cms_integration
    python manage.py migrate polls_cms_integration

The Plugin Class
~~~~~~~~~~~~~~~~

Now create a new file ``cms_plugins.py`` in the same folder your ``models.py`` is in.
The plugin class is responsible for providing django CMS with the necessary information
to render your plugin.

For our poll plugin, we're going to write the following plugin class:

.. code-block:: python

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from polls_cms_integration.models import PollPluginModel
    from django.utils.translation import gettext as _


    @plugin_pool.register_plugin  # register the plugin
    class PollPluginPublisher(CMSPluginBase):
        model = PollPluginModel  # model where plugin data are saved
        module = _("Polls")
        name = _("Poll Plugin")  # name of the plugin in the interface
        render_template = "polls_cms_integration/poll_plugin.html"

        def render(self, context, instance, placeholder):
            context.update({"instance": instance})
            return context

.. note::

    All plugin classes must inherit from :class:`cms.plugin_base.CMSPluginBase` and must
    register themselves with the :class:`plugin_pool <cms.plugin_pool.PluginPool>`.

A reasonable convention for plugin naming is:

- ``PollPluginModel``: the *model* class
- ``PollPluginPublisher``: the *plugin* class

A second convention is also countered quite frequently:

- ``Poll``: the *model* class
- ``PollPlugin``: the *plugin* class

You don't need to follow either of those convention, but choose one that makes sense and
stick to it.

The template
~~~~~~~~~~~~

The ``render_template`` attribute in the plugin class is required, and tells the plugin
which :attr:`render_template <cms.plugin_base.CMSPluginBase.render_template>` to use
when rendering.

In this case the template needs to be at
``polls_cms_integration/templates/polls_cms_integration/poll_plugin.html`` and should
look something like this:

.. code-block:: html+django

    <h1>{{ instance.poll.question }}</h1>

    <form action="{% url 'polls:vote' instance.poll.id %}" method="post">
        {% csrf_token %}
        <div class="form-group">
            {% for choice in instance.poll.choice_set.all %}
                <div class="radio">
                    <label>
                        <input type="radio" name="choice" value="{{ choice.id }}">
                        {{ choice.choice_text }}
                    </label>
                </div>
            {% endfor %}
        </div>
        <input type="submit" value="Vote" />
    </form>

Test the plugin
---------------

Now you can restart the runserver (required because you added the new ``cms_plugins.py``
file, and visit http://localhost:8000/.

You can now drop the ``Poll Plugin`` into any placeholder on any page, just as you would
any other plugin.

.. image:: /introduction/images/poll-plugin-in-menu.png
    :alt: the 'Poll plugin' in the plugin selector
    :width: 400
    :align: center

Next we'll integrate the Polls application more fully into our django CMS project.
