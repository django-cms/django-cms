
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
