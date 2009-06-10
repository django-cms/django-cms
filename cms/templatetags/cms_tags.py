from django import template
from django.core.cache import cache
from cms import settings
from cms.utils import get_language_from_request,\
    get_extended_navigation_nodes, find_children, cut_levels, find_selected
from django.core.mail import send_mail
from django.contrib.sites.models import Site
from django.utils.safestring import mark_safe
from cms.utils.moderator import get_page_model, get_title_model, get_cmsplugin_model
register = template.Library()


def show_menu(context, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template="cms/menu.html", next_page=None, root_page=None):
    """
    render a nested list of all children of the pages
    from_level: is the start level
    to_level: is the max level rendered
    render_children: if set to True will render all not direct ascendants too
    """
    request = context['request']
    PageModel = get_page_model(request)
    TitleModel = get_title_model(request)
    
    site = Site.objects.get_current()
    CMS_CONTENT_CACHE_DURATION = settings.CMS_CONTENT_CACHE_DURATION
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
            extenders = PageModel.objects.published().filter(in_navigation=True, 
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
        
        soft_root_start = 0
        for p in alist:
            ancestors.append(p[0])
            if p[1]:
                soft_root = PageModel.objects.get(pk=p[0])
                filters['lft__gte'] = soft_root.lft
                filters['rght__lte'] = soft_root.rght
                filters['tree_id'] = soft_root.tree_id
                from_level = soft_root.level
                soft_root_start = soft_root.level
        if current_page and current_page.soft_root: 
            filters['tree_id'] = current_page.tree_id
            filters['lft__gte'] = current_page.lft
            filters['rght__lte'] = current_page.rght
            from_level = current_page.level
            soft_root_start = current_page.level
        if root_page:
            root_page = PageModel.objects.get(reverse_id=root_page)
            filters['tree_id'] = root_page.tree_id
            filters['lft__gt'] = root_page.lft
            filters['rght__lt'] = root_page.rght
        if settings.CMS_HIDE_UNTRANSLATED:
            filters['title_set__language'] = lang
        pages = PageModel.objects.published().filter(**filters).order_by('tree_id', 
                                                                    'parent', 
                                                                    'lft')
        pages = list(pages)
        all_pages = pages[:]
        for page in pages:# build the tree
            if page.level >= from_level:
                ids.append(page.pk)
            if page.level == 0 or page.level == soft_root_start or page.level-1 == getattr(root_page, 'level', None):
                page.ancestors_ascending = []
                children.append(page)
                if current_page and page.pk == current_page.pk and current_page.soft_root:
                    page.soft_root = False #ugly hack for the recursive function
                if current_page:
                    pk = current_page.pk
                else:
                    pk = -1
                find_children(page, pages, extra_inactive, extra_active, ancestors, pk, request=request, to_levels=to_level)
                if current_page and page.pk == current_page.pk and current_page.soft_root:
                    page.soft_root = True
        if from_level > 0:
            children = cut_levels(children, from_level)
        titles = list(TitleModel.objects.filter(page__in=ids, language=lang))
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


def show_menu_below_id(context, root_page=None, from_level=0, to_level=100, extra_inactive=0, extra_active=100, template_file="cms/menu.html", next_page=None):
    return show_menu(context, from_level, to_level, extra_inactive, extra_active, template_file, next_page, root_page=root_page)
register.inclusion_tag('cms/dummy.html', takes_context=True)(show_menu_below_id)


def show_sub_menu(context, levels=100, template="cms/sub_menu.html"):
    """Get the root page of the current page and 
    render a nested list of all root's children pages"""
    request = context['request']
    PageModel = get_page_model(request)
    TitleModel = get_title_model(request)
    
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
        pages = PageModel.objects.published().filter(**filters)
        ids = []
        pages = list(pages)
        all_pages = pages[:]
        page.ancestors_ascending = []
        for p in pages:
            p.descendant  = True
            ids.append(p.pk)
        page.selected = True
        find_children(page, pages, levels, levels, [], page.pk, request=request)
        children = page.childrens
        titles = TitleModel.objects.filter(page__in=ids, language=lang)
        for p in all_pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == p.pk:
                    p.title_cache = title
        from_level = page.level
        to_level = page.level+levels
        extra_active = extra_inactive = levels
    else:
        extenders = PageModel.objects.published().filter(in_navigation=True, 
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
                                            

def show_breadcrumb(context, start_level=0, template="cms/breadcrumb.html"):
    request = context['request']
    PageModel = get_page_model(request)
    TitleModel = get_title_model(request)
    
    page = request.current_page
    lang = get_language_from_request(request)
    if page:
        ancestors = list(page.get_ancestors())
        ancestors.append(page)
        ids = [page.pk]
        for anc in ancestors:
            ids.append(anc.pk)
        titles = TitleModel.objects.filter(page__in=ids, language=lang)
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
        extenders = PageModel.objects.published().filter(in_navigation=True, 
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
                                         

def render_plugin(context, plugin_id):
    CMSPluginModel = get_cmsplugin_model(context['request'])
    plugin = CMSPluginModel.objects.get(pk=plugin_id)
    content = plugin.render(context)
    return  locals()
render_plugin = register.inclusion_tag('cms/plugin_base.html', takes_context=True)(render_plugin)

#def render_plugin_title(context, plugin_id):
    

def has_permission(page, request):
    return page.has_change_permission(request)
register.filter(has_permission)


def page_id_url(context, reverse_id, lang=None):
    """
    Show the url of a page with a reverse id in the right language
    This is mostly used if you want to have a static link in a template to a page
    """
    request = context.get('request', False)
    if not request:
        return {'content':''}
    
    PageModel = get_page_model(request)
    
    if lang is None:
        lang = get_language_from_request(request)
    key = 'page_id_url_pid:'+reverse_id+'_l:'+str(lang)+'_type:absolute_url'
    url = cache.get(key)
    if not url:
        try:
            page = PageModel.objects.get(reverse_id=reverse_id)
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
        CMSPluginModel = get_cmsplugin_model(request)
        page = request.current_page
        plugins = CMSPluginModel.objects.filter(page=page, language=l, placeholder__iexact=self.name, parent__isnull=True).order_by('position').select_related()
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
    PageModel = get_page_model(request)
    CMSPluginModel = get_cmsplugin_model(request)
    
    if not request:
        return {'content':''}
    if lang is None:
        lang = get_language_from_request(request)
    key = 'show_placeholder_by_id_pid:'+reverse_id+'placeholder:'+placeholder_name+'_l:'+str(lang)
    content = cache.get(key)
    if not content:
        try:
            page = PageModel.objects.get(reverse_id=reverse_id)
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

        plugins = CMSPluginModel.objects.filter(page=page, language=lang, placeholder__iexact=placeholder_name, parent__isnull=True).order_by('position').select_related()
        content = ""
        for plugin in plugins:
            content += plugin.render_plugin(context, placeholder_name)

    cache.set(key, content, settings.CMS_CONTENT_CACHE_DURATION)

    if content:
        return {'content':mark_safe(content)}
    return {'content':''}
show_placeholder_by_id = register.inclusion_tag('cms/content.html', takes_context=True)(show_placeholder_by_id)
