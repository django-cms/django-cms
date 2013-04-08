from cms.plugin_base import CMSPluginBase
from cms.utils.moderator import get_cmsplugin_queryset
from cms.utils import get_language_from_request
from cms.plugin_pool import plugin_pool
from django.utils.translation import ugettext_lazy as _
from models import InheritPagePlaceholder
from django.conf import settings
from cms.plugins.inherit.forms import InheritForm
import copy

class InheritPagePlaceholderPlugin(CMSPluginBase):
    """
    Locates the plugins associated with the "from_page" of an InheritPagePlaceholder instance
    and renders those plugins sequentially
    """
    model = InheritPagePlaceholder
    name = _("Inherit Plugins from Page")
    render_template = "cms/plugins/inherit_plugins.html"
    form = InheritForm
    admin_preview = False
    page_only = True
    
    def render(self, context, instance, placeholder):
        template_vars = {
            'placeholder': placeholder,
        }
        template_vars['object'] = instance
        lang = instance.from_language
        request = context.get('request', None)
        if not lang:
            if context.has_key('request'):
                lang = get_language_from_request(request)
            else:
                lang = settings.LANGUAGE_CODE
        page = instance.placeholder.page
        from_page = instance.from_page

        if page.publisher_is_draft:
            from_page = from_page.get_draft_object()
        else:
            from_page = from_page.get_public_object()

        plugins = get_cmsplugin_queryset(request).filter(
            placeholder__page=from_page,
            language=lang,
            placeholder__slot__iexact=placeholder,
            parent__isnull=True
        ).order_by('position').select_related()
        plugin_output = []
        template_vars['parent_plugins'] = plugins 
        for plg in plugins:
            tmpctx = copy.copy(context)
            tmpctx.update(template_vars)
            inst, name = plg.get_plugin_instance()
            if inst is None:
                continue
            outstr = inst.render_plugin(tmpctx, placeholder)
            plugin_output.append(outstr)
        template_vars['parent_output'] = plugin_output
        context.update(template_vars)
        return context
    
    def get_form(self, request, obj=None, **kwargs):
        Form = super(InheritPagePlaceholderPlugin, self).get_form(request, obj, **kwargs)
        
        # this is bit tricky, since i don't wont override add_view and 
        # change_view 
        class FakeForm(object):
            def __init__(self, Form, site):
                self.Form = Form
                self.site = site
                
                # base fields are required to be in this fake class, this may
                # do some troubles, with new versions of django, if there will
                # be something more required
                self.base_fields = Form.base_fields
            
            def __call__(self, *args, **kwargs):
                # instanciate the form on call
                form = self.Form(*args, **kwargs)
                # tell form we are on this site
                form.for_site(self.site)
                return form
            
        return FakeForm(Form, self.cms_plugin_instance.page.site or self.page.site)

plugin_pool.register_plugin(InheritPagePlaceholderPlugin)