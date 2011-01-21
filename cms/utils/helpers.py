# -*- coding: utf-8 -*-
from django.conf import settings

# modify reversions to match our needs if required...


def reversion_register(model_class, fields=None, follow=(), format="json", exclude_fields=None):
    """CMS interface to reversion api - helper function. Registers model for 
    reversion only if reversion is available.
    
    Auto excludes publisher fields.
     
    """
    
    if not 'reversion' in settings.INSTALLED_APPS:
        return
    
    if fields and exclude_fields:
        raise ValueError("Just one of fields, exclude_fields arguments can be passed.")
    
    opts = model_class._meta
    local_fields = opts.local_fields + opts.local_many_to_many
    if fields is None:
        fields = [field.name for field in local_fields]
    
    exclude_fields = exclude_fields or []
    
    fields = filter(lambda name: not name in exclude_fields, fields)        

    from cms.utils import reversion_hacks
    reversion_hacks.register_draft_only(model_class, fields, follow, format)


def make_revision_with_plugins(obj, user=None, message=None):
    from cms.models.pluginmodel import CMSPlugin
    import reversion
    """
    Only add to revision if it is a draft.
    """
    revision_manager = reversion.revision
    
    cls = obj.__class__
    
    if cls in revision_manager._registry:
        
        placeholder_relation = find_placeholder_relation(obj)

        if revision_manager.is_active():      
            # add toplevel object to the revision
            revision_manager.add(obj)
            # add plugins and subclasses to the revision
            filters = {'placeholder__%s' % placeholder_relation: obj}
            for plugin in CMSPlugin.objects.filter(**filters):
                plugin_instance, admin = plugin.get_plugin_instance()
                if plugin_instance:
                    revision_manager.add(plugin_instance)
                revision_manager.add(plugin)
                
def find_placeholder_relation(obj):
    return 'page'