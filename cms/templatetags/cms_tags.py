from cms.models import Page, Placeholder
from cms.plugin_rendering import render_plugins, render_placeholder, \
    render_placeholder_toolbar
from cms.plugins.utils import get_plugins
from cms.utils import get_language_from_request, get_template_from_request
from cms.utils.moderator import get_cmsplugin_queryset, get_page_queryset
from django import template
from django.conf import settings
from django.contrib.sites.models import Site
from django.core.cache import cache
from django.core.mail import mail_managers
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from itertools import chain
import operator

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

def has_permission(page, request):
    return page.has_change_permission(request)
register.filter(has_permission)

def _get_cache_key(name, page_lookup, lang, site_id):
    if isinstance(page_lookup, Page):
        page_key = str(page_lookup.pk)
    else:
        page_key = str(page_lookup)
    return name+'__page_lookup:'+page_key+'_site:'+str(site_id)+'_lang:'+str(lang)

def _get_page_by_untyped_arg(page_lookup, request, site_id):
    """
    The `page_lookup` argument can be of any of the following types:
    - Integer: interpreted as `pk` of the desired page
    - String: interpreted as `reverse_id` of the desired page
    - `dict`: a dictionary containing keyword arguments to find the desired page
    (for instance: `{'pk': 1}`)
    - `Page`: you can also pass a Page object directly, in which case there will be no database lookup.
    - `None`: the current page will be used
    """
    if page_lookup is None:
        return request.current_page
    if isinstance(page_lookup, Page):
        return page_lookup
    if isinstance(page_lookup, basestring):
        page_lookup = {'reverse_id': page_lookup}
    elif isinstance(page_lookup, (int, long)):
        page_lookup = {'pk': page_lookup}
    elif not isinstance(page_lookup, dict):
        raise TypeError('The page_lookup argument can be either a Dictionary, Integer, Page, or String.')
    page_lookup.update({'site': site_id})
    try:
        return get_page_queryset(request).get(**page_lookup)
    except Page.DoesNotExist:
        site = Site.objects.get_current()
        subject = _('Page not found on %(domain)s') % {'domain':site.domain}
        body = _("A template tag couldn't find the page with lookup arguments `%(page_lookup)s\n`. "
            "The URL of the request was: http://%(host)s%(path)s") \
            % {'page_lookup': repr(page_lookup), 'host': site.domain, 'path': request.path}
        if settings.DEBUG:
            raise Page.DoesNotExist(body)
        else:
            mail_managers(subject, body, fail_silently=True)
            return None

def page_url(context, page_lookup, lang=None, site=None):
    """
    Show the url of a page with a reverse id in the right language
    This is mostly used if you want to have a static link in a template to a page
    """
    site_id = get_site_id(site)
    request = context.get('request', False)
    if not request:
        return {'content': ''}

    if request.current_page == "dummy":
        return {'content': ''}

    if lang is None:
        lang = get_language_from_request(request)
    cache_key = _get_cache_key('page_url', page_lookup, lang, site_id)+'_type:absolute_url'
    url = cache.get(cache_key)
    if not url:
        page = _get_page_by_untyped_arg(page_lookup, request, site_id)
        if page:
            url = page.get_absolute_url(language=lang)
            cache.set(cache_key, url, settings.CMS_CONTENT_CACHE_DURATION)
    if url:
        return {'content': url}
    return {'content': ''}
page_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_url)

def page_id_url(context, reverse_id, lang=None, site=None):
    return page_url(context, reverse_id, lang, site)
page_id_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_id_url)

def do_placeholder(parser, token):
    error_string = '%r tag requires at least 1 and accepts at most 2 arguments'
    nodelist_or = None
    inherit = False
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
        # if the `placeholderor` tag was used, look for closing tag, and pass the enclosed nodes
        # to PlaceholderNode below
        if bits[-1].lower() == 'or':
            bits.pop()
            nodelist_or = parser.parse(('endplaceholder',))
            parser.delete_first_token()
        elif bits[-1].lower() == 'inherit':
            bits.pop()
            inherit = True
        else:
            bit = bits[-1]
            if bit[0] == bit[-1] and bit[0] in ('"', "'"):
                bit = bit[1:-1]
            if bit.isdigit():
                import warnings
                warnings.warn("The width parameter for the placeholder tag is deprecated.", DeprecationWarning)
    except ValueError:
        raise template.TemplateSyntaxError(error_string % bits[0])
    if len(bits) == 2:
        #tag_name, name
        return PlaceholderNode(bits[1], nodelist_or=nodelist_or, inherit=inherit)
    elif len(bits) == 3:
        #tag_name, name, width
        return PlaceholderNode(bits[1], bits[2], nodelist_or=nodelist_or, inherit=inherit)
    else:
        raise template.TemplateSyntaxError(error_string % bits[0])

class PlaceholderNode(template.Node):
    """This template node is used to output page content and
    is also used in the admin to dynamically generate input fields.

    eg: {% placeholder "placeholder_name" %}

    {% placeholder "sidebar" inherit %}

    {% placeholder "footer" inherit or %}
        <a href="/about/">About us</a>
    {% endplaceholder %}

    Keyword arguments:
    name -- the name of the placeholder
    width -- additional width attribute (integer) which gets added to the plugin context
    (deprecated, use `{% with 320 as width %}{% placeholder "foo"}{% endwith %}`)
    inherit -- optional argument which if given will result in inheriting
        the content of the placeholder with the same name on parent pages
    or -- optional argument which if given will make the template tag a block
        tag whose content is shown if the placeholder is empty
    """
    def __init__(self, name, width=None, nodelist_or=None, inherit=False):
        self.name = "".join(name.lower().split('"'))
        if width:
            self.width_var = template.Variable(width)
        self.nodelist_or = nodelist_or
        self.inherit = inherit

    def __repr__(self):
        return "<Placeholder Node: %s>" % self.name

    def render(self, context):
        if not 'request' in context:
            return ''
        request = context['request']
        width_var = getattr(self, 'width_var', None)
        if width_var:
            try:
                width = int(width_var.resolve(context))
                context.update({'width': width})
            except (template.VariableDoesNotExist, ValueError):
                pass

        page = request.current_page
        if not page or page == 'dummy':
            return ''
        
        content, placeholder = self.get_content(request, page, context)
        if not content:
            if self.nodelist_or:
                content = self.nodelist_or.render(context)
            return content
        return content
    
    @staticmethod
    def _get_placeholder(current_page, page, context, name):
        placeholder_cache = getattr(current_page, '_tmp_placeholders_cache', {})
        if page.pk in placeholder_cache:
            return placeholder_cache[page.pk].get(name, None)
        placeholder_cache[page.pk] = {}
        placeholders = page.placeholders.all()
        for placeholder in placeholders:
            placeholder_cache[page.pk][placeholder.slot] = placeholder
        current_page._tmp_placeholders_cache = placeholder_cache
        return placeholder_cache[page.pk].get(name, None)

    def get_content(self, request, current_page, context):
        pages = [current_page]
        if self.inherit:
            pages = chain([current_page], current_page.get_cached_ancestors(ascending=True))
        for page in pages:
            template = get_template_from_request(request, page)
            placeholder = self._get_placeholder(current_page, page, context, self.name)
            if placeholder is None:
                continue
            if not get_plugins(request, placeholder):
                continue
            if hasattr(request, 'placeholder_media'):
                request.placeholder_media = reduce(operator.add, [request.placeholder_media, placeholder.get_media(request, context)])
            #request.placeholder_media += placeholder.get_media(request, context)
            content = render_placeholder(placeholder, context)
            if content:
                return content, placeholder
        return '', None

register.tag('placeholder', do_placeholder)

def do_page_attribute(parser, token):
    error_string = '%r tag requires one argument' % token.contents[0]
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(bits) >= 2:
        # tag_name, name
        # tag_name, name, page_lookup
        page_lookup = len(bits) == 3 and bits[2] or None
        return PageAttributeNode(bits[1], page_lookup)
    else:
        raise template.TemplateSyntaxError(error_string)

class PageAttributeNode(template.Node):
    """This template node is used to output attribute from a page such
    as its title or slug.

    Synopsis
         {% page_attribute "field-name" %}
         {% page_attribute "field-name" page_lookup %}

    Example
         {# Output current page's page_title attribute: #}
         {% page_attribute "page_title" %}
         {# Output page_title attribute of the page with reverse_id "the_page": #}
         {% page_attribute "page_title" "the_page" %}
         {# Output slug attribute of the page with pk 10: #}
         {% page_attribute "slug" 10 %}

    Keyword arguments:
    field-name -- the name of the field to output. Use one of:
    - title
    - menu_title
    - page_title
    - slug
    - meta_description
    - meta_keywords

    page_lookup -- lookup argument for Page, if omitted field-name of current page is returned.
    See _get_page_by_untyped_arg() for detailed information on the allowed types and their interpretation
    for the page_lookup argument.
    """
    def __init__(self, name, page_lookup=None):
        self.name_var = template.Variable(name)
        self.page_lookup = None
        self.valid_attributes = ["title", "slug", "meta_description", "meta_keywords", "page_title", "menu_title"]
        if page_lookup:
            self.page_lookup_var = template.Variable(page_lookup)

    def render(self, context):
        if not 'request' in context:
            return ''
        var_name = self.name_var.var.lower()
        if var_name in self.valid_attributes:
            # Variable name without quotes works, but is deprecated
            self.name = var_name
        else:
            self.name = self.name_var.resolve(context)
        lang = get_language_from_request(context['request'])
        page_lookup_var = getattr(self, 'page_lookup_var', None)
        if page_lookup_var:
            page_lookup = page_lookup_var.resolve(context)
        else:
            page_lookup = None
        page = _get_page_by_untyped_arg(page_lookup, context['request'], get_site_id(None))
        if page == "dummy":
            return ''
        if page and self.name in self.valid_attributes:
            f = getattr(page, "get_"+self.name)
            return f(language=lang, fallback=True)
        return ''

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

def _show_placeholder_for_page(context, placeholder_name, page_lookup, lang=None,
        site=None, cache_result=True):
    """
    Shows the content of a page with a placeholder name and given lookup arguments in the given language.
    This is useful if you want to have some more or less static content that is shared among many pages,
    such as a footer.

    See _get_page_by_untyped_arg() for detailed information on the allowed types and their interpretation
    for the page_lookup argument.
    """
    request = context.get('request', False)
    site_id = get_site_id(site)

    if not request:
        return {'content': ''}
    if lang is None:
        lang = get_language_from_request(request)

    content = None

    if cache_result:
        cache_key = _get_cache_key('_show_placeholder_for_page', page_lookup, lang, site_id)+'_placeholder:'+placeholder_name
        content = cache.get(cache_key)

    if not content:
        page = _get_page_by_untyped_arg(page_lookup, request, site_id)
        if not page:
            return {'content': ''}
        placeholder = page.placeholders.get(slot=placeholder_name)
        plugins = get_cmsplugin_queryset(request).filter(placeholder=placeholder, language=lang, placeholder__slot__iexact=placeholder_name, parent__isnull=True).order_by('position').select_related()
        c = render_plugins(plugins, context, placeholder)
        content = "".join(c)

    if cache_result:
        cache.set(cache_key, content, settings.CMS_CONTENT_CACHE_DURATION)

    if content:
        return {'content': mark_safe(content)}
    return {'content': ''}

def show_placeholder_by_id(context, placeholder_name, reverse_id, lang=None, site=None):
    """
    Show the content of a specific placeholder, from a page found by reverse id, in the given language.
    This templatetag is deprecated, replace with `show_placeholder`.
    """
    return _show_placeholder_for_page(context, placeholder_name, reverse_id, lang=lang, site=site)
show_placeholder_by_id = register.inclusion_tag('cms/content.html', takes_context=True)(show_placeholder_by_id)

def show_uncached_placeholder_by_id(context, placeholder_name, reverse_id, lang=None, site=None):
    """
    Show the uncached content of a specific placeholder, from a page found by reverse id, in the given language.
    This templatetag is deprecated, replace with `show_uncached_placeholder`.
    """
    return _show_placeholder_for_page(context, placeholder_name, reverse_id,
            lang=lang, site=site, cache_result=False)
show_uncached_placeholder_by_id = register.inclusion_tag('cms/content.html', takes_context=True)(show_uncached_placeholder_by_id)

def show_placeholder(context, placeholder_name, page_lookup, lang=None, site=None):
    """
    Show the content of a specific placeholder, from a page found by pk|reverse_id|dict
    or passed to the function, in the given language.
    """
    return _show_placeholder_for_page(context, placeholder_name, page_lookup, lang=lang, site=site)
show_placeholder_for_page = register.inclusion_tag('cms/content.html', takes_context=True)(show_placeholder)

def show_uncached_placeholder(context, placeholder_name, page_lookup, lang=None, site=None):
    """
    Show the uncached content of a specific placeholder, from a page found by pk|reverse_id|dict
    or passed to the function, in the given language.
    """
    return _show_placeholder_for_page(context, placeholder_name, page_lookup, lang=lang, site=site, cache_result=False)
show_uncached_placeholder_for_page = register.inclusion_tag('cms/content.html', takes_context=True)(show_uncached_placeholder)

def do_plugins_media(parser, token):
    args = token.split_contents()
    if len(args) > 2:
        raise template.TemplateSyntaxError("Invalid syntax. Expected "
            "'{%% %s [page_lookup] %%}'" % args[0])
    elif len(args) == 2:
        page_lookup = args[1]
    else:
        page_lookup = None
    return PluginsMediaNode(page_lookup)


class PluginsMediaNode(template.Node):
    """
    This template node is used to output media for plugins.

    eg: {% plugins_media %}

    You can also pass the object a page_lookup arg if you want to output media tags for a specific
    page other than the current page.

    eg: {% plugins_media "gallery" %}
    """

    def __init__(self, page_lookup=None):
        if page_lookup:
            self.page_lookup_var = template.Variable(page_lookup)

    def render(self, context):
        from cms.plugins.utils import get_plugins_media
        if not 'request' in context:
            return ''
        request = context['request']
        from cms.plugins.utils import get_plugins_media
        plugins_media = None
        page_lookup_var = getattr(self, 'page_lookup_var', None)
        if page_lookup_var:
            page_lookup = page_lookup_var.resolve(context)
            page = _get_page_by_untyped_arg(page_lookup, request, get_site_id(None))
            plugins_media = get_plugins_media(request, context, page)
        else:
            page = request.current_page
            if page == "dummy":
                return ''
            # make sure the plugin cache is filled
            plugins_media = get_plugins_media(request, context, request._current_page_cache)
        if plugins_media:
            return plugins_media.render()
        else:
            return u''

    def __repr__(self):
        return "<PluginsMediaNode Node: %s>" % getattr(self, 'name', '')

register.tag('plugins_media', do_plugins_media)

