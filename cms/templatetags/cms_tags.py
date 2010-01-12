from django.conf import settings
from django import template
from django.core.cache import cache
from django.core.mail import send_mail, mail_managers
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from django.utils.translation import ugettext_lazy as _
from cms.exceptions import NoHomeFound
from cms.models import Page
from cms.utils.moderator import get_cmsplugin_queryset, get_page_queryset, get_title_queryset
from cms.utils.plugin import render_plugins_for_context
from cms.utils import get_language_from_request,\
    get_extended_navigation_nodes, find_children, \
    cut_levels, find_selected, mark_descendants
from cms.utils import navigation
from cms.utils.i18n import get_fallback_languages
from django.template.defaultfilters import title
from django.template import TemplateSyntaxError, Node
from django.utils.translation import get_language
from django.utils.encoding import smart_str



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

def show_menu(context, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template="cms/menu.html", next_page=None, root_id=None):
    """
    render a nested list of all children of the pages
    from_level: is the start level
    to_level: is the max level rendered
    render_children: if set to True will render all not direct ascendants too
    """
    try:
        # If there's an exception (500), default context_processors may not be called.
        request = context['request']
    except KeyError:
        return {'template': 'cms/content.html'}
    page_queryset = get_page_queryset(request)
    site = Site.objects.get_current()
    lang = get_language_from_request(request)
    current_page = request.current_page
    if current_page == "dummy":
        context.update({'children':[],
                    'template':template,
                    'from_level':from_level,
                    'to_level':to_level,
                    'extra_inactive':extra_inactive,
                    'extra_active':extra_active})
        return context
    if hasattr(current_page, "home_pk_cache"):
        home_pk = current_page.home_pk_cache
    else:
        try:
            home_pk = page_queryset.get_home(site).pk
        except NoHomeFound:
            home_pk = 0
    if not next_page: #new menu... get all the data so we can save a lot of queries
        
        children = []
        ancestors = []
        alist = None
        if current_page:
            alist = current_page.get_ancestors().values_list('id', 'soft_root')
        if not alist:  # == None:# maybe the active node is in an extender?
            alist = []
            extenders = page_queryset.published().filter(in_navigation=True, 
                                                        site=site, 
                                                        level__lte=to_level)
            extenders = extenders.exclude(navigation_extenders__isnull=True).exclude( navigation_extenders__exact="")
            for ext in extenders:
                ext.childrens = []
                ext.ancestors_ascending = []
                get_extended_navigation_nodes(request, 100, [ext], ext.level, 100, 100, False, ext.navigation_extenders)
                if hasattr(ext, "ancestor"):
                    alist = list(ext.get_ancestors().values_list('id', 'soft_root'))
                    alist = [(ext.pk, ext.soft_root)] + alist
                    break
        filters = {'in_navigation' : True, 
                   'site' : site,
                   'level__lte' : to_level}
        #check the ancestors for softroots
        soft_root_pk = None
        for p in alist:
            ancestors.append(p[0])
            if p[1]:
                soft_root_pk = p[0]
        #modify filters if we don't start from the root
        root_page = None
        if root_id:
            try:
                root_page = page_queryset.get(reverse_id=root_id, site=site)
            except:
                send_missing_mail(root_id, request)
        else:
            if current_page and current_page.soft_root:
                root_page = current_page
                soft_root_pk = current_page.pk
            elif soft_root_pk:
                root_page = page_queryset.get(pk=soft_root_pk)
        if root_page:
            if isinstance(root_page, int):
                root_page = page_queryset.get(pk=root_page)
            if isinstance(root_page, Page):
                root_page = page_queryset.get(pk=root_page.id)
            elif isinstance(root_page, unicode):
                root_page = page_queryset.get(reverse_id=root_page, site=site)
            filters['tree_id'] = root_page.tree_id
            filters['lft__gt'] = root_page.lft
            filters['rght__lt'] = root_page.rght
            filters['level__lte'] = root_page.level + to_level
            db_from_level = root_page.level + from_level
        else:
            db_from_level = from_level
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        if not request.user.is_authenticated():
            filters['menu_login_required'] = False
        pages = page_queryset.published().filter(**filters).order_by('tree_id', 
                                                                    'parent', 
                                                                    'lft')
        pages = list(pages)
        if root_page:
            pages = [root_page] + pages
        all_pages = pages[:]
        root_level = getattr(root_page, 'level', None)
        ids = []
        current = None
        for page in pages:# build the tree
            if current_page and current_page.pk == page.pk:
                current = page
            if page.level >= db_from_level:
                ids.append(page.pk)
            if page.level == 0 or page.level == root_level:
                if page.parent_id:
                    page.get_cached_ancestors()
                else:
                    page.ancestors_ascending = []
                page.home_pk_cache = home_pk
                page.menu_level = 0 - from_level
                page.childrens = []
                children.append(page)
                if page.pk == soft_root_pk:
                    page.soft_root = False #ugly hack for the recursive function
                if current_page:
                    pk = current_page.pk
                else:
                    pk = -1
                find_children(page, pages, extra_inactive, extra_active, ancestors, pk, request=request, to_levels=to_level)
                if page.pk == soft_root_pk:
                    page.soft_root = True
        if db_from_level > 0:
            children = cut_levels(children, db_from_level)
        titles = list(get_title_queryset(request).filter(page__in=ids, language=lang))
        for page in all_pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == page.pk:
                    if not hasattr(page, "title_cache"):
                        page.title_cache = {}
                    page.title_cache[title.language] = title
                    ids.remove(page.pk)
            if current_page and page.pk == current_page.pk and not getattr(current, 'ancestor', False):
                    page.selected = True
                    if hasattr(page, "childrens"):
                        mark_descendants(page.childrens)
            if page.pk in ancestors:
                page.ancestor = True
            if current_page and page.parent_id == current_page.parent_id and not page.pk == current_page.pk and not getattr(current, 'ancestor', False):
                page.sibling = True
        if ids:
            fallbacks = get_fallback_languages(lang)
            for l in fallbacks:
                titles = list(get_title_queryset(request).filter(page__in=ids, language=l))
                for page in all_pages:# add the title and slugs and some meta data
                    for title in titles:
                        if title.page_id == page.pk:
                            if not hasattr(page, "title_cache"):
                                page.title_cache = {}
                            page.title_cache[title.language] = title
                            ids.remove(page.pk)
                if not ids:
                    break
        children = navigation.handle_navigation_manipulators(children, request)
    else:
        children = next_page.childrens
    context.update({'children':children,
                    'template':template,
                    'from_level':from_level,
                    'to_level':to_level,
                    'extra_inactive':extra_inactive,
                    'extra_active':extra_active})
    return context
show_menu = register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu)


def show_menu_below_id(context, root_id=None, from_level=0, to_level=100, extra_inactive=100, extra_active=100, template_file="cms/menu.html", next_page=None):
    return show_menu(context, from_level, to_level, extra_inactive, extra_active, template_file, next_page, root_id=root_id)
register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu_below_id)


def show_sub_menu(context, levels=100, template="cms/sub_menu.html"):
    """Get the root page of the current page and 
    render a nested list of all root's children pages"""
    request = context['request']
    page_queryset = get_page_queryset(request)
    
    lang = get_language_from_request(request)
    site = Site.objects.get_current()
    children = []
    page = request.current_page
    if page == "dummy":
        context.update({'children':[],
                        'template':template,
                        'from_level':0,
                        'to_level':0,
                        'extra_inactive':0,
                        'extra_active':0
                        })
        return context
    
    if page:
        page.get_cached_ancestors()
        # this is not required anymore, sice home_pk_cache is a getter 
        #if not hasattr(page, "home_pk_cache"):
        #    page.home_pk_cache = page_queryset.get_home(site).pk
        filters = {'in_navigation':True, 
                  'lft__gt':page.lft, 
                  'rght__lt':page.rght, 
                  'tree_id':page.tree_id, 
                  'level__lte':page.level+levels, 
                  'site':site}
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        if not request.user.is_authenticated():
            filters['menu_login_required'] = False
        pages = page_queryset.published().filter(**filters)
       
        ids = []
        pages = list(pages)
        all_pages = pages[:]
        
        page.childrens = []
        for p in pages:
            p.descendant  = True
            ids.append(p.pk)
        page.selected = True
        page.menu_level = -1
        was_soft_root = False
        if page.soft_root:
            was_soft_root = True
            page.soft_root = False
        find_children(page, pages, levels, levels, [], page.pk, request=request)
        if was_soft_root:
            page.soft_root = True
        children = page.childrens
        titles = get_title_queryset(request).filter(page__in=ids, language=lang)
        for p in all_pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == p.pk:
                    if not hasattr(p, "title_cache"):
                        p.title_cache = {}
                    p.title_cache[title.language] = title
        from_level = page.level
        to_level = page.level+levels
        extra_active = extra_inactive = levels
    else:
        extenders = page_queryset.published().filter(in_navigation=True, site=site)
        extenders = extenders.exclude(navigation_extenders__isnull=True).exclude(navigation_extenders__exact="")
        children = []
        from_level = 0
        to_level = 0
        extra_active = 0
        extra_inactive = 0
        for ext in extenders:
            ext.childrens = []
            ext.ancestors_ascending = []
            nodes = get_extended_navigation_nodes(request, 100, [ext], ext.level, 100, levels, False, ext.navigation_extenders)
            if hasattr(ext, "ancestor"):
                selected = find_selected(nodes)
                if selected:
                    children = selected.childrens
                    from_level = selected.level
                    to_level =  from_level+levels
                    extra_active = extra_inactive = levels
    children = navigation.handle_navigation_manipulators(children, request)
    context.update({'children':children,
                    'template':template,
                    'from_level':from_level,
                    'to_level':to_level,
                    'extra_inactive':extra_inactive,
                    'extra_active':extra_active})
    return context
show_sub_menu = register.inclusion_tag('cms/dummy.html',
                                       takes_context=True)(show_sub_menu)
                                            

def show_breadcrumb(context, start_level=0, template="cms/breadcrumb.html"):
    request = context['request']
    page_queryset = get_page_queryset(request)
    title_queryset = get_title_queryset(request) 
    
    page = request.current_page
    if page == "dummy":
        context.update({
            'ancestors': [],
            'template': template,
        })
        return context
    lang = get_language_from_request(request)
    if page and not page.navigation_extenders:
        ancestors = ancestors_from_page(page, page_queryset, title_queryset, lang)
    else:
        site = Site.objects.get_current()
        ancestors = []
        extenders = page_queryset.published().filter(site=site)
        extenders = extenders.exclude(navigation_extenders__isnull=True).exclude(navigation_extenders__exact="")
        for ext in extenders:
            ext.childrens = []
            ext.ancestors_ascending = []
            nodes = get_extended_navigation_nodes(request, 100, [ext], ext.level, 100, 0, False, ext.navigation_extenders)
            if hasattr(ext, "ancestor"):
                selected = find_selected(nodes)
                if selected:
                    ancestors = list(ext.get_ancestors()) + [ext]
                    home = page_queryset.get_home()
                    if ancestors and ancestors[0].pk != home.pk: 
                        ancestors = [home] + ancestors
                    ids = []
                    for anc in ancestors:
                        ids.append(anc.pk)
                    titles = title_queryset.filter(page__in=ids, language=lang)
                    ancs = []
                    for anc in ancestors:
                        anc.home_pk_cache = home.pk
                        anc.ancestors_ascending = ancs[:]
                        ancs += [anc]
                        for title in titles:
                            if title.page_id == anc.pk:
                                if not hasattr(anc, "title_cache"):
                                    anc.title_cache = {}
                                anc.title_cache[title.language] = title
                    ancestors = ancestors + selected.ancestors_ascending[1:] + [selected]
        if not ancestors and page:
            ancestors = ancestors_from_page(page, page_queryset, title_queryset, lang)
    if len(ancestors) > start_level:
        ancestors = ancestors[start_level:]
    else:
        ancestors = []
    context.update({'ancestors':ancestors,
                    'template': template})
    return context
show_breadcrumb = register.inclusion_tag('cms/dummy.html',
                                         takes_context=True)(show_breadcrumb)
                                         
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


def page_language_url(context, lang):
    """
    Displays the url of the current page in the defined language.
    You can set a language_changer function with the set_language_changer function in the utils.py if there is no page.
    This is needed if you have slugs in more than one language.
    """
    if not 'request' in context:
        return ''
    
    request = context['request']
    page = request.current_page
    if page == "dummy":
        return ''
    if hasattr(request, "_language_changer"):
        url = "/%s" % lang + request._language_changer(lang)
    else:
        try:
            url = "/%s" % lang + page.get_absolute_url(language=lang, fallback=False)
        except:
            url = "/%s/" % lang 
    if url:
        return {'content':url}
    return {'content':''}
page_language_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_language_url)


def language_chooser(context, template="cms/language_chooser.html"):
    """
    Displays a language chooser
    """
    if not 'request' in context:
        return ''
    
    request = context['request']
    languages = []
    cms_languages = dict(settings.CMS_LANGUAGES)
    for lang in settings.CMS_FRONTEND_LANGUAGES:
        if lang in cms_languages:
            languages.append((lang, cms_languages[lang]))
    lang = get_language_from_request(request, request.current_page)
    context.update(locals())
    return context
language_chooser = register.inclusion_tag('cms/dummy.html', takes_context=True)(language_chooser)

def do_placeholder(parser, token):
    error_string = '%r tag requires at least 1 and accepts at most 2 arguments' % token.contents[0]
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(bits) == 2:
        #tag_name, name
        return PlaceholderNode(bits[1])
    elif len(bits) == 3:
        #tag_name, name, width
        return PlaceholderNode(bits[1], bits[2])
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
    def __init__(self, name, width=None):
        self.name = "".join(name.lower().split('"'))
        if width: self.width = template.Variable(width)

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
        return render_plugins_for_context(self.name, page, context, width)
 
    def __repr__(self):
        return "<Placeholder Node: %s>" % self.name

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
        # tag_name, name, reverse_id
        reverse_id = bits[2] if len(bits) == 3 else None 
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

