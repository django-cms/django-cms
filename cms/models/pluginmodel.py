from django.db.models.base import ModelBase
from cms.models.pagemodel import Page
from os.path import join
from datetime import datetime, date
from django.db import models
from django.utils.translation import ugettext_lazy as _
from django.utils.safestring import mark_safe
from django.template.loader import render_to_string
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from publisher import MpttPublisher
from django.template.context import Context
from cms import settings
from cms.utils.helpers import reversion_register

class PluginModelBase(ModelBase):
    """
    Metaclass for all plugins.
    """
    def __new__(cls, name, bases, attrs):
        new_class = super(PluginModelBase, cls).__new__(cls, name, bases, attrs)
        found = False
        for base in bases:
            if base.__name__ == "CMSPlugin":
                found = True
        if found:
            if new_class._meta.db_table.startswith("%s_" % new_class._meta.app_label):
                table = "cmsplugin_" + new_class._meta.db_table.split("%s_" % new_class._meta.app_label, 1)[1]
                new_class._meta.db_table = table
        return new_class 
         
    
class CMSPlugin(MpttPublisher):
    __metaclass__ = PluginModelBase
    
    page = models.ForeignKey(Page, verbose_name=_("page"), editable=False)
    parent = models.ForeignKey('self', blank=True, null=True, editable=False)
    position = models.PositiveSmallIntegerField(_("position"), blank=True, null=True, editable=False)
    placeholder = models.CharField(_("slot"), max_length=50, db_index=True, editable=False)
    language = models.CharField(_("language"), max_length=5, blank=False, db_index=True, editable=False)
    plugin_type = models.CharField(_("plugin_name"), max_length=50, db_index=True, editable=False)
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    level = models.PositiveIntegerField(db_index=True, editable=False)
    lft = models.PositiveIntegerField(db_index=True, editable=False)
    rght = models.PositiveIntegerField(db_index=True, editable=False)
    tree_id = models.PositiveIntegerField(db_index=True, editable=False)
    
    def __unicode__(self):
        return str(self.id) #""
        
    class Meta:
        app_label = 'cms'
        
    class PublisherMeta:
        exclude_fields = []
        exclude_fields_append = ['plugin_ptr']
    
    def get_plugin_name(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_plugin(self.plugin_type).name
    
    def get_short_description(self):
        return self.get_plugin_instance()[0].__unicode__()        
    
    def get_plugin_class(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_plugin(self.plugin_type)
        
    def get_plugin_instance(self, admin=None):
        from cms.plugin_pool import plugin_pool
        plugin_class = plugin_pool.get_plugin(self.plugin_type)
        plugin = plugin_class(plugin_class.model, admin)# needed so we have the same signature as the original ModelAdmin
        if plugin.model != self.__class__: # and self.__class__ == CMSPlugin:
            # (if self is actually a subclass, getattr below would break)
            try:
                if hasattr(self, '_is_public_model'):
                    # if it is an public model all field names have public prefix
                    instance = getattr(self, plugin.model.__name__.lower()+"public")
                else:
                    instance = getattr(self, plugin.model.__name__.lower())
                # could alternatively be achieved with:
                # instance = plugin_class.model.objects.get(cmsplugin_ptr=self)
            except (AttributeError, ObjectDoesNotExist):
                instance = None
        else:
            instance = self
        return instance, plugin
    
    def render_plugin(self, context=None, placeholder=None, admin=False):
        instance, plugin = self.get_plugin_instance()
        if context is None:
            context = Context()
        if instance and not (admin and not plugin.admin_preview):
            context = plugin.render(context, instance, placeholder)
            template = hasattr(instance, 'render_template') and instance.render_template or plugin.render_template
            if not template:
                raise ValidationError("plugin has no render_template: %s" % plugin.__class__)
            return mark_safe(render_to_string(template, context))
        else:
            return ""
            
    def get_media_path(self, filename):
        if self.page_id:
            return self.page.get_media_path(filename)
        else: # django 1.0.2 compatibility
            today = date.today()
            return join(settings.CMS_PAGE_MEDIA_PATH, str(today.year), str(today.month), str(today.day), filename)
            
    
    def get_instance_icon_src(self):
        """
        Get src URL for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        if instance:
            return plugin.icon_src(instance)
        else:
            return u''

    def get_instance_icon_alt(self):
        """
        Get alt text for instance's icon
        """
        instance, plugin = self.get_plugin_instance()
        if instance:
            return unicode(plugin.icon_alt(instance))
        else:
            return u''
        
    def save(self, no_signals=False, *args, **kwargs):
        if no_signals:# ugly hack because of mptt
            super(CMSPlugin, self).save_base(cls=self.__class__)
        else:
            super(CMSPlugin, self).save()
            
    
    def set_base_attr(self, plugin):
        for attr in ['parent_id', 'page_id', 'placeholder', 'language', 'plugin_type', 'creation_date', 'level', 'lft', 'rght', 'position', 'tree_id']:
            setattr(plugin, attr, getattr(self, attr))
    
    def _publisher_get_public_copy(self):
        """Overrides publisher public copy acessor, because of the special
        kind of relation between Plugins.
        """   
        publisher_public = self.publisher_public
        if not publisher_public:
            return
        elif publisher_public.__class__ is self.__class__:
            return publisher_public
        try:
            return self.__class__.objects.get(pk=self.publisher_public_id)
        except ObjectDoesNotExist:
            # extender dosent exist yet
            public_copy = self.__class__()
            # copy values of all local fields
            for field in publisher_public._meta.local_fields:
                value = getattr(publisher_public, field.name)
                setattr(public_copy, field.name, value)
            public_copy.publisher_is_draft=False
            return public_copy
                
reversion_register(CMSPlugin)