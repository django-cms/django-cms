#######
Plugins
#######

**********************************************
CMSPluginBase Attributes and Methods Reference
**********************************************

..  class:: cms.plugin_base.CMSPluginBase

    Inherits :class:`django:django.contrib.admin.ModelAdmin` and in most respects behaves like a
    normal sub-class. Note however that some attributes of ``ModelAdmin`` simply won't make sense in the
    context of a Plugin.


    **Attributes**

    ..  attribute:: admin_preview

        Default: ``False``

        If ``True``, displays a preview in the admin.


    ..  attribute:: allow_children

        Default: ``False``

        Allows this plugin to have child plugins - other plugins placed inside it?

        If ``True`` you need to ensure that your plugin can render its children in the plugin template. For example:

        .. code-block:: html+django

            {% load cms_tags %}
            <div class="myplugin">
                {{ instance.my_content }}
                {% for plugin in instance.child_plugin_instances %}
                    {% render_plugin plugin %}
                {% endfor %}
            </div>

        ``instance.child_plugin_instances`` provides access to all the plugin's children.
        They are pre-filled and ready to use. The child plugins should be rendered using
        the ``{% render_plugin %}`` template tag.

        See also: :attr:`child_classes`, :attr:`parent_classes`, :attr:`require_parent`.


    ..  attribute:: cache

        Default: :setting:`CMS_PLUGIN_CACHE`

        Is this plugin cacheable? If your plugin displays content based on the user or
        request or other dynamic properties set this to ``False``.

        If present and set to ``False``, the plugin will prevent the caching of
        the resulting page.

        .. important:: Setting this to ``False`` will effectively disable the
                       CMS page cache and all upstream caches for pages where
                       the plugin appears. This may be useful in certain cases
                       but for general cache management, consider using the much
                       more capable :meth:`get_cache_expiration`.

        .. warning::

            If you disable a plugin cache be sure to restart the server and clear the cache afterwards.


    ..  attribute:: change_form_template

        Default: ``admin/cms/page/plugin/change_form.html``

        The template used to render the form when you edit the plugin.

        Example::

            class MyPlugin(CMSPluginBase):
                model = MyModel
                name = _("My Plugin")
                render_template = "cms/plugins/my_plugin.html"
                change_form_template = "admin/cms/page/plugin/change_form.html"

        See also: :attr:`frontend_edit_template`.


    ..  attribute:: child_classes

        Default: ``None``

        A list of Plugin Class Names. If this is set, only plugins listed here can be
        added to this plugin.

        See also: :attr:`parent_classes`.


    ..  attribute:: disable_child_plugins

        Default: ``False``

        Disables dragging of child plugins in structure mode.


    .. attribute:: form

        Custom form class to be used to edit this plugin.


    ..  attribute:: frontend_edit_template

        *This attribute is deprecated and will be removed in 3.5.*

        Default: ``cms/toolbar/plugin.html``

        The template used for wrapping the plugin in frontend editing.

        See also: :attr:`change_form_template`.


    ..  attribute:: model

        Default: ``CMSPlugin``

        If the plugin requires per-instance settings, then this setting must be set to
        a model that inherits from :class:`~cms.models.pluginmodel.CMSPlugin`.

        See also: :ref:`storing configuration`.


    .. attribute:: module

        Will group the plugin in the plugin picker. If the module
        attribute is not provided plugin is listed in the "Generic"
        group.


    .. attribute:: name

        Will be displayed in the plugin picker.


    ..  attribute:: page_only

        Default: ``False``

        Set to ``True`` if this plugin should only be used in a placeholder that is attached to a django CMS page,
        and not other models with ``PlaceholderFields``.

        See also: :attr:`child_classes`, :attr:`parent_classes`, :attr:`require_parent`.


    ..  attribute:: parent_classes

        Default: ``None``

        A list of the names of permissible parent classes for this plugin.

        See also: :attr:`child_classes`, :attr:`require_parent`.


    ..  attribute:: render_plugin

        If set to ``False``, this plugin will not be rendered at all.
        Default: ``True``

        If ``True``, :meth:`render_template` must also be defined.

        See also: :attr:`render_template`, :meth:`get_render_template`.


    ..  attribute:: render_template

        Default: ``None``

        The path to the template used to render the template. If ``render_plugin``
        is ``True`` either this or ``get_render_template`` **must** be defined;

        See also: :attr:`render_plugin` , :meth:`get_render_template`.


    ..  attribute:: require_parent

        Default: ``False``

        Is it required that this plugin is a child of another plugin? Or can it be
        added to any placeholder, even one attached to a page.

        See also: :attr:`child_classes`, :attr:`parent_classes`.


    ..  attribute:: text_enabled

        Default: ``False``

        This attribute controls whether your plugin will be usable (and rendered)
        in a text plugin. When you edit a text plugin on a page, the plugin will show up in
        the *CMS Plugins* dropdown and can be configured and inserted. The output will even
        be previewed in the text editor.

        Of course, not all plugins are usable in text plugins. Therefore the default of this
        attribute is ``False``. If your plugin *is* usable in a text plugin:

        * set this to ``True``
        * make sure your plugin provides its own :meth:`icon_alt`, this will be used as a tooltip in
          the text-editor and comes in handy when you use multiple plugins in your text.

        See also: :meth:`icon_alt`, :meth:`icon_src`.


    **Methods**

    .. method:: get_plugin_urls(instance)

        Returns the URL patterns the plugin wants to register views for.
        They are included under django CMS's page admin URLS in the plugin path
        (e.g.: ``/admin/cms/page/plugin/<plugin-name>/`` in the default case).


        ``get_plugin_urls()`` is useful if your plugin needs to talk asynchronously to the admin.


    ..  method:: get_render_template()

        If you need to determine the plugin render model at render time
        you can implement the :meth:`get_render_template` method on the plugin
        class; this method takes the same arguments as ``render``.

        The method **must** return a valid template file path.

        Example::

            def get_render_template(self, context, instance, placeholder):
                if instance.attr = 'one':
                    return 'template1.html'
                else:
                    return 'template2.html'

        See also: :meth:`render_plugin` , :meth:`render_template`


    ..  method:: get_extra_placeholder_menu_items(self, request, placeholder)

        Extends the context menu for all placeholders.

        To add one or more custom context menu items that are displayed in the context menu for all placeholders when
        in structure mode, override this method in a related plugin to return a list of
        :class:`cms.plugin_base.PluginMenuItem` instances.


    ..  method:: get_extra_global_plugin_menu_items(self, request, plugin)

        Extends the context menu for all plugins.

        To add one or more custom context menu items that are displayed in the context menu for all plugins when in
        structure mode, override this method in a related plugin to return a list of
        :class:`cms.plugin_base.PluginMenuItem` instances.


    ..  method:: get_extra_local_plugin_menu_items()

        Extends the context menu for a specific plugin. To add one or more custom
        context menu items that are displayed in the context menu for a given plugin
        when in structure mode, override this method in the plugin to return a list of
        :class:`cms.plugin_base.PluginMenuItem` instances.

    .. _get_cache_expiration:

    ..  method:: get_cache_expiration(self, request, instance, placeholder)

        Provides expiration value to the placeholder, and in turn to the page
        for determining the appropriate Cache-Control headers to add to the
        HTTPResponse object.

        Must return one of:

            :``None``:
                This means the placeholder and the page will not even consider
                this plugin when calculating the page expiration.

            :``datetime``:
                A specific date and time (timezone-aware) in the future when
                this plugin's content expires.

                .. important:: The returned ``datetime`` must be timezone-aware
                               or the plugin will be ignored (with a warning)
                               during expiration calculations.

            :``int``:
                An number of seconds that this plugin's content can be cached.

        There are constants are defined in ``cms.constants`` that may be
        useful: :const:`~cms.constants.EXPIRE_NOW` and :data:`~cms.constants.MAX_EXPIRATION_TTL`.

        An integer value of ``0`` (zero) or :const:`~cms.constants.EXPIRE_NOW` effectively means
        "do not cache". Negative values will be treated as :const:`~cms.constants.EXPIRE_NOW`.
        Values exceeding the value :data:`~cms.constants.MAX_EXPIRATION_TTL` will be set to
        that value.

        Negative ``timedelta`` values or those greater than :data:`~cms.constants.MAX_EXPIRATION_TTL`
        will also be ranged in the same manner.

        Similarly, ``datetime`` values earlier than now will be treated as :const:`~cms.constants.EXPIRE_NOW`. Values
        greater than :const:`~cms.constants.MAX_EXPIRATION_TTL` seconds in the future will be treated as
        :data:`~cms.constants.MAX_EXPIRATION_TTL` seconds in the future.

        :param request: Relevant ``HTTPRequest`` instance.
        :param instance: The ``CMSPlugin`` instance that is being rendered.
        :rtype: ``None`` or ``datetime`` or ``int``


    .. _get_vary_cache_on:

    ..  method:: get_vary_cache_on(self, request, instance, placeholder)

        Returns an HTTP VARY header string or a list of them to be considered by the placeholder
        and in turn by the page to caching behaviour.

        Overriding this method is optional.

        Must return one of:

            :``None``:
                This means that this plugin declares no headers for the cache
                to be varied upon. (default)

            :string:
                The name of a header to vary caching upon.

            :list of strings:
                A list of strings, each corresponding to a header to vary the
                cache upon.


    ..  method:: icon_alt()

        By default :meth:`icon_alt` will return a string of the form: "[plugin type] -
        [instance]", but can be modified to return anything you like.

        This function accepts the ``instance`` as a parameter and returns a string to be
        used as the ``alt`` text for the plugin's preview or icon.

        Authors of text-enabled plugins should consider overriding this function as
        it will be rendered as a tooltip in most browser. This is useful, because if
        the same plugin is used multiple times, this tooltip can provide information about
        its configuration.

        :meth:`icon_alt` takes 1 argument:

        * ``instance``: The instance of the plugin model

        The default implementation is as follows::

            def icon_alt(self, instance):
                return "%s - %s" % (force_str(self.name), force_str(instance))

        See also: :attr:`text_enabled`, :meth:`icon_src`.


    .. method:: icon_src(instance)

        By default, this returns an empty string, which, if left unoverridden would
        result in no icon rendered at all, which, in turn, would render the plugin
        uneditable by the operator inside a parent text plugin.

        Therefore, this should be overridden when the plugin has ``text_enabled`` set to
        ``True`` to return the path to an icon to display in the text of the text
        plugin.

        Since djangocms-text-ckeditor introduced inline previews of plugins, the icon
        will not be rendered anymore.

        icon_src takes 1 argument:

        * ``instance``: The instance of the plugin model

        Example::

            def icon_src(self, instance):
                return settings.STATIC_URL + "cms/img/icons/plugins/link.png"

        See also: :attr:`text_enabled`, :meth:`icon_alt`


    .. method:: render(context, instance, placeholder)

        This method returns the context to be used to render the template
        specified in :attr:`render_template`.

        The :meth:`render` method takes three arguments:

        * ``context``: The context with which the page is rendered.
        * ``instance``: The instance of your plugin that is rendered.
        * ``placeholder``: The name of the placeholder that is rendered.

        This method must return a dictionary or an instance of
        :class:`django.template.Context`, which will be used as context to render the
        plugin template.

        By default this method will add ``instance`` and ``placeholder`` to the
        context, which means for simple plugins, there is no need to overwrite this
        method.

        If you overwrite this method it's recommended to always populate the context
        with default values by calling the render method of the super class::

            def render(self, context, instance, placeholder):
                context = super().render(context, instance, placeholder)
                ...
                return context

        :param context: Current template context.
        :param instance: Plugin instance that is being rendered.
        :param placeholder: Name of the placeholder the plugin is in.
        :rtype: ``dict``


    ..  method:: text_editor_button_icon()

        When :attr:`text_enabled` is ``True``, this plugin can be added in a text editor and
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
        for `djangocms-text-ckeditor <https://github.com/django-cms/djangocms-text-ckeditor/>`_ 2.5.0.

        See also: :attr:`text_enabled`.


.. class:: cms.plugin_base.PluginMenuItem

    .. method:: __init___(name, url, data, question=None, action='ajax', attributes=None)

        Creates an item in the plugin / placeholder menu

        :param name: Item name (label)
        :param url: URL the item points to. This URL will be called using POST
        :param data: Data to be POSTed to the above URL
        :param question: Confirmation text to be shown to the user prior to call the given URL (optional)
        :param action: Custom action to be called on click; currently supported: 'ajax', 'ajax_add'
        :param attributes: Dictionary whose content will be added as data-attributes to the menu item


******************************************
CMSPlugin Attributes and Methods Reference
******************************************

..  class:: cms.models.pluginmodel.CMSPlugin

    See also: :ref:`storing configuration`

    **Attributes**

    ..  attribute:: translatable_content_excluded_fields

    Default: ``[ ]``

    A list of plugin fields which will not be exported while using :meth:`get_translatable_content`.

    See also: :meth:`get_translatable_content`, :meth:`set_translatable_content`.

    **Methods**

    ..  method:: copy_relations()

        Handle copying of any relations attached to this plugin. Custom plugins have
        to do this themselves.

        ``copy_relations`` takes 1 argument:

        * ``old_instance``: The source plugin instance

        See also: :ref:`Handling-Relations`, :meth:`post_copy`.

    ..  method:: get_translatable_content()

        Get a dictionary of all content fields (field name / field value pairs) from
        the plugin.

        Example::

            from djangocms_text_ckeditor.models import Text

            plugin = Text.objects.get(pk=1).get_bound_plugin()[0]
            plugin.get_translatable_content()
            # returns {'body': u'<p>I am text!</p>\n'}

        See also: :attr:`translatable_content_excluded_fields`, :attr:`set_translatable_content`.


    ..  method:: post_copy()

        Can (should) be overridden to handle the copying of plugins which contain
        children plugins after the original parent has been copied.

        ``post_copy`` takes 2 arguments:

        * ``old_instance``: The old plugin instance instance
        * ``new_old_ziplist``: A list of tuples containing new copies and the old existing child plugins.

        See also: :ref:`Handling-Relations`, :meth:`copy_relations`.


    ..  method:: set_translatable_content()

        Takes a dictionary of plugin fields (field name / field value pairs) and
        overwrites the plugin's fields. Returns ``True`` if all fields have been
        written successfully, and ``False`` otherwise.

        ``set_translatable_content`` takes 1 argument:

        * ``fields``: A dictionary containing the field names and translated content for each.

        * :meth:`get_translatable_content()`

        Example::

            from djangocms_text_ckeditor.models import Text

            plugin = Text.objects.get(pk=1).get_bound_plugin()[0]
            plugin.set_translatable_content({'body': u'<p>This is a different text!</p>\n'})
            # returns True

        See also: :attr:`translatable_content_excluded_fields`, :meth:`get_translatable_content`.


    ..  method:: get_add_url()

        Returns the URL to call to add a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_edit_url()

        Returns the URL to call to edit a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_move_url()

        Returns the URL to call to move a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_delete_url()

        Returns the URL to call to delete a plugin instance; useful to implement plugin-specific
        logic in a custom view.


    ..  method:: get_copy_url()

        Returns the URL to call to copy a plugin instance; useful to implement plugin-specific
        logic in a custom view.


..  class:: cms.plugin_pool.PluginPool
