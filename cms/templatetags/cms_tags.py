from cms.exceptions import NoHomeFound
from cms.utils import get_language_from_request
from cms.utils.moderator import get_cmsplugin_queryset, get_page_queryset
from cms.utils.plugin import render_plugins_for_context
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.mail import send_mail, mail_managers
from django.template.defaultfilters import title
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _



register = template.Library()

def get_site_id(site):
    if site:
        if isinstance(site, Site):
            site_id = site.id
        elif isinstance(site, int):
            site_id = site
        else:
            site_id = settings.SITE_ID
    else:
        site_id = settings.SITE_ID
    return site_id
                                    
def ancestors_from_page(page, page_queryset, title_queryset, lang):
    ancestors = list(page.get_cached_ancestors(False))
    ancestors.append(page)
    try:
        home = page_queryset.get_home()
    except NoHomeFound:
        home = None
    if ancestors and home and ancestors[0].pk != home.pk: 
        ancestors = [home] + ancestors
    ids = [page.pk]
    for anc in ancestors:
        ids.append(anc.pk)
    titles = title_queryset.filter(page__in=ids, language=lang)
    for anc in ancestors:
        if home:
            anc.home_pk_cache = home.pk 
        for title in titles:
            if title.page_id == anc.pk:
                if not hasattr(anc, "title_cache"):
                    anc.title_cache = {}
                anc.title_cache[title.language] = title
    for title in titles:
        if title.page_id == page.pk:
            if not hasattr(page, "title_cache"):
                page.title_cache = {}
            page.title_cache[title.language] = title
    return ancestors
            
def has_permission(page, request):
    return page.has_change_permission(request)
register.filter(has_permission)


def send_missing_mail(reverse_id, request):
    site = Site.objects.get_current()
    mail_managers(_('Reverse ID not found on %(domain)s') % {'domain':site.domain},
                   _("A page_id_url template tag didn't found a page with the reverse_id %(reverse_id)s\n"
                     "The url of the page was: http://%(host)s%(path)s")
                     % {'reverse_id':reverse_id, 'host':site.domain, 'path':request.path}, 
                   fail_silently=True)

def page_id_url(context, reverse_id, lang=None, site=None):
    """
    Show the url of a page with a reverse id in the right language
    This is mostly used if you want to have a static link in a template to a page
    """
    site_id = get_site_id(site)
    request = context.get('request', False)
    if not request:
        return {'content':''}

    if request.current_page == "dummy":
        return {'content': ''}
    
    if lang is None:
        lang = get_language_from_request(request)
    key = 'page_id_url_pid:'+str(reverse_id)+'_l:'+str(lang)+'_site:'+str(site_id)+'_type:absolute_url'
    url = cache.get(key)
    if not url:
        try:
            page = get_page_queryset(request).get(reverse_id=reverse_id,site=site_id)
            url = page.get_absolute_url(language=lang)
            cache.set(key, url, settings.CMS_CONTENT_CACHE_DURATION)
        except:
            send_missing_mail(reverse_id, request)
        
    if url:
        return {'content':url}
    return {'content':''}
page_id_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_id_url)

def do_placeholder(parser, token):
    error_string = '%r tag requires at least 1 and accepts at most 2 arguments' % token.contents[0]
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
        # if the `placeholderor` tag was used, look for closing tag, and pass the enclosed nodes
        # to PlaceholderNode below
        if bits[0] == 'placeholderor':
            nodelist_or = parser.parse(('endplaceholderor',))
            parser.delete_first_token()
        else:
            nodelist_or = None
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(bits) == 2:
        #tag_name, name
        return PlaceholderNode(bits[1], nodelist_or=nodelist_or)
    elif len(bits) == 3:
        #tag_name, name, width
        return PlaceholderNode(bits[1], bits[2], nodelist_or=nodelist_or)
    else:
        raise template.TemplateSyntaxError(error_string)

class PlaceholderNode(template.Node):
    """This template node is used to output page content and
    is also used in the admin to dynamicaly generate input fields.
    
    eg: {% placeholder content-type-name width %}
    
    Keyword arguments:
    name -- the name of the placeholder
    width -- additional width attribute (integer) which gets added to the plugin context
    """
    def __init__(self, name, width=None, nodelist_or=None):
        self.name = "".join(name.lower().split('"'))
        if width: self.width = template.Variable(width)
        self.nodelist_or = nodelist_or

    def render(self, context):
        width_var = getattr(self, 'width', None)
        if width_var:
            try:
                width = width_var.resolve(context)
            except template.VariableDoesNotExist:
                # should we raise an error here?
                width = None
        else:
            width = None
            
        if context.get('display_placeholder_names_only'):
            return "<!-- PlaceholderNode: %s -->" % self.name
            
        if not 'request' in context:
            return ''
        request = context['request']
        
        page = request.current_page
        if page == "dummy":
            return ""
        content = render_plugins_for_context(self.name, page, context, width)
        if not content and self.nodelist_or:
            return self.nodelist_or.render(context)
        return content
 
    def __repr__(self):
        return "<Placeholder Node: %s>" % self.name

register.tag('placeholder', do_placeholder)
register.tag('placeholderor', do_placeholder)

def do_page_attribute(parser, token):
    error_string = '%r tag requires one argument' % token.contents[0]
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(bits) >= 2:
        # tag_name, name
        # tag_name, name, reverse_id
        reverse_id = len(bits) == 3 and bits[2] or None
        return PageAttributeNode(bits[1], reverse_id)
    else:
        raise template.TemplateSyntaxError(error_string)

class PageAttributeNode(template.Node):
    """This template node is used to output attribute from a page such
    as its title or slug.

    Synopsis
         {% page_attribute field-name %}        
         {% page_attribute field-name reverse-id %}
     
    Example
         {# Output current page's page_title attribute #}
         {% page_attribute page_title %}        
         {# Output page_title attribute of the page with reverse_id 'the_page' #}
         {% page_attribute page_title 'the_page' %}


    Keyword arguments:
    field-name -- the name of the field to output. Use one of:
    - title
    - menu_title
    - page_title
    - slug
    - meta_description
    - meta_keywords
    
    reverse-id -- The page's reverse_id property, if omitted field-name of 
    current page is returned.
    """
    def __init__(self, name, reverse_id=None):
        self.name = name.lower()
        self.reverse_id = reverse_id


    def render(self, context):
        if not 'request' in context:
            return ''
        lang = get_language_from_request(context['request'])
        page = self._get_page(context['request'])
        if page == "dummy":
            return ''
        if page and self.name in ["title", "slug", "meta_description", "meta_keywords", "page_title", "menu_title"]:
            f = getattr(page, "get_"+self.name)
            return f(language=lang, fallback=True)
        return ''

    def _get_page(self, request):
        if self.reverse_id == None:
            return request.current_page
        site = Site.objects.get_current()    
        try:
            return get_page_queryset(request).get(reverse_id=self.reverse_id, site=site)
        except:
            send_missing_mail(self.reverse_id, request)

    def __repr__(self):
        return "<PageAttribute Node: %s>" % self.name

register.tag('page_attribute', do_page_attribute)

def clean_admin_list_filter(cl, spec):
    """
    used in admin to display only these users that have actually edited a page and not everybody
    """
    choices = sorted(list(spec.choices(cl)), key=lambda k: k['query_string'])
    query_string = None
    unique_choices = []
    for choice in choices:
        if choice['query_string'] != query_string:
            unique_choices.append(choice)
            query_string = choice['query_string']
    return {'title': spec.title(), 'choices' : unique_choices}
clean_admin_list_filter = register.inclusion_tag('admin/filter.html')(clean_admin_list_filter)

def _show_placeholder_by_id(context, placeholder_name, reverse_id, lang=None,
        site=None, cache_result=True):
    """
    Show the content of a page with a placeholder name and a reverse id in the right language
    This is mostly used if you want to have static content in a template of a page (like a footer)
    """
    request = context.get('request', False)
    site_id = get_site_id(site)
    
    if not request:
        return {'content':''}
    if lang is None:
        lang = get_language_from_request(request)
        
    content = None
    
    if cache_result:
        key = 'show_placeholder_by_id_pid:'+reverse_id+'_placeholder:'+placeholder_name+'_site:'+str(site_id)+'_l:'+str(lang)
        content = cache.get(key)
        
    if not content:
        try:
            page = get_page_queryset(request).get(reverse_id=reverse_id, site=site_id)
        except:
            if settings.DEBUG:
                raise
            else:
                site = Site.objects.get_current()
                send_mail(_('Reverse ID not found on %(domain)s') % {'domain':site.domain},
                          _("A show_placeholder_by_id template tag didn't found a page with the reverse_id %(reverse_id)s\n"
                            "The url of the page was: http://%(host)s%(path)s") %
                            {'reverse_id':reverse_id, 'host':request.host, 'path':request.path},
                          settings.DEFAULT_FROM_EMAIL,
                          settings.MANAGERS,
                          fail_silently=True)
                return {'content':''}
        plugins = get_cmsplugin_queryset(request).filter(page=page, language=lang, placeholder__iexact=placeholder_name, parent__isnull=True).order_by('position').select_related()
        content = ""
        for plugin in plugins:
            content += plugin.render_plugin(context, placeholder_name)
            
    if cache_result:
        cache.set(key, content, settings.CMS_CONTENT_CACHE_DURATION)

    if content:
        return {'content':mark_safe(content)}
    return {'content':''}

def show_placeholder_by_id(context, placeholder_name, reverse_id, lang=None, site=None):
    return _show_placeholder_by_id(context, placeholder_name, reverse_id, lang=lang, site=site)

show_placeholder_by_id = register.inclusion_tag('cms/content.html', takes_context=True)(show_placeholder_by_id)

def show_uncached_placeholder_by_id(context, placeholder_name, reverse_id, lang=None, site=None):
    return _show_placeholder_by_id(context, placeholder_name, reverse_id,
            lang=lang, site=site, cache_result=False)

show_uncached_placeholder_by_id = register.inclusion_tag('cms/content.html', takes_context=True)(show_uncached_placeholder_by_id)

def do_plugins_media(parser, token):
    return PluginsMediaNode()

class PluginsMediaNode(template.Node):
    """This template node is used to output media for plugins.

    eg: {% plugins_media %}
    """
    def render(self, context):
        if not 'request' in context:
            return ''
        request = context['request']
        page = request.current_page
        if page == "dummy":
            return ''
        from cms.plugins.utils import get_plugins_media
        plugins_media = get_plugins_media(request, request._current_page_cache) # make sure the plugin cache is filled
        if plugins_media:
            return plugins_media.render()
        else:
            return u''
        
    def __repr__(self):
        return "<PluginsMediaNode Node: %s>" % self.name
        
register.tag('plugins_media', do_plugins_media)

