.. _custom-plugins:

##############
Custom Plugins
##############

CMS Plugins are reusable content publishers that can be inserted into django
CMS pages (or indeed into any content that uses django CMS placeholders). They
enable the publishing of information automatically, without further
intervention.

This means that your published web content, whatever it is, is kept
up-to-date at all times.

It's like magic, but quicker.

Unless you're lucky enough to discover that your needs can be met by the
built-in plugins, or by the many available third-party plugins, you'll have to
write your own custom CMS Plugin. Don't worry though - writing a CMS Plugin is
rather simple.

*************************************
Why would you need to write a plugin?
*************************************

A plugin is the most convenient way to integrate content from another Django
app into a django CMS page.

For example, suppose you're developing a site for a record company in django
CMS. You might like to have a "Latest releases" box on your site's home page.

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

These correspond to the familiar Model-View-Template scheme:

* the plugin **model** to store its configuration
* the plugin **view** that works out what needs to be displayed
* the plugin **template** to render the information

And so to build your plugin, you'll make it from:

* a sub-class of :class:`cms.models.pluginmodel.CMSPlugin` to
  **store the configuration** for your plugin instances
* a sub-class of :class:`cms.plugin_base.CMSPluginBase` that **defines
  the operating logic** of your plugin
* a template that **renders your plugin**

A note about :class:`cms.plugin_base.CMSPluginBase`
===================================================

:class:`cms.plugin_base.CMSPluginBase` is actually a sub-class of
:class:`django.contrib.admin.options.ModelAdmin`.

Because :class:`CMSPluginBase` sub-classes ``ModelAdmin`` several important
``ModelAdmin`` options are also available to CMS plugin developers. These
options are often used:

* ``exclude``
* ``fields``
* ``fieldsets``
* ``form``
* ``formfield_overrides``
* ``inlines``
* ``radio_fields``
* ``raw_id_fields``
* ``readonly_fields``

Please note, however, that not all ``ModelAdmin`` options are effective in a CMS
plugin. In particular, any options that are used exclusively by the
``ModelAdmin``'s ``changelist`` will have no effect. These and other notable options
that are ignored by the CMS are:

* ``actions``
* ``actions_on_top``
* ``actions_on_bottom``
* ``actions_selection_counter``
* ``date_hierarchy``
* ``list_display``
* ``list_display_links``
* ``list_editable``
* ``list_filter``
* ``list_max_show_all``
* ``list_per_page``
* ``ordering``
* ``paginator``
* ``preserve_fields``
* ``save_as``
* ``save_on_top``
* ``search_fields``
* ``show_full_result_count``
* ``view_on_site``


An aside on models and configuration
====================================

The plugin **model**, the sub-class of :class:`cms.models.pluginmodel.CMSPlugin`,
is actually optional.

You could have a plugin that doesn't need to be configured, because it only
ever does one thing.

For example, you could have a plugin that only publishes information
about the top-selling record of the past seven days. Obviously, this wouldn't
be very flexible - you wouldn't be able to use the same plugin for the
best-selling release of the last *month* instead.

Usually, you find that it is useful to be able to configure your plugin, and this
will require a model.


*******************
The simplest plugin
*******************

You may use ``python manage.py startapp`` to set up the basic layout for you
plugin app (remember to add your plugin to ``INSTALLED_APPS``). Alternatively, just add a file called ``cms_plugins.py`` to an
existing Django application.

In ``cms_plugins.py``, you place your plugins. For our example, include the following code::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from cms.models.pluginmodel import CMSPlugin
    from django.utils.translation import ugettext_lazy as _

    class HelloPlugin(CMSPluginBase):
        model = CMSPlugin
        render_template = "hello_plugin.html"
        cache = False

    plugin_pool.register_plugin(HelloPlugin)

Now we're almost done. All that's left is to add the template. Add the
following into the root template directory in a file called
``hello_plugin.html``:

.. code-block:: html+django

    <h1>Hello {% if request.user.is_authenticated %}{{ request.user.first_name }} {{ request.user.last_name}}{% else %}Guest{% endif %}</h1>

This plugin will now greet the users on your website either by their name if
they're logged in, or as Guest if they're not.

Now let's take a closer look at what we did there. The ``cms_plugins.py`` files
are where you should define your sub-classes of
:class:`cms.plugin_base.CMSPluginBase`, these classes define the different
plugins.

There are two required attributes on those classes:

* ``model``: The model you wish to use for storing information about this plugin.
  If you do not require any special information, for example configuration, to
  be stored for your plugins, you can simply use
  :class:`cms.models.pluginmodel.CMSPlugin` (we'll look at that model more
  closely in a bit). In a normal admin class, you don't need to supply this
  information because ``admin.site.register(Model, Admin)`` takes care of it,
  but a plugin is not registered in that way.
* ``name``: The name of your plugin as displayed in the admin. It is generally
  good practice to mark this string as translatable using
  :func:`django.utils.translation.ugettext_lazy`, however this is optional. By
  default the name is a nicer version of the class name.

And one of the following **must** be defined if ``render_plugin`` attribute
is ``True`` (the default):

* ``render_template``: The template to render this plugin with.

**or**

* ``get_render_template``: A method that returns a template path to render the
  plugin with.

In addition to those attributes, you can also override the :ref:`render` method
which determines the template context variables that are used to render your
plugin. By default, this method only adds ``instance`` and ``placeholder``
objects to your context, but plugins can override this to include any context
that is required.

A number of other methods are available for overriding on your CMSPluginBase
sub-classes. See: :mod:`cms.plugin_base` for further details.


***************
Troubleshooting
***************

Since plugin modules are found and loaded by django's importlib, you might
experience errors because the path environment is different at runtime. If
your `cms_plugins` isn't loaded or accessible, try the following::

    $ python manage.py shell
    >>> from importlib import import_module
    >>> m = import_module("myapp.cms_plugins")
    >>> m.some_test_function()

.. _storing configuration:

*********************
Storing configuration
*********************

In many cases, you want to store configuration for your plugin instances. For
example, if you have a plugin that shows the latest blog posts, you might want
to be able to choose the amount of entries shown. Another example would be a
gallery plugin where you want to choose the pictures to show for the plugin.

To do so, you create a Django model by sub-classing
:class:`cms.models.pluginmodel.CMSPlugin` in the ``models.py`` of an installed
application.

Let's improve our ``HelloPlugin`` from above by making its fallback name for
non-authenticated users configurable.

In our ``models.py`` we add the following::

    from cms.models.pluginmodel import CMSPlugin

    from django.db import models

    class Hello(CMSPlugin):
        guest_name = models.CharField(max_length=50, default='Guest')


If you followed the Django tutorial, this shouldn't look too new to you. The
only difference to normal models is that you sub-class
:class:`cms.models.pluginmodel.CMSPlugin` rather than
:class:`django.db.models.base.Model`.

Now we need to change our plugin definition to use this model, so our new
``cms_plugins.py`` looks like this::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from django.utils.translation import ugettext_lazy as _

    from .models import Hello

    class HelloPlugin(CMSPluginBase):
        model = Hello
        name = _("Hello Plugin")
        render_template = "hello_plugin.html"
        cache = False

        def render(self, context, instance, placeholder):
            context = super(HelloPlugin, self).render(context, instance, placeholder)
            return context

    plugin_pool.register_plugin(HelloPlugin)

We changed the ``model`` attribute to point to our newly created ``Hello``
model and pass the model instance to the context.

As a last step, we have to update our template to make use of this
new configuration:

.. code-block:: html+django

    <h1>Hello {% if request.user.is_authenticated %}
      {{ request.user.first_name }} {{ request.user.last_name}}
    {% else %}
      {{ instance.guest_name }}
    {% endif %}</h1>

The only thing we changed there is that we use the template variable ``{{
instance.guest_name }}`` instead of the hard-coded ``Guest`` string in the else
clause.

.. warning::

    You cannot name your model fields the same as any installed plugins lower-
    cased model name, due to the implicit one-to-one relation Django uses for
    sub-classed models. If you use all core plugins, this includes: ``file``,
    ``googlemap``, ``link``, ``picture``, ``snippetptr``, ``teaser``,
    ``twittersearch``, ``twitterrecententries`` and ``video``.

    Additionally, it is *recommended* that you avoid using ``page`` as a model
    field, as it is declared as a property of :class:`cms.models.pluginmodel.CMSPlugin`,
    and your plugin will not work as intended in the administration without
    further work.

.. warning::

    If you are using Python 2.x and overriding the ``__unicode__`` method of the
    model file, make sure to return its results as UTF8-string. Otherwise
    saving an instance of your plugin might fail with the frontend editor showing
    an <Empty> plugin instance. To return in Unicode use a return statement like
    ``return u'{0}'.format(self.guest_name)``.

.. _handling-relations:

Handling Relations
==================

Every time the page with your custom plugin is published the plugin is copied.
So if your custom plugin has foreign key (to it, or from it) or many-to-many
relations you are responsible for copying those related objects, if required,
whenever the CMS copies the plugin - **it won't do it for you automatically**.

Every plugin model inherits the empty
:meth:`cms.models.pluginmodel.CMSPlugin.copy_relations` method from the base
class, and it's called when your plugin is copied. So, it's there for you to
adapt to your purposes as required.

Typically, you will want it to copy related objects. To do this you should
create a method called ``copy_relations`` on your plugin model, that receives
the **old** instance of the plugin as an argument.

You may however decide that the related objects shouldn't be copied - you may
want to leave them alone, for example. Or, you might even want to choose some
altogether different relations for it, or to create new ones when it's
copied... it depends on your plugin and the way you want it to work.

If you do want to copy related objects, you'll need to do this in two slightly
different ways, depending on whether your plugin has relations *to* or *from*
other objects that need to be copied too:

For foreign key relations *from* other objects
----------------------------------------------

Your plugin may have items with foreign keys to it, which will typically be
the case if you set it up so that they are inlines in its admin. So you might
have two models, one for the plugin and one for those items::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)

    class AssociatedItem(models.Model):
        plugin = models.ForeignKey(
            ArticlePluginModel,
            related_name="associated_item"
        )

You'll then need the ``copy_relations()`` method on your plugin model to loop
over the associated items and copy them, giving the copies foreign keys to the
new plugin::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)

        def copy_relations(self, oldinstance):
            for associated_item in oldinstance.associated_item.all():
                # instance.pk = None; instance.pk.save() is the slightly odd but
                # standard Django way of copying a saved model instance
                associated_item.pk = None
                associated_item.plugin = self
                associated_item.save()

For many-to-many or foreign key relations *to* other objects
------------------------------------------------------------

Let's assume these are the relevant bits of your plugin::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections = models.ManyToManyField(Section)

Now when the plugin gets copied, you want to make sure the sections stay, so
it becomes::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections = models.ManyToManyField(Section)

        def copy_relations(self, oldinstance):
            self.sections = oldinstance.sections.all()

If your plugins have relational fields of both kinds, you may of course need
to use *both* the copying techniques described above.

Relations *between* plugins
---------------------------

It is much harder to manage the copying of relations when they are from one plugin to another.

See the GitHub issue `copy_relations() does not work for relations between cmsplugins #4143
<https://github.com/divio/django-cms/issues/4143>`_ for more details.

********
Advanced
********

Inline Admin
============

If you want to have the foreign key relation as a inline admin, you can create an
``admin.StackedInline`` class and put it in the Plugin to "inlines". Then you can use the inline
admin form for your foreign key references::

    class ItemInlineAdmin(admin.StackedInline):
        model = AssociatedItem


    class ArticlePlugin(CMSPluginBase):
        model = ArticlePluginModel
        name = _("Article Plugin")
        render_template = "article/index.html"
        inlines = (ItemInlineAdmin,)

        def render(self, context, instance, placeholder):
            context = super(ArticlePlugin, self).render(context, instance, placeholder)
            items = instance.associated_item.all()
            context.update({
                'items': items,
            })
            return context

Plugin form
===========

Since :class:`cms.plugin_base.CMSPluginBase` extends
:class:`django.contrib.admin.options.ModelAdmin`, you can customise the form
for your plugins just as you would customise your admin interfaces.

The template that the plugin editing mechanism uses is
``cms/templates/admin/cms/page/plugin/change_form.html``. You might need to
change this.

If you want to customise this the best way to do it is:

* create a template of your own that extends ``cms/templates/admin/cms/page/plugin/change_form.html``
  to provide the functionality you require;
* provide your :class:`cms.plugin_base.CMSPluginBase` sub-class with a
  ``change_form_template`` attribute pointing at your new template.

Extending ``admin/cms/page/plugin/change_form.html`` ensures that you'll keep
a unified look and functionality across your plugins.

There are various reasons *why* you might want to do this. For example, you
might have a snippet of JavaScript that needs to refer to a template
variable), which you'd likely place in ``{% block extrahead %}``, after a ``{{
block.super }}`` to inherit the existing items that were in the parent
template.

Or: ``cms/templates/admin/cms/page/plugin/change_form.html`` extends Django's
own ``admin/base_site.html``, which loads a rather elderly version of jQuery,
and your plugin admin might require something newer. In this case, in your
custom ``change_form_template`` you could do something like::

    {% block jquery %}
        <script type="text/javascript" src="///ajax.googleapis.com/ajax/libs/jquery/1.8.0/jquery.min.js" type="text/javascript"></script>
    {% endblock jquery %}``

to override the ``{% block jquery %}``.

.. _custom-plugins-handling-media:


Handling media
==============

If your plugin depends on certain media files, JavaScript or stylesheets, you
can include them from your plugin template using `django-sekizai`_. Your CMS
templates are always enforced to have the ``css`` and ``js`` sekizai namespaces,
therefore those should be used to include the respective files. For more
information about django-sekizai, please refer to the
`django-sekizai documentation`_.

Note that sekizai *can't* help you with the *admin-side* plugin templates -
what follows is for your plugins' *output* templates.

Sekizai style
-------------

To fully harness the power of django-sekizai, it is helpful to have a consistent
style on how to use it. Here is a set of conventions that should be followed
(but don't necessarily need to be):

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
    {% addtoblock "css" %}<link rel="stylesheet" type="text/css" href="{{ MEDIA_URL }}myplugin/css/astylesheet.css">{% endaddtoblock %}
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


.. _plugin-context-processors:


Plugin Context
==============

The plugin has access to the django template context. You can override
variables using the ``with`` tag.

Example::

    {% with 320 as width %}{% placeholder "content" %}{% endwith %}


Plugin Context Processors
=========================

Plugin context processors are callables that modify all plugins' context before
rendering. They are enabled using the :setting:`CMS_PLUGIN_CONTEXT_PROCESSORS`
setting.

A plugin context processor takes 3 arguments:

* ``instance``: The instance of the plugin model
* ``placeholder``: The instance of the placeholder this plugin appears in.
* ``context``: The context that is in use, including the request.

The return value should be a dictionary containing any variables to be added to
the context.

Example::

    def add_verbose_name(instance, placeholder, context):
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

Suppose you want to wrap each plugin in the main placeholder in a colored box
but it would be too complicated to edit each individual plugin's template:

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
                # Some plugin models might allow you to customise the colors,
                # for others, use default colors:
                'background_color': instance.background_color if hasattr(instance, 'background_color') else 'lightyellow',
                'border_color': instance.border_color if hasattr(instance, 'border_color') else 'lightblue',
            })
            # Finally, render the content through that template, and return the output
            return t.render(c)


.. _Django admin documentation: http://docs.djangoproject.com/en/dev/ref/contrib/admin/
.. _django-sekizai: https://github.com/ojii/django-sekizai
.. _django-sekizai documentation: http://django-sekizai.readthedocs.org


Nested Plugins
==============

You can nest CMS Plugins in themselves. There's a few things required to
achieve this functionality:

``models.py``:

.. code-block:: python

    class ParentPlugin(CMSPlugin):
        # add your fields here

    class ChildPlugin(CMSPlugin):
        # add your fields here


``cms_plugins.py``:

.. code-block:: python

    from .models import ParentPlugin, ChildPlugin

    class ParentCMSPlugin(CMSPluginBase):
        render_template = 'parent.html'
        name = 'Parent'
        model = ParentPlugin
        allow_children = True  # This enables the parent plugin to accept child plugins
        # You can also specify a list of plugins that are accepted as children,
        # or leave it away completely to accept all
        # child_classes = ['ChildCMSPlugin']

        def render(self, context, instance, placeholder):
            context = super(ParentCMSPlugin, self).render(context, instance, placeholder)
            return context

    plugin_pool.register_plugin(ParentCMSPlugin)


    class ChildCMSPlugin(CMSPluginBase):
        render_template = 'child.html'
        name = 'Child'
        model = ChildPlugin
        require_parent = True  # Is it required that this plugin is a child of another plugin?
        # You can also specify a list of plugins that are accepted as parents,
        # or leave it away completely to accept all
        # parent_classes = ['ParentCMSPlugin']

        def render(self, context, instance, placeholder):
            context = super(ChildCMSPlugin, self).render(context, instance, placeholder)
            return context

    plugin_pool.register_plugin(ChildCMSPlugin)


``parent.html``:

.. code-block:: html+django

    {% load cms_tags %}

    <div class="plugin parent">
        {% for plugin in instance.child_plugin_instances %}
            {% render_plugin plugin %}
        {% endfor %}
    </div>


`child.html`:

.. code-block:: html+django

    <div class="plugin child">
        {{ instance }}
    </div>


.. _extending_context_menus:

Extending context menus of placeholders or plugins
==================================================

There are three possibilities to extend the context menus
of placeholders or plugins.

* You can either extend a placeholder context menu.
* You can extend all plugin context menus.
* You can extend the current plugin context menu.

For this purpose you can overwrite 3 methods on CMSPluginBase.

* :ref:`get_extra_placeholder_menu_items`
* :ref:`get_extra_global_plugin_menu_items`
* :ref:`get_extra_local_plugin_menu_items`

Example::

    class AliasPlugin(CMSPluginBase):
        name = _("Alias")
        allow_children = False
        model = AliasPluginModel
        render_template = "cms/plugins/alias.html"

        def render(self, context, instance, placeholder):
            context = super(AliasPlugin, self).render(context, instance, placeholder)
            if instance.plugin_id:
                plugins = instance.plugin.get_descendants(include_self=True).order_by('placeholder', 'tree_id', 'level',
                                                                                      'position')
                plugins = downcast_plugins(plugins)
                plugins[0].parent_id = None
                plugins = build_plugin_tree(plugins)
                context['plugins'] = plugins
            if instance.alias_placeholder_id:
                content = render_placeholder(instance.alias_placeholder, context)
                print content
                context['content'] = mark_safe(content)
            return context

        def get_extra_global_plugin_menu_items(self, request, plugin):
            return [
                PluginMenuItem(
                    _("Create Alias"),
                    reverse("admin:cms_create_alias"),
                    data={'plugin_id': plugin.pk, 'csrfmiddlewaretoken': get_token(request)},
                )
            ]

        def get_extra_placeholder_menu_items(self, request, placeholder):
            return [
                PluginMenuItem(
                    _("Create Alias"),
                    reverse("admin:cms_create_alias"),
                    data={'placeholder_id': placeholder.pk, 'csrfmiddlewaretoken': get_token(request)},
                )
            ]

        def get_plugin_urls(self):
            urlpatterns = [
                url(r'^create_alias/$', self.create_alias, name='cms_create_alias'),
            ]
            return urlpatterns

        def create_alias(self, request):
            if not request.user.is_staff:
                return HttpResponseForbidden("not enough privileges")
            if not 'plugin_id' in request.POST and not 'placeholder_id' in request.POST:
                return HttpResponseBadRequest("plugin_id or placeholder_id POST parameter missing.")
            plugin = None
            placeholder = None
            if 'plugin_id' in request.POST:
                pk = request.POST['plugin_id']
                try:
                    plugin = CMSPlugin.objects.get(pk=pk)
                except CMSPlugin.DoesNotExist:
                    return HttpResponseBadRequest("plugin with id %s not found." % pk)
            if 'placeholder_id' in request.POST:
                pk = request.POST['placeholder_id']
                try:
                    placeholder = Placeholder.objects.get(pk=pk)
                except Placeholder.DoesNotExist:
                    return HttpResponseBadRequest("placeholder with id %s not found." % pk)
                if not placeholder.has_change_permission(request):
                    return HttpResponseBadRequest("You do not have enough permission to alias this placeholder.")
            clipboard = request.toolbar.clipboard
            clipboard.cmsplugin_set.all().delete()
            language = request.LANGUAGE_CODE
            if plugin:
                language = plugin.language
            alias = AliasPluginModel(language=language, placeholder=clipboard, plugin_type="AliasPlugin")
            if plugin:
                alias.plugin = plugin
            if placeholder:
                alias.alias_placeholder = placeholder
            alias.save()
            return HttpResponse("ok")


.. _plugin-datamigrations-3.1:

Plugin data migrations
======================

Due to the migration from Django MPTT to django-treebeard in version 3.1, the plugin model is
different between the two versions. Schema migrations are not affected as the migration systems
(both South and Django) detects the different bases.

Data migrations are a different story, though.

If your data migration does something like:

.. code-block:: django

    MyPlugin = apps.get_model('my_app', 'MyPlugin')

    for plugin in MyPlugin.objects.all():
        ... do something ...

You may end up with an error like
``django.db.utils.OperationalError: (1054, "Unknown column 'cms_cmsplugin.level' in 'field list'")``
because depending on the order the migrations are executed, the historical models may be out of
sync with the applied database schema.

To keep compatibility with 3.0 and 3.x you can force the data migration to run before the django CMS
migration that creates treebeard fields, by doing this the data migration will always be executed
on the "old" database schema and no conflict will exist.

For South migrations add this:

.. code-block:: django

    from distutils.version import LooseVersion
    import cms
    USES_TREEBEARD = LooseVersion(cms.__version__) >= LooseVersion('3.1')

    class Migration(DataMigration):

        if USES_TREEBEARD:
            needed_by = [
                ('cms', '0070_auto__add_field_cmsplugin_path__add_field_cmsplugin_depth__add_field_c')
            ]


For Django migrations add this:

.. code-block:: django

    from distutils.version import LooseVersion
    import cms
    USES_TREEBEARD = LooseVersion(cms.__version__) >= LooseVersion('3.1')

    class Migration(migrations.Migration):

        if USES_TREEBEARD:
            run_before = [
                ('cms', '0004_auto_20140924_1038')
            ]
