import json
import re

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import (
    ImproperlyConfigured,
    ObjectDoesNotExist,
    ValidationError,
)
from django.shortcuts import render
from django.utils.encoding import force_str, smart_str
from django.utils.html import escapejs
from django.utils.translation import gettext, gettext_lazy as _

from cms import operations
from cms.exceptions import SubClassNeededError
from cms.models import CMSPlugin
from cms.toolbar.utils import get_plugin_toolbar_info, get_plugin_tree_as_json
from cms.utils.conf import get_cms_setting


class CMSPluginBaseMetaclass(forms.MediaDefiningClass):
    """
    Ensure the CMSPlugin subclasses have sane values and set some defaults if
    they're not given.
    """
    def __new__(cls, name, bases, attrs):
        super_new = super().__new__
        parents = [base for base in bases if isinstance(base, CMSPluginBaseMetaclass)]
        if not parents:
            # If this is CMSPluginBase itself, and not a subclass, don't do anything
            return super_new(cls, name, bases, attrs)
        new_plugin = super_new(cls, name, bases, attrs)
        # validate model is actually a CMSPlugin subclass.
        if not issubclass(new_plugin.model, CMSPlugin):
            raise SubClassNeededError(
                "The 'model' attribute on CMSPluginBase subclasses must be "
                "either CMSPlugin or a subclass of CMSPlugin. %r on %r is not."
                % (new_plugin.model, new_plugin)
            )
        # validate the template:
        if (not hasattr(new_plugin, 'render_template') and not hasattr(new_plugin, 'get_render_template')):
            raise ImproperlyConfigured(
                "CMSPluginBase subclasses must have a render_template attribute"
                " or get_render_template method"
            )
        # Set the default form
        if not new_plugin.form:
            form_meta_attrs = {
                'model': new_plugin.model,
                'exclude': ('position', 'placeholder', 'language', 'plugin_type', 'path', 'depth')
            }
            form_attrs = {
                'Meta': type('Meta', (object,), form_meta_attrs)
            }
            new_plugin.form = type('%sForm' % name, (forms.ModelForm,), form_attrs)
        # Set the default fieldsets
        if not new_plugin.fieldsets:
            basic_fields = []
            advanced_fields = []
            for f in new_plugin.model._meta.fields:
                if not f.auto_created and f.editable:
                    if hasattr(f, 'advanced'):
                        advanced_fields.append(f.name)
                    else:
                        basic_fields.append(f.name)
            if advanced_fields:
                new_plugin.fieldsets = [
                    (
                        None,
                        {
                            'fields': basic_fields
                        }
                    ),
                    (
                        _('Advanced options'),
                        {
                            'fields': advanced_fields,
                            'classes': ('collapse',)
                        }
                    )
                ]
        # Set default name
        if not new_plugin.name:
            new_plugin.name = re.sub("([a-z])([A-Z])", "\\g<1> \\g<2>", name)

        # By flagging the plugin class, we avoid having to call these class
        # methods for every plugin all the time.
        # Instead, we only call them if they are actually overridden.
        if 'get_extra_placeholder_menu_items' in attrs:
            new_plugin._has_extra_placeholder_menu_items = True

        if 'get_extra_plugin_menu_items' in attrs:
            new_plugin._has_extra_plugin_menu_items = True
        return new_plugin


class CMSPluginBase(admin.ModelAdmin, metaclass=CMSPluginBaseMetaclass):
    """
    Inherits :class:`django:django.contrib.admin.ModelAdmin` and in most respects behaves like a
    normal subclass.

    Note however that some attributes of ``ModelAdmin`` simply won't make sense in the
    context of a Plugin.
    """

    #: Name of the plugin needs to be set in child classes
    name = ""

    #: Modules collect plugins of similar type
    module = _("Generic")  # To be overridden in child classes

    #: Custom form class to be used to edit this plugin.
    form = None

    change_form_template = "admin/cms/page/plugin/change_form.html"
    """
    The template used to render the form when you edit the plugin.

    Example::

        class MyPlugin(CMSPluginBase):
            model = MyModel
            name = _("My Plugin")
            render_template = "cms/plugins/my_plugin.html"
            change_form_template = "admin/cms/page/plugin_change_form.html"

    See also: :attr:`frontend_edit_template`.
    """
    #: If True, displays a preview in the admin.
    admin_preview = False

    #:  The path to the template used to render the template. If ``render_plugin`` is ``True`` either this or
    #: ``get_render_template`` **must** be defined. See also: :attr:`render_plugin` , :meth:`get_render_template`.
    render_template = None

    #: If set to ``False``, this plugin will not be rendered at all. If ``True``, :meth:`render_template` must also
    #: be defined. See also: :attr:`render_template`, :meth:`get_render_template`.
    render_plugin = True

    #: If the plugin requires per-instance settings, then this setting must be set to a model that inherits from
    #: :class:`~cms.models.pluginmodel.CMSPlugin`. See also: :ref:`storing configuration`.
    model = CMSPlugin

    text_enabled = False
    """This attribute controls whether your plugin will be usable (and rendered)
    in a text plugin. When you edit a text plugin on a page, the plugin will show up in
    the *CMS Plugins* dropdown and can be configured and inserted. The output will even
    be previewed in the text editor.

    Of course, not all plugins are usable in text plugins. Therefore the default of this
    attribute is ``False``. If your plugin *is* usable in a text plugin:

    #. set this to ``True``
    #. make sure your plugin provides its own :meth:`icon_alt`, this will be used as a tooltip in
      the text-editor and comes in handy when you use multiple plugins in your text.

    See also: :meth:`icon_alt`, :meth:`icon_src`."""

    #: Set to ``True`` if this plugin should only be used in a placeholder that is attached to a django CMS page,
    #: and not other models with ``PlaceholderFields``. See also: :attr:`child_classes`, :attr:`parent_classes`,
    #: :attr:`require_parent`.
    page_only = False

    allow_children = False
    """Allows this plugin to have child plugins - other plugins placed inside it?

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
    """

    #: A list of Plugin Class Names. If this is set, only plugins listed here can be added to this plugin.
    #: See also: :attr:`parent_classes`.
    child_classes = None

    #: Is it required that this plugin is a child of another plugin? Or can it be added to any placeholder, even one
    #: attached to a page. See also: :attr:`child_classes`, :attr:`parent_classes`.
    require_parent = False

    #: A list of the names of permissible parent classes for this plugin. See also: :attr:`child_classes`,
    #: :attr:`require_parent`.
    parent_classes = None

    #: Disables *dragging* of child plugins in structure mode.
    disable_child_plugins = False

    # Warning: setting these to False, may have a serious performance impact,
    # because their child-parent-relation must be recomputed each
    # time the plugin tree is rendered.
    cache_child_classes = True
    cache_parent_classes = True

    _has_extra_placeholder_menu_items = False
    _has_extra_plugin_menu_items = False

    cache = get_cms_setting('PLUGIN_CACHE')
    """Is this plugin cacheable? If your plugin displays content based on the user or
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
    """

    system = False

    opts = {}

    def __init__(self, model=None, admin_site=None):
        if admin_site:
            super().__init__(self.model, admin_site)

        self.object_successfully_changed = False
        self.placeholder = None
        self.page = None
        self.cms_plugin_instance = None
        # The _cms_initial_attributes acts as a hook to set
        # certain values when the form is saved.
        # Currently, this only happens on plugin creation.
        self._cms_initial_attributes = {}
        self._operation_token = None

    def _get_render_template(self, context, instance, placeholder):
        if hasattr(self, 'get_render_template'):
            template = self.get_render_template(context, instance, placeholder)
        elif getattr(self, 'render_template', False):
            template = getattr(self, 'render_template', False)
        else:
            template = None

        if not template:
            raise ValidationError("plugin has no render_template: %s" % self.__class__)
        return template

    @classmethod
    def get_render_queryset(cls):
        return cls.model._default_manager.all()

    def render(self, context, instance, placeholder):
        """This method returns the context to be used to render the template
        specified in :attr:`render_template`.

        :param dict context: The context with which the page is rendered.
        :param instance: The instance of your plugin that is rendered.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance
        :param str placeholder: The name of the placeholder that is rendered.
        :rtype: `dict` or :class:`django.template.Context`

        This method must return a dictionary or an instance of
        :class:`django.template.Context`, which will be used as context to render the
        plugin template.

        By default, this method will add ``instance`` and ``placeholder`` to the
        context, which means for simple plugins, there is no need to overwrite this
        method.

        If you overwrite this method it's recommended to always populate the context
        with default values by calling the render method of the super class::

            def render(self, context, instance, placeholder):
                context = super().render(context, instance, placeholder)
                ...
                return context

        """
        context['instance'] = instance
        context['placeholder'] = placeholder
        return context

    @classmethod
    def requires_parent_plugin(cls, slot, page):
        if cls.get_require_parent(slot, page):
            return True

        allowed_parents = cls.get_parent_classes(slot, page)
        return bool(allowed_parents)

    @classmethod
    def get_require_parent(cls, slot, page):
        from cms.utils.placeholder import get_placeholder_conf

        template = page.get_template() if page else None

        # config overrides..
        require_parent = get_placeholder_conf('require_parent', slot, template, default=cls.require_parent)
        return require_parent

    def get_cache_expiration(self, request, instance, placeholder):
        """
        Provides hints to the placeholder, and in turn to the page for
        determining the appropriate Cache-Control headers to add to the
        HTTPResponse object.

        :param request: Relevant ``HTTPRequest`` instance.
        :param instance: The ``CMSPlugin`` instance that is being rendered.
        :rtype: ``None`` or ``datetime`` or ```time_delta`` or ``int``

        Must return one of:

        :``None``:
            This means the placeholder and the page will not even
            consider this plugin when calculating the page expiration;

        :``datetime``:
            A specific date and time (timezone-aware) in the future
            when this plugin's content expires;

            .. important:: The returned ``datetime`` must be timezone-aware
                           or the plugin will be ignored (with a warning)
                           during expiration calculations.


        :``datetime.timedelta``:
            A timedelta instance indicating how long, relative to
            the response timestamp that the content can be cached;

        :``int``:
            An integer number of seconds that this plugin's content can be cached.

        There are constants are defined in ``cms.constants`` that may be
        useful: :const:`~cms.constants.EXPIRE_NOW` and :data:`~cms.constants.MAX_EXPIRATION_TTL`.

        An integer value of 0 (zero) or :const:`~cms.constants.EXPIRE_NOW` effectively means "do not
        cache". Negative values will be treated as `EXPIRE_NOW`. Values exceeding the value
        `~cms.constants.MAX_EXPIRATION_TTL` will be set to that value.

        Negative `timedelta` values or those greater than `MAX_EXPIRATION_TTL`
        will also be ranged in the same manner.

        Similarly, `datetime` values earlier than now will be treated as
        `EXPIRE_NOW`. Values greater than `MAX_EXPIRATION_TTL` seconds in the
        future will be treated as `MAX_EXPIRATION_TTL` seconds in the future.
        """
        return None

    def get_vary_cache_on(self, request, instance, placeholder):
        """
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

        .. note::
            This only makes sense to use with caching. If this plugin has
            ``cache = False`` or plugin.get_cache_expiration(...) returns 0,
            get_vary_cache_on() will have no effect.
        """
        return None

    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        We just need the popup interface here
        """
        context.update({
            'preview': "no_preview" not in request.GET,
            'is_popup': True,
            'plugin': obj,
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        })

        return super().render_change_form(request, context, add, change, form_url, obj)

    def render_close_frame(self, request, obj, extra_context=None):
        try:
            root = obj.parent.get_bound_plugin() if obj.parent else obj
        except ObjectDoesNotExist:
            # This is a nasty edge-case.
            # If the parent plugin is a ghost plugin, fetching the plugin tree
            # will fail because the downcasting function filters out all ghost plugins.
            # Currently this case is only present in the djangocms-text-ckeditor app
            # which uses ghost plugins to create inline plugins on the text.
            root = obj

        plugins = [root] + list(root.get_descendants())

        child_classes = self.get_child_classes(
            slot=obj.placeholder.slot,
            page=obj.page,
            instance=obj,
        )

        parent_classes = self.get_parent_classes(
            slot=obj.placeholder.slot,
            page=obj.page,
            instance=obj,
        )

        data = get_plugin_toolbar_info(
            obj,
            children=child_classes,
            parents=parent_classes,
        )
        data['plugin_desc'] = escapejs(force_str(obj.get_short_description()))

        context = {
            'plugin': obj,
            'is_popup': True,
            'plugin_data': json.dumps(data),
            'plugin_structure': get_plugin_tree_as_json(request, plugins),
        }

        if extra_context:
            context.update(extra_context)
        return render(
            request, 'admin/cms/page/plugin/confirm_form.html', context
        )

    def save_model(self, request, obj, form, change):
        """
        Override original method, and add some attributes to obj
        This has to be made, because if the object is newly created, it must know
        where it lives.
        """
        from django.contrib.admin import site

        pl = obj.placeholder
        pl_admin = site._registry[obj.placeholder.__class__]
        operation_kwargs = {
            'request': request,
            'placeholder': pl,
        }
        if change:
            operation_kwargs['old_plugin'] = self.model.objects.get(pk=obj.pk)
            operation_kwargs['new_plugin'] = obj
            operation_kwargs['operation'] = operations.CHANGE_PLUGIN
        else:
            parent_id = obj.parent.pk if obj.parent else None
            tree_order = obj.placeholder.get_plugin_tree_order(parent_id)
            operation_kwargs['plugin'] = obj
            operation_kwargs['operation'] = operations.ADD_PLUGIN
            operation_kwargs['tree_order'] = tree_order
        # Remember the operation token
        self._operation_token = pl_admin._send_pre_placeholder_operation(**operation_kwargs)
        # Saves the plugin
        # remember the saved object
        self.saved_object = pl.add_plugin(obj)
        pl.clear_cache(obj.language)

    def save_form(self, request, form, change):
        obj = super().save_form(request, form, change)

        for field, value in self._cms_initial_attributes.items():
            # Set the initial attribute hooks (if any)
            setattr(obj, field, value)
        return obj

    def response_add(self, request, obj, **kwargs):
        self.object_successfully_changed = True
        # Normally we would add the user message to say the object
        # was added successfully but looks like the CMS has not
        # supported this and can lead to issues with plugins
        # like ckeditor.
        return self.render_close_frame(request, obj)

    def response_change(self, request, obj):
        self.object_successfully_changed = True
        opts = self.model._meta
        msg_dict = {'name': force_str(opts.verbose_name), 'obj': force_str(obj)}
        msg = _('The %(name)s "%(obj)s" was changed successfully.') % msg_dict
        self.message_user(request, msg, messages.SUCCESS)
        return self.render_close_frame(request, obj)

    def log_addition(self, request, obj, bypass=None):
        pass

    def log_change(self, request, obj, message, bypass=None):
        pass

    def log_deletion(self, request, obj, object_repr, bypass=None):
        pass

    def icon_src(self, instance):
        """By default, this returns an empty string, which, if left un-overridden would result in no icon
        rendered at all, which, in turn, would render the plugin un-editable by the operator inside a parent
        text plugin.

        Therefore, this should be overridden when the plugin has text_enabled set to True to return the path
        to an icon to display in the text of the text plugin.

        Since djangocms-text-ckeditor introduced inline previews of plugins, the icon will not be
        rendered in TextPlugins anymore.

        :param instance: The instance of the plugin model.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance

        Example::

            def icon_src(self, instance):
                return settings.STATIC_URL + "cms/img/icons/plugins/link.png"

        See also: :attr:`text_enabled`, :meth:`icon_alt`
        """
        return ""

    def icon_alt(self, instance):
        """
        Overwrite this if necessary if ``text_enabled = True``
        Return the 'alt' text to be used for an icon representing
        the plugin object in a text editor.

        :param instance: The instance of the plugin model to provide specific information
            for the 'alt' text.
        :type instance: :class:`cms.models.pluginmodel.CMSPlugin` instance

        By default :meth:`icon_alt` will return a string of the form: "[plugin type] -
        [instance]", but can be modified to return anything you like.

        This function accepts the ``instance`` as a parameter and returns a string to be
        used as the ``alt`` text for the plugin's preview or icon.

        Authors of text-enabled plugins should consider overriding this function as
        it will be rendered as a tooltip in most browser. This is useful, because if
        the same plugin is used multiple times, this tooltip can provide information about
        its configuration.

        See also: :attr:`text_enabled`, :meth:`icon_src`.


        """
        return "%s - %s" % (force_str(self.name), force_str(instance))

    def get_fieldsets(self, request, obj=None):
        """
        Same as from base class except if there are no fields, show an info message.
        """
        fieldsets = super().get_fieldsets(request, obj)

        for name, data in fieldsets:
            if data.get('fields'):  # if fieldset with non-empty fields is found, return fieldsets
                return fieldsets

        if self.inlines:
            return []  # if plugin has inlines but no own fields return empty fieldsets to remove empty white fieldset

        try:  # if all fieldsets are empty (assuming there is only one fieldset then) add description
            fieldsets[0][1]['description'] = self.get_empty_change_form_text(obj=obj)
        except KeyError:
            pass
        return fieldsets

    @classmethod
    def get_empty_change_form_text(cls, obj=None):
        """
        Returns the text displayed to the user when editing a plugin
        that requires no configuration.
        """
        return gettext('There are no further settings for this plugin. Please press save.')

    @classmethod
    def get_child_class_overrides(cls, slot, page):
        """
        Returns a list of plugin types that are allowed
        as children of this plugin.
        """
        from cms.utils.placeholder import get_placeholder_conf

        template = page.get_template() if page else None

        # config overrides..
        ph_conf = get_placeholder_conf('child_classes', slot, template, default={})
        return ph_conf.get(cls.__name__, cls.child_classes)

    @classmethod
    def get_child_plugin_candidates(cls, slot, page):
        """
        Returns a list of all plugin classes
        that will be considered when fetching
        all available child classes for this plugin.
        """
        # Adding this as a separate method,
        # we allow other plugins to affect
        # the list of child plugin candidates.
        # Useful in cases like djangocms-text-ckeditor
        # where only text only plugins are allowed.
        from cms.plugin_pool import plugin_pool
        return plugin_pool.registered_plugins

    @classmethod
    def get_child_classes(cls, slot, page, instance=None):
        """
        Returns a list of plugin types that can be added
        as children to this plugin.
        """
        # Placeholder overrides are highest in priority
        child_classes = cls.get_child_class_overrides(slot, page)

        if child_classes:
            return child_classes

        # Get all child plugin candidates
        installed_plugins = cls.get_child_plugin_candidates(slot, page)

        child_classes = []
        plugin_type = cls.__name__

        # The following will go through each
        # child plugin candidate and check if
        # has configured parent class restrictions.
        # If there are restrictions then the plugin
        # is only a valid child class if the current plugin
        # matches one of the parent restrictions.
        # If there are no restrictions then the plugin
        # is a valid child class.
        for plugin_class in installed_plugins:
            allowed_parents = plugin_class.get_parent_classes(slot, page, instance)
            if not allowed_parents or plugin_type in allowed_parents:
                # Plugin has no parent restrictions or
                # Current plugin (self) is a configured parent
                child_classes.append(plugin_class.__name__)

        return child_classes

    @classmethod
    def get_parent_classes(cls, slot, page, instance=None):
        from cms.utils.placeholder import get_placeholder_conf

        template = page.get_template() if page else None

        # config overrides..
        ph_conf = get_placeholder_conf('parent_classes', slot, template, default={})
        parent_classes = ph_conf.get(cls.__name__, cls.parent_classes)
        return parent_classes

    def get_plugin_urls(self):
        """
        Returns the URL patterns the plugin wants to register views for.
        They are included under django CMS's page admin URLS in the plugin path
        (e.g.: ``/admin/cms/page/plugin/<plugin-name>/`` in the default case).


        ``get_plugin_urls()`` is useful if your plugin needs to talk asynchronously to the admin.
        """
        return []

    def plugin_urls(self):
        return self.get_plugin_urls()
    plugin_urls = property(plugin_urls)

    @classmethod
    def get_extra_placeholder_menu_items(self, request, placeholder):
        """Extends the placeholder context menu for all placeholders.

        To add one or more custom context menu items that are displayed in the context menu for all placeholders when
        in structure mode, override this method in a related plugin to return a list of
        :class:`cms.plugin_base.PluginMenuItem` instances.
        """
        pass

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        """Extends the plugin context menu for all plugins.

        To add one or more custom context menu items that are displayed in the context menu for all plugins when in
        structure mode, override this method in a related plugin to return a list of
        :class:`cms.plugin_base.PluginMenuItem` instances.
        """
        pass

    def __repr__(self):
        return smart_str(self.name)

    def __str__(self):
        return self.name


class PluginMenuItem:
    """
    Creates an item in the plugin / placeholder menu

    :param name: Item name (label)
    :param url: URL the item points to. This URL will be called using POST
    :param data: Data to be POSTed to the above URL
    :param question: Confirmation text to be shown to the user prior to call the given URL (optional)
    :param action: Custom action to be called on click; currently supported: 'ajax', 'ajax_add'
    :param attributes: Dictionary whose content will be added as data-attributes to the menu item

    """
    def __init__(self, name, url, data=None, question=None, action='ajax', attributes=None):
        if not attributes:
            attributes = {}

        if data:
            data = json.dumps(data)

        self.name = name
        self.url = url
        self.data = data
        self.question = question
        self.action = action
        self.attributes = attributes
