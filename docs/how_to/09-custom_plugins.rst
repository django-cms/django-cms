.. _custom-plugins:

How to create Plugins
=====================

The simplest plugin
-------------------

We'll start with an example of a very simple plugin.

You may use ``python -m manage startapp`` to set up the basic layout for your plugin app
(remember to add your plugin to ``INSTALLED_APPS``). Alternatively, just add a file
called ``cms_plugins.py`` to an existing Django application.

Place your plugins in ``cms_plugins.py``. For our example, include the following code:

.. code-block::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from cms.models.pluginmodel import CMSPlugin
    from django.utils.translation import gettext_lazy as _

    @plugin_pool.register_plugin
    class HelloPlugin(CMSPluginBase):
        model = CMSPlugin
        render_template = "hello_plugin.html"
        cache = False

Now we're almost done. All that's left is to add the template. Add the following into
the root template directory in a file called ``hello_plugin.html``:

.. code-block:: html+django

    <h1>Hello {% if request.user.is_authenticated %}{{ request.user.first_name }} {{ request.user.last_name}}{% else %}Guest{% endif %}</h1>

This plugin will now greet the users on your website either by their name if they're
logged in, or as Guest if they're not.

Now let's take a closer look at what we did there. The ``cms_plugins.py`` files are
where you should define your sub-classes of :class:`cms.plugin_base.CMSPluginBase`,
these classes define the different plugins.

There are two required attributes on those classes:

- ``model``: The model you wish to use for storing information about this plugin. If you
  do not require any special information, for example configuration, to be stored for
  your plugins, you can simply use :class:`cms.models.pluginmodel.CMSPlugin` (we'll look
  at that model more closely in a bit). In a normal admin class, you don't need to
  supply this information because ``admin.site.register(Model, Admin)`` takes care of
  it, but a plugin is not registered in that way.
- ``name``: The name of your plugin as displayed in the admin. It is generally good
  practice to mark this string as translatable using
  :func:`django.utils.translation.gettext_lazy`, however this is optional. By default
  the name is a nicer version of the class name.

And one of the following **must** be defined if ``render_plugin`` attribute is ``True``
(the default):

- ``render_template``: The template to render this plugin with.

**or**

- ``get_render_template``: A method that returns a template path to render the plugin
  with.

In addition to those attributes, you can also override the
:meth:`~cms.plugin_base.CMSPluginBase.render()` method which determines the template
context variables that are used to render your plugin. By default, this method only adds
``instance`` and ``placeholder`` objects to your context, but plugins can override this
to include any context that is required.

A number of other methods are available for overriding on your CMSPluginBase
sub-classes. See: :class:`~cms.plugin_base.CMSPluginBase` for further details.

Troubleshooting
---------------

Since plugin modules are found and loaded by django's importlib, you might experience
errors because the path environment is different at runtime. If your `cms_plugins` isn't
loaded or accessible, try the following:

.. code-block::

    $ python -m manage shell
    >>> from importlib import import_module
    >>> m = import_module("myapp.cms_plugins")
    >>> m.some_test_function()  # from the myapp.cms_plugins module

.. _storing configuration:

Storing configuration
---------------------

In many cases, you want to store configuration for your plugin instances. For example,
if you have a plugin that shows the latest blog posts, you might want to be able to
choose the amount of entries shown. Another example would be a gallery plugin where you
want to choose the pictures to show for the plugin.

To do so, you create a Django model by sub-classing
:class:`cms.models.pluginmodel.CMSPlugin` in the ``models.py`` of an installed
application.

Let's improve our ``HelloPlugin`` from above by making its fallback name for
non-authenticated users configurable.

In our ``models.py`` we add the following:

.. code-block::

    from cms.models.pluginmodel import CMSPlugin

    from django.db import models

    class Hello(CMSPlugin):
        guest_name = models.CharField(max_length=50, default='Guest')

If you followed the Django tutorial, this shouldn't look too new to you. The only
difference to normal models is that you sub-class
:class:`cms.models.pluginmodel.CMSPlugin` rather than :class:`django.db.models.Model`.

Now we need to change our plugin definition to use this model, so our new
``cms_plugins.py`` looks like this:

.. code-block::

    from cms.plugin_base import CMSPluginBase
    from cms.plugin_pool import plugin_pool
    from django.utils.translation import gettext_lazy as _

    from .models import Hello

    @plugin_pool.register_plugin
    class HelloPlugin(CMSPluginBase):
        model = Hello
        name = _("Hello Plugin")
        render_template = "hello_plugin.html"
        cache = False

        def render(self, context, instance, placeholder):
            context = super().render(context, instance, placeholder)
            return context

We changed the ``model`` attribute to point to our newly created ``Hello`` model and
pass the model instance to the context.

As a last step, we have to update our template to make use of this new configuration:

.. code-block:: html+django

    <h1>Hello {% if request.user.is_authenticated %}
      {{ request.user.first_name }} {{ request.user.last_name}}
    {% else %}
      {{ instance.guest_name }}
    {% endif %}</h1>

The only thing we changed there is that we use the template variable ``{{
instance.guest_name }}`` instead of the hard-coded ``Guest`` string in the else clause.

.. warning::

    You cannot name your model fields the same as any installed plugins lower- cased
    model name, due to the implicit one-to-one relation Django uses for sub-classed
    models. If you use all core plugins, this includes: ``file``, ``googlemap``,
    ``link``, ``picture``, ``snippetptr``, ``teaser``, ``twittersearch``,
    ``twitterrecententries`` and ``video``.

    Additionally, it is *recommended* that you avoid using ``page`` as a model field, as
    it is declared as a property of :class:`cms.models.pluginmodel.CMSPlugin`. While the
    use of ``CMSPlugin.page`` is deprecated the property still exists as a compatibility
    shim.

.. _handling-relations:

Handling Relations
~~~~~~~~~~~~~~~~~~

Some user interactions make it necessary to create a copy of the plugin, most notably if
a user copies and pastes contents of a placeholder. So if your custom plugin has foreign
key (to it, or from it) or many-to-many relations you are responsible for copying those
related objects, if required, whenever the CMS copies the plugin - **it won't do it for
you automatically**.

Every plugin model inherits the empty
:meth:`cms.models.pluginmodel.CMSPlugin.copy_relations` method from the base class, and
it's called when your plugin is copied. So, it's there for you to adapt to your purposes
as required.

Typically, you will want it to copy related objects. To do this you should create a
method called ``copy_relations`` on your plugin model, that receives the **old
instance** of the plugin as an argument.

You may however decide that the related objects shouldn't be copied - you may want to
leave them alone, for example. Or, you might even want to choose some altogether
different relations for it, or to create new ones when it's copied... it depends on your
plugin and the way you want it to work.

If you do want to copy related objects, you'll need to do this in two slightly different
ways, depending on whether your plugin has relations *to* or *from* other objects that
need to be copied too:

For foreign key relations *from* other objects
++++++++++++++++++++++++++++++++++++++++++++++

Your plugin may have items with foreign keys to it, which will typically be the case if
you set it up so that they are inlines in its admin. So you might have two models, one
for the plugin and one for those items:

.. code-block::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)

    class AssociatedItem(models.Model):
        plugin = models.ForeignKey(
            ArticlePluginModel,
            related_name="associated_item"
        )

You'll then need the ``copy_relations()`` method on your plugin model to loop over the
associated items and copy them, giving the copies foreign keys to the new plugin:

.. code-block::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)

        def copy_relations(self, oldinstance):
            # Before copying related objects from the old instance, the ones
            # on the current one need to be deleted. Otherwise, duplicates may
            # appear on the public version of the page
            self.associated_item.all().delete()

            for associated_item in oldinstance.associated_item.all():
                # instance.pk = None; instance.pk.save() is the slightly odd but
                # standard Django way of copying a saved model instance
                associated_item.pk = None
                associated_item.plugin = self
                associated_item.save()

For many-to-many or foreign key relations *to* other objects
++++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

Let's assume these are the relevant bits of your plugin:

.. code-block::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections = models.ManyToManyField(Section)

Now when the plugin gets copied, you want to make sure the sections stay, so it becomes:

.. code-block::

    class ArticlePluginModel(CMSPlugin):
        title = models.CharField(max_length=50)
        sections = models.ManyToManyField(Section)

        def copy_relations(self, oldinstance):
            self.sections.set(oldinstance.sections.all())

If your plugins have relational fields of both kinds, you may of course need to use
*both* the copying techniques described above.

Relations *between* plugins
+++++++++++++++++++++++++++

It is much harder to manage the copying of relations when they are from one plugin to
another.

See the GitHub issue `copy_relations() does not work for relations between cmsplugins
#4143 <https://github.com/django-cms/django-cms/issues/4143>`_ for more details.

Advanced
--------

Inline Admin
~~~~~~~~~~~~

If you want to have the foreign key relation as a inline admin, you can create an
``admin.StackedInline`` class and put it in the Plugin to "inlines". Then you can use
the inline admin form for your foreign key references:

.. code-block::

    class ItemInlineAdmin(admin.StackedInline):
        model = AssociatedItem


    class ArticlePlugin(CMSPluginBase):
        model = ArticlePluginModel
        name = _("Article Plugin")
        render_template = "article/index.html"
        inlines = (ItemInlineAdmin,)

        def render(self, context, instance, placeholder):
            context = super().render(context, instance, placeholder)
            items = instance.associated_item.all()
            context.update({
                'items': items,
            })
            return context

Plugin form
~~~~~~~~~~~

Since :class:`cms.plugin_base.CMSPluginBase` extends
:class:`django:django.contrib.admin.ModelAdmin`, you can customise the form for your
plugins just as you would customise your admin interfaces.

The template that the plugin editing mechanism uses is
``cms/templates/admin/cms/page/plugin/change_form.html``. You might need to change this.

If you want to customise this the best way to do it is:

- create a template of your own that extends
  ``cms/templates/admin/cms/page/plugin/change_form.html`` to provide the functionality
  you require;
- provide your :class:`cms.plugin_base.CMSPluginBase` sub-class with a
  ``change_form_template`` attribute pointing at your new template.

Extending ``admin/cms/page/plugin/change_form.html`` ensures that you'll keep a unified
look and functionality across your plugins.

There are various reasons *why* you might want to do this. For example, you might have a
snippet of JavaScript that needs to refer to a template variable), which you'd likely
place in ``{% block extrahead %}``, after a ``{{ block.super }}`` to inherit the
existing items that were in the parent template.

.. _custom-plugins-handling-media:

Handling media
~~~~~~~~~~~~~~

If your plugin depends on certain media files, JavaScript or stylesheets, you can
include them from your plugin template using django-sekizai_. Your CMS templates are
always enforced to have the ``css`` and ``js`` sekizai namespaces, therefore those
should be used to include the respective files. For more information about
django-sekizai, please refer to the `django-sekizai documentation`_.

Note that sekizai **can't** help you with the **admin-side** plugin templates - what
follows is for your plugins' **output templates**.

Sekizai style
+++++++++++++

To fully harness the power of django-sekizai, it is helpful to have a consistent style
on how to use it. Here is a set of conventions that should be followed (but don't
necessarily need to be):

- One bit per ``addtoblock``. Always include one external CSS or JS file per
  ``addtoblock`` or one snippet per ``addtoblock``. This is needed so django-sekizai
  properly detects duplicate files.
- External files should be on one line, with no spaces or newlines between the
  ``addtoblock`` tag and the HTML tags.
- When using embedded javascript or CSS, the HTML tags should be on a newline.

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

.. note::

    If the Plugin requires javascript code to be rendered properly, the class
    ``'cms-execute-js-to-render'`` can be added to the script tag. This will download
    and execute all scripts with this class, which weren't present before, when the
    plugin is first added to the page. If the javascript code is protected from
    prematurely executing by the EventListener for the event ``'load'`` and/or
    ``'DOMContentLoaded'``, the following classes can be added to the script tag:

    =========================================== =============================
    Classname                                   Corresponding javascript code
    =========================================== =============================
    cms-trigger-event-document-DOMContentLoaded ``document.dispatchEvent(new
                                                Event('DOMContentLoaded')``
    cms-trigger-event-window-DOMContentLoaded   ``window.dispatchEvent(new
                                                Event('DOMContentLoaded')``
    cms-trigger-event-window-load               ``window.dispatchEvent(new
                                                Event('load')``
    =========================================== =============================

    The events will be triggered once after all scripts are successfully injected into
    the DOM.

.. note::

    Some plugins might need to run a certain bit of javascript after a content refresh.
    In such a case, you can use the ``cms-content-refresh`` event to take care of that,
    by adding something like:

    .. code-block:: html+django

        {% if request.toolbar and request.toolbar.edit_mode_active %}
            <script>
            CMS.$(window).on('cms-content-refresh', function () {
                // Here comes your code of the plugin's javascript which
                // needs to be run after a content refresh
            });
            </script>
        {% endif %}

.. _plugin-context-processors:

Plugin Context
~~~~~~~~~~~~~~

The plugin has access to the django template context. You can override variables using
the ``with`` tag.

Example:

.. code-block::

    {% with 320 as width %}{% placeholder "content" %}{% endwith %}

Plugin Context Processors
~~~~~~~~~~~~~~~~~~~~~~~~~

Plugin context processors are callables that modify all plugins' context before
rendering. They are enabled using the :setting:`CMS_PLUGIN_CONTEXT_PROCESSORS` setting.

A plugin context processor takes 3 arguments:

- ``instance``: The instance of the plugin model
- ``placeholder``: The instance of the placeholder this plugin appears in.
- ``context``: The context that is in use, including the request.

The return value should be a dictionary containing any variables to be added to the
context.

Example:

.. code-block::

    def add_verbose_name(instance, placeholder, context):
        '''
        This plugin context processor adds the plugin model's verbose_name to context.
        '''
        return {'verbose_name': instance._meta.verbose_name}

Plugin Processors
~~~~~~~~~~~~~~~~~

Plugin processors are callables that modify all plugins' output after rendering. They
are enabled using the :setting:`CMS_PLUGIN_PROCESSORS` setting.

A plugin processor takes 4 arguments:

- ``instance``: The instance of the plugin model
- ``placeholder``: The instance of the placeholder this plugin appears in.
- ``rendered_content``: A string containing the rendered content of the plugin.
- ``original_context``: The original context for the template used to render the plugin.

.. note::

    Plugin processors are also applied to plugins embedded in Text plugins (and any
    custom plugin allowing nested plugins). Depending on what your processor does, this
    might break the output. For example, if your processor wraps the output in a
    ``<div>`` tag, you might end up having ``<div>`` tags inside of ``<p>`` tags, which
    is invalid. You can prevent such cases by returning ``rendered_content`` unchanged
    if ``instance._render_meta.text_enabled`` is ``True``, which is the case when
    rendering an embedded plugin.

Example
+++++++

Suppose you want to wrap each plugin in the main placeholder in a colored box but it
would be too complicated to edit each individual plugin's template:

In your ``settings.py``:

.. code-block::

    CMS_PLUGIN_PROCESSORS = (
        'yourapp.cms_plugin_processors.wrap_in_colored_box',
    )

In your ``yourapp.cms_plugin_processors.py``:

.. code-block::

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

.. _django admin documentation: http://docs.djangoproject.com/en/dev/ref/contrib/admin/

.. _django-sekizai: https://github.com/ojii/django-sekizai

.. _django-sekizai documentation: https://django-sekizai.readthedocs.io

Nested Plugins
~~~~~~~~~~~~~~

You can nest CMS Plugins in themselves. There's a few things required to achieve this
functionality:

``models.py``:

.. code-block:: python

    class ParentPlugin(CMSPlugin):
        # add your fields here

    class ChildPlugin(CMSPlugin):
        # add your fields here

``cms_plugins.py``:

.. code-block:: python

    from .models import ParentPlugin, ChildPlugin


    @plugin_pool.register_plugin
    class ParentCMSPlugin(CMSPluginBase):
        render_template = "parent.html"
        name = "Parent"
        model = ParentPlugin
        allow_children = True  # This enables the parent plugin to accept child plugins
        # You can also specify a list of plugins that are accepted as children,
        # or leave it away completely to accept all
        # child_classes = ['ChildCMSPlugin']

        def render(self, context, instance, placeholder):
            context = super().render(context, instance, placeholder)
            return context


    @plugin_pool.register_plugin
    class ChildCMSPlugin(CMSPluginBase):
        render_template = "child.html"
        name = "Child"
        model = ChildPlugin
        require_parent = (
            True  # Is it required that this plugin is a child of another plugin?
        )
        # You can also specify a list of plugins that are accepted as parents,
        # or leave it away completely to accept all
        # parent_classes = ['ParentCMSPlugin']

        def render(self, context, instance, placeholder):
            context = super(ChildCMSPlugin, self).render(context, instance, placeholder)
            return context

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

If you have attributes of the parent plugin which you need to access in the child you
can access the parent instance using ``get_bound_plugin``:

.. code-block:: django

    class ChildPluginForm(forms.ModelForm):

        class Meta:
            model = ChildPlugin
            exclude = ()

        def __init__(self, *args, **kwargs):
            super().__init__(*args, **kwargs)
            if self.instance:
                parent, parent_cls = self.instance.parent.get_bound_plugin()

.. _extending_context_menus:

Extending context menus of placeholders or plugins
~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~

There are three possibilities to extend the context menus of placeholders or plugins.

- You can either extend a placeholder context menu.
- You can extend all plugin context menus.

For this purpose you can overwrite the two methods on CMSPluginBase.

- :meth:`~cms.plugin_base.CMSPluginBase.get_extra_placeholder_menu_items`
- :meth:`~cms.plugin_base.CMSPluginBase.get_extra_plugin_menu_items`

Example:

.. code-block::

    class AliasPlugin(CMSPluginBase):
        name = _("Alias")
        allow_children = False
        model = AliasPluginModel
        render_template = "cms/plugins/alias.html"

        def render(self, context, instance, placeholder):
            context = super().render(context, instance, placeholder)
            if instance.plugin_id:
                plugins = instance.plugin.get_descendants(
                    include_self=True
                ).order_by('placeholder', 'tree_id', 'level', 'position')
                plugins = downcast_plugins(plugins)
                plugins[0].parent_id = None
                plugins = build_plugin_tree(plugins)
                context['plugins'] = plugins
            if instance.alias_placeholder_id:
                content = render_placeholder(instance.alias_placeholder, context)
                print content
                context['content'] = mark_safe(content)
            return context

        def get_extra_plugin_menu_items(self, request, plugin):
            return [
                PluginMenuItem(
                    _("Create Alias"),
                    reverse("admin:cms_create_alias"),
                    data={
                        'plugin_id': plugin.pk,
                        'csrfmiddlewaretoken': get_token(request)
                    },
                )
            ]

        def get_extra_placeholder_menu_items(self, request, placeholder):
            return [
                PluginMenuItem(
                    _("Create Alias"),
                    reverse("admin:cms_create_alias"),
                    data={
                        'placeholder_id': placeholder.pk,
                        'csrfmiddlewaretoken': get_token(request)
                    },
                )
            ]

        def get_plugin_urls(self):
            urlpatterns = [
                re_path(r'^create_alias/$', self.create_alias, name='cms_create_alias'),
            ]
            return urlpatterns

        def create_alias(self, request):
            if not request.user.is_staff:
                return HttpResponseForbidden("not enough privileges")
            if not 'plugin_id' in request.POST and not 'placeholder_id' in request.POST:
                return HttpResponseBadRequest(
                    "plugin_id or placeholder_id POST parameter missing."
                )
            plugin = None
            placeholder = None
            if 'plugin_id' in request.POST:
                pk = request.POST['plugin_id']
                try:
                    plugin = CMSPlugin.objects.get(pk=pk)
                except CMSPlugin.DoesNotExist:
                    return HttpResponseBadRequest(
                        "plugin with id %s not found." % pk
                    )
            if 'placeholder_id' in request.POST:
                pk = request.POST['placeholder_id']
                try:
                    placeholder = Placeholder.objects.get(pk=pk)
                except Placeholder.DoesNotExist:
                    return HttpResponseBadRequest(
                        "placeholder with id %s not found." % pk
                    )
                if not placeholder.has_change_permission(request):
                    return HttpResponseBadRequest(
                        "You do not have enough permission to alias this placeholder."
                    )
            clipboard = request.toolbar.clipboard
            clipboard.cmsplugin_set.all().delete()
            language = request.LANGUAGE_CODE
            if plugin:
                language = plugin.language
            alias = AliasPluginModel(
                language=language, placeholder=clipboard,
                plugin_type="AliasPlugin"
            )
            if plugin:
                alias.plugin = plugin
            if placeholder:
                alias.alias_placeholder = placeholder
            alias.save()
            return HttpResponse("ok")

.. _placeholder-plugin-api:

Creating and deleting plugin instances
--------------------------------------

.. versionadded:: 4.0

Plugins live inside placeholders. Since django CMS version 4 placeholders manage the
creation, and especially the deletion of plugins. Besides creating (or deleting)
database entries for the plugins the placeholders make all necessary changes to the
entire plugin tree. **Not using the placeholders to create or delete plugins can lead to
corrupted plugin trees.**

- Use :meth:`cms.models.placeholdermodel.Placeholder.add_plugin` or
  :func:`cms.api.add_plugin` to create plugins:

  .. code-block::

      new_instance = MyPluginModel(
          plugin_data="secret"
          placeholder=placeholder_to_add_to,
          position=1,  # First plugin in placeholder
      )

      placeholder_to_add_to.add_plugin(new_instance)
      assert new_instance_pk is not None  # Saved to db

  or:

  .. code-block::

      new_plugin = cms.api.add_plugin(
          placeholder_to_add_to,
          "MyPlugin",
          position='first-child',  # First position in placeholder (no parent)
          data=dict(plugin_data="secret"),
      )

- Use :meth:`cms.models.placeholdermodel.Placeholder.delete_plugin` to delete a plugin
      **including its children**:

      .. code-block::

          old_instance.placeholder.delete_plugin(old_instance)

.. warning::

    **Do not** use ``PluginModel.objects.create(...)`` or
    ``PluginModel.objects.delete()`` to create or delete plugin instances. This most
    likely either throw a database integrity exception or create a inconsistent plugin
    tree leading to unexpected behavior.

    Also, **do not** use ``queryset.delete()`` to remove multiple plugins at the same
    time. This will most likely damage the plugin tree.
