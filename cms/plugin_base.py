from cms.models import CMSPlugin
from cms.exceptions import SubClassNeededError
from django.conf import settings
from django.forms.models import ModelForm
from django.utils.encoding import smart_str
from django.contrib import admin
from django.forms.widgets import Media, MediaDefiningClass

def pluginmedia_property(cls):
    def _media(self):
        # Get the plugin media property of the superclass, if it exists
        if hasattr(super(cls, self), 'pluginmedia'):
            base = super(cls, self).pluginmedia
        else:
            base = Media()

        # Get the media definition for this class
        definition = getattr(cls, 'PluginMedia', None)
        if definition:
            extend = getattr(definition, 'extend', True)
            if extend:
                if extend == True:
                    m = base
                else:
                    m = Media()
                    for medium in extend:
                        m = m + base[medium]
                return m + Media(definition)
            else:
                return Media(definition)
        else:
            return base
    return property(_media)

class PluginMediaDefiningClass(MediaDefiningClass):
    def __new__(cls, name, bases, attrs):
        new_class = super(PluginMediaDefiningClass, cls).__new__(cls, name, bases,
                                                           attrs)
        if 'pluginmedia' not in attrs:
            new_class.pluginmedia = pluginmedia_property(new_class)
        return new_class



class CMSPluginBase(admin.ModelAdmin):
    
    __metaclass__ = PluginMediaDefiningClass # just define a PluginMedia class to add media
    
    name = ""
    
    form = None
    change_form_template = "admin/cms/page/plugin_change_form.html"
    admin_preview = True # Should the plugin be rendered in the admin?
    
    render_template = None
    render_plugin = True # Should the plugin be rendered at all, or doesn't it have any output?
    model = CMSPlugin
    text_enabled = False
    
    opts = {}
    module = None #track in which module/application belongs
    
    def __init__(self, model=None,  admin_site=None):
        if self.model:
            if not CMSPlugin in self.model._meta.parents and self.model != CMSPlugin:
                found = False
                bases = self.model.__bases__
                while bases:
                    cls = bases[0]
                    if cls.__name__ == "CMSPlugin":
                        found = True
                        bases = False
                    else:
                        bases = cls.__bases__  
                if not found:
                    raise SubClassNeededError, "plugin model needs to subclass CMSPlugin"
            if not self.form:
                class DefaultModelForm(ModelForm):
                    class Meta:
                        model = self.model
                        exclude = ('page', 'position', 'placeholder', 'language', 'plugin_type')
                self.form = DefaultModelForm
        
            # Move 'advanced' fields into separate fieldset.
            # Currently disabled if fieldsets already set, though
            # could simply append an additional 'advanced' fieldset -- 
            # but then the plugin can't customise the advanced fields
            if not self.__class__.fieldsets:
                basic_fields = []
                advanced_fields = []
                for f in self.model._meta.fields:
                    if not f.auto_created and f.editable:
                        if hasattr(f,'advanced'): 
                            advanced_fields.append(f.name)
                        else: basic_fields.append(f.name)
                if advanced_fields: # leave well enough alone otherwise
                    self.__class__.fieldsets = (
                        (None, { 'fields' : basic_fields}),
                        (_('Advanced options'), 
                         {'fields' : advanced_fields, 
                          'classes' : ('collapse',)})
                        )

        if admin_site:
            super(CMSPluginBase, self).__init__(self.model, admin_site)
        
        self.object_successfully_changed = False
        
        # variables will be overwritten in edit_view, so we got required
        self.cms_plugin_instance = None
        self.placeholder = None
        self.page = None

    def render(self, context, instance, placeholder):
        raise NotImplementedError, "render needs to be implemented"
    
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
    
    def get_plugin_media(self, request, context, plugin):
        return self.pluginmedia
        
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
