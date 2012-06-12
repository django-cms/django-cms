# -*- coding: utf-8 -*-
from django.conf import settings

# modify reversions to match our needs if required...


def reversion_register(model_class, fields=None, follow=(), format="json", exclude_fields=None):
    """CMS interface to reversion api - helper function. Registers model for 
    reversion only if reversion is available.
    
    Auto excludes publisher fields.
     
    """
    
    # reversion's merely recommended, not required
    if not 'reversion' in settings.INSTALLED_APPS:
        return
    
    from reversion.models import VERSION_CHANGE
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
    # we can safely import reversion - calls here always check for 
    # reversion in installed_applications first
    import reversion
    from reversion.models import VERSION_CHANGE
    """
    Only add to revision if it is a draft.
    """
    revision_manager = reversion.revision
    revision_context = reversion.revision_context_manager
    
    cls = obj.__class__
    
    if cls in revision_manager._registered_models:
        
        placeholder_relation = find_placeholder_relation(obj)

        if revision_context.is_active():      
            # add toplevel object to the revision
            adapter = revision_manager.get_adapter(obj.__class__)
            revision_context.add_to_context(revision_manager, obj, adapter.get_version_data(obj, VERSION_CHANGE))
            # add plugins and subclasses to the revision
            filters = {'placeholder__%s' % placeholder_relation: obj}
            for plugin in CMSPlugin.objects.filter(**filters):
                plugin_instance, admin = plugin.get_plugin_instance()
                if plugin_instance:
                    padapter = revision_manager.get_adapter(plugin_instance.__class__)
                    revision_context.add_to_context(revision_manager, plugin_instance, padapter.get_version_data(plugin_instance, VERSION_CHANGE))
                bpadapter = revision_manager.get_adapter(plugin.__class__)
                revision_context.add_to_context(revision_manager, plugin, bpadapter.get_version_data(plugin, VERSION_CHANGE))
                
def find_placeholder_relation(obj):
    return 'page'