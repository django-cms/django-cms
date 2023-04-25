import json
import re

from django import forms
from django.contrib import admin, messages
from django.core.exceptions import ImproperlyConfigured, ObjectDoesNotExist
from django.shortcuts import render as render_to_response
from django.utils.encoding import force_str
from django.utils.html import escapejs
from django.utils.translation import gettext
from django.utils.translation import gettext_lazy as _

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
        super_new = super(CMSPluginBaseMetaclass, cls).__new__
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
            new_plugin.name = re.sub("([a-z])([A-Z])", r"\g<1> \g<2>", name)

        # By flagging the plugin class, we avoid having to call these class
        # methods for every plugin all the time.
        # Instead, we only call them if they are actually overridden.
        if 'get_extra_placeholder_menu_items' in attrs:
            new_plugin._has_extra_placeholder_menu_items = True

        if 'get_extra_plugin_menu_items' in attrs:
            new_plugin._has_extra_plugin_menu_items = True
        return new_plugin


class CMSPluginBase(admin.ModelAdmin, metaclass=CMSPluginBaseMetaclass):

    name = ""
    module = _("Generic")  # To be overridden in child classes

    form = None
    change_form_template = 'admin/cms/page/plugin/change_form.html'
    plugin_confirm_template = 'admin/cms/page/plugin/confirm_form.html'
    # Should the plugin be rendered in the admin?
    admin_preview = False

    render_template = None

    # Should the plugin be rendered at all, or doesn't it have any output?
    render_plugin = True

    model = CMSPlugin
    text_enabled = False
    page_only = False

    allow_children = False
    child_classes = None

    require_parent = False
    parent_classes = None

    disable_child_plugins = False

    # Warning: setting these to False, may have a serious performance impact,
    # because their child-parent-relation must be recomputed each
    # time the plugin tree is rendered.
    cache_child_classes = True
    cache_parent_classes = True

    _has_extra_placeholder_menu_items = False
    _has_extra_plugin_menu_items = False

    cache = get_cms_setting('PLUGIN_CACHE')
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
            raise ImproperlyConfigured("plugin has no render_template: %s" % self.__class__)
        return template

    @classmethod
    def get_render_queryset(cls):
        return cls.model._default_manager.all()

    def render(self, context, instance, placeholder):
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

        Must return one of:
            - None: This means the placeholder and the page will not even
              consider this plugin when calculating the page expiration;

            - A TZ-aware `datetime` of a specific date and time in the future
              when this plugin's content expires;

            - A `datetime.timedelta` instance indicating how long, relative to
              the response timestamp that the content can be cached;

            - An integer number of seconds that this plugin's content can be
              cached.

        There are constants are defined in `cms.constants` that may be helpful:
            - `EXPIRE_NOW`
            - `MAX_EXPIRATION_TTL`

        An integer value of 0 (zero) or `EXPIRE_NOW` effectively means "do not
        cache". Negative values will be treated as `EXPIRE_NOW`. Values
        exceeding the value `MAX_EXPIRATION_TTL` will be set to that value.

        Negative `timedelta` values or those greater than `MAX_EXPIRATION_TTL`
        will also be ranged in the same manner.

        Similarly, `datetime` values earlier than now will be treated as
        `EXPIRE_NOW`. Values greater than `MAX_EXPIRATION_TTL` seconds in the
        future will be treated as `MAX_EXPIRATION_TTL` seconds in the future.
        """
        return None

    def get_vary_cache_on(self, request, instance, placeholder):
        """
        Provides hints to the placeholder, and in turn to the page for
        determining VARY headers for the response.

        Must return one of:
            - None (default),
            - String of a case-sensitive header name, or
            - iterable of case-sensitive header names.

        NOTE: This only makes sense to use with caching. If this plugin has
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
            # Currently, this case is only present in the djangocms-text-ckeditor app
            # which uses ghost plugins to create inline plugins on the text.
            root = obj

        plugins = [root] + list(root.get_descendants().order_by('path'))
        # simulate the call to the unauthorized CMSPlugin.page property
        cms_page = obj.placeholder.page if obj.placeholder_id else None

        child_classes = self.get_child_classes(
            slot=obj.placeholder.slot,
            page=cms_page,
            instance=obj,
        )

        parent_classes = self.get_parent_classes(
            slot=obj.placeholder.slot,
            page=cms_page,
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
        return render_to_response(
            request, self.plugin_confirm_template, context
        )

    def save_model(self, request, obj, form, change):
        """
        Override original method, and add some attributes to obj
        This have to be made, because if object is newly created, he must know
        where he lives.
        """
        pl_admin = obj.placeholder._get_attached_admin()

        if pl_admin:
            operation_kwargs = {
                'request': request,
                'placeholder': obj.placeholder,
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

        # remember the saved object
        self.saved_object = obj
        return super().save_model(request, obj, form, change)

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
        """
        Overwrite this if text_enabled = True

        Return the URL for an image to be used for an icon for this
        plugin instance in a text editor.
        """
        return ""

    def icon_alt(self, instance):
        """
        Overwrite this if necessary if text_enabled = True
        Return the 'alt' text to be used for an icon representing
        the plugin object in a text editor.
        """
        return "%s - %s" % (force_str(self.name), force_str(instance))

    def get_fieldsets(self, request, obj=None):
        """
        Same as from base class except if there are no fields, show an info message.
        """
        fieldsets = super().get_fieldsets(request, obj)

        for _name, data in fieldsets:
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
        # where only text-enabled plugins are allowed.
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
        Return URL patterns for which the plugin wants to register
        views for.
        """
        return []

    def plugin_urls(self):
        return self.get_plugin_urls()
    plugin_urls = property(plugin_urls)

    @classmethod
    def get_extra_placeholder_menu_items(self, request, placeholder):
        pass

    @classmethod
    def get_extra_plugin_menu_items(cls, request, plugin):
        pass

    def __str__(self):
        return force_str(self.name)


class PluginMenuItem:

    def __init__(self, name, url, data=None, question=None, action='ajax', attributes=None):
        """
        Creates an item in the plugin / placeholder menu

        :param name: Item name (label)
        :param url: URL the item points to. This URL will be called using POST
        :param data: Data to be POSTed to the above URL
        :param question: Confirmation text to be shown to the user prior to call the given URL (optional)
        :param action: Custom action to be called on click; currently supported: 'ajax', 'ajax_add'
        :param attributes: Dictionary whose content will be added as data-attributes to the menu item
        """
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
