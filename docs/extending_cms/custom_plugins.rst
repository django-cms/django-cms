##############
Custom Plugins
##############

CMS Plugins are reusable content publishers, that can be inserted into django 
CMS pages (or indeed into any content that uses django CMS placeholders) in 
order to publish information automatically, without further intervention.

This means that your published web content, whatever it is, can be kept 
instantly up-to-date at all times. 

It's like magic, but quicker.

Unless you're lucky enough to discover that your needs can be met by the 
built-in plugins, or by the many available 3rd-party plugins, you'll have 
to write your own custom CMS Plugin.

Don't worry though, since writing a CMS Plugin is rather simple.

*************************************
Why would you need to write a plugin?
*************************************

A plugin is the most convenient way to integrate content from another Django 
app into a django CMS page.

For example, suppose you're developing a site for a record company in django 
CMS. You might like to have on your site's home page a "Latest releases" box.

Of course, you could every so often edit that page and update the information. 
However, a sensible record company will manage its catalogue in Django too, 
which means Django already knows what this week's new releases are.

This is an excellent opportunity to make use of that information to make your 
life easier - all you need to do is create a django CMS plugin that you can 
insert into your home page, and leave it to do the work of publishing information 
about the latest releases for you.

Plugins are **reusable**. Perhaps your record company is producing a series of 
reissues of seminal Swiss punk records; on your site's page about the series, 
you could insert the same plugin, configured a little differently, that will 
publish information about recent new releases in that series. 

********
Overview
********

A django CMS plugin is fundamentally composed of three things.

* a plugin **editor**, to configure a plugin each time it is deployed
* a plugin **publisher**, to do the automated work of deciding what to publish
* a plugin **template**, to render the information into a web page

These correspond to the familiar with the Model-View-Template scheme:

* the plugin **model** to store its configuration
* the plugin **view** that works out what needs to be displayed
* the plugin **template** to render the information

And so to build your plugin, you'll make it out of: 

* a subclass of :class:`cms.models.pluginmodel.CMSPlugin` to
  **store the configuration** for your plugin instances
* a subclass of :class:`cms.plugin_base.CMSPluginBase` that **defines
  the operating logic** of your plugin
* a template that **renders your plugin**

A note about :class:`cms.plugin_base.CMSPluginBase`
===================================================

:class:`cms.plugin_base.CMSPluginBase` is actually a subclass of :class:`django.contrib.admin.options.ModelAdmin`.

It is its :meth:`render` method that is the plugin's **view** function.

An aside on models and configuration
====================================

The plugin **model**, the subclass of :class:`cms.models.pluginmodel.CMSPlugin`,
is actually optional.

You could have a plugin that didn't need to be configured, because it only
ever did one thing. 

For example, you could have a plugin that always and only publishes information 
about the top-selling record of the past seven days. Obviously, this wouldn't 
be very flexible - you wouldn't be able to use the same plugin to for the 
best-selling release of the last *month* instead.

Usually, you find that it is useful to be able to configure your plugin, and it
will require a model.


*******************
The simplest plugin
*******************

You may use ``python manage.py startapp`` to set up the basic layout for you
plugin app, alternatively, just add a file called ``cms_plugins.py`` to an
existing Django application.

In there, you place your plugins, in our example the following code::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from cms.models.pluginmodel import CMSPlugin
    from django.utils.translation import ugettext_lazy as _

    class HelloPlugin(CMSPluginBase):
        model = CMSPlugin
        name = _("Hello Plugin")
        render_template = "hello_plugin.html"

        def render(self, context, instance, placeholder):
            return context

    plugin_pool.register_plugin(HelloPlugin)

Now we're almost done, all that's left is adding the template. Add the
following into the root template directory in a file called
``hello_plugin.html``:

.. code-block:: html+django

    <h1>Hello {% if request.user.is_authenticated %}{{ request.user.first_name }} {{ request.user.last_name}}{% else %}Guest{% endif %}</h1>

This plugin will now greet the users on your website either by their name if
they're logged in, or as Guest if they're not.

Now let's take a closer look at what we did there. The ``cms_plugins.py`` files
are where you should define your subclasses of
:class:`cms.plugin_base.CMSPluginBase`, these classes define the different
plugins.

There are three required attributes on those classes:

* ``model``: The model you wish to use to store information about this plugin,
  if you do not require any special information, for example configuration, to
  be stored for your plugins, you may just use
  :class:`cms.models.pluginmodel.CMSPlugin`. We'll look at that model more
  closely in a bit.
* ``name``: The name of your plugin as displayed in the admin. It is generally
  good practice to mark this string as translatable using
  :func:`django.utils.translation.ugettext_lazy`, however this is optional.
* ``render_template``: The template to render this plugin with.

In addition to those three attributes, you must also define a 
:meth:`render` method on your subclasses. It is specifically this `render` 
method that is the **view** for your plugin.

That `render` method takes three arguments:

* ``context``: The context with which the page is rendered.
* ``instance``: The instance of your plugin that is rendered.
* ``placeholder``: The name of the placeholder that is rendered. 

This method must return a dictionary or an instance of
:class:`django.template.Context`, which will be used as context to render the
plugin template.


*********************
Storing configuration
*********************

In many cases, you want to store configuration for your plugin instances, for
example if you have a plugin that shows the latest blog posts, you might want
to be able to choose the amount of entries shown. Another example would be a
gallery plugin, where you want to choose the pictures to show for the plugin.

To do so, you create a Django model by subclassing
:class:`cms.models.pluginmodel.CMSPlugin` in the ``models.py`` of an installed
application.

Let's improve our ``HelloPlugin`` from above by making it configurable what the
fallback name for non-authenticated users should be.

In our ``models.py`` we add following model::

    from cms.models.pluginmodel import CMSPlugin
    
    from django.db import models

    class Hello(CMSPlugin):
        guest_name = models.CharField(max_length=50, default='Guest')


If you followed the Django tutorial, this shouldn't look too new to you. The 
only difference to normal models is that you subclass
:class:`cms.models.pluginmodel.CMSPlugin` rather than
:class:`django.db.models.base.Model`.

Now we need to change our plugin definition to use this model, so our new
``cms_plugins.py`` looks like this::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from django.utils.translation import ugettext_lazy as _
    
    from models import Hello

    class HelloPlugin(CMSPluginBase):
        model = Hello
        name = _("Hello Plugin")
        render_template = "hello_plugin.html"

        def render(self, context, instance, placeholder):
            context['instance'] = instance
            return context

    plugin_pool.register_plugin(HelloPlugin)

We changed the ``model`` attribute to point to our newly created ``Hello``
model and pass the model instance to the context.

As a last step, we have to update our template to make use of this
new configuration:

.. code-block:: html+django

    <h1>Hello {% if request.user.is_authenticated %}{{ request.user.first_name }} {{ request.user.last_name}}{% else %}{{ instance.guest_name }}{% endif %}</h1>

The only thing we changed there is that we use the template variable
``{{ instance.guest_name }}`` instead of the hardcoded ``Guest`` string in the
else clause.

.. warning::

    :class:`cms.models.pluginmodel.CMSPlugin` subclasses cannot be further
    subclassed at the moment. In order to make your plugin models reusable,
    please use abstract base models.

.. warning::
    
    You cannot name your model fields the same as any installed plugins
    lower-cased model name, due to the implicit one-to-one relation Django uses
    for subclassed models. If you use all core plugins, this includes:
    ``file``, ``flash``, ``googlemap``, ``link``, ``picture``, ``snippetptr``,
    ``teaser``, ``twittersearch``, ``twitterrecententries`` and ``video``.

    Additionally, it is *recommended* that you avoid using ``page`` as a model
    field, as it is declared as a property of :class:`cms.models.pluginmodel.CMSPlugin`,
    and your plugin will not work as intended in the administration without
    further work.

Handling Relations
==================

If your custom plugin has foreign key or many-to-many relations you are
responsible for copying those if necessary whenever the CMS copies the plugin.

To do this you can implement a method called
:meth:`cms.models.pluginmodel.CMSPlugin.copy_relations` on your plugin
model which gets the **old** instance of the plugin as argument.

Lets assume this is your plugin::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections =  models.ManyToManyField(Section)

        def __unicode__(self):
            return self.title

Now when the plugin gets copied, you want to make sure the sections stay::

        def copy_relations(self, oldinstance):
            self.sections = oldinstance.sections.all()

Your full model now::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections =  models.ManyToManyField(Section)

        def __unicode__(self):
            return self.title

        def copy_relations(self, oldinstance):
            self.sections = oldinstance.sections.all()


********
Advanced
********


Plugin form
===========

Since :class:`cms.plugin_base.CMSPluginBase` extends
:class:`django.contrib.admin.options.ModelAdmin`, you can customize the form
for your plugins just as you would customize your admin interfaces.

.. note::

    If you want to overwrite the form be sure to extend from
    ``admin/cms/page/plugin_change_form.html`` to have a unified look across the
    plugins and to have the preview functionality automatically installed.

.. _custom-plugins-handling-media:


Handling media
==============

If your plugin depends on certain media files, javascript or stylesheets, you
can include them from your plugin template using `django-sekizai`_. Your CMS
templates are always enforced to have the ``css`` and ``js`` sekizai namespaces,
therefore those should be used to include the respective files. For more 
information about django-sekizai, please refer to the
`django-sekizai documentation`_.

Sekizai style
-------------

To fully harness the power of django-sekizai, it is helpful to have a consistent
style on how to use it. Here is a set of conventions that should, but don't
necessarily need to, be followed:

* One bit per ``addtoblock``. Always include one external CSS or JS file per
  ``addtoblock`` or one snippet per ``addtoblock``. This is needed so
  django-sekizai properly detects duplicate files.
* External files should be on one line, with no spaces or newlines between the
  ``addtoblock`` tag and the HTML tags.
* When using embedded javascript or CSS, the HTML tags should be on a newline.

A **good** example:

.. code-block:: html+django

    {% load sekizai_tags %}
    
    {% addtoblock "js" %}<script type="text/javascript" src="{{ MEDIA_URL }}myplugin/js/myjsfile.js"></script>{% endaddtoblock %}
    {% addtoblock "js" %}<script type="text/javascript" src="{{ MEDIA_URL }}myplugin/js/myotherfile.js"></script>{% endaddtoblock %}
    {% addtoblock "css" %}<link rel="stylesheet" type="text/css" href="{{ MEDIA_URL }}myplugin/css/astylesheet.css"></script>{% endaddtoblock %}
    {% addtoblock "js" %}
    <script type="text/javascript">
        $(document).ready(function(){
            doSomething();
        });
    </script>
    {% endaddtoblock %}

A **bad** example:

.. code-block:: html+django

    {% load sekizai_tags %}
    
    {% addtoblock "js" %}<script type="text/javascript" src="{{ MEDIA_URL }}myplugin/js/myjsfile.js"></script>
    <script type="text/javascript" src="{{ MEDIA_URL }}myplugin/js/myotherfile.js"></script>{% endaddtoblock %}
    {% addtoblock "css" %}
        <link rel="stylesheet" type="text/css" href="{{ MEDIA_URL }}myplugin/css/astylesheet.css"></script>
    {% endaddtoblock %}
    {% addtoblock "js" %}<script type="text/javascript">
        $(document).ready(function(){
            doSomething();
        });
    </script>{% endaddtoblock %}



Plugin Context Processors
=========================

Plugin context processors are callables that modify all plugins' context before
rendering. They are enabled using the :setting:`CMS_PLUGIN_CONTEXT_PROCESSORS`
setting.

A plugin context processor takes 2 arguments:

* ``instance``: The instance of the plugin model
* ``placeholder``: The instance of the placeholder this plugin appears in.

The return value should be a dictionary containing any variables to be added to
the context.

Example::

    def add_verbose_name(instance, placeholder):
        '''
        This plugin context processor adds the plugin model's verbose_name to context.
        '''
        return {'verbose_name': instance._meta.verbose_name}



Plugin Processors
=================

Plugin processors are callables that modify all plugins' output after rendering.
They are enabled using the :setting:`CMS_PLUGIN_PROCESSORS` setting.

A plugin processor takes 4 arguments:

* ``instance``: The instance of the plugin model
* ``placeholder``: The instance of the placeholder this plugin appears in.
* ``rendered_content``: A string containing the rendered content of the plugin.
* ``original_context``: The original context for the template used to render
  the plugin.

.. note:: Plugin processors are also applied to plugins embedded in Text
          plugins (and any custom plugin allowing nested plugins). Depending on
          what your processor does, this might break the output. For example,
          if your processor wraps the output in a ``div`` tag, you might end up
          having ``div`` tags inside of ``p`` tags, which is invalid. You can
          prevent such cases by returning ``rendered_content`` unchanged if
          ``instance._render_meta.text_enabled`` is ``True``, which is the case
          when rendering an embedded plugin.

Example
-------

Suppose you want to put wrap each plugin in the main placeholder in a colored
box, but it would be too complicated to edit each individual plugin's template:

In your ``settings.py``::

    CMS_PLUGIN_PROCESSORS = (
        'yourapp.cms_plugin_processors.wrap_in_colored_box',
    )

In your ``yourapp.cms_plugin_processors.py``::

    def wrap_in_colored_box(instance, placeholder, rendered_content, original_context):
        '''
        This plugin processor wraps each plugin's output in a colored box if it is in the "main" placeholder.
        '''
        # Plugins not in the main placeholder should remain unchanged
        # Plugins embedded in Text should remain unchanged in order not to break output
        if placeholder.slot != 'main' or (instance._render_meta.text_enabled and instance.parent):
            return rendered_content
        else:
            from django.template import Context, Template
            # For simplicity's sake, construct the template from a string:
            t = Template('<div style="border: 10px {{ border_color }} solid; background: {{ background_color }};">{{ content|safe }}</div>')
            # Prepare that template's context:
            c = Context({
                'content': rendered_content,
                # Some plugin models might allow you to customize the colors,
                # for others, use default colors:
                'background_color': instance.background_color if hasattr(instance, 'background_color') else 'lightyellow',
                'border_color': instance.border_color if hasattr(instance, 'border_color') else 'lightblue',
            })
            # Finally, render the content through that template, and return the output
            return t.render(c)


.. _Django admin documentation: http://docs.djangoproject.com/en/1.2/ref/contrib/admin/
.. _django-sekizai: https://github.com/ojii/django-sekizai
.. _django-sekizai documentation: http://django-sekizai.readthedocs.org