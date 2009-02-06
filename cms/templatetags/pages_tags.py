from django import template
from django.core.cache import cache

from cms import settings
from cms.models import Page, Title, CMSPlugin
from cms.utils import get_language_from_request, get_page_from_request,\
    get_extended_navigation_nodes, find_children, cut_levels, find_selected
from django.core.mail import send_mail

register = template.Library()

def show_menu(context, from_level=0, to_level=100, extra_inactive=0, extra_active=100, next_page=None):
    """
    render a nested list of all children of the pages
    from_level: is the start level
    to_level: is the max level rendered
    render_children: if set to True will render all not direct ascendants too
    """
    request = context['request']
    site = request.site
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
            extenders = Page.objects.published().filter(in_navigation=True, 
                                                        sites__domain=site.domain, 
                                                        level__lte=to_level)
            extenders = extenders.exclude(navigation_extenders__isnull=True).exclude( navigation_extenders__exact="")
            for ext in extenders:
                ext.childrens = []
                ext.ancestors_ascending = []
                get_extended_navigation_nodes(request, 100, [ext], ext.level, 100, False)
                if hasattr(ext, "ancestor"):
                    alist = list(ext.get_ancestors().values_list('id', 'soft_root'))
                    alist = [(ext.pk, ext.soft_root)] + alist
                    break
        soft_root_filter = {}
        #check the ancestors for softroots
        for p in alist:
            ancestors.append(p[0])
            if p[1]:
                soft_root = Page.objects.get(pk=p[0])
                soft_root_filter['lft__gte'] = soft_root.lft
                soft_root_filter['rght__lte'] = soft_root.rght
                soft_root_filter['tree_id'] = soft_root.tree_id
                from_level = soft_root.level
        if current_page and current_page.soft_root: 
            soft_root_filter['tree_id'] = current_page.tree_id
            soft_root_filter['lft__gte'] = current_page.lft
            soft_root_filter['rght__lte'] = current_page.rght
            from_level = current_page.level
        pages = Page.objects.published().filter(in_navigation=True, 
                                                sites__domain=site.domain, 
                                                level__lte=to_level, 
                                                **soft_root_filter).order_by('tree_id', 
                                                                             'parent', 
                                                                             'lft')
        pages = list(pages)
        all_pages = pages[:]
        last = None
        for page in pages:# build the tree
            if page.level >= from_level:
                ids.append(page.pk)
            if page.level == 0:
                page.ancestors_ascending = []
                children.append(page)
                if current_page and page.pk == current_page.pk and current_page.soft_root:
                    page.soft_root = False #ugly hack for the recursive function
                if current_page:
                    pk = current_page.pk
                else:
                    pk = -1
                find_children(page, pages, extra_inactive+from_level, extra_active, ancestors, pk, request=request)
                if current_page and page.pk == current_page.pk and current_page.soft_root:
                    page.soft_root = True
        if from_level > 0:
            children = cut_levels(children, from_level)
        titles = list(Title.objects.filter(page__in=ids, language=lang))
        for page in all_pages:# add the title and slugs and some meta data
            for title in titles:
                if title.page_id == page.pk:
                    page.title_cache = title
                    titles.remove(title)
            if page.pk in ancestors:
                page.ancestor = True
            if current_page and page.parent_id == current_page.parent_id and not page.pk == current_page.pk:
                page.sibling = True
    else:
        #if current_page and next_page.childrens:
        children = next_page.childrens
        #else:
        #    children = []
    return locals()
show_menu = register.inclusion_tag('cms/menu.html', takes_context=True)(show_menu)



def show_sub_menu(context, levels=100):
    """Get the root page of the current page and 
    render a nested list of all root's children pages"""
    request = context['request']
    lang = get_language_from_request(request)
    site = request.site
    children = []
    page = request.current_page
    if page:
        root = page.get_root()
        pages = Page.objects.published().filter(in_navigation=True, 
                                                lft__gt=page.lft, 
                                                rght__lt=page.rght, 
                                                tree_id=page.tree_id, 
                                                level__lte=page.level+levels, 
                                                sites__domain=site.domain)
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
        for ext in extenders:
            ext.childrens = []
            ext.ancestors_ascending = []
            nodes = get_extended_navigation_nodes(request, 100, [ext], ext.level, levels, False)
            if hasattr(ext, "ancestor"):
                selected = find_selected(nodes)
                if selected:
                    children = selected.childrens
                    from_level = selected.level
                    to_level =  from_level+levels
                    extra_active = extra_inactive = levels
    return locals()
show_sub_menu = register.inclusion_tag('cms/sub_menu.html',
                                       takes_context=True)(show_sub_menu)

                                            
def show_admin_menu(context, page, no_children=False, level=None):
    """Render the admin table of pages"""
    request = context['request']
    site = request.site
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
    return locals()
show_admin_menu = register.inclusion_tag('admin/cms/page/menu.html',
                                         takes_context=True)(show_admin_menu)

def show_breadcrumb(context, start_level=0):
    request = context['request']
    page = request.current_page
    lang = get_language_from_request(request)
    if page:
        ancestors = list(page.get_ancestors())
        ancestors.append(page)
        ids = []
        for anc in ancestors:
            ids.append(anc.pk)
        titles = Title.objects.filter(pk__in=ids, language=lang)
        for anc in ancestors:
            for title in titles:
                if title.page_id == anc.pk:
                    anc.title_cache = title
    else:
        site = request.site
        ancestors = []
        extenders = Page.objects.published().filter(in_navigation=True, 
                                                    sites__domain=site.domain)
        extenders = extenders.exclude(navigation_extenders__isnull=True).exclude(navigation_extenders__exact="")
        for ext in extenders:
            ext.childrens = []
            ext.ancestors_ascending = []
            nodes = get_extended_navigation_nodes(request, 100, [ext], ext.level, 0, False)
            if hasattr(ext, "ancestor"):
                selected = find_selected(nodes)
                if selected:
                    ancestors = list(ext.get_ancestors()) + [ext]
                    ids = []
                    for anc in ancestors:
                        ids.append(anc.pk)
                    titles = Title.objects.filter(pk__in=ids, language=lang)
                    ancs = []
                    for anc in ancestors:
                        anc.ancestors_ascending = ancs[:]
                        ancs += [anc]
                        for title in titles:
                            if title.page_id == anc.pk:
                                anc.title_cache = title
                    ancestors = ancestors + selected.ancestors_ascending[1:] + [selected]
    return locals()
show_breadcrumb = register.inclusion_tag('cms/breadcrumb.html',
                                         takes_context=True)(show_breadcrumb)
                                         

def render_plugin(context, plugin_id):
    plugin = CMSPlugin.objects.get(pk=plugin_id)
    content = plugin.render(context)
    return  locals()
render_plugin = register.inclusion_tag('cms/plugin_base.html', takes_context=True)(render_plugin)

#def render_plugin_title(context, plugin_id):
    

def has_permission(page, request):
    return page.has_page_permission(request)
register.filter(has_permission)

#def show_content(context, content_type, lang=None):
#    """Display a content type from a page.
#    
#    eg: {% show_content page_object "title" %}
#    
#    You can also use the slug of a page
#    
#    eg: {% show_content "my-page-slug" "title" %}
#    
#    Keyword arguments:
#    page -- the page object
#    args -- content_type used by a placeholder
#    lang -- the wanted language (default None, use the request object to know)
#    """
#    page = get_page_from_request(context)
#    request = context.get('request', False)
#    if not request or not page:
#        return {'content':''}
#    # if the page is a SafeUnicode, try to use it like a slug
#    #if isinstance(page, SafeUnicode):
#    #    c = Content.objects.filter(type='slug', body=page)
#    #    if len(c):
#    #        page = c[0].page
#    #    else:
#    #        return {'content':''}
#    if lang is None:
#        lang = get_language_from_request(context['request'])
#    if hasattr(settings, 'CMS_CONTENT_CACHE_DURATION'):
#        key = 'content_cache_pid:'+str(page.id)+'_l:'+str(lang)+'_type:'+str(content_type)
#        c = cache.get(key)
#        if not c:
#            c = Content.objects.get_content(page, lang, content_type, True)
#            cache.set(key, c, settings.CMS_CONTENT_CACHE_DURATION)
#    else:
#        c = Content.objects.get_content(page, lang, content_type, True)
#    if c:
#        return {'content':c}
#    return {'content':''}
#show_content = register.inclusion_tag('cms/content.html',
#                                      takes_context=True)(show_content)

def page_url(context, reverse_id, lang=None):
    """Show the url of a page in the right language"""
    request = context.get('request', False)
    if not request:
        return {'content':''}
    if lang is None:
        lang = get_language_from_request(request)
    if hasattr(settings, 'CMS_CONTENT_CACHE_DURATION'):
        key = 'page_url_pid:'+reverse_id+'_l:'+str(lang)+'_type:absolute_url'
        url = cache.get(key)
        if not url:
            try:
                page = Page.objects.get(reverse_id=reverse_id)
            except:
                if settings.DEBUG:
                    raise
                else:
                    site = request.site
                    send_mail(_('Reverse ID not found on %(domain)s') % {'domain':site.domain},
                              _("A page_url template tag didn't found a page with the reverse_id %(reverse_id)s\nThe url of the page was: http://%(host)s%(path)s")%{'reverse_id':reverse_id, 'host':request.host, 'path':request.path},
                               settings.DEFAULT_FROM_EMAIL,
                               settings.MANAGERS, 
                               fail_silently=True)

            url = page.get_absolute_url(language=lang)
            cache.set(key, url, settings.CMS_CONTENT_CACHE_DURATION)
    else:
        url = page.get_absolute_url(language=lang)
    if url:
        return {'content':url}
    return {'content':''}
page_url = register.inclusion_tag('cms/content.html', takes_context=True)(page_url)

#def show_revisions(context, page, content_type, lang=None):
#    """Render the last 10 revisions of a page content with a list"""
#    if not settings.CMS_CONTENT_REVISION:
#        return {'revisions':None}
#    revisions = Content.objects.filter(page=page, language=lang,
#                                type=content_type).order_by('-creation_date')
#    if len(revisions) < 2:
#        return {'revisions':None}
#    return {'revisions':revisions[0:10]}
#
#show_revisions = register.inclusion_tag('cms/revisions.html',
#                                        takes_context=True)(show_revisions)

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
        self.name = name
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
        c = None
        if self.name.lower() == "title":
            t = Title.objects.get_title(page, l, True)
            if t:
                c = t.title
        elif self.name.lower() == "slug":
            t = Title.objects.get_title(page, l, True)
            if t:
                c = t.slug
        else:
            plugins = CMSPlugin.objects.filter(page=page, language=l, placeholder=self.name).order_by('position')
            c = ""
            for plugin in plugins:
                c += plugin.render(context)
                    
            
        if not c:
            return ''
        return '<div id="%s" class="placeholder">%s</div>' % (self.name, c)
        
    def __repr__(self):
        return "<Placeholder Node: %s>" % self.name

register.tag('placeholder', do_placeholder)
