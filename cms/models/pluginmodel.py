# -*- coding: utf-8 -*-
import os
import warnings
from datetime import datetime, date

from django.conf import settings
from django.core.exceptions import ValidationError, ObjectDoesNotExist
from django.db import models
from django.db.models.base import (model_unpickle, simple_class_factory)
from django.db.models.query_utils import DeferredAttribute
from django.utils.translation import ugettext_lazy as _

from cms.exceptions import DontUsePageAttributeWarning
from cms.models.placeholdermodel import Placeholder
from cms.plugin_rendering import PluginContext, render_plugin
from cms.utils.helpers import reversion_register
from cms.utils.placeholder import get_page_from_placeholder_if_exists

from mptt.models import MPTTModel, MPTTModelBase


class BoundRenderMeta(object):
    def __init__(self, meta):
        self.index = 0
        self.total = 1
        self.text_enabled = getattr(meta, 'text_enabled', False)


class PluginModelBase(MPTTModelBase):
    """
    Metaclass for all CMSPlugin subclasses. This class should not be used for
    any other type of models.
    """
    def __new__(cls, name, bases, attrs):
        # remove RenderMeta from the plugin class
        attr_meta = attrs.pop('RenderMeta', None)

        # create a new class (using the super-metaclass)
        new_class = super(PluginModelBase, cls).__new__(cls, name, bases, attrs)
        
        # if there is a RenderMeta in attrs, use this one
        if attr_meta:
            meta = attr_meta
        else:
            # else try to use the one from the superclass (if present)
            meta = getattr(new_class, '_render_meta', None)
        
        # set a new BoundRenderMeta to prevent leaking of state
        new_class._render_meta = BoundRenderMeta(meta)

        # turn 'myapp_mymodel' into 'cmsplugin_mymodel' by removing the
        # 'myapp_' bit from the db_table name.
        if [base for base in bases if isinstance(base, PluginModelBase)]:
            splitter = '%s_' % new_class._meta.app_label
            
            if splitter in new_class._meta.db_table:
                splitted = new_class._meta.db_table.split(splitter, 1)
                table_name = 'cmsplugin_%s' % splitted[1]
            else:
                table_name = new_class._meta.db_table
            new_class._meta.db_table = table_name
        
        return new_class
         
    
class CMSPlugin(MPTTModel):
    '''
    The base class for a CMS plugin model. When defining a new custom plugin, you should
    store plugin-instance specific information on a subclass of this class.
    
    An example for this would be to store the number of pictures to display in a galery.

    Two restrictions apply when subclassing this to use in your own models:
    1. Subclasses of CMSPlugin *cannot be further subclassed*
    2. Subclasses of CMSPlugin cannot define a "text" field.

    '''
    __metaclass__ = PluginModelBase
    
    placeholder = models.ForeignKey(Placeholder, editable=False, null=True)
    parent = models.ForeignKey('self', blank=True, null=True, editable=False)
    position = models.PositiveSmallIntegerField(_("position"), blank=True, null=True, editable=False)
    language = models.CharField(_("language"), max_length=15, blank=False, db_index=True, editable=False)
    plugin_type = models.CharField(_("plugin_name"), max_length=50, db_index=True, editable=False)
    creation_date = models.DateTimeField(_("creation date"), editable=False, default=datetime.now)
    
    level = models.PositiveIntegerField(db_index=True, editable=False)
    lft = models.PositiveIntegerField(db_index=True, editable=False)
    rght = models.PositiveIntegerField(db_index=True, editable=False)
    tree_id = models.PositiveIntegerField(db_index=True, editable=False)
        
    class Meta:
        app_label = 'cms'
        
    class RenderMeta:
        index = 0
        total = 1
        text_enabled = False

    def __reduce__(self):
        """
        Provide pickling support. Normally, this just dispatches to Python's
        standard handling. However, for models with deferred field loading, we
        need to do things manually, as they're dynamically created classes and
        only module-level classes can be pickled by the default path.
        """
        data = self.__dict__
        model = self.__class__
        # The obvious thing to do here is to invoke super().__reduce__()
        # for the non-deferred case. Don't do that.
        # On Python 2.4, there is something wierd with __reduce__,
        # and as a result, the super call will cause an infinite recursion.
        # See #10547 and #12121.
        defers = []
        pk_val = None
        if self._deferred:
            factory = deferred_class_factory
            for field in self._meta.fields:
                if isinstance(self.__class__.__dict__.get(field.attname),
                        DeferredAttribute):
                    defers.append(field.attname)
                    if pk_val is None:
                        # The pk_val and model values are the same for all
                        # DeferredAttribute classes, so we only need to do this
                        # once.
                        obj = self.__class__.__dict__[field.attname]
                        model = obj.model_ref()
        else:
            factory = simple_class_factory
        return (model_unpickle, (model, defers, factory), data)

    def __unicode__(self):
        return unicode(self.id)

    def get_plugin_name(self):
        from cms.plugin_pool import plugin_pool
        return plugin_pool.get_plugin(self.plugin_type).name
    
    def get_short_description(self):
        instance = self.get_plugin_instance()[0]
        if instance:
            return instance.__unicode__()
        else:
            return _("<Empty>")
    
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
                instance = getattr(self, plugin.model.__name__.lower())
                # could alternatively be achieved with:
                # instance = plugin_class.model.objects.get(cmsplugin_ptr=self)
                instance._render_meta = self._render_meta
            except (AttributeError, ObjectDoesNotExist):
                instance = None
        else:
            instance = self
        return instance, plugin
    
    def render_plugin(self, context=None, placeholder=None, admin=False, processors=None):
        instance, plugin = self.get_plugin_instance()
        if instance and not (admin and not plugin.admin_preview):
            if isinstance(placeholder, Placeholder):
                placeholder_slot = placeholder.slot
            else:
                placeholder_slot = placeholder or instance.placeholder.slot
            placeholder = instance.placeholder
            context = PluginContext(context, instance, placeholder)
            context = plugin.render(context, instance, placeholder_slot)
            if plugin.render_plugin:
                template = hasattr(instance, 'render_template') and instance.render_template or plugin.render_template
                if not template:
                    raise ValidationError("plugin has no render_template: %s" % plugin.__class__)
            else:
                template = None
            return render_plugin(context, instance, placeholder, template, processors)
        return ""
            
    def get_media_path(self, filename):
        pages = self.placeholder.page_set.all()
        if pages.count():
            return pages[0].get_media_path(filename)
        else: # django 1.0.2 compatibility
            today = date.today()
            return os.path.join(settings.CMS_PAGE_MEDIA_PATH,
                str(today.year), str(today.month), str(today.day), filename)

    @property
    def page(self):
        warnings.warn(
            "Don't use the page attribute on CMSPlugins! CMSPlugins are not "
            "guaranteed to have a page associated with them!",
            DontUsePageAttributeWarning)
        return get_page_from_placeholder_if_exists(self.placeholder)
    
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
        for attr in ['parent_id', 'placeholder', 'language', 'plugin_type', 'creation_date', 'level', 'lft', 'rght', 'position', 'tree_id']:
            setattr(plugin, attr, getattr(self, attr))
    
    def copy_plugin(self, target_placeholder, target_language, plugin_tree):
        """
        Copy this plugin and return the new plugin.
        """
        try:
            plugin_instance, cls = self.get_plugin_instance()
        except KeyError: #plugin type not found anymore
            return
        new_plugin = CMSPlugin()
        new_plugin.placeholder = target_placeholder
        new_plugin.tree_id = None
        new_plugin.lft = None
        new_plugin.rght = None
        new_plugin.level = None
        if self.parent:
            pdif = self.level - plugin_tree[-1].level
            if pdif < 0:
                plugin_tree[:] = plugin_tree[:pdif-1]
            new_plugin.parent = plugin_tree[-1]
            if pdif != 0:
                plugin_tree.append(new_plugin)
        else:
            plugin_tree[:] = [new_plugin]
        new_plugin.level = None
        new_plugin.language = target_language
        new_plugin.plugin_type = self.plugin_type
        new_plugin.position = self.position
        new_plugin.save()
        if plugin_instance:
            plugin_instance.pk = new_plugin.pk
            plugin_instance.id = new_plugin.pk
            plugin_instance.placeholder = target_placeholder
            plugin_instance.tree_id = new_plugin.tree_id
            plugin_instance.lft = new_plugin.lft
            plugin_instance.rght = new_plugin.rght
            plugin_instance.level = new_plugin.level
            plugin_instance.cmsplugin_ptr = new_plugin
            plugin_instance.language = target_language
            plugin_instance.parent = new_plugin.parent
            plugin_instance.position = new_plugin.position # added to retain the position when creating a public copy of a plugin
            plugin_instance.save()
            old_instance = plugin_instance.__class__.objects.get(pk=self.pk)
            plugin_instance.copy_relations(old_instance)
        return new_plugin
        
    def post_copy(self, old_instance, new_old_ziplist):
        """
        Handle more advanced cases (eg Text Plugins) after the original is
        copied
        """
        pass 
 
    def copy_relations(self, old_instance):
        """
        Handle copying of any relations attached to this plugin. Custom plugins
        have to do this themselves!
        """
        pass
        
    def delete_with_public(self):
        """
            Delete the public copy of this plugin if it exists,
            then delete the draft
        """
        position = self.position
        slot = self.placeholder.slot
        page = get_page_from_placeholder_if_exists(self.placeholder)
        if page and getattr(page, 'publisher_public'):
            try:
                placeholder = Placeholder.objects.get(page=page.publisher_public, slot=slot)
            except Placeholder.DoesNotExist:
                pass                
            else:
                public_plugin = CMSPlugin.objects.filter(placeholder=placeholder, position=position)
                public_plugin.delete()
        self.placeholder = None
        self.delete()
        
    def has_change_permission(self, request):
        page = get_page_from_placeholder_if_exists(self.placeholder)
        if page:
            return page.has_change_permission(request)
        elif self.placeholder:
            return self.placeholder.has_change_permission(request)
        elif self.parent:
            return self.parent.has_change_permission(request)
        return False
        
    def is_first_in_placeholder(self):
        return self.position == 0
    
    def is_last_in_placeholder(self):
        """
        WARNING: this is a rather expensive call compared to is_first_in_placeholder!
        """
        return self.placeholder.cmsplugin_set.all().order_by('-position')[0].pk == self.pk
    
    def get_position_in_placeholder(self):
        """
        1 based position!
        """
        return self.position + 1

reversion_register(CMSPlugin)

def deferred_class_factory(model, attrs):
    """
    Returns a class object that is a copy of "model" with the specified "attrs"
    being replaced with DeferredAttribute objects. The "pk_value" ties the
    deferred attributes to a particular instance of the model.
    """
    class Meta:
        pass
    setattr(Meta, "proxy", True)
    setattr(Meta, "app_label", model._meta.app_label)

    class RenderMeta:
        pass
    setattr(RenderMeta, "index", model._render_meta.index)
    setattr(RenderMeta, "total", model._render_meta.total)
    setattr(RenderMeta, "text_enabled", model._render_meta.text_enabled)

    # The app_cache wants a unique name for each model, otherwise the new class
    # won't be created (we get an old one back). Therefore, we generate the
    # name using the passed in attrs. It's OK to reuse an old case if the attrs
    # are identical.
    name = "%s_Deferred_%s" % (model.__name__, '_'.join(sorted(list(attrs))))

    overrides = dict([(attr, DeferredAttribute(attr, model))
            for attr in attrs])
    overrides["Meta"] = RenderMeta
    overrides["RenderMeta"] = RenderMeta
    overrides["__module__"] = model.__module__
    overrides["_deferred"] = True
    return type(name, (model,), overrides)

# The above function is also used to unpickle model instances with deferred
# fields.
deferred_class_factory.__safe_for_unpickling__ = True
