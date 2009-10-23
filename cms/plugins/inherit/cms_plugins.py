from cms.plugin_base import CMSPluginBase
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils import get_language_from_request
from cms.utils.plugin import render_plugins_for_context
from cms.plugin_pool import plugin_pool
from cms.settings import CMS_MEDIA_URL
from django import template
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from django.template.context import Context
from django.conf import settings
from cms.settings import CMS_MEDIA_URL
from cms.models import CMSPlugin
from models import InheritPagePlaceholder
from django.template.context import Context
from django.conf import settings
import copy

class InheritPagePlaceholderPlugin(CMSPluginBase):
    """
    Locates the plugins associated with the "parent_page" of an InheritPagePlaceholder instance
    and renders those plugins sequentially
    """
    model = InheritPagePlaceholder
    name = _("Inherit Plugins from Parent Page")
    render_template = "cms/plugins/inherit_plugins.html"

    def render(self, context, instance, placeholder):
        #print 'rendering inherited plugins!'
        template_vars = {
            'placeholder': placeholder,
        }
        template_vars['object'] = instance
        # locate the plugins assigned to the given page for the indicated placeholder
        lang = None
        request = None
        if context.has_key('request'):
            request = context['request']
            lang = get_language_from_request(request)
        else:
            lang = settings.LANGUAGE_CODE
        #print 'language CONTEXT FOR PLUGIN:', lang
        plugins = get_cmsplugin_queryset(request).filter(page=instance.parent_page, language=lang, placeholder__iexact=placeholder, parent__isnull=True).order_by('position').select_related()
        #plugins = CMSPlugin.objects.filter(page=instance.parent_page, placeholder=placeholder, language=lang)
        plugin_output = []
        template_vars['parent_plugins'] = plugins 
        for plg in plugins:
            #print 'added a parent plugin:', plg, plg.__class__
            # use a temporary context to prevent plugins from overwriting context
            tmpctx = copy.copy(context)
            tmpctx.update(template_vars)
            inst, name = plg.get_plugin_instance()
            #print 'got a plugin instance:', inst
            outstr = inst.render_plugin(tmpctx, placeholder)
            plugin_output.append(outstr)
            #print 'render result:', outstr
        template_vars['parent_output'] = plugin_output
        context.update(template_vars)
#        plugin_output = render_plugins_for_context(placeholder, instance.parent_page, context)
#        print 'PLUGIN OUTPUT:', plugin_output
#        template_vars['parent_output'] = plugin_output
#        context.update(template_vars)
#        print 'inherit returning output:', context['parent_output']
        return context

plugin_pool.register_plugin(InheritPagePlaceholderPlugin)