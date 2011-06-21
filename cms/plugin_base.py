# -*- coding: utf-8 -*-
from cms.exceptions import SubClassNeededError, Deprecated
from cms.models import CMSPlugin
from django import forms
from django.conf import settings
from django.contrib import admin
from django.core.exceptions import ImproperlyConfigured
from django.db.models.options import get_verbose_name
from django.forms.models import ModelForm
from django.utils.encoding import smart_str
from django.utils.translation import ugettext_lazy as _

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
                "either 'None' or a subclass of CMSPlugin. %r on %r is not."
                % (new_plugin.model, new_plugin)
            )
        # validate the template:
        if not hasattr(new_plugin, 'render_template'):
            raise ImproperlyConfigured(
                "CMSPluginBase subclasses must have a render_template attribute"
            )
        # Set the default form
        if not new_plugin.form:
            form_meta_attrs = {
                'model': new_plugin.model,
                'exclude': ('position', 'placeholder', 'language', 'plugin_type')
            }
            form_attrs = {
                'Meta': type('Meta', (object,), form_meta_attrs)
            }
            new_plugin.form = type('%sForm' % name, (ModelForm,), form_attrs)
        # Set the default fieldsets
        if not new_plugin.fieldsets:
            basic_fields = []
            advanced_fields = []
            for f in new_plugin.model._meta.fields:
                if not f.auto_created and f.editable:
                    if hasattr(f,'advanced'): 
                        advanced_fields.append(f.name)
                    else: basic_fields.append(f.name)
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
                            'fields' : advanced_fields, 
                            'classes' : ('collapse',)
                        }
                    )
                ]
        # Set default name
        if not new_plugin.name:
            new_plugin.name = get_verbose_name(new_plugin.__name__)
        return new_plugin


class CMSPluginBase(admin.ModelAdmin):
    __metaclass__ = CMSPluginBaseMetaclass
    
    name = ""
    
    form = None
    change_form_template = "admin/cms/page/plugin_change_form.html"
    # Should the plugin be rendered in the admin?
    admin_preview = True 
    
    render_template = None
    # Should the plugin be rendered at all, or doesn't it have any output?
    render_plugin = True 
    model = CMSPlugin
    text_enabled = False
    page_only = False
    
    opts = {}
    module = None #track in which module/application belongs
    
    def __init__(self, model=None,  admin_site=None):
        if admin_site:
            super(CMSPluginBase, self).__init__(self.model, admin_site)
        
        self.object_successfully_changed = False
        
        # variables will be overwritten in edit_view, so we got required
        self.cms_plugin_instance = None
        self.placeholder = None
        self.page = None

    def render(self, context, instance, placeholder):
        raise NotImplementedError("render needs to be implemented")
    
    @property
    def parent(self):
        return self.cms_plugin_instance.parent
    
    def render_change_form(self, request, context, add=False, change=False, form_url='', obj=None):
        """
        We just need the popup interface here
        """
        context.update({
            'preview': not "no_preview" in request.GET,
            'is_popup': True,
            'plugin': self.cms_plugin_instance,
            'CMS_MEDIA_URL': settings.CMS_MEDIA_URL,
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
    
    def response_add(self, request, obj):
        """
        Just set a flag, so we know something was changed, and can make
        new version if reversion installed.
        New version will be created in admin.views.edit_plugin
        """
        self.object_successfully_changed = True
        return super(CMSPluginBase, self).response_add(request, obj)

    def log_addition(self, request, object):
        pass

    def log_change(self, request, object, message):
        pass

    def log_deletion(self, request, object, object_repr):
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
        return "%s - %s" % (unicode(self.name), unicode(instance))
    
    def __repr__(self):
        return smart_str(self.name)
    
    def __unicode__(self):
        return self.name
    
    #===========================================================================
    # Deprecated APIs
    #===========================================================================
    
    @property
    def pluginmedia(self):
        raise Deprecated(
            "CMSPluginBase.pluginmedia is deprecated in favor of django-sekizai"
        )
        
    
    def get_plugin_media(self, request, context, plugin):
        raise Deprecated(
            "CMSPluginBase.get_plugin_media is deprecated in favor of django-sekizai"
        )