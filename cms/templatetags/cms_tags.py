from django import template
from django.core.cache import cache

from cms import settings
from cms.models import Page, Title, CMSPlugin
from cms.utils import get_language_from_request,\
    get_extended_navigation_nodes, find_children, cut_levels, find_selected
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
register = template.Library()


def show_menu(context, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template="cms/menu.html", next_page=None, root_id=None):
    """
    render a nested list of all children of the pages
    from_level: is the start level
    to_level: is the max level rendered
    render_children: if set to True will render all not direct ascendants too
    """
    request = context['request']
    site = Site.objects.get_current()
    lang = get_language_from_request(request)
    current_page = request.current_page
   
    if not next_page: #new menu... get all the data so we can save a lot of queries
        ids = []
        children = []
        ancestors = []
        if current_page:
            alist = current_page.get_ancestors().values_list('id', 'soft_root')
        else:# maybe the active node is in an extender?
            alist = []
            extenders = Page.objects.published().filter(in_navigation=True, 
                                                        sites__domain=site.domain, 
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
                   'sites__domain' : site.domain,
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
            root_page = Page.objects.get(reverse_id=root_page)
        else:
            if current_page and current_page.soft_root:
                root_page = current_page
                soft_root_pk = current_page.pk
            elif soft_root_pk:
                root_page = Page.objects.get(pk=soft_root_pk)
        if root_page:
            filters['tree_id'] = root_page.tree_id
            filters['lft__gt'] = root_page.lft
            filters['rght__lt'] = root_page.rght
            filters['level__lte'] = root_page.level + to_level
            db_from_level = root_page.level + from_level
        else:
            db_from_level = from_level
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        pages = Page.objects.published().filter(**filters).order_by('tree_id', 
                                                                    'parent', 
                                                                    'lft')
        pages = list(pages)
        if root_page:
            pages = [root_page] + pages
        all_pages = pages[:]
        root_level = getattr(root_page, 'level', None)
        for page in pages:# build the tree
            if page.level >= db_from_level:
                ids.append(page.pk)
            if page.level == 0 or page.level == root_level:
                page.ancestors_ascending = []
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
        titles = list(Title.objects.filter(page__in=ids, language=lang))
        for page in all_pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == page.pk:
                    page.title_cache = title
                    #titles.remove(title)
            if page.pk in ancestors:
                page.ancestor = True
            if current_page and page.parent_id == current_page.parent_id and not page.pk == current_page.pk:
                page.sibling = True
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


def show_menu_below_id(context, root_id=None, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template_file="cms/menu.html", next_page=None):
    return show_menu(context, from_level, to_level, extra_inactive, extra_active, template_file, next_page, root_id=root_id)
register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu_below_id)


def show_sub_menu(context, levels=100, template="cms/sub_menu.html"):
    """Get the root page of the current page and 
    render a nested list of all root's children pages"""
    request = context['request']
    lang = get_language_from_request(request)
    site = Site.objects.get_current()
    children = []
    page = request.current_page
    if page:
        root = page.get_root()
        filters = {'in_navigation':True, 
                  'lft__gt':page.lft, 
                  'rght__lt':page.rght, 
                  'tree_id':page.tree_id, 
                  'level__lte':page.level+levels, 
                  'sites__domain':site.domain}
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        pages = Page.objects.published().filter(**filters)
        ids = []
        pages = list(pages)
        all_pages = pages[:]
        page.ancestors_ascending = []
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
        titles = Title.objects.filter(page__in=ids, language=lang)
        for p in all_pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == p.pk:
                    p.title_cache = title
        from_level = page.level
        to_level = page.level+levels
        extra_active = extra_inactive = levels
    else:
        extenders = Page.objects.published().filter(in_navigation=True, 
                                                    sites__domain=site.domain)
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
    context.update({'children':children,
                    'template':template,
                    'from_level':from_level,
                    'to_level':to_level,
                    'extra_inactive':extra_inactive,
                    'extra_active':extra_active})
    return context
show_sub_menu = register.inclusion_tag('cms/dummy.html',
                                       takes_context=True)(show_sub_menu)

                                            
def show_admin_menu(context, page, no_children=False, level=None):
    """Render the admin table of pages"""
    request = context['request']
    site = Site.objects.get_current()
    lang = get_language_from_request(request)
    softroot = context['softroot']
    if context.has_key("cl"):
        filtered = context['cl'].is_filtered()
    elif context.has_key('filtered'):
        filtered = context['filtered']
    children = page.childrens
    has_permission = page.has_page_permission(request)
    has_publish_permission = page.has_publish_permission(request)
    # level is used to add a left margin on table row
    if level is None:
        level = 0
    else:
        level = level+2
    context.update(locals())
    return context
show_admin_menu = register.inclusion_tag('admin/cms/page/menu.html',
                                         takes_context=True)(show_admin_menu)

def show_breadcrumb(context, start_level=0, template="cms/breadcrumb.html"):
    request = context['request']
    page = request.current_page
    lang = get_language_from_request(request)
    if page:
        ancestors = list(page.get_ancestors())
        ancestors.append(page)
        ids = [page.pk]
        for anc in ancestors:
            ids.append(anc.pk)
        titles = Title.objects.filter(page__in=ids, language=lang)
        for anc in ancestors:
            for title in titles:
                if title.page_id == anc.pk:
                    anc.title_cache = title
        for title in titles:
            if title.page_id == page.pk:
                page.title_cache = title
    else:
        site = Site.objects.get_current()
        ancestors = []
        extenders = Page.objects.published().filter(in_navigation=True, 
                                                    sites__domain=site.domain)
        extenders = extenders.exclude(navigation_extenders__isnull=True).exclude(navigation_extenders__exact="")
        for ext in extenders:
            ext.childrens = []
            ext.ancestors_ascending = []
            nodes = get_extended_navigation_nodes(request, 100, [ext], ext.level, 100, 0, False, ext.navigation_extenders)
            if hasattr(ext, "ancestor"):
                selected = find_selected(nodes)
                if selected:
                    ancestors = list(ext.get_ancestors()) + [ext]
                    ids = []
                    for anc in ancestors:
                        ids.append(anc.pk)
                    titles = Title.objects.filter(page__in=ids, language=lang)
                    ancs = []
                    for anc in ancestors:
                        anc.ancestors_ascending = ancs[:]
                        ancs += [anc]
                        for title in titles:
                            if title.page_id == anc.pk:
                                anc.title_cache = title
                    ancestors = ancestors + selected.ancestors_ascending[1:] + [selected]
    context.update(locals())
    return context
show_breadcrumb = register.inclusion_tag('cms/dummy.html',
                                         takes_context=True)(show_breadcrumb)

def has_permission(page, request):
    return page.has_page_permission(request)
register.filter(has_permission)


def page_id_url(context, reverse_id, lang=None):
    """
    Show the url of a page with a reverse id in the right language
    This is mostly used if you want to have a static link in a template to a page
    """
    request = context.get('request', False)
    if not request:
        return {'content':''}
    if lang is None:
        lang = get_language_from_request(request)
    key = 'page_id_url_pid:'+reverse_id+'_l:'+str(lang)+'_type:absolute_url'
    url = cache.get(key)
    if not url:
        try:
            page = Page.objects.get(reverse_id=reverse_id)
        except:
            if settings.DEBUG:
                raise
            else:
                site = Site.objects.get_current()
                send_mail(_('Reverse ID not found on %(domain)s') % {'domain':site.domain},
                          _("A page_id_url template tag didn't found a page with the reverse_id %(reverse_id)s\n"
                            "The url of the page was: http://%(host)s%(path)s")
                            % {'reverse_id':reverse_id, 'host':request.host, 'path':request.path},
                          settings.DEFAULT_FROM_EMAIL,
                          settings.MANAGERS, 
                          fail_silently=True)

        url = page.get_absolute_url(language=lang)
        cache.set(key, url, settings.CMS_CONTENT_CACHE_DURATION)
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
    if hasattr(request, "_language_changer"):
        url = "/%s" % lang + request._language_changer(lang)
    else:
        try:
            url = "/%s" % lang + page.get_absolute_url(language=lang, fallback=not settings.CMS_HIDE_UNTRANSLATED)
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
    languages = settings.LANGUAGES
    lang = get_language_from_request(request, request.current_page)
    context.update(locals())
    return context
language_chooser = register.inclusion_tag('cms/dummy.html', takes_context=True)(language_chooser)

def do_placeholder(parser, token):
    error_string = '%r tag requires three arguments' % token.contents[0]
    try:
        # split_contents() knows not to split quoted strings.
        bits = token.split_contents()
    except ValueError:
        raise template.TemplateSyntaxError(error_string)
    if len(bits) == 2:
        #tag_name, name
        return PlaceholderNode(bits[1])
    elif len(bits) == 3:
        #tag_name, name, widget
        return PlaceholderNode(bits[1], bits[2])
    else:
        raise template.TemplateSyntaxError(error_string)

class PlaceholderNode(template.Node):
    """This template node is used to output page content and
    is also used in the admin to dynamicaly generate input fields.
    
    eg: {% placeholder content-type-name page-object widget-name %}
    
    Keyword arguments:
    content-type-name -- the content type you want to show/create
    page-object -- the page object
    widget-name -- the widget name you want into the admin interface. Take
        a look into pages.admin.widgets to see which widgets are available.
    """
    def __init__(self, name, plugins=None):
        self.name = name.lower()
        if plugins:
            self.plugins = plugins
        else:
            self.plugins = []
        

    def render(self, context):
        if not 'request' in context:
            return ''
        l = get_language_from_request(context['request'])
        request = context['request']
        page = request.current_page
        plugins = CMSPlugin.objects.filter(page=page, language=l, placeholder__iexact=self.name, parent__isnull=True).order_by('position').select_related()
        if settings.CMS_PLACEHOLDER_CONF and self.name in settings.CMS_PLACEHOLDER_CONF:
            if "extra_context" in settings.CMS_PLACEHOLDER_CONF[self.name]:
                context.update(settings.CMS_PLACEHOLDER_CONF[self.name]["extra_context"])
        c = ""
        for plugin in plugins:
            c += plugin.render_plugin(context, self.name)
        return c
        
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
    if len(bits) == 2:
        #tag_name, name
        return PageAttributeNode(bits[1])
    else:
        raise template.TemplateSyntaxError(error_string)

class PageAttributeNode(template.Node):
    """This template node is used to output attribute from page such
    as its title and slug.
    
    eg: {% page attribute field-name %}
    
    Keyword arguments:
    field-name -- the name of the field to output. One of "title",
    "slug", "meta_description" or "meta_keywords"
    """
    def __init__(self, name):
        self.name = name.lower()

    def render(self, context):
        if not 'request' in context:
            return ''
        lang = get_language_from_request(context['request'])
        request = context['request']
        page = request.current_page
        if page and self.name in ["title", "slug", "meta_description", "meta_keywords", "page_title", "menu_title"]:
            f = getattr(page, "get_"+self.name)
            return f(language=lang, fallback=True)
        else:
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


def show_placeholder_by_id(context, placeholder_name, reverse_id, lang=None):
    """
    Show the content of a page with a placeholder name and a reverse id in the right language
    This is mostly used if you want to have static content in a template of a page (like a footer)
    """
    request = context.get('request', False)
    if not request:
        return {'content':''}
    if lang is None:
        lang = get_language_from_request(request)
    key = 'show_placeholder_by_id_pid:'+reverse_id+'placeholder:'+placeholder_name+'_l:'+str(lang)
    content = cache.get(key)
    if not content:
        try:
            page = Page.objects.get(reverse_id=reverse_id)
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

        plugins = CMSPlugin.objects.filter(page=page, language=lang, placeholder__iexact=placeholder_name, parent__isnull=True).order_by('position').select_related()
        content = ""
        for plugin in plugins:
            content += plugin.render_plugin(context, placeholder_name)

    cache.set(key, content, settings.CMS_CONTENT_CACHE_DURATION)

    if content:
        return {'content':mark_safe(content)}
    return {'content':''}
show_placeholder_by_id = register.inclusion_tag('cms/content.html', takes_context=True)(show_placeholder_by_id)


