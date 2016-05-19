# -*- coding: utf-8 -*-
import json
import re
import warnings

from django.http import HttpResponseBadRequest
from django.http import HttpResponseForbidden
from django.shortcuts import render_to_response

from django import forms
from django.contrib import admin
from django.contrib import messages
from django.core.exceptions import (
    ImproperlyConfigured,
    PermissionDenied,
    ValidationError,
)
from django.template.defaultfilters import force_escape
from django.utils import six
from django.utils.encoding import force_text, python_2_unicode_compatible, smart_str
from django.utils.translation import ugettext_lazy as _

from cms.constants import PLUGIN_MOVE_ACTION, PLUGIN_COPY_ACTION
from cms.exceptions import SubClassNeededError, Deprecated
from cms.models import CMSPlugin
from cms.utils import get_cms_setting


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
        if (not hasattr(new_plugin, 'render_template') and
                not hasattr(new_plugin, 'get_render_template')):
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
            new_plugin.name = re.sub("([a-z])([A-Z])", "\g<1> \g<2>", name)
        return new_plugin


@python_2_unicode_compatible
class CMSPluginBase(six.with_metaclass(CMSPluginBaseMetaclass, admin.ModelAdmin)):

    name = ""
    module = _("Generic")  # To be overridden in child classes

    form = None
    change_form_template = "admin/cms/page/plugin/change_form.html"
    frontend_edit_template = 'cms/toolbar/plugin.html'
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
    disable_child_plugin = False  # DEPRECATED: REMOVE IN CMS v3.3

    cache = get_cms_setting('PLUGIN_CACHE')
    system = False

    opts = {}

    action_options = {
        PLUGIN_MOVE_ACTION: {
            'requires_reload': False
        },
        PLUGIN_COPY_ACTION: {
            'requires_reload': True
        },
    }

    def __init__(self, model=None, admin_site=None):
        if admin_site:
            super(CMSPluginBase, self).__init__(self.model, admin_site)

        self.object_successfully_changed = False

        # variables will be overwritten in edit_view, so we got required
        self.cms_plugin_instance = None
        self.placeholder = None
        self.page = None

    def _get_render_template(self, context, instance, placeholder):
        if getattr(instance, 'render_template', False):
            warnings.warn('CMSPlugin.render_template attribute is deprecated '
                          'and it will be removed in version 3.2; please move'
                          'template in plugin classes', DeprecationWarning)
            return getattr(instance, 'render_template', False)
        elif hasattr(self, 'get_render_template'):
            return self.get_render_template(context, instance, placeholder)
        elif getattr(self, 'render_template', False):
            return getattr(self, 'render_template', False)

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

        allowed_parents = cls().get_parent_classes(slot, page) or []
        return bool(allowed_parents)

    @classmethod
    def get_require_parent(cls, slot, page):
        from cms.utils.placeholder import get_placeholder_conf

        template = page and page.get_template() or None

        # config overrides..
        require_parent = get_placeholder_conf('require_parent', slot, template, default=cls.require_parent)
        return require_parent

    @property
    def parent(self):
        return self.cms_plugin_instance.parent

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
            'plugin': self.cms_plugin_instance,
            'CMS_MEDIA_URL': get_cms_setting('MEDIA_URL'),
        })

        return super(CMSPluginBase, self).render_change_form(request, context, add, change, form_url, obj)

    def has_change_permission(self, request, obj=None):
        """
        By default requires the user to have permission to change the plugin
        instance and the object, to which the plugin is attached (eg a page).
        """
        if obj:
            return obj.has_change_permission(request)
        # When obj is None, we can't check permissions correctly
        # because we need a placeholder object to do so.
        return False
    has_delete_permission = has_change_permission

    def get_form(self, request, obj=None, **kwargs):
        form_class = super(CMSPluginBase, self).get_form(request, obj, **kwargs)

        if obj:
            return form_class

        plugin_data = self.validate_add_request(request)

        # Setting attributes on the form class is perfectly fine.
        # The form class is created by modelform factory every time
        # this get_form() method is called.
        # Subclassing is not advisable because Django does metaclass
        # magic and some attributes get lost. Ticket #5273

        # The _cms_initial_attributes acts as a hook to set
        # certain values when the form is saved.
        # Currently this only happens on plugin creation.
        form_class._cms_initial_attributes = {
            'language': plugin_data['plugin_language'],
            'placeholder': plugin_data['placeholder_id'],
            'parent': plugin_data.get('plugin_parent', None),
            'plugin_type': plugin_data['plugin_type'],
            'position': plugin_data['position'],
        }
        return form_class

    def validate_add_request(self, request):
        from cms.admin.forms import PluginAddValidationForm

        if getattr(self, "cms_plugin_instance"):
            # cms_plugin_instance points to an instance of CMSPlugin
            # that has no real instance aka a "ghost plugin".
            # This can easily happen in <= CMS 3.2 if the user
            # adds a plugin and then reloads the page without canceling
            # or submitting the form.
            # No need to validate the data in this plugin because
            # it's already been created.
            plugin = self.cms_plugin_instance
            plugin_data = {
                'placeholder_id': plugin.placeholder,
                'plugin_language': plugin.language,
                'plugin_parent': plugin.parent,
                'plugin_position': plugin.position,
                'plugin_type': plugin.plugin_type,
            }
        else:
            form = PluginAddValidationForm(
                data=request.GET,
                plugin_type=self.__class__.__name__,
            )

            if form.is_valid():
                plugin_data = form.cleaned_data
                plugin_data['plugin_type'] = form.plugin_type
            else:
                # list() is necessary for python 3 compatibility.
                # errors is s dict mapping fields to a list of errors
                # for that field.
                error = list(form.errors.values())[0][0]
                raise ValidationError(message=force_text(error))

        if not plugin_data['placeholder_id'].has_add_permission(request):
            # No need to run self.has_add_permission(request)
            # This method (validate_add_request) is called on get_form
            # and get_form is called after Django checks permissions.
            raise PermissionDenied

        parent = plugin_data.get('plugin_parent')

        if parent:
            position = parent.cmsplugin_set.count()
        else:
            position = CMSPlugin.objects.filter(
                parent__isnull=True,
                language=plugin_data['plugin_language'],
                placeholder=plugin_data['placeholder_id'],
            ).count()

        plugin_data['position'] = position
        return plugin_data

    def add_view(self, request, form_url='', extra_context=None):
        try:
            response = super(CMSPluginBase, self).add_view(
                request, form_url, extra_context)
        except PermissionDenied:
            message = force_text(_('You do not have permission to add a plugin'))
            return HttpResponseForbidden(message)
        except ValidationError as error:
            return HttpResponseBadRequest(error.message)
        return response

    def render_close_frame(self, obj, extra_context=None):
        context = {
            'plugin': obj,
            'is_popup': True,
            'name': force_text(obj),
            "type": obj.get_plugin_name(),
            'plugin_id': obj.pk,
            'icon': force_escape(obj.get_instance_icon_src()),
            'alt': force_escape(obj.get_instance_icon_alt()),
        }

        if extra_context:
            context.update(extra_context)
        return render_to_response(
            'admin/cms/page/plugin/confirm_form.html', context
        )

    def save_model(self, request, obj, form, change):
        """
        Override original method, and add some attributes to obj
        This have to be made, because if object is newly created, he must know
        where he lives.
        Attributes from cms_plugin_instance have to be assigned to object, if
        is cms_plugin_instance attribute available.
        """

        if getattr(self, "cms_plugin_instance"):
            # assign stuff to object
            fields = self.cms_plugin_instance._meta.fields
            for field in fields:
                # assign all the fields - we can do this, because object is
                # subclassing cms_plugin_instance (one to one relation)
                value = getattr(self.cms_plugin_instance, field.name)
                setattr(obj, field.name, value)

        # remember the saved object
        self.saved_object = obj

        return super(CMSPluginBase, self).save_model(request, obj, form, change)

    def save_form(self, request, form, change):
        obj = super(CMSPluginBase, self).save_form(request, form, change)
        initial_attributes = getattr(form, '_cms_initial_attributes', None)

        if initial_attributes:
            # Form has the initial attribute hooks
            for field, value in initial_attributes.items():
                setattr(obj, field, value)
        return obj

    def response_add(self, request, obj, **kwargs):
        self.object_successfully_changed = True
        # Normally we would add the user message to say the object
        # was added successfully but looks like the CMS has not
        # supported this and can lead to issues with plugins
        # like ckeditor.
        return self.render_close_frame(obj)

    def response_change(self, request, obj):
        self.object_successfully_changed = True
        opts = self.model._meta
        msg_dict = {'name': force_text(opts.verbose_name), 'obj': force_text(obj)}
        msg = _('The %(name)s "%(obj)s" was changed successfully.') % msg_dict
        self.message_user(request, msg, messages.SUCCESS)
        return self.render_close_frame(obj)

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
        return "%s - %s" % (force_text(self.name), force_text(instance))

    def get_fieldsets(self, request, obj=None):
        """
        Same as from base class except if there are no fields, show an info message.
        """
        fieldsets = super(CMSPluginBase, self).get_fieldsets(request, obj)

        for name, data in fieldsets:
            if data.get('fields'):  # if fieldset with non-empty fields is found, return fieldsets
                return fieldsets

        if self.inlines:
            return []  # if plugin has inlines but no own fields return empty fieldsets to remove empty white fieldset

        try:  # if all fieldsets are empty (assuming there is only one fieldset then) add description
            fieldsets[0][1]['description'] = _('There are no further settings for this plugin. Please press save.')
        except KeyError:
            pass

        return fieldsets

    @classmethod
    def get_child_class_overrides(cls, slot, page):
        """
        Returns a list of plugin types that are allowed
        as children of this plugin.
        """
        from cms.utils.placeholder import get_placeholder_conf

        template = page and page.get_template() or None

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
        return plugin_pool.get_all_plugins(slot, page)

    def get_child_classes(self, slot, page):
        """
        Returns a list of plugin types that can be added
        as children to this plugin.
        """
        # Placeholder overrides are highest in priority
        child_classes = self.get_child_class_overrides(slot, page)

        if child_classes:
            return child_classes

        # Get all child plugin candidates
        installed_plugins = self.get_child_plugin_candidates(slot, page)

        child_classes = []
        plugin_type = self.__class__.__name__

        # The following will go through each
        # child plugin candidate and check if
        # has configured parent class restrictions.
        # If there are restrictions then the plugin
        # is only a valid child class if the current plugin
        # matches one of the parent restrictions.
        # If there are no restrictions then the plugin
        # is a valid child class.
        for plugin_class in installed_plugins:
            allowed_parents = plugin_class().get_parent_classes(slot, page) or []

            if not allowed_parents or plugin_type in allowed_parents:
                # Plugin has no parent restrictions or
                # Current plugin (self) is a configured parent
                child_classes.append(plugin_class.__name__)
            else:
                continue
        return child_classes

    def get_parent_classes(self, slot, page):
        from cms.utils.placeholder import get_placeholder_conf

        template = page and page.get_template() or None

        # config overrides..
        ph_conf = get_placeholder_conf('parent_classes', slot, template, default={})
        parent_classes = ph_conf.get(self.__class__.__name__, self.parent_classes)
        return parent_classes

    def get_action_options(self):
        return self.action_options

    def requires_reload(self, action):
        actions = self.get_action_options()
        reload_required = False
        if action in actions:
            options = actions[action]
            reload_required = options.get('requires_reload', False)
        return reload_required

    def get_plugin_urls(self):
        """
        Return URL patterns for which the plugin wants to register
        views for.
        """
        return []

    def plugin_urls(self):
        return self.get_plugin_urls()
    plugin_urls = property(plugin_urls)

    def get_extra_placeholder_menu_items(self, request, placeholder):
        pass

    def get_extra_global_plugin_menu_items(self, request, plugin):
        pass

    def get_extra_local_plugin_menu_items(self, request, plugin):
        pass

    def __repr__(self):
        return smart_str(self.name)

    def __str__(self):
        return self.name

    # ===============
    # Deprecated APIs
    # ===============

    @property
    def pluginmedia(self):
        raise Deprecated(
            "CMSPluginBase.pluginmedia is deprecated in favor of django-sekizai"
        )

    def get_plugin_media(self, request, context, plugin):
        raise Deprecated(
            "CMSPluginBase.get_plugin_media is deprecated in favor of django-sekizai"
        )


class PluginMenuItem(object):
    def __init__(self, name, url, data, question=None, action='ajax', attributes=None):
        """
        Creates an item in the plugin / placeholder menu

        :param name: Item name (label)
        :param url: URL the item points to. This URL will be called using POST
        :param data: Data to be POSTed to the above URL
        :param question: Confirmation text to be shown to the user prior to call the given URL (optional)
        :param action: Custom action to be called on click; currently supported: 'ajax', 'ajax_add'
        :param attributes: Dictionary whose content will be addes as data-attributes to the menu item
        """
        if not attributes:
            attributes = {}
        self.name = name
        self.url = url
        self.data = json.dumps(data)
        self.question = question
        self.action = action
        self.attributes = attributes
