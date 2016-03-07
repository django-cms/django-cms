#######
Plugins
#######

**********************************************
CMSPluginBase Attributes and Methods Reference
**********************************************

These are a list of attributes and methods that can (or should) be overridden
on your Plugin definition.

Attributes
==========

admin_preview
-------------

Default: ``False``

If ``True``, displays a preview in the admin.


allow_children
--------------

Default: ``False``

Can this plugin have child plugins? Or can other plugins be placed inside this
plugin? If set to ``True`` you are responsible to render the children in your
plugin template.

Please use something like this or something similar:

.. code-block:: html+django

    {% load cms_tags %}
    <div class="myplugin">
        {{ instance.my_content }}
        {% for plugin in instance.child_plugin_instances %}
            {% render_plugin plugin %}
        {% endfor %}
    </div>


Be sure to access ``instance.child_plugin_instances`` to get all children.
They are pre-filled and ready to use. To finally render your child plugins use
the ``{% render_plugin %}`` template tag.

See also: `child_classes`_, `parent_classes`_, `require_parent`_


cache
-----

Default: :setting:`CMS_PLUGIN_CACHE`

Is this plugin cacheable? If your plugin displays content based on the user or
request or other dynamic properties set this to False.

.. warning::
    If you disable a plugin cache be sure to restart the server and clear the cache afterwards.


change_form_template
--------------------

Default: ``admin/cms/page/plugin_change_form.html``

The template used to render the form when you edit the plugin.

Example::

    class MyPlugin(CMSPluginBase):
        model = MyModel
        name = _("My Plugin")
        render_template = "cms/plugins/my_plugin.html"
        change_form_template = "admin/cms/page/plugin_change_form.html"

See also: `frontend_edit_template`_


child_classes
-------------

Default: ``None``

A List of Plugin Class Names. If this is set, only plugins listed here can be
added to this plugin.

See also: `parent_classes`_


disable_child_plugins
---------------------

Default: ``False``

Disables dragging of child plugins in structure mode.


frontend_edit_template
----------------------

Default: ``cms/toolbar/placeholder_wrapper.html``

The template used for wrapping the plugin in frontend editing.

See also: `change_form_template`_


model
-----

Default: ``CMSPlugin``

If the plugin requires per-instance settings, then this setting must be set to
a model that inherits from :class:`CMSPlugin`.

See also: :ref:`storing configuration`


page_only
---------

Default: ``False``

Can this plugin only be attached to a placeholder that is attached to a page?
Set this to ``True`` if you always need a page for this plugin.

See also: `child_classes`_, `parent_classes`_, `require_parent`_,


parent_classes
--------------

Default: ``None``

A list of Plugin Class Names. If this is set, this plugin may only be added
to plugins listed here.

See also: `child_classes`_, `require_parent`_


render_plugin
-------------

Default: ``True``

Should the plugin be rendered at all, or doesn't it have any output?  If
`render_plugin` is ``True``, then you must also define :meth:`render_template`

See also: `render_template`_, `get_render_template`_


render_template
---------------

Default: ``None``

The path to the template used to render the template. If ``render_plugin``
is ``True`` either this or ``get_render_template`` **must** be defined;

See also: `render_plugin`_ , `get_render_template`_


require_parent
--------------

Default: ``False``

Is it required that this plugin is a child of another plugin? Or can it be
added to any placeholder, even one attached to a page.

See also: `child_classes`_, `parent_classes`_


text_enabled
------------

Default: ``False``

Can the plugin be inserted inside the text plugin?  If this is ``True`` then
:meth:`icon_src` must be overridden.

See also: `icon_src`_, `icon_alt`_


Methods
=======

.. _render:

render
------

The :meth:`render` method takes three arguments:

* ``context``: The context with which the page is rendered.
* ``instance``: The instance of your plugin that is rendered.
* ``placeholder``: The name of the placeholder that is rendered.

This method must return a dictionary or an instance of
:class:`django.template.Context`, which will be used as context to render the
plugin template.

.. versionadded:: 2.4

By default this method will add ``instance`` and ``placeholder`` to the
context, which means for simple plugins, there is no need to overwrite this
method.

If you overwrite this method it's recommended to always populate the context
with default values by calling the render method of the super class::

    def render(self, context, instance, placeholder):
        context = super(MyPlugin, self).render(context, instance, placeholder)
        ...
        return context


get_render_template
-------------------

If you need to determine the plugin render model at render time
you can implement :meth:`get_render_template` method on the plugin
class; this method takes the same arguments as ``render``.
The method **must** return a valid template file path.

Example::

    def get_render_template(self, context, instance, placeholder):
        if instance.attr = 'one':
            return 'template1.html'
        else:
            return 'template2.html'

See also: `render_plugin`_ , `render_template`_

icon_src
--------

By default, this returns an empty string, which, if left unoverridden would
result in no icon rendered at all, which, in turn, would render the plugin
uneditable by the operator inside a parent text plugin.

Therefore, this should be overridden when the plugin has ``text_enabled`` set to
``True`` to return the path to an icon to display in the text of the text
plugin.

icon_src takes 1 argument:

* ``instance``: The instance of the plugin model

Example::

    def icon_src(self, instance):
        return settings.STATIC_URL + "cms/img/icons/plugins/link.png"

See also: `text_enabled`_, `icon_alt`_


icon_alt
--------

Although it is optional, authors of "text enabled" plugins should consider
overriding this function as well.

This function accepts the ``instance`` as a parameter and returns a string to be
used as the alt text for the plugin's icon which will appear as a tooltip in
most browsers.  This is useful, because if the same plugin is used multiple
times within the same text plugin, they will typically all render with the
same icon rendering them visually identical to one another. This alt text and
related tooltip will help the operator distinguish one from the others.

By default :meth:`icon_alt` will return a string of the form: "[plugin type] -
[instance]", but can be modified to return anything you like.

:meth:`icon_alt` takes 1 argument:

* ``instance``: The instance of the plugin model

The default implementation is as follows::

    def icon_alt(self, instance):
        return "%s - %s" % (force_text(self.name), force_text(instance))

See also: `text_enabled`_, `icon_src`_

text_editor_button_icon
-----------------------

When `text_enabled`_ is ``True``, this plugin can be added in a text editor and
there might be an icon button for that purpose. This method allows to override
this icon.

By default, it returns ``None`` and each text editor plugin may have its own
fallback icon.

:meth:`text_editor_button_icon` takes 2 arguments:

* ``editor_name``: The plugin name of the text editor
* ``icon_context``: A dictionary containing information about the needed icon
  like `width`, `height`, `theme`, etc

Usually this method should return the icon URL. But, it may depends on the text
editor because what is needed may differ. Please consult the documentation of
your text editor plugin.

This requires support from the text plugin; support for this is currently planned
for `djangocms-text-ckeditor <https://github.com/divio/djangocms-text-ckeditor/>`_ 2.5.0.

See also: `text_enabled`_

.. _get_extra_placeholder_menu_items:

get_extra_placeholder_menu_items
--------------------------------

``get_extra_placeholder_menu_items(self, request, placeholder)``

Extends the context menu for all placeholders. To add one or more custom context
menu items that are displayed in the context menu for all placeholders when in
structure mode, override this method in a related plugin to return a list of
``cms.plugin_base.PluginMenuItem`` instances.

.. _get_extra_global_plugin_menu_items:

get_extra_global_plugin_menu_items
----------------------------------

``get_extra_global_plugin_menu_items(self, request, plugin)``

Extends the context menu for all plugins. To add one or more custom context menu
items that are displayed in the context menu for all plugins when in structure
mode, override this method in a related plugin to return a list of
``cms.plugin_base.PluginMenuItem`` instances.

.. _get_extra_local_plugin_menu_items:

get_extra_local_plugin_menu_items
---------------------------------

``get_extra_local_plugin_menu_items(self, request, plugin)``

Extends the context menu for a specific plugin. To add one or more custom
context menu items that are displayed in the context menu for a given plugin
when in structure mode, override this method in the plugin to return a list of
``cms.plugin_base.PluginMenuItem`` instances.

******************************************
CMSPlugin Attributes and Methods Reference
******************************************

These are a list of attributes and methods that can (or should) be overridden
on your plugin's `model` definition.

See also: :ref:`storing configuration`


Attributes
==========


translatable_content_excluded_fields
------------------------------------

Default: ``[ ]``

A list of plugin fields which will not be exported while using :meth:`get_translatable_content`.

See also: `get_translatable_content`_, `set_translatable_content`_


Methods
=======


copy_relations
--------------

Handle copying of any relations attached to this plugin. Custom plugins have
to do this themselves.

``copy_relations`` takes 1 argument:

* ``old_instance``: The source plugin instance

See also: :ref:`Handling-Relations`, `post_copy`_


get_translatable_content
------------------------

Get a dictionary of all content fields (field name / field value pairs) from
the plugin.

Example::

    from djangocms_text_ckeditor.models import Text

    plugin = Text.objects.get(pk=1).get_plugin_instance()[0]
    plugin.get_translatable_content()
    # returns {'body': u'<p>I am text!</p>\n'}


See also: `translatable_content_excluded_fields`_, `set_translatable_content`_


post_copy
---------

Can (should) be overridden to handle the copying of plugins which contain
children plugins after the original parent has been copied.

``post_copy`` takes 2 arguments:

* ``old_instance``: The old plugin instance instance
* ``new_old_ziplist``: A list of tuples containing new copies and the old existing child plugins.

See also: :ref:`Handling-Relations`, `copy_relations`_


set_translatable_content
------------------------

Takes a dictionary of plugin fields (field name / field value pairs) and
overwrites the plugin's fields. Returns ``True`` if all fields have been
written successfully, and ``False`` otherwise.

set_translatable_content takes 1 argument:

* ``fields``: A dictionary containing the field names and translated content for each.

Example::

    from djangocms_text_ckeditor.models import Text

    plugin = Text.objects.get(pk=1).get_plugin_instance()[0]
    plugin.set_translatable_content({'body': u'<p>This is a different text!</p>\n'})
    # returns True

See also: `translatable_content_excluded_fields`_, `get_translatable_content`_


get_add_url
-----------

Returns the URL to call to add a plugin instance; useful to implement plugin-specific
logic in a custom view.

get_edit_url
------------

Returns the URL to call to edit a plugin instance; useful to implement plugin-specific
logic in a custom view.

get_move_url
------------

Returns the URL to call to move a plugin instance; useful to implement plugin-specific
logic in a custom view.

get_delete_url
--------------

Returns the URL to call to delete a plugin instance; useful to implement plugin-specific
logic in a custom view.

get_copy_url
------------

Returns the URL to call to copy a plugin instance; useful to implement plugin-specific
logic in a custom view.


add_url
-------

Returns the URL to call to add a plugin instance; useful to implement plugin-specific
logic in a custom view.

This property is now deprecated. Will be removed in 3.4.
Use the ``get_add_url`` method instead.

Default: None (``cms_page_add_plugin`` view is used)

edit_url
--------

Returns the URL to call to edit a plugin instance; useful to implement plugin-specific
logic in a custom view.

This property is now deprecated. Will be removed in 3.4.
Use the ``get_edit_url`` method instead.

Default: None (``cms_page_edit_plugin`` view is used)

move_url
--------

Returns the URL to call to move a plugin instance; useful to implement plugin-specific
logic in a custom view.

This property is now deprecated. Will be removed in 3.4.
Use the ``get_move_url`` method instead.

Default: None (``cms_page_move_plugin`` view is used)

delete_url
----------

Returns the URL to call to delete a plugin instance; useful to implement plugin-specific
logic in a custom view.

This property is now deprecated. Will be removed in 3.4.
Use the ``get_delete_url`` method instead.

Default: None (``cms_page_delete_plugin`` view is used)

copy_url
--------

Returns the URL to call to copy a plugin instance; useful to implement plugin-specific
logic in a custom view.

This property is now deprecated. Will be removed in 3.4.
Use the ``get_copy_url`` method instead.

Default: None (``cms_page_copy_plugins`` view is used)
