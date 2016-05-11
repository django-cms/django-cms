.. _plugins_tutorial:

#######
Plugins
#######

Our application exists and is installed, but so far, does absolutely nothing at all. In this section we'll add some
new functionality: a Polls plugin.


****************
The Plugin model
****************

In the ``models.py`` of ``polls_cms_integration`` add the following:

.. code-block:: python

    from django.db import models
    from cms.models import CMSPlugin
    from polls.models import Poll


    class PollPluginModel(CMSPlugin):
        poll = models.ForeignKey(Poll)

        def __unicode__(self):
            return self.poll.question

.. note::

    django CMS plugins inherit from :class:`cms.models.CMSPlugin` (or a
    sub-class thereof) and not :class:`models.Model <django.db.models.Model>`.

    ``PollPluginModel`` might seem an odd choice for a model name (that is, with ``model`` in the
    name) but it helps distinguish it from the next class, ``PollPluginPublisher``, that we need to
    create.


****************
The Plugin class
****************

Now create a new file ``cms_plugins.py`` in the same folder your ``models.py`` is in.
The plugin class is responsible for providing django CMS with the necessary
information to render your plugin.

For our poll plugin, we're going to write the following plugin class:

.. code-block:: python

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from polls_cms_integration.models import PollPluginModel
    from django.utils.translation import ugettext as _


    class PollPluginPublisher(CMSPluginBase):
        model = PollPluginModel  # model where plugin data are saved
        module = _("Polls")
        name = _("Poll Plugin")  # name of the plugin in the interface
        render_template = "polls_cms_integration/poll_plugin.html"

        def render(self, context, instance, placeholder):
            context.update({'instance': instance})
            return context

    plugin_pool.register_plugin(PollPluginPublisher)  # register the plugin

.. note::

    All plugin classes must inherit from :class:`cms.plugin_base.CMSPluginBase`
    and must register themselves with the :data:`cms.plugin_pool.plugin_pool`.

A reasonable convention for plugin naming is:

* ``PollPluginModel``: the *model* class
* ``PollPluginPublisher``: the *plugin* class

You don't need to follow this convention, but choose one that makes sense and stick to it.


************
The template
************

The ``render_template`` attribute in the plugin class is required, and tells the plugin which
:attr:`render_template <cms.plugin_base.CMSPluginBase.render_template>` to use when rendering.

In this case the template needs to be at ``polls_cms_integration/templates/polls_cms_integration/poll_plugin.html`` and should look something like this:

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


********************
Prepare the database
********************

Create a database migration to add the plugin table::

    python manage.py makemigrations polls_cms_integration
    python manage.py migrate polls_cms_integration


**********************
Try out the new plugin
**********************

Finally, start the runserver and visit http://localhost:8000/.

You can now drop the ``Poll Plugin`` into any placeholder on any page, just as
you would any other plugin.

.. image:: /introduction/images/poll-plugin-in-menu.png
   :alt: the 'Poll plugin' in the plugin selector
   :width: 400
   :align: center
