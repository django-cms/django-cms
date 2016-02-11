# -*- coding: utf-8 -*-
import json
import re
import warnings

from django import forms
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import reverse
from django.utils import six
from django.utils.encoding import force_text, python_2_unicode_compatible, smart_str
from django.utils.translation import ugettext_lazy as _
try:  # Django 1.6, 1.7
    from django.contrib.admin.options import (RenameBaseModelAdminMethods as
        ModelAdminMetaClass)
except:  # Django 1.8+
    ModelAdminMetaClass = forms.MediaDefiningClass

from cms.constants import PLUGIN_MOVE_ACTION, PLUGIN_COPY_ACTION
from cms.exceptions import SubClassNeededError, Deprecated
from cms.models import CMSPlugin
from cms.utils import get_cms_setting


class CMSPluginBaseMetaclass(ModelAdminMetaClass):
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
    def get_require_parent(cls, slot, page):
        from cms.utils.placeholder import get_placeholder_conf

        template = page and page.get_template() or None

        # config overrides..
        require_parent = get_placeholder_conf('require_parent', slot, template, default=cls.require_parent)
        return require_parent

    @property
    def parent(self):
        return self.cms_plugin_instance.parent

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

    def has_add_permission(self, request, *args, **kwargs):
        """Permission handling change - if user is allowed to change the page
        he must be also allowed to add/change/delete plugins..

        Not sure if there will be plugin permission requirement in future, but
        if, then this must be changed.
        """
        return self.cms_plugin_instance.has_change_permission(request)
    has_delete_permission = has_change_permission = has_add_permission

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

    def response_change(self, request, obj):
        """
        Just set a flag, so we know something was changed, and can make
        new version if reversion installed.
        New version will be created in admin.views.edit_plugin
        """
        self.object_successfully_changed = True
        return super(CMSPluginBase, self).response_change(request, obj)

    def response_add(self, request, obj, **kwargs):
        """
        Just set a flag, so we know something was changed, and can make
        new version if reversion installed.
        New version will be created in admin.views.edit_plugin
        """
        self.object_successfully_changed = True

        post_url_continue = reverse('admin:cms_page_edit_plugin',
                args=(obj._get_pk_val(),),
                current_app=self.admin_site.name)
        kwargs.setdefault('post_url_continue', post_url_continue)
        return super(CMSPluginBase, self).response_add(request, obj, **kwargs)

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

    def get_child_classes(self, slot, page):
        from cms.utils.placeholder import get_placeholder_conf

        template = page and page.get_template() or None

        # config overrides..
        ph_conf = get_placeholder_conf('child_classes', slot, template, default={})
        child_classes = ph_conf.get(self.__class__.__name__, self.child_classes)
        if child_classes:
            return child_classes
        from cms.plugin_pool import plugin_pool
        installed_plugins = plugin_pool.get_all_plugins(slot, page)
        return [cls.__name__ for cls in installed_plugins]

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
    def __init__(self, name, url, data, question=None, action='ajax'):
        """
        Creates an item in the plugin / placeholder menu

        :param name: Item name (label)
        :param url: URL the item points to. This URL will be called using POST
        :param data: Data to be POSTed to the above URL
        :param question: Confirmation text to be shown to the user prior to call the given URL (optional)
        :param action: Custom action to be called on click; currently supported: 'ajax', 'ajax_add'
        """
        self.name = name
        self.url = url
        self.data = json.dumps(data)
        self.question = question
        self.action = action
