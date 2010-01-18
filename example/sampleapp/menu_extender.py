from cms.utils.navigation import NavigationNode
from django.core.urlresolvers import reverse
from django.utils.translation import ugettext_lazy as _

def get_nodes(request):
    res = [] # result list
    lang = request.LANGUAGE_CODE
    n = NavigationNode(_('Sublevel'), reverse('%s:sample-app-sublevel' % lang))
    n2 = NavigationNode(_('Sublevel3'), reverse('%s:sample-app-sublevel3' % lang))
    n.childrens = [n2]
    res.append(n)
    n = NavigationNode(_('Sublevel 2'), reverse('%s:sample-app-sublevel2' % lang))
    res.append(n)
    return res


from categories.models import Category

def get_nodes(request):
    cats = list(Category.objects.all())
    res = []
    all_cats = cats[:]
    childs = []
    for cat in cats:
        if cat.parent_id:
            childs.append(cat)
        else:
            res.append(cat)
    for cat in all_cats:
        cat.childrens = []
        for child in childs:
            if child.parent_id == cat.pk:
                cat.childrens.append(child)
    return res